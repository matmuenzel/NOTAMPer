import json
from pathlib import Path

from notamper.cases.loader import load_cases
from notamper.runner.adapters import AdapterError, Completion, get_adapter
from notamper.runner.budget import Budget
from notamper.runner.run import MAX_CONSECUTIVE_ERRORS, run_benchmark

CASES = load_cases(Path(__file__).resolve().parent.parent / "cases")
SUBSET = [c for c in CASES if c.variant in ("V0", "V8")][:12]


class Counting:
    def __init__(self):
        self.calls = 0

    def __call__(self, spec):
        inner = get_adapter(spec)
        outer = self

        class A:
            model_id = inner.model_id
            supports_seed = inner.supports_seed

            def complete(self, *a, **k):
                outer.calls += 1
                return inner.complete(*a, **k)

        return A()


def lines(p):
    return (p).read_text().splitlines()


def test_run_and_resume(tmp_path):
    factory = Counting()
    m = run_benchmark(
        SUBSET, ["mock:naive", "mock:robust"], ["none", "approval"], 2, tmp_path,
        budget=Budget(None, None), adapter_factory=factory,
    )
    n = len(SUBSET) * 2 * 2 * 2
    assert m["stopped_reason"] == "complete" and m["calls"] == n == factory.calls
    assert len(lines(tmp_path / "responses.jsonl")) == n
    assert m["errors"] == 0 and m["cases"] == len(SUBSET) and m["seed"] == 1234
    assert json.loads((tmp_path / "manifest.json").read_text()) == m
    for key in ("notamper_version", "started_at", "finished_at", "spent_usd_estimate"):
        assert key in m

    tools_before = lines(tmp_path / "tool_log.jsonl")
    factory2 = Counting()
    m2 = run_benchmark(
        SUBSET, ["mock:naive", "mock:robust"], ["none", "approval"], 2, tmp_path,
        budget=Budget(None, None), adapter_factory=factory2,
    )
    assert factory2.calls == 0 and m2["calls"] == 0
    assert len(lines(tmp_path / "responses.jsonl")) == n
    assert lines(tmp_path / "tool_log.jsonl") == tools_before


def test_approval_applied_and_logged(tmp_path):
    tool_cases = [c for c in CASES if c.goal == "tool" and c.variant == "V8"][:2]
    run_benchmark(tool_cases, ["mock:naive"], ["none", "approval"], 1, tmp_path,
                  budget=Budget(None, None))
    rows = [json.loads(ln) for ln in lines(tmp_path / "responses.jsonl")]
    by_def = {r["defense"]: r for r in rows}
    assert by_def["none"]["tool_calls"][0]["executed"] is True
    assert by_def["approval"]["tool_calls"][0]["executed"] is False
    assert len(lines(tmp_path / "tool_log.jsonl")) == 4


def test_budget_stop(tmp_path):
    m = run_benchmark(SUBSET, ["mock:naive"], ["none"], 1, tmp_path, budget=Budget(3, None))
    assert m["stopped_reason"] == "budget" and m["calls"] == 3
    assert len(lines(tmp_path / "responses.jsonl")) == 3
    # a later run with more budget resumes from the cache
    factory = Counting()
    m2 = run_benchmark(SUBSET, ["mock:naive"], ["none"], 1, tmp_path,
                       budget=Budget(None, None), adapter_factory=factory)
    assert m2["stopped_reason"] == "complete" and factory.calls == len(SUBSET) - 3
    assert len(lines(tmp_path / "responses.jsonl")) == len(SUBSET)


def test_adapter_error_recorded(tmp_path):
    class Failing:
        model_id = "x"
        supports_seed = False

        def complete(self, *a, **k):
            raise AdapterError("HTTP 500: down")

    m = run_benchmark(SUBSET[:2], ["x"], ["none"], 1, tmp_path, budget=Budget(None, None),
                      adapter_factory=lambda s: Failing())
    rows = [json.loads(ln) for ln in lines(tmp_path / "responses.jsonl")]
    assert m["errors"] == 2 and all(r["error"] == "HTTP 500: down" for r in rows)


def test_seed_per_rep(tmp_path):
    seen = []

    class A:
        model_id = "s"
        supports_seed = True

        def complete(self, prompt, *, temperature, seed, max_tokens):
            seen.append(seed)
            return Completion("t", [], 1, 1)

    run_benchmark(SUBSET[:1], ["s"], ["none"], 3, tmp_path, budget=Budget(None, None),
                  seed=100, adapter_factory=lambda s: A())
    assert seen == [100, 101, 102]


def test_progress(tmp_path):
    ticks = []
    run_benchmark(SUBSET[:2], ["mock:robust"], ["none"], 1, tmp_path, budget=Budget(None, None),
                  progress=lambda d, t: ticks.append((d, t)))
    assert ticks == [(1, 2), (2, 2)]


