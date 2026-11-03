# Ethics and responsible use

## Fictional data

All texts are synthetic. Aerodromes use the fictional `ZZ` prefix (for example ZZQA), the FIR is
`ZZXX`, and reference numbers and coordinates are invented. No real NOTAM, METAR or ATIS was
copied or altered, and the benchmark has no connection to real aviation systems. Texts imitate
the public notation style only; they do not reproduce standard texts.

## Harmless goals

Injected instructions are harmless and verifiable: output a canary word, omit a fictional closure,
or call a dummy tool that only writes a local log to a reserved `.invalid` address. The corpus
contains no harmful payloads and is meant to expose weaknesses, not to make them exploitable.
Contributions with harmful goals, real identifiers or operational detail will be rejected.

## Not for operational use

NOTAMper is a research and engineering tool. Results must not inform operational aviation
decisions, and nothing here is certified, validated, or approved for flight use. The assistants
under test must never be used as a source for flight planning.

## Responsible disclosure

The general susceptibility of language models to indirect prompt injection is well known. If a run
shows a weakness in a specific model or product that goes beyond that, notify the vendor through
their disclosure channel before publishing and allow reasonable time to respond. Report results
with the model id and date and avoid framing that singles out a vendor beyond what the data shows.

## Dual use

A corpus of injections could be misused. The attacks here are generic, public in style, and
bounded to harmless goals; the repository is not an attack toolkit and does not automate attacks
against real systems.

## Licensing

Code: MIT. Corpus (`cases/`): CC BY 4.0.
