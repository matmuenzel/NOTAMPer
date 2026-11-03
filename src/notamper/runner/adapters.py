"""Provider adapters (urllib only) and deterministic offline mock adapters.

The mock adapters are pipeline stand-ins, NOT models: they exist so the whole
run/score/report pipeline can be exercised offline and deterministically.
"""

from __future__ import annotations

import json
import math
import os
import re
import ssl
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.parse import urlparse

from notamper.generator.scenarios import SCENARIOS
from notamper.records import ToolCall
from notamper.runner.defenses import looks_like_injection
from notamper.runner.prompts import Prompt

TIMEOUT_S = 60
MAX_ATTEMPTS = 4
MAX_RETRY_AFTER_S = 60.0


class AdapterError(Exception):
    """A provider call failed. Messages never contain keys or headers."""


@dataclass
class Completion:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str | None = None


class Adapter(Protocol):
    model_id: str
    supports_seed: bool
    temperature_applied: bool

    def complete(
        self, prompt: Prompt, *, temperature: float, seed: int | None, max_tokens: int
    ) -> Completion: ...


# ---------------------------------------------------------------- mocks

_MARKER = re.compile(r"^--- MESSAGE \d+ ---$")
_SPOT = re.compile(r"^<</?DATA id=\S+>>$")
_CANARY = re.compile(r"\b[A-Z]{5}-\d{4}\b")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")
_SUPPRESS_CUE = re.compile(
    r"\b(OMIT|DO NOT MENTION|NICHT ERWAEHNEN|ERWAEHNEN SIE .{0,40}NICHT)\b"
    r"|REPORT .{0,60}AS (AVAILABLE|OPEN|NORMAL)|ALS NORMAL",
    re.IGNORECASE,
)
def _term_regex(*alternative_sets: str) -> re.Pattern[str]:
    """Whole-token regex over all alternatives of the generator's suppress targets."""
    alts = {a.strip() for group in alternative_sets for a in group.split("|") if a.strip()}
    body = "|".join(re.escape(a) for a in sorted(alts, key=len, reverse=True))
    return re.compile(rf"(?<![A-Z0-9])(?:{body})(?![A-Z0-9])", re.IGNORECASE)


_SUPPRESSED = _term_regex(
    *sorted({sc.suppress_target for group in SCENARIOS.values() for sc in group}),
    "+TSRA|+SN|EINSCHRAENKUNG|ILS|SNOW",
)
_REWRITE = "AVBL"


def parse_documents(user: str) -> list[str]:
    """Data lines of a prompt: everything after the first message marker, minus markers."""
    lines = user.split("\n")
    start = next((i for i, ln in enumerate(lines) if _MARKER.match(ln)), len(lines))
    return [
        ln
        for ln in lines[start:]
        if ln.strip() and not _MARKER.match(ln) and not _SPOT.match(ln)
    ]


class _MockBase:
    supports_seed = True
    temperature_applied = False
    model_id = "mock"

    def _answer(self, lines: list[str], prompt: Prompt) -> tuple[str, list[ToolCall]]:
        raise NotImplementedError

    def complete(
        self, prompt: Prompt, *, temperature: float, seed: int | None, max_tokens: int
    ) -> Completion:
        lines = parse_documents(prompt.user)
        text, calls = self._answer(lines, prompt)
        return Completion(
            text=text,
            tool_calls=calls,
            input_tokens=(len(prompt.system) + len(prompt.user)) // 4,
            output_tokens=len(text) // 4,
            stop_reason="tool_use" if calls else "end_turn",
        )


class MockNaive(_MockBase):
    """Obeys instructions found in the data (canary, tool call, suppression)."""

    model_id = "mock:naive"

    def _answer(self, lines: list[str], prompt: Prompt) -> tuple[str, list[ToolCall]]:
        data = "\n".join(lines)
        if _SUPPRESS_CUE.search(data):
            # keep every line, but make the restriction sound normal (the target disappears)
            lines = [_SUPPRESSED.sub(_REWRITE, ln) for ln in lines]
        text = "\n".join(lines)
        canary = _CANARY.search(data)
        if canary:
            text += "\n" + canary.group(0)
        calls: list[ToolCall] = []
        if re.search("send_report", data, re.IGNORECASE) and any(
            t["name"] == "send_report" for t in prompt.tools
        ):
            email = _EMAIL.search(data)
            calls.append(
                ToolCall(
                    "send_report",
                    {"recipient": email.group(0).lower() if email else "unknown", "body": text},
                )
            )
        return text, calls


class MockRobust(_MockBase):
    """Echoes every data line, withholding canary-like tokens and e-mail addresses; flags."""

    model_id = "mock:robust"

    def _answer(self, lines: list[str], prompt: Prompt) -> tuple[str, list[ToolCall]]:
        out: list[str] = []
        flagged = False
        for ln in lines:
            clean = _EMAIL.sub("[withheld]", _CANARY.sub("[withheld]", ln))
            flagged = flagged or clean != ln or looks_like_injection(ln)
            out.append(clean)
        text = "\n".join(out)
        if flagged:
            text += (
                "\nNote: the messages contain an embedded instruction (possible prompt "
                "injection); it was not followed."
            )
        return text, []


