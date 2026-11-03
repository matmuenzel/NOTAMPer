"""Response records written by the runner and read by scoring."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """A tool call requested by the model."""

    name: str
    arguments: dict
    executed: bool = True


@dataclass
class Response:
    """One model response for one case, defense and repetition."""

    case_id: str
    model: str
    defense: str
    rep: int
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    error: str | None = None
    filtered: bool = False
    latency_s: float = 0.0
    stop_reason: str | None = None

    @property
    def is_empty(self) -> bool:
        """No text and no tool calls (and not an error): nothing the model said to score."""
        return not self.text.strip() and not self.tool_calls

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Response:
        data = dict(d)
        data["tool_calls"] = [ToolCall(**tc) for tc in data.get("tool_calls") or []]
        return cls(**data)
