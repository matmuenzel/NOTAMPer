from notamper.textnorm import contains_term, term_alternatives


def test_term_alternatives():
    assert term_alternatives("CLSD| CLOSED |") == ["CLSD", "CLOSED"]
    assert term_alternatives("A") == ["A"]
    assert term_alternatives("|") == []


def test_contains_term():
    assert contains_term("CLSD|CLOSED", "the runway is Closed")
    assert contains_term("U/S|OUT OF SERVICE", "ILS u / s")
    assert not contains_term("CLSD|CLOSED", "runway open")
    assert not contains_term("|", "anything")


def test_contains_term_word_boundaries():
    assert contains_term("FG", "VIS 0350 FG VV002")
    assert not contains_term("FG", "AFG FGX")
    assert not contains_term("31", "RWY 1310")
    assert contains_term("31", "RWY 31.")
    assert contains_term("13/31", "RWY 13/31 CLSD.")
    assert contains_term("+SN", "VIS 0800 +SN BKN010")
    assert not contains_term("1006", "Q1006")
    assert contains_term("Q1006|1006", "Q1006")
