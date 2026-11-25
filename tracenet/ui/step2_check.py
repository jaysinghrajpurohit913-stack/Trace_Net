"""Step 2: show what was understood, let the user link names/UPI ids to accounts, then go."""
import pandas as pd
import streamlit as st

from ..importer import ImportProblem, convert, unlinked_parties, apply_aliases


def render(ctx):
    t, ss = ctx.t, ctx.ss
    problem_text = ctx.problem_text
    st.subheader(t("check_title"))
    try:
        manual = pd.concat(ss.manual, ignore_index=True) if ss.manual else None
        ds0 = convert(ss.files, manual, ss.get("log_zone", ""))
    except ImportProblem as e:
        st.error(problem_text(e))
        if st.button(t("back")): ss.step = 1; st.rerun()
        st.stop()
    tx = ds0.tx
    m = st.columns(5)
    m[0].metric(t("c_tx"), f"{len(tx):,}"); m[1].metric(t("c_acc"), f"{ds0.acc.account_id.nunique():,}"); m[2].metric(t("c_comp"), len(ds0.comp))
    m[3].metric(t("c_range"), f"{tx.ts.min():%d %b %Y}" if tx.ts.min().date() == tx.ts.max().date() else f"{tx.ts.min():%d %b}–{tx.ts.max():%d %b}")
    m[4].metric(t("c_cash"), tx.dst.str.startswith("CASHOUT").sum())
    if len(ds0.domains) or len(ds0.iplog):
        st.caption(t("c_digital", d=len(ds0.domains), l=len(ds0.iplog)))
    for lvl, key, params in ds0.notes:
        {"warn": st.warning}.get(lvl, st.info)(t(f"note_{key}", **params))
    if ds0.comp.empty:
        st.error(t("no_complaint"))
    else:
        st.dataframe(ds0.comp[["complaint_id", "victim_account", "amount", "fraud_ts"]], hide_index=True, width="stretch")

    un = unlinked_parties(ds0)
    alias = {}
    if len(un):
        with st.expander("🔗 " + t("link_title")):
            st.caption(t("link_help"))
            un["same"] = ""
            ed = st.data_editor(un.rename(columns={"party": t("col_party"), "times": t("col_times"), "amount": t("col_amt"), "same": t("col_same")}),
                                hide_index=True, width="stretch", disabled=[t("col_party"), t("col_times"), t("col_amt")], key="alias_ed")
            alias = {r[t("col_party")]: r[t("col_same")] for _, r in ed.iterrows() if str(r[t("col_same")]).strip()}
    b1, b2 = st.columns([1, 5])
    if b1.button(t("back")): ss.step = 1; st.rerun()
    if b2.button(t("go"), type="primary", disabled=ds0.comp.empty):
        ss.ds = apply_aliases(ds0, alias); ss.is_demo = False; ss.analysis = None; ss.step = 3; st.rerun()
