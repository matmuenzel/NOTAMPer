"""Format grammar checks for NOTAM, METAR, ATIS and generic documents."""

from __future__ import annotations

import re

_NOTAM_HEAD = re.compile(r"^[A-Z]\d{4}/\d{2} NOTAM[NRC]")
_METAR_HEAD = re.compile(r"^(METAR|SPECI) ZZ[A-Z]{2} \d{6}Z ")
_METAR_WIND = re.compile(r"(?<=\s)(\d{5}|VRB\d{2})(G\d{2})?KT(?=\s|=|$)")
_ATIS_HEAD = re.compile(r"^ZZ[A-Z]{2} (ARRIVAL |DEPARTURE )?ATIS INFORMATION [A-Z]\b")
_ATIS_ACK = re.compile(r"ACKNOWLEDGE (RECEIPT OF )?INFORMATION [A-Z]\b")

_NOTAM_FIELDS = (
    ("Q) ZZ", re.compile(r"^Q\) ZZ", re.MULTILINE)),
    ("A) ZZxx", re.compile(r"(?:^|\s)A\) ZZ[A-Z]{2}(?=\s|$)", re.MULTILINE)),
    ("B) <10 digits>", re.compile(r"(?:^|\s)B\) \d{10}(?=\s|$)", re.MULTILINE)),
    ("C) <10 digits>|PERM", re.compile(r"(?:^|\s)C\) (\d{10}|PERM)(?=\s|$)", re.MULTILINE)),
    ("E) ", re.compile(r"^E\) ", re.MULTILINE)),
)


def _notam(text: str) -> list[str]:
    errors = []
    lines = text.strip().splitlines()
    if not lines or not _NOTAM_HEAD.match(lines[0]):
        errors.append("NOTAM: first line must match 'A0123/26 NOTAM[NRC]'")
    for label, pattern in _NOTAM_FIELDS:
        if not pattern.search(text):
            errors.append(f"NOTAM: missing or malformed field {label}")
    return errors


def _metar(text: str) -> list[str]:
    errors = []
    stripped = text.strip()
    if not _METAR_HEAD.match(stripped):
        errors.append("METAR: must start with 'METAR|SPECI ZZxx ddhhmmZ '")
    if not _METAR_WIND.search(stripped):
        errors.append("METAR: missing wind group")
    if not stripped.endswith("="):
        errors.append("METAR: must end with '='")
    return errors


def _atis(text: str) -> list[str]:
    errors = []
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    if not lines or not _ATIS_HEAD.match(lines[0]):
        errors.append(
            "ATIS: first line must match 'ZZxx [ARRIVAL |DEPARTURE ]ATIS INFORMATION x'"
        )
    if not re.search(r"\b(RUNWAY|RWY)\b", text):
        errors.append("ATIS: must mention RUNWAY or RWY")
    if not lines or not _ATIS_ACK.search(lines[-1]):
        errors.append("ATIS: last line must be 'ACKNOWLEDGE [RECEIPT OF ]INFORMATION x'")
    return errors


def _generic(text: str) -> list[str]:
    return [] if text.strip() else ["generic: document must not be empty"]


_VALIDATORS = {"notam": _notam, "metar": _metar, "atis": _atis, "generic": _generic}


def validate_document(fmt: str, text: str) -> list[str]:
    """Return grammar violations for a document in the given format (empty = valid)."""
    validator = _VALIDATORS.get(fmt)
    if validator is None:
        return [f"unknown format: {fmt}"]
    return validator(text)
