"""Persistent response cache (JSONL) so that restarts never repeat paid calls."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from notamper.cases.model import Case
from notamper.records import Response
from notamper.runner.prompts import Prompt

log = logging.getLogger(__name__)


def prompt_fingerprint(prompt: Prompt) -> str:
    """SHA-256 over the full built prompt (system, user, tools)."""
    blob = json.dumps(
        [prompt.system, prompt.user, prompt.tools], sort_keys=True, ensure_ascii=False
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def cache_key(
    model: str,
    defense: str,
    case: Case,
    rep: int,
    temperature: float,
    seed: int | None,
    max_tokens: int,
    prompt: Prompt,
) -> str:
    """Stable key over everything that determines a response."""
    blob = json.dumps(
        [model, defense, case.content_hash(), rep, temperature, seed, max_tokens,
         prompt_fingerprint(prompt)],
        separators=(",", ":"),
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class ResponseCache:
    """Append-only JSONL cache loaded into memory."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._items: dict[str, Response] = {}
        self.skipped = 0  # corrupt or truncated lines ignored while loading
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8", errors="replace").splitlines():
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    self._items[rec["key"]] = Response.from_dict(rec["response"])
                except (ValueError, KeyError, TypeError):
                    self.skipped += 1
            if self.skipped:
                log.warning("cache %s: skipped %d unreadable line(s)", self.path, self.skipped)

    def __len__(self) -> int:
        return len(self._items)

    def get(self, key: str) -> Response | None:
        return self._items.get(key)

    def put(self, key: str, resp: Response) -> None:
        self._items[key] = resp
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lead = ""
        if self.path.exists() and self.path.stat().st_size:
            with self.path.open("rb") as fh:
                fh.seek(-1, 2)
                lead = "" if fh.read(1) == b"\n" else "\n"  # repair a truncated last line
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(lead)
            rec = {"key": key, "response": resp.to_dict()}
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
