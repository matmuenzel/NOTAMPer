"""Corpus-level invariant checks."""

from __future__ import annotations

from collections import Counter

from notamper.cases.formats import validate_document
from notamper.cases.model import Case
from notamper.textnorm import contains_term, normalize


def corpus_errors(cases: list[Case]) -> list[str]:
    """Return all invariant violations across a list of cases (empty = consistent)."""
    errors: list[str] = []
    by_id = {c.id: c for c in cases}
    for cid, n in sorted(Counter(c.id for c in cases).items()):
        if n > 1:
            errors.append(f"{cid}: duplicate id")

    controls_of: Counter[str] = Counter()
    for c in cases:
        if c.control_of and c.control_of in by_id and c.is_control:
            controls_of[c.control_of] += 1

    for c in cases:
        errors.extend(_case_errors(c, by_id, controls_of))
    return errors


def _case_errors(c: Case, by_id: dict[str, Case], controls_of: Counter[str]) -> list[str]:
    errors: list[str] = []
    for i, doc in enumerate(c.documents):
        for msg in validate_document(c.format, doc):
            errors.append(f"{c.id}: document {i}: {msg}")

    e = c.expect
    if c.is_control:
        if not c.control_of:
            errors.append(f"{c.id}: control must set control_of")
        else:
            target = by_id.get(c.control_of)
            if target is None:
                errors.append(f"{c.id}: control_of references unknown case {c.control_of}")
            elif target.is_control:
                errors.append(f"{c.id}: control_of references a control case {c.control_of}")
        if c.goal != "none":
            errors.append(f"{c.id}: control must have goal 'none'")
        if e.contains_any or e.missing_any or e.tool_called:
            errors.append(f"{c.id}: control must have empty attack expectations")
    else:
        if c.control_of:
            errors.append(f"{c.id}: control_of set on a non-control case")
        n = controls_of.get(c.id, 0)
        if n != 1:
            errors.append(f"{c.id}: expected exactly one control, found {n}")

    raw = "\n".join(c.documents)
    joined = normalize(raw)
    for item in e.utility_requires:
        if not contains_term(item, raw):
            errors.append(f"{c.id}: utility_requires item {item!r} not found in documents")

    if c.goal == "canary":
        if not c.canary:
            errors.append(f"{c.id}: canary goal requires canary")
        else:
            if c.canary not in e.contains_any:
                errors.append(f"{c.id}: canary must be in contains_any")
            if normalize(c.canary) not in joined:
                errors.append(f"{c.id}: canary not present in documents")
    elif c.goal == "suppress":
        if not e.missing_any:
            errors.append(f"{c.id}: suppress goal requires missing_any")
        for item in e.missing_any:
            if not contains_term(item, raw):
                errors.append(f"{c.id}: missing_any item {item!r} not found in documents")
    elif c.goal == "tool" and e.tool_called != "send_report":
        errors.append(f"{c.id}: tool goal requires tool_called == 'send_report'")

    if (c.task == "question") != (c.question is not None):
        errors.append(f"{c.id}: task 'question' requires question, and only that task may set it")
    return errors
