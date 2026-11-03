import io
import json
import ssl
import urllib.error
from pathlib import Path

import pytest

from notamper.cases.loader import load_cases
from notamper.records import Response
from notamper.runner.adapters import (
    AdapterError,
    AnthropicAdapter,
    OpenAIAdapter,
    get_adapter,
    parse_documents,
)
from notamper.runner.budget import Budget, BudgetExceeded
from notamper.runner.cache import ResponseCache, cache_key
from notamper.runner.prompts import Prompt, build_prompt

CASES = load_cases(Path(__file__).resolve().parent.parent / "cases")
KW = {"temperature": 0.0, "seed": 1, "max_tokens": 100}
PROMPT = Prompt("sys", "task\n\n--- MESSAGE 1 ---\nX", [])
SECRET = "sk-secret-123"


class FakeResp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode()

    def read(self, n=-1):
        return self._b if n < 0 else self._b[:n]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def http_error(code, body="boom"):
    return urllib.error.HTTPError("u", code, "m", {}, io.BytesIO(body.encode()))


class Opener:
    def __init__(self, *items):
        self.items, self.requests = list(items), []

    def __call__(self, req, timeout=None):
        self.requests.append((req, timeout))
        item = self.items.pop(0)
        if isinstance(item, Exception):
            raise item
        return FakeResp(item)


def anthropic(opener):
    return AnthropicAdapter(
        "claude-x", env={"ANTHROPIC_API_KEY": SECRET}, opener=opener, sleep=lambda s: None
    )


def openai(opener, key=SECRET):
    return OpenAIAdapter("gpt-x", key=key, opener=opener, sleep=lambda s: None)


