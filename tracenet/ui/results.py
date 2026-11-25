"""Step 3: run the analysis ONCE per dataset, then show the screen chosen in the view switch."""
import streamlit as st

from ..engine import evaluate
from ..notes import load_notes
from ..pipeline import run_analysis
from . import complaint_file, complaints, digital_page, links_page, workspace_page

VIEWS = ["list", "one", "links", "digital", "workspace"]


def get_analysis(ctx):
    """Cached in the session. `ss.intel` (public-lookup results) replaces the imported indicator tables when present."""
    ss = ctx.ss
    key = (id(ss.ds), id(ss.get("intel")), ss.get("log_zone", ""))
    if ss.get("analysis") is None or ss.analysis[0] != key:
        with st.spinner("…"):
            ss.analysis = (key, run_analysis(ss.ds, ss.get("intel"), ss.get("log_zone", "")))
    return ss.analysis[1]


def render(ctx):
    t, ss = ctx.t, ctx.ss
    if ss.ds is None:
        ss.step = 1; st.rerun()
    an = get_analysis(ctx)
    if ss.get("view") not in VIEWS:
        ss.view = "list"
    view = st.radio(" ", VIEWS, format_func=lambda v: t("view_" + v), horizontal=True, label_visibility="collapsed", key="view")
    st.caption(t("g3_help")); ctx.glossary()
    prefix = "demo:" if ss.is_demo else "data:"
    notes = load_notes(ctx.here, prefix)
    an.table["status"] = an.table.complaint_id.map(lambda c: notes.get(c, {}).get("status", "new"))
    if ss.is_demo and (ctx.here / "data/ground_truth.csv").exists():
        import pandas as pd
        with st.sidebar:
            with st.expander(t("test_title")):
                mm = evaluate(an.feats, pd.read_csv(ctx.here / "data/ground_truth.csv"))
                st.write(t("test_body", tp=mm["tp"], tot=mm["tp"] + mm["fn"], fp=mm["fp"]))
    if view == "list":
        complaints.render(ctx, an)
    elif view == "one":
        complaint_file.render(ctx, an, prefix, notes)
    elif view == "links":
        links_page.render(ctx, an)
    elif view == "digital":
        digital_page.render(ctx, an)
    else:
        workspace_page.render(ctx, an, prefix, notes)