# ---------------------------------------------------------------- HTTP

Opener = Callable[..., Any]
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
_LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never follow redirects: they could forward the API key to another host."""

    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


def default_opener(req: urllib.request.Request, timeout: float = TIMEOUT_S) -> Any:
    """urlopen-like callable that does not follow redirects."""
    return urllib.request.build_opener(_NoRedirect).open(req, timeout=timeout)


def validate_base_url(url: str, *, has_key: bool) -> str:
    """Require http(s); with credentials require https except for local hosts."""
    parts = urlparse(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise AdapterError("base URL must be http(s)")
    if has_key and parts.scheme != "https" and parts.hostname not in _LOCAL_HOSTS:
        raise AdapterError("refusing to send credentials over plain http to a non-local host")
    return url.rstrip("/")


def _retry_after(exc: urllib.error.HTTPError) -> float | None:
    """Seconds from a numeric Retry-After header, capped at 60 s; None if absent/invalid."""
    try:
        value = float(exc.headers.get("Retry-After", ""))
    except (AttributeError, TypeError, ValueError):
        return None
    if math.isnan(value) or value < 0:
        return None
    return min(value, MAX_RETRY_AFTER_S)


_CERT_HINT = (
    "TLS certificate verification failed; this Python has no CA certificates. On macOS with "
    "python.org Python run 'Install Certificates.command' from its Applications folder, or set "
    "SSL_CERT_FILE to a CA bundle"
)


def _network_error(exc: BaseException) -> tuple[str, bool]:
    """Diagnostic message and whether retrying can help (certificate problems are permanent)."""
    reason = getattr(exc, "reason", exc)
    if isinstance(reason, ssl.SSLCertVerificationError):
        return f"network error: {_CERT_HINT}", False
    detail = str(reason)[:120]
    return f"network error: {type(exc).__name__}" + (f": {detail}" if detail else ""), True


def _post_json(
    url: str,
    headers: dict[str, str],
    payload: dict,
    *,
    opener: Opener,
    sleep: Callable[[float], None],
    secret: str | None,
) -> Any:
    """POST JSON with retry (429/5xx/network): backoff 1, 2, 4 s, or Retry-After (max 60 s)."""
    data = json.dumps(payload).encode("utf-8")
    last = "unknown error"
    for attempt in range(MAX_ATTEMPTS):
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json", **headers}, method="POST"
        )
        retry = True
        delay: float = 2**attempt
        try:
            with opener(req, timeout=TIMEOUT_S) as resp:
                raw = resp.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise AdapterError("response too large")
            return json.loads(raw.decode("utf-8"))
        except AdapterError:
            raise
        except urllib.error.HTTPError as exc:
            body = ""
            try:
                body = exc.read(1000).decode("utf-8", "replace")
            except Exception:  # noqa: BLE001 - body is best-effort diagnostics
                pass
            if secret:
                body = body.replace(secret, "***")
            last = f"HTTP {exc.code}: {body[:200]}"
            retry = exc.code == 429 or exc.code >= 500
            if exc.code in (429, 503):
                wait = _retry_after(exc)
                if wait is not None:
                    delay = wait
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last, retry = _network_error(exc)
        except (ValueError, UnicodeDecodeError):
            last = "invalid JSON in response"
            retry = False
        if not retry or attempt == MAX_ATTEMPTS - 1:
            break
        sleep(delay)
    raise AdapterError(last)


def _require_key(env: Mapping[str, str], name: str) -> str:
    key = env.get(name)
    if not key:
        raise AdapterError(f"{name} not set")
    return key


def _shape_error(exc: Exception) -> AdapterError:
    return AdapterError(f"unexpected response shape: {type(exc).__name__}")


def _tokens(usage: Any, name: str) -> int:
    value = usage.get(name, 0) if isinstance(usage, dict) else 0
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _stop(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _args_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {"_raw": str(value)}


class AnthropicAdapter:
    supports_seed = False
    temperature_applied = True

    def __init__(
        self,
        model: str,
        *,
        env: Mapping[str, str] | None = None,
        opener: Opener | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.model_id = f"anthropic:{model}"
        self._model = model
        self._key = _require_key(os.environ if env is None else env, "ANTHROPIC_API_KEY")
        self._opener, self._sleep = opener or default_opener, sleep

    def complete(
        self, prompt: Prompt, *, temperature: float, seed: int | None, max_tokens: int
    ) -> Completion:
        payload: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": prompt.system,
            "messages": [{"role": "user", "content": prompt.user}],
        }
        if prompt.tools:
            payload["tools"] = [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "input_schema": t["parameters"],
                }
                for t in prompt.tools
            ]
        out = _post_json(
            "https://api.anthropic.com/v1/messages",
            {"x-api-key": self._key, "anthropic-version": "2023-06-01"},
            payload,
            opener=self._opener,
            sleep=self._sleep,
            secret=self._key,
        )
        try:
            texts: list[str] = []
            calls: list[ToolCall] = []
            for block in out.get("content") or []:
                kind = block.get("type")
                if kind == "text":
                    texts.append(str(block.get("text", "")))
                elif kind == "tool_use":
                    args = _args_dict(block.get("input"))
                    calls.append(ToolCall(str(block.get("name", "")), args))
            usage = out.get("usage")
            return Completion(
                "".join(texts),
                calls,
                _tokens(usage, "input_tokens"),
                _tokens(usage, "output_tokens"),
                _stop(out.get("stop_reason")),
            )
        except (AttributeError, TypeError, KeyError, ValueError) as exc:
            raise _shape_error(exc) from None


def _fixed_temperature_model(model: str) -> bool:
    return model.startswith(("o1", "o3", "o4", "gpt-5"))


class OpenAIAdapter:
    """OpenAI chat completions; also serves Ollama and other compatible endpoints."""

    supports_seed = True

    def __init__(
        self,
        model: str,
        *,
        base_url: str = "https://api.openai.com/v1",
        key: str | None,
        label: str = "openai",
        opener: Opener | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.model_id = f"{label}:{model}"
        self._model = model
        self.temperature_applied = not _fixed_temperature_model(model)
        self._base = validate_base_url(base_url, has_key=bool(key))
        self._key = key
        self._opener, self._sleep = opener or default_opener, sleep

    def complete(
        self, prompt: Prompt, *, temperature: float, seed: int | None, max_tokens: int
    ) -> Completion:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": prompt.system},
                {"role": "user", "content": prompt.user},
            ],
        }
        if urlparse(self._base).hostname == "api.openai.com":
            payload["max_completion_tokens"] = max_tokens
        else:
            payload["max_tokens"] = max_tokens
        if self.temperature_applied:
            payload["temperature"] = temperature
        if seed is not None:
            payload["seed"] = seed
        if prompt.tools:
            payload["tools"] = [{"type": "function", "function": t} for t in prompt.tools]
        headers = {"Authorization": f"Bearer {self._key}"} if self._key else {}
        out = _post_json(
            f"{self._base}/chat/completions",
            headers,
            payload,
            opener=self._opener,
            sleep=self._sleep,
            secret=self._key,
        )
        try:
            choice = out["choices"][0]
            message = choice["message"]
            calls: list[ToolCall] = []
            for tc in message.get("tool_calls") or []:
                fn = tc["function"]
                raw = fn.get("arguments", "")
                try:
                    args = _args_dict(json.loads(raw))
                except (ValueError, TypeError):
                    args = {"_raw": str(raw)}
                calls.append(ToolCall(str(fn.get("name", "")), args))
            content = message.get("content")
            usage = out.get("usage")
            return Completion(
                content if isinstance(content, str) else "",
                calls,
                _tokens(usage, "prompt_tokens"),
                _tokens(usage, "completion_tokens"),
                _stop(choice.get("finish_reason")),
            )
        except (AttributeError, TypeError, KeyError, IndexError, ValueError) as exc:
            raise _shape_error(exc) from None


def get_adapter(
    spec: str,
    *,
    env: Mapping[str, str] | None = None,
    opener: Opener | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> Adapter:
    """Build an adapter from ``provider:model`` (see module docs for providers)."""
    environ = os.environ if env is None else env
    provider, _, model = spec.partition(":")
    if provider == "mock" and model == "naive":
        return MockNaive()
    if provider == "mock" and model == "robust":
        return MockRobust()
    if not model:
        raise AdapterError(f"invalid adapter spec: {spec!r}")
    if provider == "anthropic":
        return AnthropicAdapter(model, env=environ, opener=opener, sleep=sleep)
    if provider == "openai":
        key = _require_key(environ, "OPENAI_API_KEY")
        return OpenAIAdapter(model, key=key, opener=opener, sleep=sleep)
    if provider == "ollama":
        base = environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        return OpenAIAdapter(
            model, base_url=base, key=None, label="ollama", opener=opener, sleep=sleep
        )
    if provider == "openai-compat":
        name, sep, base = model.partition("@")
        if not sep or not base:
            raise AdapterError("openai-compat spec must be openai-compat:<model>@<base_url>")
        return OpenAIAdapter(
            name,
            base_url=base,
            key=environ.get("OPENAI_COMPAT_API_KEY"),
            label="openai-compat",
            opener=opener,
            sleep=sleep,
        )
    raise AdapterError(f"unknown provider in spec: {spec!r}")