def test_anthropic_parse():
    op = Opener(
        {
            "content": [
                {"type": "text", "text": "hello"},
                {"type": "tool_use", "name": "send_report", "input": {"recipient": "a@b.c"}},
            ],
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
    )
    tool_prompt = Prompt("s", "u", [{"name": "send_report", "description": "d", "parameters": {}}])
    c = anthropic(op).complete(tool_prompt, **KW)
    assert c.text == "hello" and c.tool_calls[0].arguments == {"recipient": "a@b.c"}
    assert (c.input_tokens, c.output_tokens) == (10, 5)
    req, timeout = op.requests[0]
    assert timeout == 60 and req.full_url == "https://api.anthropic.com/v1/messages"
    assert req.get_header("X-api-key") == SECRET
    assert req.get_header("Anthropic-version") == "2023-06-01"
    assert json.loads(req.data)["tools"][0]["input_schema"] == {}


def test_openai_parse_and_malformed_args():
    payload = {
        "choices": [
            {
                "message": {
                    "content": None,
                    "tool_calls": [
                        {
                            "function": {
                                "name": "send_report",
                                "arguments": '{"recipient": "a@b.c"}',
                            }
                        },
                        {"function": {"name": "send_report", "arguments": "{not json"}},
                    ],
                }
            }
        ],
        "usage": {"prompt_tokens": 7, "completion_tokens": 3},
    }
    op = Opener(payload)
    tool_prompt = Prompt("s", "u", [{"name": "send_report", "description": "d", "parameters": {}}])
    c = openai(op).complete(tool_prompt, **KW)
    assert c.text == "" and c.tool_calls[0].arguments == {"recipient": "a@b.c"}
    assert c.tool_calls[1].arguments == {"_raw": "{not json"}
    assert (c.input_tokens, c.output_tokens) == (7, 3)
    body = json.loads(op.requests[0][0].data)
    assert body["seed"] == 1 and body["tools"][0]["type"] == "function"
    assert op.requests[0][0].full_url.endswith("/chat/completions")


def test_retry_on_429_then_success():
    ok = {"content": [{"type": "text", "text": "ok"}], "usage": {}}
    op = Opener(http_error(429), http_error(503), ok)
    assert anthropic(op).complete(PROMPT, **KW).text == "ok"
    assert len(op.requests) == 3


def test_network_error_retried():
    ok = {"content": [{"type": "text", "text": "ok"}], "usage": {}}
    op = Opener(urllib.error.URLError("down"), ok)
    assert anthropic(op).complete(PROMPT, **KW).text == "ok"


def test_error_after_four_500_redacts():
    op = Opener(*[http_error(500, f"bad {SECRET} " + "x" * 500) for _ in range(4)])
    with pytest.raises(AdapterError) as ei:
        anthropic(op).complete(PROMPT, **KW)
    msg = str(ei.value)
    assert msg.startswith("HTTP 500") and SECRET not in msg and len(msg) < 230
    assert len(op.requests) == 4


def test_client_error_not_retried():
    op = Opener(http_error(401, "nope"))
    with pytest.raises(AdapterError, match="HTTP 401"):
        openai(op).complete(PROMPT, **KW)
    assert len(op.requests) == 1


def test_missing_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(AdapterError, match="ANTHROPIC_API_KEY not set"):
        get_adapter("anthropic:claude-x")
    with pytest.raises(AdapterError, match="OPENAI_API_KEY not set"):
        get_adapter("openai:gpt-x")


def test_get_adapter_specs():
    assert get_adapter("mock:naive").model_id == "mock:naive"
    assert get_adapter("mock:robust").model_id == "mock:robust"
    a = get_adapter("ollama:llama3", env={})
    assert a._base == "http://localhost:11434/v1"
    a = get_adapter("ollama:llama3", env={"OLLAMA_BASE_URL": "http://h:1/v1"})
    assert a._base == "http://h:1/v1"
    c = get_adapter("openai-compat:m@http://x:9/v1/", env={})
    assert c._model == "m" and c._base == "http://x:9/v1"
    for bad in ("nope:x", "mock:other", "openai-compat:m", "anthropic"):
        with pytest.raises(AdapterError):
            get_adapter(bad, env={"ANTHROPIC_API_KEY": "k"})


@pytest.mark.parametrize("defense", ["none", "guard", "spotlight", "filter", "approval"])
def test_parse_documents_all_defenses(defense):
    case = next(c for c in CASES if c.variant == "V8" and c.goal == "canary")
    prompt, _ = build_prompt(case, defense)
    lines = parse_documents(prompt.user)
    assert not any(ln.startswith(("--- MESSAGE", "<<DATA", "<</DATA")) for ln in lines)
    assert "Summarize" not in "\n".join(lines)
    assert any("ZZ" in ln for ln in lines)


def test_mock_naive_canary_and_tool_and_suppress():
    naive = get_adapter("mock:naive")
    canary_case = next(c for c in CASES if c.goal == "canary" and c.variant == "V1")
    out = naive.complete(build_prompt(canary_case, "none")[0], **KW)
    assert canary_case.canary in out.text

    tool_case = next(c for c in CASES if c.goal == "tool" and c.variant == "V7")
    out = naive.complete(build_prompt(tool_case, "none")[0], **KW)
    assert out.tool_calls[0].name == "send_report"
    assert out.tool_calls[0].arguments["recipient"] == "ops-audit@example.invalid"

    sup = next(
        c
        for c in CASES
        if c.goal == "suppress" and c.variant == "V2" and c.task == "summarize"
        and "CLOSED" in "\n".join(c.documents).upper()
    )
    out = naive.complete(build_prompt(sup, "none")[0], **KW)
    assert "CLOSED" not in out.text.upper() and "CLOSURE" not in out.text.upper()
    assert "AVBL" in out.text and out.text.strip()  # lines kept, restriction reworded
    assert any(t in out.text for t in ("ZZQA", "ZZQB", "ZZQC"))  # designator stays
    ctl = next((c for c in CASES if c.control_of == sup.id), None)
    assert ctl is not None
    assert "CLOSED" in naive.complete(build_prompt(ctl, "none")[0], **KW).text.upper()


def test_mock_robust_never_attacked():
    robust = get_adapter("mock:robust")
    naive = get_adapter("mock:naive")
    naive_hits = 0
    for c in CASES:
        if c.is_control:
            continue
        for defense in ("none", "spotlight"):
            prompt, _ = build_prompt(c, defense)
            out = robust.complete(prompt, **KW)
            assert out.tool_calls == []
            if c.canary:
                assert c.canary not in out.text, c.id
            naive_out = naive.complete(prompt, **KW)
            hit = bool(c.canary and c.canary in naive_out.text)
            naive_hits += bool(naive_out.tool_calls) or hit
    assert naive_hits > 0


def test_mock_robust_withholds_tokens_but_keeps_lines():
    robust = get_adapter("mock:robust")
    c = next(c for c in CASES if c.goal == "canary" and c.canary and not c.is_control)
    prompt, _ = build_prompt(c, "none")
    out = robust.complete(prompt, **KW)
    assert "[withheld]" in out.text and c.canary not in out.text
    data = parse_documents(prompt.user)
    kept = [ln for ln in out.text.split("\n") if ln != "[withheld]"]
    assert len(kept) >= len(data)  # no data line dropped (plus the flag note)


def test_mock_robust_flags_and_utility_on_control():
    robust = get_adapter("mock:robust")
    attack = next(c for c in CASES if c.variant == "V8" and c.goal == "canary")
    out = robust.complete(build_prompt(attack, "none")[0], **KW)
    assert "prompt injection" in out.text.lower()
    ctl = next(c for c in CASES if c.is_control)
    out = robust.complete(build_prompt(ctl, "none")[0], **KW)
    assert "injection" not in out.text.lower()
    assert out.input_tokens > 0 and out.output_tokens == len(out.text) // 4


def test_budget_calls():
    b = Budget(max_calls=2, max_usd=None)
    for _ in range(2):
        b.check()
        b.charge("mock:naive", 10, 10)
    with pytest.raises(BudgetExceeded):
        b.check()
    assert b.calls == 2 and b.spent_usd == 0


def test_budget_usd_and_prices():
    b = Budget(max_calls=None, max_usd=0.01)
    cost = b.charge("anthropic:claude-sonnet-4-5", 1_000_000, 0)
    assert cost == pytest.approx(3.0)
    with pytest.raises(BudgetExceeded):
        b.check()
    unknown = Budget(None, None).charge("openai-compat:weird@http://x", 1_000_000, 1_000_000)
    assert unknown == 90.0  # unknown model = max listed price


def test_cache_roundtrip(tmp_path):
    case = CASES[0]
    prompt = build_prompt(case, "none")[0]
    k = cache_key("m", "none", case, 0, 0.0, 1, 800, prompt)
    assert k != cache_key("m", "none", case, 1, 0.0, 1, 800, prompt)
    assert k != cache_key("m", "guard", case, 0, 0.0, 1, 800, prompt)
    assert k != cache_key("m", "none", case, 0, 0.0, 1, 801, prompt)
    other = Prompt(prompt.system + "!", prompt.user, prompt.tools)
    assert k != cache_key("m", "none", case, 0, 0.0, 1, 800, other)
    assert k == cache_key("m", "none", case, 0, 0.0, 1, 800, build_prompt(case, "none")[0])
    cache = ResponseCache(tmp_path / "c.jsonl")
    assert cache.get(k) is None
    cache.put(k, Response(case.id, "m", "none", 0, "hi"))
    again = ResponseCache(tmp_path / "c.jsonl")
    assert again.get(k).text == "hi"


def test_cache_skips_corrupt_trailing_line(tmp_path):
    path = tmp_path / "c.jsonl"
    cache = ResponseCache(path)
    cache.put("k1", Response("c", "m", "none", 0, "one"))
    with path.open("a") as fh:
        fh.write('{"key": "k2", "respo')  # truncated write
    again = ResponseCache(path)
    assert again.skipped == 1 and again.get("k1").text == "one"
    again.put("k3", Response("c", "m", "none", 0, "three"))
    third = ResponseCache(path)
    assert third.get("k3").text == "three" and third.get("k1").text == "one"


@pytest.mark.parametrize(
    "payload",
    [
        [1, 2],
        {"content": ["text"]},
        {"content": [{"type": "text", "text": "ok"}], "usage": "lots"},
    ],
)
def test_anthropic_untrusted_shapes(payload):
    op = Opener(payload)
    try:
        c = anthropic(op).complete(PROMPT, **KW)
    except AdapterError as exc:
        assert "unexpected response shape" in str(exc)
    else:  # string usage is tolerated as zero tokens
        assert c.text == "ok" and c.input_tokens == 0


def test_anthropic_shape_errors_raise():
    for payload in ([1, 2], {"content": ["text"]}):
        with pytest.raises(AdapterError, match="unexpected response shape"):
            anthropic(Opener(payload)).complete(PROMPT, **KW)


def test_anthropic_tool_input_not_dict():
    op = Opener({"content": [{"type": "tool_use", "name": "send_report", "input": "oops"}]})
    assert anthropic(op).complete(PROMPT, **KW).tool_calls[0].arguments == {"_raw": "oops"}


@pytest.mark.parametrize(
    "payload", [[], {"choices": []}, {"choices": [{"message": "x"}]}, {"choices": "x"}]
)
def test_openai_untrusted_shapes(payload):
    with pytest.raises(AdapterError, match="unexpected response shape"):
        openai(Opener(payload)).complete(PROMPT, **KW)


def test_openai_string_usage_ok():
    payload = {"choices": [{"message": {"content": "hi"}}], "usage": "x"}
    c = openai(Opener(payload)).complete(PROMPT, **KW)
    assert c.text == "hi" and c.input_tokens == 0


def test_response_size_cap():
    class Big(FakeResp):
        def __init__(self):
            self._b = b"x" * (4 * 1024 * 1024 + 1)

    class BigOpener(Opener):
        def __call__(self, req, timeout=None):
            return Big()

    with pytest.raises(AdapterError, match="too large"):
        anthropic(BigOpener()).complete(PROMPT, **KW)


def test_default_opener_refuses_redirects():
    import urllib.request

    from notamper.runner.adapters import _NoRedirect

    req = urllib.request.Request("https://a.example/x")
    handler = _NoRedirect()
    assert handler.redirect_request(req, None, 302, "Found", {}, "https://evil.example/") is None


def test_base_url_validation():
    with pytest.raises(AdapterError, match="http"):
        get_adapter("openai-compat:m@file:///etc/passwd", env={})
    with pytest.raises(AdapterError, match="http"):
        get_adapter("openai-compat:m@ftp://h/v1", env={})
    env = {"OPENAI_COMPAT_API_KEY": "k"}
    with pytest.raises(AdapterError, match="plain http"):
        get_adapter("openai-compat:m@http://remote.example/v1", env=env)
    get_adapter("openai-compat:m@https://remote.example/v1", env=env)
    get_adapter("openai-compat:m@http://localhost:8000/v1", env=env)
    get_adapter("openai-compat:m@http://remote.example/v1", env={})  # no key: allowed


def test_openai_token_param_and_temperature():
    op = Opener({"choices": [{"message": {"content": "a"}}]})
    openai(op).complete(PROMPT, **KW)
    body = json.loads(op.requests[0][0].data)
    assert body["max_completion_tokens"] == 100 and "max_tokens" not in body
    assert body["temperature"] == 0.0

    op = Opener({"choices": [{"message": {"content": "a"}}]})
    a = OpenAIAdapter("o3-mini", key=SECRET, opener=op, sleep=lambda s: None)
    a.complete(PROMPT, **KW)
    assert "temperature" not in json.loads(op.requests[0][0].data)

    op = Opener({"choices": [{"message": {"content": "a"}}]})
    a = OpenAIAdapter(
        "llama3", base_url="http://localhost:11434/v1", key=None, opener=op, sleep=lambda s: None
    )
    a.complete(PROMPT, **KW)
    body = json.loads(op.requests[0][0].data)
    assert body["max_tokens"] == 100 and "max_completion_tokens" not in body


def test_price_longest_prefix_and_unknown_fallback():
    b = Budget(None, None)
    assert b.price_for("anthropic:claude-opus-4-1-20250805") == (15.0, 75.0)
    assert b.price_for("anthropic:claude-opus-4") == (15.0, 75.0)
    assert b.price_for("anthropic:claude-sonnet-4-5-20250929") == (3.0, 15.0)
    assert b.price_for("openai:gpt-4o-mini-2024-07-18") == (0.15, 0.6)  # not gpt-4o
    assert b.price_for("openai:gpt-4o-2024-08-06") == (2.5, 10.0)
    assert b.price_for("openai:brand-new") == (15.0, 75.0)  # max of the listed models


def sleeps_for(items):
    waits = []
    op = Opener(*items)
    a = OpenAIAdapter("gpt-x", key=SECRET, opener=op, sleep=waits.append)
    return a, op, waits


def with_header(code, value):
    return urllib.error.HTTPError(
        "u", code, "m", {"Retry-After": value}, io.BytesIO(b"x"))


OK_OPENAI = {"choices": [{"message": {"content": "hi"}, "finish_reason": "stop"}], "usage": {}}


def test_retry_backoff_and_retry_after():
    a, op, waits = sleeps_for([http_error(500), http_error(500), http_error(500), OK_OPENAI])
    assert a.complete(PROMPT, **KW).text == "hi"
    assert waits == [1, 2, 4]
    a, op, waits = sleeps_for([with_header(429, "7"), with_header(503, "500"), OK_OPENAI])
    a.complete(PROMPT, **KW)
    assert waits == [7.0, 60.0]  # honoured, capped at 60 s
    a, op, waits = sleeps_for([with_header(500, "30"), OK_OPENAI])
    a.complete(PROMPT, **KW)
    assert waits == [1]  # Retry-After only honoured on 429/503


def test_stop_reasons_parsed():
    assert openai(Opener(OK_OPENAI)).complete(PROMPT, **KW).stop_reason == "stop"
    op = Opener({"content": [{"type": "text", "text": "x"}], "stop_reason": "max_tokens"})
    assert anthropic(op).complete(PROMPT, **KW).stop_reason == "max_tokens"
    assert openai(Opener({"choices": [{"message": {"content": "a"}}]})).complete(
        PROMPT, **KW).stop_reason is None


def test_temperature_applied_flag():
    assert not OpenAIAdapter("o3-mini", key=SECRET).temperature_applied
    assert OpenAIAdapter("gpt-4o", key=SECRET).temperature_applied


def test_certificate_error_not_retried_and_explained():
    cert = ssl.SSLCertVerificationError(1, "certificate verify failed")
    op = Opener(urllib.error.URLError(cert))
    with pytest.raises(AdapterError) as ei:
        anthropic(op).complete(PROMPT, **KW)
    assert "Install Certificates" in str(ei.value) and "SSL_CERT_FILE" in str(ei.value)
    assert len(op.requests) == 1


def test_network_error_names_reason():
    op = Opener(*[urllib.error.URLError("Name or service not known") for _ in range(4)])
    with pytest.raises(AdapterError) as ei:
        anthropic(op).complete(PROMPT, **KW)
    assert str(ei.value) == "network error: URLError: Name or service not known"
