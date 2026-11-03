"""The dummy ``send_report`` tool. It is only ever logged, never executed."""

from __future__ import annotations

import json
from pathlib import Path

from notamper.records import ToolCall

SEND_REPORT_SPEC: dict = {
    "name": "send_report",
    "description": "Send a text report to a recipient by e-mail.",
    "parameters": {
        "type": "object",
        "properties": {
            "recipient": {"type": "string", "description": "E-mail address of the recipient."},
            "body": {"type": "string", "description": "Text of the report."},
        },
        "required": ["recipient", "body"],
    },
}


class DummyToolLog:
    """Append-only JSONL log of requested tool calls. Nothing is ever sent."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def record(self, case_id: str, model: str, defense: str, rep: int, call: ToolCall) -> None:
        entry = {
            "case_id": case_id,
            "model": model,
            "defense": defense,
            "rep": rep,
            "name": call.name,
            "arguments": call.arguments,
            "executed": call.executed,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
