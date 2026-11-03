"""Text normalisation shared by corpus checks and scoring."""

from __future__ import annotations

import re

_WS = re.compile(r"\s+")
_SLASH = re.compile(r"\s*/\s*")


def normalize(s: str) -> str:
    """Uppercase, collapse whitespace, and remove spaces around ``/``."""
    s = _WS.sub(" ", s.upper()).strip()
    return _SLASH.sub("/", s)


def term_alternatives(term: str) -> list[str]:
    """Split an expectation term on ``|`` into stripped, non-empty alternatives."""
    return [alt.strip() for alt in term.split("|") if alt.strip()]


def contains_term(term: str, text: str) -> bool:
    """True if any alternative of ``term`` occurs in ``text`` as a whole token.

    Both sides are normalised; an alternative must not be glued to a letter or digit
    on either side, so ``FG`` does not match ``AFG`` and ``31`` does not match ``1310``.
    """
    haystack = normalize(text)
    for alt in term_alternatives(term):
        pattern = rf"(?<![A-Z0-9]){re.escape(normalize(alt))}(?![A-Z0-9])"
        if re.search(pattern, haystack):
            return True
    return False
