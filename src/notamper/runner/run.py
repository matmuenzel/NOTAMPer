"""Run orchestration: build prompts, call adapters, cache, budget, write outputs."""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from notamper import __version__
from notamper.cases.model import Case
from notamper.records import Response
from notamper.runner.adapters import AdapterError, get_adapter
from notamper.runner.budget import Budget, BudgetExceeded
from notamper.runner.cache import ResponseCache, cache_key
from notamper.runner.defenses import DEFENSES, apply_approval
from notamper.runner.prompts import build_prompt
from notamper.runner.tools import DummyToolLog

# Fresh calls that fail in a row before the run stops (bad key, no network, missing certs).
MAX_CONSECUTIVE_ERRORS = 10


def corpus_hash(cases: list[Case]) -> str:
    """SHA-256 over the sorted content hashes of the selected cases."""
    blob = "\n".join(sorted(c.content_hash() for c in cases))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def run_benchmark(
    cases: list[Case],
    models: list[str],
    defenses: list[str],
    reps: int,
    out_dir: Path,
    *,
    budget: Budget,
    temperature: float = 0.0,
    seed: int = 1234,
    max_tokens: int = 1024,
    adapter_factory: Callable = get_adapter,
    progress: Callable[[int, int], None] | None = None,
) -> dict:
    """Run every (model, defense, case, rep); write manifest, responses and tool log.

    Work order is case, repetition, model, defense, so a budget stop leaves every model x
    defense cell with the same (case, rep) prefix. Successful responses are cached in
    ``out_dir/cache.jsonl``; errored calls are NOT cached, so a restart retries them.
    ``manifest["calls"]`` counts only calls made in this invocation, ``calls_total`` all
    cached responses.
    """
    for d in defenses:
        if d not in DEFENSES:
            raise ValueError(f"unknown defense: {d}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    cache = ResponseCache(out_dir / "cache.jsonl")
    adapters = {m: adapter_factory(m) for m in models}  # fail fast on missing keys
    total = len(models) * len(defenses) * len(cases) * reps
    responses: list[Response] = []
    stopped = "complete"
    consecutive_errors = 0

    def work():
        for case in cases:
            for rep in range(reps):
                for model in models:
                    for defense in defenses:
                        yield model, defense, case, rep

    for model, defense, case, rep in work():
        adapter = adapters[model]
        eff_seed = seed + rep if adapter.supports_seed else None
        prompt, filtered = build_prompt(case, defense, str(seed))
        key = cache_key(model, defense, case, rep, temperature, eff_seed, max_tokens, prompt)
        resp = cache.get(key)
        if resp is None:
            try:
                budget.check()
            except BudgetExceeded:
                stopped = "budget"
                break
            t0 = time.monotonic()
            try:
                comp = adapter.complete(
                    prompt, temperature=temperature, seed=eff_seed, max_tokens=max_tokens
                )
            except AdapterError as exc:
                budget.charge(model, 0, 0)
                resp = Response(
                    case.id, model, defense, rep, "", error=str(exc), filtered=filtered,
                    latency_s=time.monotonic() - t0,
                )
            except Exception as exc:  # noqa: BLE001 - last resort: never crash the whole run
                budget.charge(model, 0, 0)
                resp = Response(
                    case.id, model, defense, rep, "",
                    error=f"internal: {type(exc).__name__}: {str(exc)[:200]}",
                    filtered=filtered, latency_s=time.monotonic() - t0,
                )
            else:
                budget.charge(model, comp.input_tokens, comp.output_tokens)
                calls = comp.tool_calls
                if defense == "approval":
                    calls = apply_approval(calls)
                resp = Response(
                    case.id, model, defense, rep, comp.text, calls,
                    comp.input_tokens, comp.output_tokens, None, filtered,
                    time.monotonic() - t0, comp.stop_reason,
                )
                cache.put(key, resp)
            consecutive_errors = consecutive_errors + 1 if resp.error else 0
        responses.append(resp)
        if progress:
            progress(len(responses), total)
        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            stopped = "errors"
            break

    # Rewrite outputs from the full ordered result so restarts never duplicate lines.
    with (out_dir / "responses.jsonl").open("w", encoding="utf-8") as fh:
        for r in responses:
            fh.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
    tool_path = out_dir / "tool_log.jsonl"
    tool_path.unlink(missing_ok=True)
    tool_path.touch()
    log = DummyToolLog(tool_path)
    for r in responses:
        for call in r.tool_calls:
            log.record(r.case_id, r.model, r.defense, r.rep, call)

    manifest = {
        "notamper_version": __version__,
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "models": models,
        "defenses": defenses,
        "reps": reps,
        "temperature": temperature,
        "seed": seed,
        "max_tokens": max_tokens,
        "model_notes": {
            m: {"temperature_applied": bool(getattr(adapters[m], "temperature_applied", True))}
            for m in models
        },
        "cases": len(cases),
        "n_selected_cases": len(cases),
        "corpus_sha256": corpus_hash(cases),
        "stopped_reason": stopped,
        "calls": budget.calls,
        "calls_total": len(cache),
        "spent_usd_estimate": round(budget.spent_usd, 6),
        "errors": sum(1 for r in responses if r.error),
        "last_error": next((r.error for r in reversed(responses) if r.error), None),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
