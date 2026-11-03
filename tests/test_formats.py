import pytest

from notamper.cases.formats import validate_document

NOTAM = (
    "A0123/26 NOTAMN\nQ) ZZXX/QMRLC/IV/NBO/A/000/999\nA) ZZQA\n"
    "B) 2601010000\nC) PERM\nE) RWY 07/25 CLSD\n"
)
METAR = "METAR ZZQA 011200Z 27015G25KT 9999 FEW030 15/08 Q1013="
ATIS = (
    "ZZQA ARRIVAL ATIS INFORMATION B\nRWY 07 IN USE\n"
    "ACKNOWLEDGE RECEIPT OF INFORMATION B\n"
)

VALID = [("notam", NOTAM), ("metar", METAR), ("metar", "SPECI ZZQB 011200Z VRB03KT CAVOK="),
         ("atis", ATIS), ("generic", "hello"),
         ("notam", NOTAM.replace("C) PERM", "C) 2601012359"))]


@pytest.mark.parametrize("fmt,text", VALID)
def test_valid(fmt, text):
    assert validate_document(fmt, text) == []


INVALID = [
    ("notam", NOTAM.replace("NOTAMN", "FOO")),
    ("notam", NOTAM.replace("Q) ZZ", "Q) EG")),
    ("notam", NOTAM.replace("A) ZZQA", "A) EGLL")),
    ("notam", NOTAM.replace("B) 2601010000\n", "")),
    ("notam", NOTAM.replace("C) PERM", "C) SOON")),
    ("notam", NOTAM.replace("E) ", "F) ")),
    ("metar", METAR.replace("ZZQA", "EGLL")),
    ("metar", METAR.replace("27015G25KT", "27015")),
    ("metar", METAR.rstrip("=")),
    ("atis", ATIS.replace("ZZQA", "EGLL")),
    ("atis", ATIS.replace("RWY", "STRIP")),
    ("atis", ATIS.replace("ACKNOWLEDGE", "THANKS")),
    ("notam", NOTAM.replace("C) PERM", "C) PERMANENT")),
    ("notam", NOTAM.replace("B) 2601010000", "B) 26010100001")),
    ("atis", ATIS.replace("INFORMATION B\nRWY", "INFORMATION BB\nRWY")),
    ("atis", ATIS.replace("RWY 07 IN USE", "XRWYX 07 IN USE")),
    ("atis", ATIS.replace("RECEIPT OF INFORMATION B", "RECEIPT OF INFORMATION BX")),
    ("generic", "  \n"),
    ("bogus", "x"),
]


@pytest.mark.parametrize("fmt,text", INVALID)
def test_invalid(fmt, text):
    assert validate_document(fmt, text)


def test_notam_abc_on_one_line_and_separate_lines():
    one = (
        "A0001/26 NOTAMN\nQ) ZZXX/QMRLC/IV/NBO/A/000/999/4500N01000E005\n"
        "A) ZZQA B) 2611010600 C) PERM\nE) RWY 07/25 CLSD."
    )
    assert validate_document("notam", one) == []
    sep = one.replace("A) ZZQA B)", "A) ZZQA\nB)").replace("2611010600 C)", "2611010600\nC)")
    assert validate_document("notam", sep) == []
    assert validate_document("notam", one.replace("PERM", "PERMANENT"))
    assert validate_document("notam", one.replace("2611010600", "26110106001"))
