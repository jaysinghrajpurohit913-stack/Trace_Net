"""The complaints list with the search bar and filters."""
import pandas as pd
import streamlit as st

from ..theme import kpis

from ..engine import short
from ..notes import STATUSES


def render(ctx, an):
    t, ss = ctx.t, ctx.ss
    ct = an.table
    open_cid = ctx.open_complaint
    st.subheader(t("list_title")); st.caption(t("list_help"))
    kpis([("📋", t("list_title"), f"{len(ct)}", t("cl_amt") + f": ₹{ct.amount.sum():,.0f}", "teal"),
          ("🆕", t("st_new"), f"{int((ct.status == 'new').sum())}", t("st_investigating") + f": {int((ct.status == 'investigating').sum())}", "blue"),
          ("🧊", t("st_frozen"), f"{int((ct.status == 'frozen').sum())}", t("st_closed") + f": {int((ct.status == 'closed').sum())}", "amber"),
          ("🔗", t("cl_case"), f"{ct.case[ct.case != ''].nunique()}", t("cl_inside") + f": ₹{ct.inside.sum():,.0f}", "red")])
    q = st.text_input(t("search_lbl"), placeholder=t("search_ph"), help=t("search_help"), key="q").strip().lower()
    with st.expander("🎚️ " + t("flt_title")):
        f1, f2, f3, f4 = st.columns(4)
        allbanks = sorted({b for bl in ct.banks for b in bl})
        fb = f1.multiselect(t("flt_bank"), allbanks)
        d0, d1 = ct.fraud_ts.min().date(), ct.fraud_ts.max().date()
        fd = f2.date_input(t("flt_date"), (d0, d1), min_value=d0, max_value=d1) if d0 < d1 else (d0, d1)
        amax = float(ct.amount.max())
        fa = f3.slider(t("flt_amt"), 0.0, amax, (0.0, amax)) if amax > 0 else (0.0, 0.0)
        fs = f4.multiselect(t("flt_status"), STATUSES, format_func=lambda x: t("st_" + x))
        fc = st.checkbox(t("flt_case"))
    r = ct
    for w in q.split():
        r = r[r.blob.str.contains(w, regex=False)]
    if fb: r = r[r.banks.map(lambda bl: bool(set(bl) & set(fb)))]
    if isinstance(fd, (tuple, list)) and len(fd) == 2:
        r = r[(r.fraud_ts.dt.date >= fd[0]) & (r.fraud_ts.dt.date <= fd[1])]
    r = r[(r.amount >= fa[0]) & (r.amount <= fa[1])]
    if fs: r = r[r.status.isin(fs)]
    if fc: r = r[r.case != ""]

    def matched(row):
        hits = []
        for w in q.split():
            if w in row.complaint_id.lower(): hits.append(t("cl_id"))
            elif w in (row.victim_name + " " + row.victim_phone).lower(): hits.append(t("cl_victim"))
            elif w in (row.victim_account + " " + row.victim_upi).lower(): hits.append(t("who_acct"))
            elif any(w in m.lower() for m in row.mules): hits.append("🕸 " + next(short(m) for m in row.mules if w in m.lower()))
            elif any(w in b.lower() for b in row.banks): hits.append(t("flt_bank"))
            elif w in row.case.lower(): hits.append(t("cl_case"))
        return ", ".join(dict.fromkeys(hits))
    st.markdown(f"**{t('res_n', k=len(r), n=len(ct))}**")
    if r.empty:
        st.info(t("res_none"))
    else:
        tab = pd.DataFrame({
            t("cl_id"): r.complaint_id, t("cl_victim"): r.victim_name.replace("", "—"), t("cl_phone"): r.victim_phone.replace("", "—"),
            t("cl_fraud"): r.fraud_ts.dt.strftime("%d %b %Y %H:%M"),
            t("cl_filed"): r.reported_ts.dt.strftime("%d %b %Y %H:%M").fillna("—"),
            t("cl_delay"): r.delay_h.round(1), t("cl_amt"): r.amount.round(0),
            t("cl_status"): r.status.map(lambda x: t("st_" + x)), t("cl_case"): r.case.replace("", "—"),
            t("cl_inside"): r.inside.round(0), t("cl_cash"): r.cashed.round(0)})
        if q:
            tab[t("cl_match")] = r.apply(matched, axis=1)
        cc = st.column_config
        cfg = {t("cl_id"): cc.TextColumn(help=t("ch_id")), t("cl_victim"): cc.TextColumn(help=t("ch_victim")), t("cl_fraud"): cc.TextColumn(help=t("ch_fraud")),
               t("cl_filed"): cc.TextColumn(help=t("ch_filed")), t("cl_delay"): cc.NumberColumn(help=t("ch_delay")),
               t("cl_amt"): cc.NumberColumn(format="₹%d"), t("cl_status"): cc.TextColumn(help=t("ch_status")), t("cl_case"): cc.TextColumn(help=t("ch_case")),
               t("cl_inside"): cc.NumberColumn(format="₹%d", help=t("ch_inside")), t("cl_cash"): cc.NumberColumn(format="₹%d", help=t("ch_cash"))}
        st.caption(t("click_hint"))
        ev = st.dataframe(tab, hide_index=True, width="stretch", column_config=cfg, on_select="rerun", selection_mode="single-row", key="ct_tbl")
        ids = r.complaint_id.tolist()
        sel = ev.selection.rows[0] if ev.selection.rows else 0
        sel = sel if sel < len(ids) else 0
        if ev.selection.rows:
            ss.pick_list = ids[sel]
        pick = st.selectbox(t("open_pick"), ids, index=ids.index(ss.pick_list) if ss.get("pick_list") in ids else 0,
                            format_func=lambda c_: f"{c_} · {ct.set_index('complaint_id').victim_name.get(c_, '') or '—'} · ₹{ct.set_index('complaint_id').amount[c_]:,.0f}")
        st.button(t("open_btn"), type="primary", on_click=open_cid, args=(pick,))
