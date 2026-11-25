"""Smoke test: open every screen in both languages and make sure nothing raises."""
import pytest
from streamlit.testing.v1 import AppTest

VIEWS = ["list", "one", "links", "digital", "workspace"]


@pytest.mark.slow
def test_every_screen_both_languages():
    at = AppTest.from_file(str(__import__("pathlib").Path(__file__).resolve().parents[1] / "app.py"), default_timeout=180).run()
    next(b for b in at.button if "डेमो" in b.label).click(); at.run()
    for i in (0, 1):
        at.radio(key="lang").set_value(at.radio(key="lang").options[i]).run()
        for v in VIEWS:
            at.radio(key="view").set_value(v).run()
            assert not at.exception, (i, v, [e.value for e in at.exception])
