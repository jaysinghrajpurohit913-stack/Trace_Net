"""TraceNet.   Run:  streamlit run app.py   (or double-click START_TraceNet)

This file only wires things together. Where to look:
  words / translations ........ tracenet/i18n.py        numbers & thresholds ... tracenet/config.py
  look and feel ............... tracenet/theme.py       the analysis order ..... tracenet/pipeline.py
  one screen per file ......... tracenet/ui/*.py         developer guide ........ DEVELOPING.md
"""
from pathlib import Path

import streamlit as st

from tracenet.theme import inject, hero, stepper
from tracenet.ui import step1_data, step2_check, results
from tracenet.ui.common import lang_switch, make_ctx

HERE = Path(__file__).parent
st.set_page_config(page_title="TraceNet", layout="wide", page_icon="🔎")
inject()

ss = st.session_state
for k, v in dict(step=1, parsed={}, manual=[], ds=None, is_demo=False, analysis=None, errors=[], intel=None).items():
    ss.setdefault(k, v)

with st.sidebar:
    lang_switch()
    ctx = make_ctx(HERE)
    if st.button(ctx.t("start_over"), width="stretch"):
        for k in ["step", "parsed", "manual", "ds", "is_demo", "analysis", "errors", "open_cid", "view", "pick_list", "intel", "files", "log_zone"]:
            ss.pop(k, None)
        st.rerun()
    st.caption(ctx.t("disclaimer"))

hero("TraceNet", ctx.t("app_sub"), ["Team ALTER", "R4C · PS05", "हिंदी · English"])
stepper(ss.step, [ctx.t("step1"), ctx.t("step2"), ctx.t("step3")])

{1: step1_data, 2: step2_check}.get(ss.step, results).render(ctx)
