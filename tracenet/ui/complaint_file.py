"""One complaint = one 'file': card (who / when / how much / status / gang) -> headline -> what to do -> tabs.

To add a tab: write  def tab_xxx(ctx, f):  and add (label key, function) to TABS at the bottom. `f` (FileData) holds
everything a tab needs, so tabs never recompute the trail.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from ..engine import (trace_funds, freeze_list, trace_in_rounds, export_watchlist, precheck, lien_file, evaluate, pretty, short)
from ..explain import trail_nodes
from ..notes import STATUSES, load_notes, save_note
from ..report import build_report, bank_requests
from ..summary import case_brief
from ..theme import kpis, chip, file_header
from ..viz import story_figure


@dataclass
class FileData:
    an: object
    cid: str
    c: object            # the complaint row
    crow: object         # its row in the complaints table
    trail: object
    fl: pd.DataFrame     # freeze list
    brief: dict
    as_of: object
    seeds: list
    friendly: dict


def node_lines(ctx, nodes):
    """Plain-language line for every number drawn on the money-trail picture."""
    t = ctx.t
    for n in nodes:
        when = f"{n['t']:%d %b %H:%M}"
        bank = n["bank"] or "?"
        if n["kind"] == "cash":
            st.markdown(t("tr_cash", n=n["n"], acct=pretty(n["acct"], short_ids=True), recv=f"{n['recv']:,.0f}", t=when))
        elif n["kind"] == "inside":
            st.markdown(t("tr_inside", n=n["n"], acct=short(n["acct"]), bank=bank, recv=f"{n['recv']:,.0f}", held=f"{n['held']:,.0f}", t=when))
        elif n["kind"] == "unknown":
            st.markdown(t("tr_unknown", n=n["n"], acct=short(n["acct"]), bank=bank, recv=f"{n['recv']:,.0f}", t=when))
        else:
            d = t("tr_passed_d", m=n["delay"]) if n["delay"] is not None else ""
            st.markdown(t("tr_passed", n=n["n"], acct=short(n["acct"]), bank=bank, recv=f"{n['recv']:,.0f}", t=when, d=d))


def trail_next_text(ctx, nodes):
    t = ctx.t
    ins = [n for n in nodes if n["kind"] == "inside"]; unk = [n for n in nodes if n["kind"] == "unknown"]
    parts = []
    if ins:
        parts.append(t("tr_next_inside", n=len(ins), amt=f"{sum(n['held'] for n in ins):,.0f}"))
    if unk:
        parts.append(t("tr_next_unknown", n=len(unk)))
    if not parts:
        parts.append(t("tr_next_none"))
    return "  \n".join(parts)


# ------------------------------------------------------------------ the card ----
def card(ctx, an, cid, prefix, notes):
    t, ss = ctx.t, ctx.ss
    lk, c = an.lk, an.ds.comp[an.ds.comp.complaint_id == cid].iloc[0]
    crow = an.table[an.table.complaint_id == cid].iloc[0]
    lag_h = crow.delay_h if pd.notna(crow.delay_h) else None
    _st = ss.get(f"st_{prefix}{cid}", notes.get(cid, {}).get("status", "new"))
    chips = [chip(t("st_" + _st), dict(new="blue", investigating="amber", frozen="teal", closed="grey").get(_st, "blue"))]
    if lag_h is not None:
        chips.append(chip("⚡ " + t("in_hour").split(":")[0], "teal") if lag_h <= 1 else chip(f"⏳ {t('delay_val', h=lag_h)}", "amber"))
    if crow.case:
        chips.append(chip("🔗 " + lk.group_of.get(cid, ""), "red"))
    file_header("📁", f"{t('card_title')} · {cid}", f"{crow.victim_name or t('na')} · ₹{c.amount:,.0f} · {c.fraud_ts:%d %b %Y %H:%M}", chips)
    st.caption(t("card_help"))
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.2, 1.4])
        c1.markdown(f"**{t('card_who')}**")
        c1.markdown(f"{t('who_name')}: **{crow.victim_name or t('na')}**  \n{t('who_phone')}: **{crow.victim_phone or t('na')}**  \n"
                    f"{t('who_acct')}: **{short(c.victim_account)}**" + (f"  \n{t('who_upi')}: **{crow.victim_upi}**" if crow.victim_upi else ""))
        c2.markdown(f"**{t('card_when')}**")
        c2.markdown(f"{t('when_fraud')}: **{c.fraud_ts:%d %b %Y, %H:%M}**  \n"
                    f"{t('when_filed')}: **{(f'{c.reported_ts:%d %b %Y, %H:%M}' if pd.notna(c.reported_ts) else t('na'))}**  \n"
                    f"{t('when_delay')}: **{(t('delay_val', h=lag_h) if lag_h is not None else t('delay_unknown'))}**")
        if lag_h is not None:
            (c2.success if lag_h <= 1 else c2.warning)(t("in_hour") if lag_h <= 1 else t("late", h=lag_h))
        c3.markdown(f"**{t('card_money')}**")
        c3.metric(t("m_lost"), ctx.money(c.amount))
        c3.metric(t("m_inside"), ctx.money(crow.inside), help=t("ch_inside")); c3.metric(t("m_cash"), ctx.money(crow.cashed), help=t("ch_cash"))
        c4.markdown(f"**{t('cl_status')}**")
        cur = notes.get(cid, {})
        skey, nkey = f"st_{prefix}{cid}", f"nt_{prefix}{cid}"
        if skey not in ss:
            ss[skey] = cur.get("status", "new") if cur.get("status") in STATUSES else "new"
            ss[nkey] = cur.get("note", "")
        c4.selectbox(t("cl_status"), STATUSES, format_func=lambda x: t("st_" + x), key=skey, help=t("ch_status"), label_visibility="collapsed")
        c4.text_area(t("note_lbl"), key=nkey, height=70)
        if ss[skey] != cur.get("status", "new") or ss[nkey] != cur.get("note", ""):
            if save_note(ctx.here, prefix, cid, ss[skey], ss[nkey]):
                c4.caption("💾 " + t("note_saved"))
        gid = lk.group_of.get(cid, "")
        st.markdown(f"**{t('card_case')}**")
        grp = next((g for g in lk.groups if g["id"] == gid), None)
        if grp and len(grp["complaints"]) > 1:
            others = [x for x in grp["complaints"] if x != cid]
            st.markdown(t("case_with", gid=gid, n=len(others)))
            for col_, o in zip(st.columns(min(len(others), 6)), others[:6]):
                col_.button(t("case_open", cid=o), key=f"op_{o}", on_click=ctx.open_complaint, args=(o,))
        else:
            st.caption(t("case_single"))
        st.caption(f"{t('banks_inv')}: " + (", ".join(crow.banks) or "—"))
        dom = an.intel.domains[an.intel.domains.complaint_id.str.contains(cid, regex=False)] if len(an.intel.domains) else []
        if len(dom):
            st.caption("🌐 " + t("card_domains", d=", ".join(sorted({x for x in dom.domain if x} | {x for x in dom.ip if x}))))
    return c, crow, lag_h


# ------------------------------------------------------------------ tabs ----
def tab_trail(ctx, f):
    t = ctx.t
    nodes = trail_nodes(f.trail, f.an.feats)
    ctx.show_box("tr_show")
    st.plotly_chart(story_figure(f.trail, f.an.feats, nodes, t), width="stretch")
    st.markdown(f"#### {t('expl_lbl')}")
    st.markdown(t("tr_victim_line", acct=short(f.c.victim_account), amt=f"{f.c.amount:,.0f}", time=f"{f.c.fraud_ts:%d %b %H:%M}"))
    node_lines(ctx, nodes)
    st.caption(t("tr_warn"))
    ctx.next_box(trail_next_text(ctx, nodes))


def tab_act(ctx, f):
    t = ctx.t
    ctx.show_box("act_show"); st.caption(t("act_cols"))
    show = f.fl[["account_id", "bank", "hop", "tainted_still_held", "mule_score", "ring", "action"]].copy()
    show["account_id"] = show.account_id.map(pretty)
    st.dataframe(show.rename(columns=f.friendly), width="stretch", hide_index=True)
    st.download_button("⬇ " + t("dl_bank"), lien_file(f.fl, f.cid).to_csv(index=False), file_name=f"{f.cid}_bank_file.csv")
    ctx.next_box(t("act_next"))


def tab_suspects(ctx, f):
    t, feats, rings = ctx.t, f.an.feats, f.an.rings
    ctx.show_box("sus_show"); st.caption(t("sus_scale")); st.caption(t("sus_cap"))
    lb = feats[feats.mule_score > 0].sort_values("mule_score", ascending=False).head(30)
    if lb.empty:
        st.info(t("sus_none"))
    else:
        st.dataframe(lb[["bank", "mule_score", "reasons"]].rename(columns={"bank": f.friendly["bank"], "mule_score": f.friendly["mule_score"], "reasons": "Why / क्यों"}), width="stretch")
    ctx.next_box(t("sus_next"))
    st.markdown("#### " + t("gang_cap"))
    for i, r in enumerate(rings, 1):
        st.write(f"**{t('gang_n', i=i, n=len(r))}**: " + ", ".join(r))
    if not rings:
        st.caption(t("gang_none"))


def tab_ask_banks(ctx, f):
    t, ds = ctx.t, f.an.ds
    ctx.show_box("rd_show")
    rounds = trace_in_rounds(ds.tx, ds.acc, f.c.victim_account, f.c.fraud_ts, f.c.amount, as_of=f.as_of, seed_txn_ids=f.seeds)
    rn = st.slider(t("wave"), 0, max(len(rounds) - 1, 0), 0) if len(rounds) > 1 else 0
    R = rounds[rn]
    a1, a2 = st.columns(2)
    a1.metric(t("w_known"), len(R["trail"].depth)); a2.metric(t("w_banks"), len(R["ask"]))
    if len(R["trail"].edges):
        nodes = trail_nodes(R["trail"], f.an.feats, R["frontier"])
        st.plotly_chart(story_figure(R["trail"], f.an.feats, nodes, t, R["frontier"]), width="stretch")
        st.markdown(f"#### {t('expl_lbl')}"); node_lines(ctx, nodes)
    ctx.next_box(t("rd_next"))
    st.markdown(bank_requests(R, f.cid, f.c.fraud_ts))


def tab_report(ctx, f):
    t, ds, an = ctx.t, f.an.ds, f.an
    full = trace_funds(ds.tx, f.c.victim_account, f.c.fraud_ts, f.c.amount, seed_txn_ids=f.seeds)
    rep = build_report(f.c, full, freeze_list(full, an.feats, an.rings), an.rings, an.feats)
    st.download_button("⬇ " + t("dl_rep"), rep, file_name=f"{f.cid}_report.md")
    st.markdown(rep)


def tab_more(ctx, f):
    t, ds, an = ctx.t, f.an.ds, f.an
    st.subheader(t("wl_title"))
    wl = export_watchlist(an.feats, an.rings)
    st.dataframe(wl, width="stretch", hide_index=True)
    st.download_button("⬇ " + t("dl_wl"), wl.to_csv(index=False), file_name="tracenet_watchlist.csv")
    st.subheader(t("pre_title")); st.caption(t("pre_cap"))
    q1, q2 = st.columns(2)
    names = sorted(ds.acc.account_id)
    first = next((a for a in f.fl.account_id if a in names), names[0])
    target = q1.selectbox(t("pre_acc"), names, index=names.index(first))
    use_wl = q2.checkbox(t("pre_use"), value=True)
    res = precheck(ds.acc, ds.tx, target, f.c.fraud_ts, set(wl.account_id) if use_wl else (), an.rings)
    label = t("risk_" + res["level"]) + ": " + res["action"]
    {"HIGH": st.error, "MEDIUM": st.warning}.get(res["level"], st.success)(label)
    for r_ in res["reasons"]:
        st.write("• " + r_)


TABS = [("tab_trail", tab_trail), ("tab_act", tab_act), ("tab_sus", tab_suspects), ("tab_ask", tab_ask_banks), ("tab_rep", tab_report), ("tab_more", tab_more)]

FR = {"account_id": ("Account", "खाता"), "bank": ("Bank", "बैंक"), "hop": ("Steps from victim", "पीड़ित से कदम"),
      "tainted_still_held": ("Stolen money still inside (Rs)", "अभी अंदर चोरी का पैसा (रु.)"),
      "mule_score": ("Suspicion score (0-100)", "संदेह स्कोर (0-100)"), "ring": ("Gang", "गिरोह"), "action": ("What to do", "क्या करें")}


# ------------------------------------------------------------------ the page ----
def render(ctx, an, prefix, notes):
    t, ss = ctx.t, ctx.ss
    ds, comp = an.ds, an.ds.comp
    st.button(t("back_list"), on_click=lambda: ss.update(view="list"))
    ids = comp.complaint_id.tolist()
    cid = ss.get("open_cid") if ss.get("open_cid") in ids else ids[0]
    ss.open_cid = cid
    c, crow, lag_h = card(ctx, an, cid, prefix, notes)
    as_of = None
    if ds.time_known:
        default = int(min(max((lag_h or 24) * 60, 5), 24 * 60))
        with st.expander("⏱️ " + t("when_box")):
            mins = st.slider(t("when"), 5, 24 * 60, default, 5, key=f"tt_{cid}")
            st.caption(t("when_help"))
        as_of = c.fraud_ts + pd.Timedelta(minutes=mins)
    seeds = list(c.seed_ids) if "seed_ids" in comp and isinstance(c.seed_ids, (list, tuple)) else []
    trail = trace_funds(ds.tx, c.victim_account, c.fraud_ts, c.amount, as_of=as_of, seed_txn_ids=seeds)
    if trail.edges.empty:
        st.info(t("nothing_moved"))
        if not (ds.tx.src == c.victim_account).any():
            st.warning(t("note_victim_not_in_tx", cid=cid, acct=c.victim_account))
        return
    fl = freeze_list(trail, an.feats, an.rings)
    brief = case_brief(c, trail, fl, an.rings, an.feats)
    f = FileData(an=an, cid=cid, c=c, crow=crow, trail=trail, fl=fl, brief=brief, as_of=as_of, seeds=seeds, friendly={k: v[ctx.li] for k, v in FR.items()})
    held, cash = sum(trail.held.values()), sum(trail.cashed.values())
    st.subheader(t(brief["headline_k"][0], **brief["headline_k"][1]))
    kpis([("🧊", t("k_held"), ctx.money(held), t("k_held_h"), "amber"), ("💸", t("k_cash"), ctx.money(cash), t("k_cash_h"), "red"),
          ("🏦", t("k_acc"), f"{len(fl[~fl.is_cashout])}", t("tab_sus"), "teal")])
    st.markdown(f"### ✅ {t('todo')}")
    for i, (key, prm) in enumerate(brief["steps_k"], 1):
        st.markdown(f"**{i}.** {t(key, **prm)}")
    if brief["gang_k"]:
        st.info(t(brief["gang_k"][0], **brief["gang_k"][1]))
    for tab, (_, fn) in zip(st.tabs([t(k) for k, _ in TABS]), TABS):
        with tab:
            fn(ctx, f)
