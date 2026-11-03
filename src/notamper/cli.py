"""Command-line interface: validate, generate, run, score, report, sample."""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

from notamper import __version__
from notamper.cases.corpus import corpus_errors
from notamper.cases.loader import CaseError, load_cases
from notamper.cases.model import Case
from notamper.generator import generate_corpus, write_corpus
from notamper.records import Response
from notamper.report.render import headline_markdown, render_html, render_markdown
from notamper.report.sample import review_sample, write_csv
from notamper.runner.adapters import AdapterError
from notamper.runner.budget import Budget
from notamper.runner.defenses import DEFENSES
from notamper.runner.run import run_benchmark
from notamper.scoring.score import CaseScore, score_responses, scores_to_jsonl


def _csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def select_cases(
    cases: list[Case], fmt: str | None, variant: str | None, limit: int | None
) -> list[Case]:
    """Apply filters, then ``limit``; attack/control pairs are always kept together."""
    by_id = {c.id: c for c in cases}

    def keep(c: Case) -> bool:
        if fmt and c.format != fmt:
            return False
        if variant:
            attack = by_id.get(c.control_of) if c.is_control and c.control_of else c
            return attack is not None and attack.variant == variant
        return True

    chosen = [c for c in cases if keep(c)]
    if limit is not None:
        head = chosen[:limit]
        ids = {c.id for c in head}
        pool = {c.id: c for c in chosen}
        for c in head:
            if c.is_control and c.control_of in pool:
                ids.add(c.control_of)
        for c in chosen:
            if c.control_of in ids:
                ids.add(c.id)
        chosen = [c for c in chosen if c.id in ids]
    return chosen


def sample_pairs(cases: list[Case], n: int, seed: int) -> list[Case]:
    """Deterministic stratified sample of ``n`` attack cases plus their controls.

    Strata are (format, variant, goal); each is sampled in proportion to its size, so a
    small sample keeps the corpus mix (including the aviation/generic balance).
    """
    rng = random.Random(seed)
    strata: dict[tuple[str, str, str], list[Case]] = {}
    for c in cases:
        if not c.is_control:
            strata.setdefault((c.format, c.variant, c.goal), []).append(c)
    keyed: list[tuple[float, str]] = []
    for key in sorted(strata):
        members = sorted(strata[key], key=lambda c: c.id)
        rng.shuffle(members)
        offset = rng.random()
        keyed += [((i + offset) / len(members), c.id) for i, c in enumerate(members)]
    ids = {cid for _, cid in sorted(keyed)[:n]}
    return [c for c in cases if c.id in ids or (c.is_control and c.control_of in ids)]


def _load_responses(run_dir: Path) -> list[Response]:
    path = run_dir / "responses.jsonl"
    with open(path, encoding="utf-8") as f:
        return [Response.from_dict(json.loads(line)) for line in f if line.strip()]


def _load_manifest(run_dir: Path) -> dict:
    return json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))


def _compute_scores(run_dir: Path, cases_dir: Path) -> list[CaseScore]:
    cases = load_cases(cases_dir)
    scores, warnings = score_responses(cases, _load_responses(run_dir))
    for w in warnings:
        _err(f"warning: {w}")
    scores_to_jsonl(scores, run_dir / "scores.jsonl")
    return scores


