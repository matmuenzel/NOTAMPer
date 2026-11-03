"""Load, serialise and dump case files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from notamper.cases.model import DEFAULT_DETECTION_KEYWORDS, Case, Expect
from notamper.cases.schema import schema_errors


class CaseError(Exception):
    """Raised when a case file is invalid."""


def case_from_dict(d: dict) -> Case:
    """Build a Case from a plain dict; raises CaseError on schema violations."""
    if not isinstance(d, dict):
        raise CaseError("<root>: case must be a mapping")
    errors = schema_errors(d)
    if errors:
        raise CaseError("; ".join(errors))
    e = d["expect"]
    attack = e.get("attack_success_if") or {}
    expect = Expect(
        utility_requires=tuple(e["utility_requires"]),
        contains_any=tuple(attack.get("contains_any", ())),
        missing_any=tuple(attack.get("missing_any", ())),
        tool_called=attack.get("tool_called"),
        detection_keywords=tuple(e.get("detection_keywords", DEFAULT_DETECTION_KEYWORDS)),
    )
    return Case(
        id=d["id"],
        format=d["format"],
        variant=d["variant"],
        goal=d["goal"],
        task=d["task"],
        documents=tuple(d["documents"]),
        expect=expect,
        control_of=d.get("control_of"),
        canary=d.get("canary"),
        question=d.get("question"),
    )


def case_to_dict(c: Case) -> dict:
    """Serialise a Case to a plain dict (inverse of case_from_dict)."""
    return c.to_dict()


def load_case(path: Path) -> Case:
    """Load one YAML case file; errors are prefixed with the path."""
    path = Path(path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return case_from_dict(data)
    except (CaseError, yaml.YAMLError, OSError, UnicodeDecodeError) as exc:
        raise CaseError(f"{path}: {exc}") from exc


def load_cases(root: Path) -> list[Case]:
    """Load all ``*.yaml`` files under root recursively, sorted by id."""
    cases = [load_case(p) for p in Path(root).rglob("*.yaml")]
    return sorted(cases, key=lambda c: c.id)


class _LiteralDumper(yaml.SafeDumper):
    pass


def _str_representer(dumper: yaml.SafeDumper, value: str) -> Any:
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_LiteralDumper.add_representer(str, _str_representer)


def dump_case(c: Case) -> str:
    """Serialise a Case to YAML with multi-line documents as literal block scalars."""
    return yaml.dump(
        case_to_dict(c),
        Dumper=_LiteralDumper,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
