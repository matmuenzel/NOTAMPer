# Contributing

Thanks for helping. The most useful contributions are new cases, better scoring rules, and
additional model adapters.

## Setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
make lint test validate
```

Python 3.10 or newer. Runtime dependencies are limited to `pyyaml` and `jsonschema`; please do not
add provider SDKs (adapters use `urllib.request`).

## Ground rules

- Test-first: add or change a test before the behaviour. `pytest -q` and `ruff check src tests`
  must pass; CI also runs `notamper validate` and a mock smoke run.
- Type hints and short docstrings. Everything in English.
- The scoring package must stay deterministic and free of network or model calls.
- API keys come from environment variables only and must never reach logs, caches, errors, or
  reports.
- Never edit `cases/generated/` by hand. Change the generator and run `make generate`.

## Corpus rules

All content must be fictional and harmless; see `docs/ethics.md` and `docs/adding-cases.md`.
Aerodromes are `ZZ` plus two letters, the FIR is `ZZXX`. No real NOTAMs, no real aerodromes,
no harmful goals. Every attack case needs a matching control.

## Pull requests

Keep PRs focused, describe the motivation, and mention whether results of previous runs change.
If a scoring rule changes, rerun the affected runs rather than editing recorded results.
Code contributions are MIT licensed, corpus contributions CC BY 4.0.
