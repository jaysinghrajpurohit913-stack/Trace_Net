import re
from tracenet.i18n import T, ROLE


def test_every_text_has_both_languages():
    bad = [k for k, v in T.items() if not (isinstance(v, tuple) and len(v) == 2 and all(str(x).strip() for x in v))]
    assert not bad, bad


def test_placeholders_match_between_languages():
    pat = re.compile(r"\{(\w+)")
    bad = [k for k, (en, hi) in T.items() if set(pat.findall(en)) != set(pat.findall(hi))]
    assert not bad, bad


def test_role_names_bilingual():
    assert all(len(v) == 2 and all(v) for v in ROLE.values())