def cmd_validate(args: argparse.Namespace) -> int:
    cases = load_cases(Path(args.cases))
    errors = corpus_errors(cases)
    if errors:
        for e in errors:
            _err(e)
        return 1
    print(f"OK: {len(cases)} cases")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    cases = generate_corpus(args.seed)
    errors = corpus_errors(cases)
    if errors:
        for e in errors:
            _err(e)
        return 1
    n = write_corpus(cases, Path(args.out))
    print(f"Wrote {n} cases to {args.out}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    models = _csv(args.models)
    defenses = _csv(args.defenses)
    unknown = [d for d in defenses if d not in DEFENSES]
    if unknown:
        _err(f"unknown defense(s): {', '.join(unknown)} (choose from {', '.join(DEFENSES)})")
        return 1
    if args.reps < 1:
        _err("error: --reps must be >= 1")
        return 1
    if args.limit is not None and args.limit < 1:
        _err("error: --limit must be >= 1")
        return 1
    if args.sample is not None and (args.sample < 1 or args.limit is not None):
        _err("error: --sample must be >= 1 and cannot be combined with --limit")
        return 1
    if args.max_tokens < 1:
        _err("error: --max-tokens must be >= 1")
        return 1
    cases = select_cases(
        load_cases(Path(args.cases)), args.filter_format, args.filter_variant, args.limit
    )
    if args.sample is not None:
        cases = sample_pairs(cases, args.sample, args.seed)
    if not cases:
        _err("no cases selected")
        return 1
    out = Path(args.out) if args.out else Path(
        "results") / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def progress(done: int, total: int) -> None:
        # at most ~20 lines per run (every 5 %), on stderr
        if done == total or done * 20 // total != (done - 1) * 20 // total:
            _err(f"progress: {done}/{total}")

    try:
        manifest = run_benchmark(
            cases, models, defenses, args.reps, out,
            budget=Budget(args.max_calls, args.max_usd),
            temperature=args.temperature, seed=args.seed, max_tokens=args.max_tokens,
            progress=progress,
        )
    except AdapterError as exc:
        _err(f"error: {exc}")
        return 1
    if manifest["stopped_reason"] == "budget":
        _err("warning: budget reached; run stopped early (partial results written)")
    elif manifest["stopped_reason"] == "errors":
        _err("error: too many failed calls in a row; run stopped (partial results written)")
        _err(f"last error: {manifest['last_error']}")
    print(f"Run directory: {out}")
    for key in ("cases", "calls", "errors", "spent_usd_estimate", "stopped_reason"):
        print(f"  {key}: {manifest[key]}")
    return 1 if manifest["stopped_reason"] == "errors" else 0


def cmd_score(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    scores = _compute_scores(run_dir, Path(args.cases))
    manifest_path = run_dir / "manifest.json"
    manifest = _load_manifest(run_dir) if manifest_path.exists() else None
    print(headline_markdown(scores, manifest))
    print(f"Wrote {run_dir / 'scores.jsonl'}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    manifest = _load_manifest(run_dir)
    scores = _compute_scores(run_dir, Path(args.cases))  # always rescore; rewrites scores.jsonl
    (run_dir / "report.md").write_text(render_markdown(manifest, scores), encoding="utf-8")
    (run_dir / "report.html").write_text(render_html(manifest, scores), encoding="utf-8")
    print(f"Wrote {run_dir / 'report.md'} and {run_dir / 'report.html'}")
    return 0


def cmd_sample(args: argparse.Namespace) -> int:
    if not 0 < args.fraction <= 1:
        _err("error: --fraction must be in (0, 1]")
        return 1
    run_dir = Path(args.run_dir)
    cases = load_cases(Path(args.cases))
    responses = _load_responses(run_dir)
    scores, _ = score_responses(cases, responses)  # never trust a possibly stale scores.jsonl
    rows = review_sample(scores, responses, cases, args.fraction, args.seed)
    write_csv(rows, run_dir / "review_sample.csv")
    print(f"Wrote {len(rows)} rows to {run_dir / 'review_sample.csv'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="notamper", description="Prompt-injection benchmark for aviation text formats."
    )
    p.add_argument("--version", action="version", version=f"notamper {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="validate a case corpus")
    v.add_argument("--cases", default="cases")
    v.set_defaults(func=cmd_validate)

    g = sub.add_parser("generate", help="generate the corpus")
    g.add_argument("--out", default="cases/generated")
    g.add_argument("--seed", type=int, default=2026)
    g.set_defaults(func=cmd_generate)

    r = sub.add_parser("run", help="run the benchmark")
    r.add_argument("--models", required=True, help="comma-separated provider:model specs")
    r.add_argument("--defenses", default="none", help=f"comma-separated of {','.join(DEFENSES)}")
    r.add_argument("--reps", type=int, default=3)
    r.add_argument("--cases", default="cases")
    r.add_argument("--filter-format")
    r.add_argument("--filter-variant")
    r.add_argument("--limit", type=int, help="first N cases (quick checks; not representative)")
    r.add_argument(
        "--sample", type=int,
        help="N attack cases plus controls, stratified by format/variant/goal (uses --seed)",
    )
    r.add_argument("--max-calls", type=int)
    r.add_argument("--max-usd", type=float)
    r.add_argument("--max-tokens", type=int, default=1024)
    r.add_argument("--temperature", type=float, default=0.0)
    r.add_argument("--seed", type=int, default=1234)
    r.add_argument("--out", help="default: results/<UTC timestamp>")
    r.set_defaults(func=cmd_run)

    for name, func, help_ in (
        ("score", cmd_score, "score a run"),
        ("report", cmd_report, "write report.md and report.html"),
        ("sample", cmd_sample, "export a manual-review CSV"),
    ):
        s = sub.add_parser(name, help=help_)
        s.add_argument("run_dir")
        s.add_argument("--cases", default="cases")
        if name == "sample":
            s.add_argument("--fraction", type=float, default=0.1)
            s.add_argument("--seed", type=int, default=0)
        s.set_defaults(func=func)
    return p


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; returns the process exit code."""
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (CaseError, FileNotFoundError, NotADirectoryError, ValueError) as exc:
        _err(f"error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
