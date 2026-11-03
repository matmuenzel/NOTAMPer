# Threat model

A STRIDE-lite description of the system NOTAMper models, and of NOTAMper itself.

## Modelled system

An LLM assistant receives aeronautical messages (NOTAM, METAR, ATIS, operations e-mail) from
external feeds and produces a briefing, a filtered list, or an answer. In the tool-using variant it
may call a `send_report(recipient, body)` function.

## Attacker

The attacker can influence free-text fields of an externally sourced message: the NOTAM E) line,
METAR remarks, trailing ATIS sentences, e-mail paragraphs. The attacker cannot change the system
prompt, the user's task, the tool definitions, or the model. The attacker does not see the output.
Adaptive attackers who observe the defense are out of scope for the v0.1 measurements.

## Assets

| Asset | Compromise |
|-------|------------|
| Integrity of the briefing | Output carries attacker-chosen content (canary) or omits real facts (suppression of a closure or significant weather). |
| Tool actions | The assistant triggers an action the user did not ask for. |
| Confidentiality of the briefing | The assistant forwards briefing content to an attacker-chosen recipient via `send_report` (exfiltration). |

## Trust boundaries

1. External message source to the prompt builder: everything inside a message is untrusted.
2. Prompt to model: the model cannot reliably separate data from instructions; defenses try to help.
3. Model output to tools: tool calls must pass an approval gate before they have effect.
4. Provider response to NOTAMper: response bodies are untrusted input to the runner.

## Threats (STRIDE-lite)

| Category | Threat in the modelled system |
|----------|-------------------------------|
| Spoofing | Text that claims to come from ATC, a system administrator or the operator (V5). |
| Tampering | Instructions embedded in data fields (V1-V4, V6-V8); instructions split across messages (V7). |
| Repudiation | Not modelled. |
| Information disclosure | Exfiltration of briefing text through `send_report`. |
| Denial of service | Suppression of a closure so that a hazard is not reported (goal `suppress`). |
| Elevation of privilege | A data field obtains the effect of a user command (tool call). |

## Out of scope

Attacks on real aviation systems or real messages; network-level attacks; supply-chain compromise
of model providers; adaptive and optimisation-based attacks; training-time poisoning; multi-turn
agent loops; operational use of any result. All goals in the corpus are harmless by construction.

## Hardening of the benchmark itself

NOTAMper handles credentials and untrusted model output, so it is built defensively:

- No secrets on disk: API keys are read from environment variables only, and are not written to
  the cache, manifest, logs, error messages or reports.
- HTTP is stdlib `urllib` with no provider SDKs. Redirects are never followed, so a key cannot be
  forwarded to another host. Only `http` and `https` URLs are accepted, and a request carrying a
  key requires `https` unless the host is local.
- Response bodies are size-capped (4 MiB) before parsing, and provider JSON is parsed
  defensively; malformed output becomes an error record, never a crash.
- The dummy tool only appends to a local log; nothing is sent anywhere. Reserved
  `.invalid` addresses are used for all recipients.
- Spotlight delimiters carry a tag derived by HMAC from the run seed and the case id: not
  guessable without the seed, but deterministic for reproducibility (anyone who knows the seed can
  compute it). Document text that tries to forge message markers or delimiters is neutralised.
- The manual-review CSV neutralises spreadsheet formula injection: any text cell starting with
  `=`, `+`, `-`, `@`, tab or carriage return gets a leading `'`.
- `notamper generate` only replaces case files directly inside `<out>/<format>/` and refuses to
  write into a directory that contains `handwritten/`.
- Reports escape all case and model text before emitting HTML; the HTML report is self-contained
  (no external scripts, fonts or requests).
- Budget limits (`--max-calls`, `--max-usd`) bound spending; the response cache prevents repeated
  paid calls after a restart.
- Scoring makes no network or model calls.