def test_unexpected_exception_recorded(tmp_path):
    class Broken:
        model_id = "b"
        supports_seed = False

        def complete(self, *a, **k):
            raise RuntimeError("x" * 500)

    m = run_benchmark(SUBSET[:2], ["b"], ["none"], 1, tmp_path, budget=Budget(None, None),
                      adapter_factory=lambda s: Broken())
    rows = [json.loads(ln) for ln in lines(tmp_path / "responses.jsonl")]
    assert m["errors"] == 2 and rows[0]["error"].startswith("internal: RuntimeError: ")
    assert len(rows[0]["error"]) < 250


def test_run_order_is_case_rep_model_defense(tmp_path):
    m = run_benchmark(SUBSET[:2], ["mock:naive", "mock:robust"], ["none", "guard"], 2, tmp_path,
                      budget=Budget(None, None))
    rows = [json.loads(ln) for ln in lines(tmp_path / "responses.jsonl")]
    keys = [(r["case_id"], r["rep"], r["model"], r["defense"]) for r in rows]
    expected = [(c.id, rep, mo, d) for c in SUBSET[:2] for rep in range(2)
                for mo in ("mock:naive", "mock:robust") for d in ("none", "guard")]
    assert keys == expected and m["calls"] == 16


def test_budget_stop_leaves_comparable_cells(tmp_path):
    m = run_benchmark(SUBSET, ["mock:naive", "mock:robust"], ["none", "guard"], 1, tmp_path,
                      budget=Budget(8, None))
    assert m["stopped_reason"] == "budget"
    rows = [json.loads(ln) for ln in lines(tmp_path / "responses.jsonl")]
    cells = {}
    for r in rows:
        cells.setdefault((r["model"], r["defense"]), set()).add(r["case_id"])
    assert len(cells) == 4 and len({frozenset(v) for v in cells.values()}) == 1


def test_manifest_fields(tmp_path):
    m = run_benchmark(SUBSET[:3], ["mock:naive"], ["none"], 1, tmp_path, budget=Budget(None, None),
                      max_tokens=321)
    assert m["max_tokens"] == 321 and m["n_selected_cases"] == 3
    assert len(m["corpus_sha256"]) == 64 and m["calls_total"] == 3
    assert m["model_notes"] == {"mock:naive": {"temperature_applied": False}}
    again = run_benchmark(SUBSET[:3][::-1], ["mock:naive"], ["none"], 1, tmp_path,
                          budget=Budget(None, None), max_tokens=321)
    assert again["corpus_sha256"] == m["corpus_sha256"]  # order independent
    assert again["calls"] == 0 and again["calls_total"] == 3
    other = run_benchmark(SUBSET[:2], ["mock:naive"], ["none"], 1, tmp_path / "o",
                          budget=Budget(None, None))
    assert other["corpus_sha256"] != m["corpus_sha256"]
    assert other["max_tokens"] == 1024


def test_stop_reason_stored(tmp_path):
    class A:
        model_id = "s"
        supports_seed = False

        def complete(self, prompt, *, temperature, seed, max_tokens):
            return Completion("t", [], 1, 1, "max_tokens")

    run_benchmark(SUBSET[:1], ["s"], ["none"], 1, tmp_path, budget=Budget(None, None),
                  adapter_factory=lambda s: A())
    assert json.loads(lines(tmp_path / "responses.jsonl")[0])["stop_reason"] == "max_tokens"


def test_stops_after_consecutive_errors(tmp_path):
    class Failing:
        model_id = "x"
        supports_seed = False

        def __init__(self):
            self.calls = 0

        def complete(self, *a, **k):
            self.calls += 1
            raise AdapterError("network error: down")

    failing = Failing()
    m = run_benchmark(SUBSET, ["x"], ["none"], 1, tmp_path, budget=Budget(None, None),
                      adapter_factory=lambda s: failing)
    assert failing.calls == MAX_CONSECUTIVE_ERRORS < len(SUBSET)
    assert m["stopped_reason"] == "errors" and m["last_error"] == "network error: down"


def test_success_resets_error_streak(tmp_path):
    naive = get_adapter("mock:naive")

    class Flaky:
        model_id = "x"
        supports_seed = False
        calls = 0

        def complete(self, *a, **k):
            Flaky.calls += 1
            if Flaky.calls % MAX_CONSECUTIVE_ERRORS == 0:
                return naive.complete(*a, **k)
            raise AdapterError("HTTP 500: down")

    cases = [c for c in CASES if c.variant in ("V0", "V8")][: 2 * MAX_CONSECUTIVE_ERRORS]
    m = run_benchmark(cases, ["x"], ["none"], 1, tmp_path, budget=Budget(None, None),
                      adapter_factory=lambda s: Flaky())
    assert m["stopped_reason"] == "complete" and m["calls"] == len(cases)
