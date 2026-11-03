"""Stratified manual-review sample of scored responses."""

from __future__ import annotations

import csv
import json
import random
from dataclasses import asdict
from pathlib import Path
from typing import Any

from notamper.cases.model import Case
from notamper.records import Response
from notamper.scoring.score import CaseScore

FIELDS = (
    "case_id", "model", "defense", "rep", "variant", "goal", "target", "auto_attack_success",
    "auto_utility", "auto_detected", "auto_empty", "stop_reason", "tool_calls",
    "response_text", "manual_attack_success", "manual_utility", "notes",
)
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def neutralise_cell(value: Any) -> Any:
    """Prefix string cells that a spreadsheet would read as a formula with a quote."""
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


def case_target(case: Case | None) -> str:
    """What the attack is after: the canary, the facts to omit, or the tool name."""
    if case is None or case.is_control:
        return ""
    if case.goal == "canary":
        return case.canary or "|".join(case.expect.contains_any)
    if case.goal == "suppress":
        return " || ".join(case.expect.missing_any)
    if case.goal == "tool":
        return case.expect.tool_called or ""
    return ""


def review_sample(
    scores: list[CaseScore],
    responses: list[Response],
    cases: list[Case],
    fraction: float = 0.1,
    seed: int = 0,
) -> list[dict]:
    """Draw ``fraction`` of non-error scores per model x defense (at least one each).

    Empty responses stay in the pool so reviewers can check the empty rule.
    """
    by_case = {c.id: c for c in cases}
    by_key = {(r.case_id, r.model, r.defense, r.rep): r for r in responses}
    strata: dict[tuple[str, str], list[CaseScore]] = {}
    for s in scores:
        if s.error or (s.case_id, s.model, s.defense, s.rep) not in by_key:
            continue
        strata.setdefault((s.model, s.defense), []).append(s)
    rng = random.Random(seed)
    rows: list[dict] = []
    for key in sorted(strata):
        items = sorted(strata[key], key=lambda s: (s.case_id, s.rep))
        k = min(len(items), max(1, round(fraction * len(items))))
        for s in sorted(rng.sample(items, k), key=lambda s: (s.case_id, s.rep)):
            r = by_key[(s.case_id, s.model, s.defense, s.rep)]
            rows.append({
                "case_id": s.case_id, "model": s.model, "defense": s.defense, "rep": s.rep,
                "variant": s.variant, "goal": s.goal, "target": case_target(by_case.get(s.case_id)),
                "auto_attack_success": s.attack_success, "auto_utility": s.utility,
                "auto_detected": s.detected, "auto_empty": s.empty,
                "stop_reason": r.stop_reason or "",
                "tool_calls": json.dumps([asdict(tc) for tc in r.tool_calls], ensure_ascii=False),
                "response_text": r.text,
                "manual_attack_success": "", "manual_utility": "", "notes": "",
            })
    return rows


def write_csv(rows: list[dict], path: str | Path) -> None:
    """Write sample rows as UTF-8 CSV with the fixed column order."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for row in rows:
            w.writerow({k: neutralise_cell(v) for k, v in row.items()})
