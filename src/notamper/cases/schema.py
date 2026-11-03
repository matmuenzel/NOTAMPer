"""JSON Schema for case files."""

from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator

from notamper.cases.model import FORMATS, GOALS, TASKS, VARIANTS

_STR = {"type": "string", "minLength": 1}
_STR_LIST = {"type": "array", "items": _STR}
_NULLABLE_STR = {"type": ["string", "null"]}

CASE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "format", "variant", "goal", "task", "documents", "expect"],
    "properties": {
        "id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]*$"},
        "format": {"enum": list(FORMATS)},
        "variant": {"enum": list(VARIANTS)},
        "goal": {"enum": list(GOALS)},
        "task": {"enum": list(TASKS)},
        "control_of": _NULLABLE_STR,
        "canary": {"type": ["string", "null"], "pattern": "^[A-Z]{5}-\\d{4}$"},
        "question": _NULLABLE_STR,
        "documents": {"type": "array", "minItems": 1, "items": _STR},
        "expect": {
            "type": "object",
            "additionalProperties": False,
            "required": ["utility_requires"],
            "properties": {
                "utility_requires": {**_STR_LIST, "minItems": 1},
                "attack_success_if": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "contains_any": _STR_LIST,
                        "missing_any": _STR_LIST,
                        "tool_called": _NULLABLE_STR,
                    },
                },
                "detection_keywords": _STR_LIST,
            },
        },
    },
}

_VALIDATOR = Draft202012Validator(CASE_SCHEMA)


def schema_errors(data: dict) -> list[str]:
    """Return human-readable schema violations, e.g. ``expect.x: ... is a required property``."""
    errors = []
    for err in sorted(_VALIDATOR.iter_errors(data), key=lambda e: list(map(str, e.absolute_path))):
        path = ".".join(str(p) for p in err.absolute_path)
        errors.append(f"{path or '<root>'}: {err.message}")
    return errors
