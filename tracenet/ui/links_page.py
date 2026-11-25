"""Connections between complaints: new-complaint alert, gang cases, shared accounts, time pattern, combined report."""
import pandas as pd
import streamlit as st

from ..engine import pretty, short
from ..explain import shared_nodes
from ..linking import alert_for, group_report, group_bank_file
from ..viz import network_figure, timeline_figure, hour_figure, split_figure


def render(ctx, an):
    """The 'connections between complaints' screen."""
    t, show_box, next_box, money = ctx.t, ctx.show_box, ctx.next_box, ctx.money
    lk = an.lk
    friendly_gang = "Gang / गिरोह"
    comp = lk.comp
    if len(comp) < 2:
        st.info(t("lk_one")); return
    multi = [g for g in lk.groups if len(g["complaints"]) > 1]
    single = [g for g in lk.groups if len(g["complaints"]) == 1]
    st.subheader(t("lk_headline", g=len(multi), n=len(comp), s=len(single)))
    with st.expander(t("lk_how")):
        st.markdown(t("lk_how_body"))

    def reasons_text(rs):
        return "; ".join(t(f"lk_r_{k}", **d) for k, d in rs)

    def group_line(g):
        ex = t("lk_group_ex", e=len(g["exits"])) if g["exits"] else ""
        return t("lk_group_sum", n=len(g["complaints"]), lost=f"{g['lost']:,.0f}", k=len(g["shared"]), ex=ex, inside=f"{g['inside']:,.0f}")

    # ---- new-complaint alert (always visible: this is the most useful thing at the desk)
    arrival = comp.set_index("complaint_id").apply(lambda r: r.reported_ts if pd.notna(r.reported_ts) else r.fraud_ts, axis=1)
    st.markdown(f"#### 🔔 {t('alert_title')}")
    newc = st.selectbox(t("alert_pick"), arrival.sort_values(ascending=False).index.tolist(), key="alert_pick")
    al = alert_for(lk, newc)
    if len(al["links"]):
        st.error(t("alert_yes", n=len(al["links"]), gid=al["group"], inside=f"{al['inside']:,.0f}"))
        st.dataframe(pd.DataFrame({t("col_compl"): al["links"].other, t("col_level"): al["links"].level.map(lambda x: t("lvl_" + x)),
                                   t("col_score"): al["links"].score, t("col_reason"): al["links"].reasons.map(reasons_text)}), hide_index=True, width="stretch")
        if al["shared_accounts"]:
            st.write(f"**{t('alert_shared')}:** " + ", ".join(pretty(a) for a in al["shared_accounts"]))
    else:
        st.success(t("alert_no"))
    st.divider()
    if not multi:
        st.info(t("lk_none")); return

    labels = {g["id"]: f"{g['id']} · {len(g['complaints'])} · ₹{g['lost']:,.0f}" for g in multi}
    gid = st.selectbox(t("lk_pick_group"), list(labels), format_func=labels.get, key="lk_group")
    g = next(x for x in multi if x["id"] == gid)
    st.info(group_line(g))
    k1, k2, k3 = st.columns(3)
    k1.metric(t("k_held"), money(g["inside"])); k2.metric(t("k_cash"), money(g["cashed"])); k3.metric(t("c_comp"), len(g["complaints"]))
    ta, tb, tc, td, te = st.tabs([t("lk_tab_sum"), t("lk_tab_net"), t("lk_tab_shared"), t("lk_tab_time"), t("lk_tab_rep")])
    pr = lk.pairs[lk.pairs.a.isin(g["complaints"]) & lk.pairs.b.isin(g["complaints"])]
    with ta:
        st.caption(t("how_group", s=g["strong"], p=g["probable"]))
        st.markdown(f"**{t('lk_why')}**")
        st.dataframe(pd.DataFrame({t("col_a"): pr.a, t("col_b"): pr.b, t("col_level"): pr.level.map(lambda x: t("lvl_" + x)), t("col_score"): pr.score,
                                   t("col_reason"): pr.reasons.map(reasons_text)}), hide_index=True, width="stretch")
        for o in multi:
            if o["id"] != gid:
                with st.expander(f"{o['id']}: {', '.join(o['complaints'])}"):
                    st.write(group_line(o))
        if single:
            st.caption(f"{t('lk_alone')}: " + ", ".join(x["complaints"][0] for x in single))
    with tb:
        show_box("net_show")
        c1, c2 = st.columns(2)
        sa = c1.checkbox(t("lk_show_all"), value=False); ag = c2.checkbox(t("lk_all_groups"), value=False)
        cids = [c for x in multi for c in x["complaints"]] if ag else g["complaints"]
        ranked = shared_nodes(lk, cids)
        st.plotly_chart(network_figure(lk, cids, show_all=sa, ranked=ranked), width="stretch")
        st.caption(t("lk_net_cap"))
        st.markdown(f"#### {t('expl_lbl')}")
        for r in ranked:
            if r["is_exit"]:
                st.markdown(t("net_line_exit", n=r["n"], acct=pretty(r["acct"], short_ids=True), k=r["k"], total=f"{r['total']:,.0f}"))
            else:
                st.markdown(t("net_line", n=r["n"], acct=short(r["acct"]), bank=r["bank"] or "?", k=r["k"], total=f"{r['total']:,.0f}",
                              inside=f"{r['inside']:,.0f}", score=f"{r['score']:.0f}"))
        next_box(t("net_next"))
    with tc:
        show_box("lk_sh_cap")
        sh = lk.shared[lk.shared.account.isin(g["shared"])]
        st.dataframe(pd.DataFrame({t("col_acc"): sh.account, t("col_bank"): sh.bank, t("col_n"): sh.n, t("col_which"): sh.complaints,
                                   t("col_total"): sh.total.round(0), t("col_inside2"): sh.inside.round(0), t("col_mule"): sh.score.round(0),
                                   friendly_gang: sh.ring, t("col_firstuse"): sh.first_use.dt.strftime("%d-%b %H:%M"),
                                   t("col_lastuse"): sh.last_use.dt.strftime("%d-%b %H:%M"), t("col_fh"): sh.first_hop_in}), hide_index=True, width="stretch")
        ex = lk.exits[lk.exits.account.isin(g["exits"])]
        if len(ex):
            st.markdown(f"**{t('lk_exits')}**")
            st.dataframe(pd.DataFrame({t("col_acc"): ex.account.map(pretty), t("col_n"): ex.n, t("col_which"): ex.complaints, t("col_total"): ex.total.round(0)}),
                         hide_index=True, width="stretch")
        st.markdown(f"**{t('lk_split')}**"); show_box("sp_show")
        st.plotly_chart(split_figure(lk, gid), width="stretch")
        st.caption(t("lk_split_cap")); next_box(t("sp_next"))
        with st.expander(t("lk_split_tbl")):
            sp = lk.split[lk.split.complaint.isin(g["complaints"]) & lk.split.account.isin(g["shared"])]
            st.dataframe(pd.DataFrame({t("col_acc"): sp.account, t("col_compl"): sp.complaint, t("col_total"): sp.received.round(0), t("col_inside2"): sp.still_inside.round(0)}),
                         hide_index=True, width="stretch")
    with td:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(t("tm_window"), f"{g['start']:%d %b %H:%M} → {g['end']:%d %b %H:%M}")
        if g["gap_h"] is not None: m2.metric(t("tm_gap"), t("tm_gap_u", h=g["gap_h"]))
        if g["speed_min"] is not None: m3.metric(t("tm_speed"), t("tm_speed_u", m=g["speed_min"]))
        night = sum(n for h, n in g["hours"].items() if h < 6 or h >= 22)
        m4.metric(t("tm_night"), f"{night} / {len(g['complaints'])}")
        if g["speed_min"] is not None and g["speed_min"] <= 60: st.warning(t("tm_ins_fast", m=g["speed_min"]))
        if night >= max(2, len(g["complaints"]) / 2): st.warning(t("tm_ins_night"))
        if g["gap_h"] is not None and g["gap_h"] <= 24: st.info(t("tm_ins_gap", h=g["gap_h"]))
        st.markdown(f"**{t('tm_hours')}**"); show_box("hr_show")
        st.plotly_chart(hour_figure(g["hours"]), width="stretch"); next_box(t("hr_next"))
        st.markdown(f"**{t('tm_tl')}**"); show_box("tl_show")
        st.plotly_chart(timeline_figure(lk, gid), width="stretch"); st.caption(t("tm_tl_cap")); next_box(t("tl_next"))
        st.markdown(f"**{t('tm_new')}**")
        st.dataframe(pd.DataFrame({t("col_day"): [str(d) for d in g["new_per_day"]], t("col_newacc"): list(g["new_per_day"].values())}), hide_index=True)
    with te:
        st.write(f"**{t('lk_banks')}:** " + ", ".join(f"{b} ({n})" for b, n in g["banks"].items()))
        st.caption(t("lk_bank_cap"))
        bf = group_bank_file(lk, gid)
        st.dataframe(bf, hide_index=True, width="stretch")
        d1, d2 = st.columns(2)
        d1.download_button("⬇ " + t("lk_dl_rep"), group_report(lk, gid), file_name=f"{gid}_combined_report.md")
        d2.download_button("⬇ " + t("lk_dl_bank"), bf.to_csv(index=False), file_name=f"{gid}_bank_file.csv")
        st.markdown(group_report(lk, gid))
