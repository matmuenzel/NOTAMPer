import csv
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from notamper.cases.loader import load_cases
from notamper.cli import main, sample_pairs
from notamper.records import Response
from notamper.report.render import fmt_interval, render_html, render_markdown
from notamper.report.sample import review_sample, write_csv
from notamper.scoring.score import load_scores, score_responses

ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT / "cases"


@pytest.fixture(scope="module")
def run_dir(tmp_path_factory):
    out = tmp_path_factory.mktemp("run")
    rc = main([
        "run", "--models", "mock:naive,mock:robust", "--defenses", "none,filter",
        "--reps", "1", "--limit", "20", "--cases", str(CASES_DIR), "--out", str(out),
    ])
    assert rc == 0
    return out


def test_run_score_report_sample(run_dir, capsys):
    assert main(["score", str(run_dir), "--cases", str(CASES_DIR)]) == 0
    scores = load_scores(run_dir / "scores.jsonl")
    assert scores
    asr = {}
    for m in ("mock:naive", "mock:robust"):
        att = [s for s in scores if s.model == m and s.defense == "none" and not s.is_control]
        asr[m] = sum(bool(s.attack_success) for s in att) / len(att)
    assert asr["mock:naive"] > asr["mock:robust"]

    assert main(["report", str(run_dir), "--cases", str(CASES_DIR)]) == 0
    page = (run_dir / "report.html").read_text()
    assert not re.findall(r'(?:src|href)\s*=\s*["\']?\s*https?:', page, flags=re.I)
    assert "http" not in page
    assert "<script" not in page
    assert "Not for operational use" in page
    md = (run_dir / "report.md").read_text()
    assert "mock:naive" in md and "Domain comparison" in md

    assert main(["sample", str(run_dir), "--fraction", "0.2"]) == 0
    with open(run_dir / "review_sample.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) >= 4
    assert {(r["model"], r["defense"]) for r in rows} == {
        (m, d) for m in ("mock:naive", "mock:robust") for d in ("none", "filter")
    }
    assert rows[0]["manual_attack_success"] == ""


def test_limit_keeps_pairs(run_dir):
    cases = {c.id: c for c in load_cases(CASES_DIR)}
    ids = {json.loads(line)["case_id"] for line in
           (run_dir / "responses.jsonl").read_text().splitlines()}
    for cid in ids:
        c = cases[cid]
        if c.is_control:
            assert c.control_of in ids
        else:
            assert any(o.control_of == cid for o in map(cases.get, ids))


def test_html_escapes_and_nan():
    cases = load_cases(CASES_DIR)[:1]
    c = cases[0]
    r = Response(c.id, "<b>m</b>", "none", 0, "<script>alert(1)</script>")
    scores, _ = score_responses(cases, [r])
    manifest = {"models": ["<i>x</i>"], "defenses": ["none"], "started_at": "2026-01-01"}
    page = render_html(manifest, scores)
    assert "<script" not in page
    assert "&lt;i&gt;x&lt;/i&gt;" in page and "&lt;b&gt;m&lt;/b&gt;" in page
    assert "–" in page
    rows = review_sample(scores, [r], cases, 0.5)
    assert rows[0]["response_text"] == "<script>alert(1)</script>"
    assert "Not for operational use" in render_markdown(manifest, scores)


def test_fmt_interval():
    assert fmt_interval((0.42, 0.351, 0.492)) == "42.0 % [35.1–49.2]"
    assert fmt_interval((float("nan"),) * 3) == "–"


def test_write_csv_empty(tmp_path):
    write_csv([], tmp_path / "x.csv")
    assert (tmp_path / "x.csv").read_text().startswith("case_id,")


def test_validate_ok_and_broken(tmp_path, capsys):
    assert main(["validate", "--cases", str(CASES_DIR)]) == 0
    assert capsys.readouterr().out.startswith("OK: ")
    bad = tmp_path / "bad.yaml"
    bad.write_text("id: [unclosed\n")
    assert main(["validate", "--cases", str(tmp_path)]) == 1
    assert "bad.yaml" in capsys.readouterr().err


def test_missing_dir_clean_error(tmp_path, capsys):
    assert main(["score", str(tmp_path / "nope")]) == 1
    assert "Traceback" not in capsys.readouterr().err


def test_missing_api_key(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    rc = main(["run", "--models", "openai:gpt-4o", "--cases", str(CASES_DIR),
               "--limit", "2", "--out", str(tmp_path / "o")])
    assert rc == 1
    assert "OPENAI_API_KEY" in capsys.readouterr().err


def test_budget_stop_exit_zero(tmp_path, capsys):
    rc = main(["run", "--models", "mock:naive", "--defenses", "none", "--reps", "1",
               "--limit", "6", "--max-calls", "2", "--cases", str(CASES_DIR),
               "--out", str(tmp_path / "o")])
    assert rc == 0
    assert "budget" in capsys.readouterr().err.lower()


def test_generate(tmp_path, capsys):
    assert main(["generate", "--out", str(tmp_path / "g")]) == 0
    assert list((tmp_path / "g").rglob("*.yaml"))


def test_version_and_module(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0
    assert "0.1.0" in capsys.readouterr().out
    out = subprocess.run([sys.executable, "-m", "notamper", "--version"],
                         capture_output=True, text=True)
    assert out.returncode == 0 and "0.1.0" in out.stdout


def test_ordering_and_observations(run_dir):
    scores = load_scores(run_dir / "scores.jsonl")
    manifest = {"models": ["mock:robust", "mock:naive"], "defenses": ["none", "filter"]}
    md = render_markdown(manifest, scores)
    assert "Key observations" in md
    assert "lowest ASR with defense" in md
    head = md.split("### Headline")[1].split("### ASR by goal")[0]
    order = [ln.split("|")[1:3] for ln in head.splitlines() if ln.startswith("| mock")]
    assert [(m.strip(), d.strip()) for m, d in order] == [
        ("mock:robust", "none"), ("mock:robust", "filter"),
        ("mock:naive", "none"), ("mock:naive", "filter"),
    ]
    fmts = [ln.split("|")[3].strip() for ln in md.split("### ASR by format")[1]
            .split("### ASR by variant")[0].splitlines()
            if ln.startswith("| mock:robust | none")]
    canon = ["notam", "metar", "atis", "generic"]
    assert fmts == sorted(fmts, key=canon.index)
    assert "<li>" in render_html(manifest, scores)


def test_csv_formula_injection_neutralised_and_columns(tmp_path):
    cases = load_cases(CASES_DIR)
    attack = next(c for c in cases if c.goal == "canary" and not c.is_control)
    tool = next(c for c in cases if c.goal == "tool" and not c.is_control)
    sup = next(c for c in cases if c.goal == "suppress" and not c.is_control)
    from notamper.records import ToolCall
    resps = [
        Response(attack.id, "=cmd|' /C calc'!A0", "none", 0, '=HYPERLINK("http://x","y")',
                 stop_reason="stop"),
        Response(tool.id, "m", "none", 0, "-2+3", [ToolCall("send_report", {"body": "@x"})]),
        Response(sup.id, "m", "none", 0, "+ok\tx"),
        Response(sup.id, "m", "none", 1, "   "),
    ]
    scores, _ = score_responses(cases, resps)
    rows = review_sample(scores, resps, cases, 1.0)
    path = tmp_path / "s.csv"
    write_csv(rows, path)
    with open(path, encoding="utf-8", newline="") as f:
        out = {(r["case_id"], r["rep"]): r for r in csv.DictReader(f)}
    a = out[(attack.id, "0")]
    assert a["response_text"] == "'=HYPERLINK(\"http://x\",\"y\")"
    assert a["model"].startswith("'=")
    assert a["target"] == attack.canary and a["stop_reason"] == "stop"
    t = out[(tool.id, "0")]
    assert t["target"] == "send_report" and t["response_text"] == "'-2+3"
    assert json.loads(t["tool_calls"])[0]["name"] == "send_report"
    assert out[(sup.id, "0")]["response_text"].startswith("'+ok")
    assert out[(sup.id, "0")]["target"] == " || ".join(sup.expect.missing_any)
    e = out[(sup.id, "1")]
    assert e["auto_empty"] == "True" and e["auto_attack_success"] == ""
    assert {"auto_detected", "auto_empty", "stop_reason", "tool_calls", "target"} <= set(a)


def test_report_always_rescores(tmp_path):
    out = tmp_path / "r"
    assert main(["run", "--models", "mock:naive", "--defenses", "none", "--reps", "1",
                 "--limit", "6", "--cases", str(CASES_DIR), "--out", str(out)]) == 0
    (out / "scores.jsonl").write_text("garbage that is stale\n")
    assert main(["report", str(out), "--cases", str(CASES_DIR)]) == 0
    assert load_scores(out / "scores.jsonl")  # rewritten from responses.jsonl
    assert "Headline" in (out / "report.md").read_text()


@pytest.mark.parametrize("extra", [["--reps", "0"], ["--limit", "0"], ["--max-tokens", "0"]])
def test_run_cli_validation(tmp_path, capsys, extra):
    rc = main(["run", "--models", "mock:naive", "--cases", str(CASES_DIR),
               "--out", str(tmp_path / "o"), *extra])
    assert rc == 1 and "error:" in capsys.readouterr().err


@pytest.mark.parametrize("frac", ["0", "-1", "1.5"])
def test_sample_fraction_validation(run_dir, capsys, frac):
    assert main(["sample", str(run_dir), "--fraction", frac]) == 1
    assert "--fraction" in capsys.readouterr().err


def test_progress_is_limited(tmp_path, capsys):
    rc = main(["run", "--models", "mock:naive", "--defenses", "none,guard", "--reps", "2",
               "--limit", "30", "--cases", str(CASES_DIR), "--out", str(tmp_path / "o")])
    assert rc == 0
    lines = [ln for ln in capsys.readouterr().err.splitlines() if ln.startswith("progress")]
    assert 1 < len(lines) <= 21


def test_generate_refuses_cases_root(capsys):
    assert main(["generate", "--out", str(CASES_DIR)]) == 1
    assert "handwritten" in capsys.readouterr().err


def test_canary_pattern_enforced():
    from notamper.cases.loader import CaseError, case_from_dict

    d = {"id": "x", "format": "notam", "variant": "V1", "goal": "canary", "task": "summarize",
         "canary": "bad-1", "documents": ["d"], "expect": {"utility_requires": ["a"]}}
    with pytest.raises(CaseError):
        case_from_dict(d)
    d["canary"] = "MOOSE-5342"
    assert case_from_dict(d).canary == "MOOSE-5342"


def _score(model, defense, cid, rep=0, **kw):
    from notamper.scoring.score import CaseScore

    base = dict(case_id=cid, model=model, defense=defense, rep=rep, format="notam",
                variant="V1", goal="canary", task="summarize", is_control=False,
                attack_success=True, utility=True, detected=False, error=False)
    base.update(kw)
    return CaseScore(**base)


def test_partial_run_is_balanced_with_banner():
    scores = [_score(m, d, c) for m in ("a", "b") for d in ("none", "guard") for c in ("1", "2")]
    scores.append(_score("a", "none", "3"))  # only one cell got case 3 before the stop
    manifest = {"models": ["a", "b"], "defenses": ["none", "guard"], "stopped_reason": "budget"}
    md = render_markdown(manifest, scores)
    assert "run stopped early" in md and "1 scored responses were dropped" in md
    assert "Scored responses: 9 (8 used)" in md
    assert "run stopped early" not in render_markdown({**manifest, "stopped_reason": "complete"},
                                                      scores[:-1])
    assert "run stopped early" in render_html(manifest, scores)


def test_report_contents_goal_stop_reasons_empty_and_tests():
    scores = []
    for i in range(20):
        scores.append(_score("m", "none", f"a{i}", format="notam", attack_success=i < 10,
                             stop_reason="end_turn" if i else "max_tokens"))
        scores.append(_score("m", "none", f"g{i}", format="generic", attack_success=i < 10))
    scores.append(_score("m", "none", "e", empty=True, attack_success=None, utility=None,
                         detected=None))
    manifest = {"models": ["m"], "defenses": ["none"], "stopped_reason": "complete",
                "max_tokens": 1024, "corpus_sha256": "ab" * 32, "calls_total": 41,
                "model_notes": {"m": {"temperature_applied": False}}}
    md = render_markdown(manifest, scores)
    assert "### ASR by goal" in md and "end_turn: 19, max_tokens: 1" in md
    assert "n empty" in md and "Tool attempt" in md and "False alarm" in md
    assert "Omission (control)" in md and "n = unique cases" in md
    assert "p = 1.00, not significant at α=0.05" in md
    assert "all variants equal" not in md  # single variant only
    assert "Temperature not applied:** m" in md and "Max tokens:** 1024" in md
    html_page = render_html(manifest, scores)
    assert "ASR by goal" in html_page and "Stop reasons by model" in html_page
    # significant difference
    scores2 = [_score("m", "none", f"a{i}", attack_success=True) for i in range(20)]
    scores2 += [_score("m", "none", f"g{i}", format="generic", attack_success=False)
                for i in range(20)]
    assert "significant at α=0.05" in render_markdown(manifest, scores2)
    assert "not significant" not in render_markdown(manifest, scores2)


def test_all_variants_tie_statement():
    scores = []
    for v in ("V1", "V2"):
        scores += [_score("m", "none", f"{v}{i}", variant=v, attack_success=i < 2)
                   for i in range(4)]
    md = render_markdown({"models": ["m"]}, scores)
    assert "all variants equal (50.0 %)" in md


def test_sample_is_stratified_paired_and_deterministic():
    cases = load_cases(CASES_DIR)
    chosen = sample_pairs(cases, 120, seed=7)
    attacks = [c for c in chosen if not c.is_control]
    assert len(attacks) == 120 and len(chosen) == 240
    ids = {c.id for c in chosen}
    assert all(c.id + "-ctl" in ids for c in attacks)
    generic = sum(c.format == "generic" for c in attacks)
    assert 45 <= generic <= 75  # corpus is half generic
    assert {c.variant for c in attacks} == {f"V{i}" for i in range(1, 9)}
    assert {c.goal for c in attacks} == {"canary", "suppress", "tool"}
    assert sample_pairs(cases, 120, seed=7) == chosen
    assert sample_pairs(cases, 120, seed=8) != chosen


def test_sample_rejects_limit(tmp_path, capsys):
    rc = main(["run", "--models", "mock:naive", "--sample", "5", "--limit", "5",
               "--out", str(tmp_path / "r")])
    assert rc == 1 and "--sample" in capsys.readouterr().err
