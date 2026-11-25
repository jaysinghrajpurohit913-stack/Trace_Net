"""Shared pieces for every screen. `Ctx` is created once per run in app.py and handed to each screen."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import streamlit as st

from ..i18n import LANGS, make_t


@dataclass
class Ctx:
    lang: str
    t: object            # t("key", **params) -> text in the chosen language
    role: object         # role("victim_name") -> friendly column name
    ss: object           # st.session_state
    here: Path           # folder of app.py (data/, case_notes.json, cache live here)

    @property
    def li(self) -> int:
        """0 = English, 1 = Hindi: index into (English, Hindi) tuples."""
        return 1 if self.lang == LANGS[0] else 0

    # ---- small widgets used by many screens
    def money(self, x):
        return f"₹{x:,.0f}"

    def show_box(self, key):
        st.info(f"**{self.t('show_lbl')}** · {self.t(key)}", icon="👁️")

    def next_box(self, text):
        st.success(f"**{self.t('next_lbl')}** · {text}", icon="➡️")

    def glossary(self):
        with st.expander(self.t("gl_title")):
            q = st.text_input(self.t("gl_search"), key="gl_q").strip().lower()
            lines = [x for x in (self.t("gl_body") + self.t("gl_extra") + self.t("gl_digital")).split("\n") if x.strip()]
            st.markdown("\n".join(x for x in lines if q in x.lower()) if q else "\n".join(lines))

    def problem_text(self, e) -> str:
        return self.t(f"err_{e.key}", **e.params)

    def goto(self, view: str):
        self.ss.view = view

    def open_complaint(self, cid):
        """Button callback: jump to one complaint's file."""
        self.ss.open_cid = cid
        self.ss.view = "one"


def make_ctx(here: Path) -> Ctx:
    lang = st.session_state.get("lang", LANGS[0])
    t, role = make_t(lang)
    return Ctx(lang=lang, t=t, role=role, ss=st.session_state, here=here)


def lang_switch():
    """Sidebar language radio (must run before make_ctx so the choice is in session_state)."""
    return st.radio("भाषा / Language", LANGS, horizontal=True, key="lang")
