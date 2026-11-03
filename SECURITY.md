# Security policy

## Vulnerabilities in NOTAMper itself

If you find a vulnerability in the tool (for example key leakage, unsafe handling of provider
responses, injection into generated reports, or unsafe file handling), please report it privately
through GitHub private vulnerability reporting: open the repository's **Security** tab and choose
**Report a vulnerability**. Do not open a public issue. Please include the version, a minimal
reproduction, and the impact you expect. We aim to acknowledge reports within a few days.

The design of the tool's own hardening is described in `docs/threat-model.md`.

## Model weaknesses found with the benchmark

NOTAMper exists to show that models can be manipulated through embedded text. That general
weakness is well known and not a vulnerability in this repository. If your results show a
weakness in a specific model or product that goes beyond the generally known susceptibility to
indirect prompt injection, report it to the vendor through their disclosure channel first, and
publish only after they had a reasonable chance to respond. See `docs/ethics.md`.

## Supported versions

Only the latest release on the default branch receives fixes.
