"""TraceNet dashboard.  Run:  streamlit run app.py   (or double-click START_TraceNet)

Three simple steps:  1 Add data  ->  2 Check  ->  3 Result
All the words are in tracenet/i18n.py (Hindi + English).
"""
import datetime as dt
from pathlib import Path

import pandas as pd
import streamlit as st

from tracenet.engine import (account_features, score_mules, link_entities, link_by_flow, merge_rings, trace_funds, freeze_list,
                             trace_in_rounds, export_watchlist, precheck, lien_file, evaluate, pretty, short)
from tracenet.i18n import LANGS, make_t
from tracenet.importer import (ImportProblem, KINDS, REQUIRED, SYN, load_file, detect_roles, guess_owner, convert, make_complaint,
                               unlinked_parties, apply_aliases, load_demo)
from tracenet.theme import inject, hero, stepper, kpis, chip, file_header
from tracenet.notes import STATUSES, load_notes, save_note
from tracenet.report import build_report, bank_requests
from tracenet.summary import case_brief
from tracenet.templates import template_xlsx
from tracenet.linking import analyse_links, alert_for, group_report, group_bank_file, complaint_table
from tracenet.explain import trail_nodes, shared_nodes
from tracenet.viz import story_figure, network_figure, timeline_figure, hour_figure, split_figure

HERE = Path(__file__).parent
st.set_page_config(page_title="TraceNet", layout="wide", page_icon="🔎")
inject()
ss = st.session_state
for k, v in dict(step=1, parsed={}, manual=[], ds=None, is_demo=False, analysis=None, errors=[]).items():
    ss.setdefault(k, v)

# ------------------------------------------------------------------ sidebar ----
with st.sidebar:
    lang = st.radio("भाषा / Language", LANGS, horizontal=True, key="lang")
    t, role_name = make_t(lang)
    if st.button(t("start_over"), width="stretch"):
        for k in ["step", "parsed", "manual", "ds", "is_demo", "analysis", "errors", "open_cid", "view", "pick_list"]:
            ss.pop(k, None)
        st.rerun()
    st.caption(t("disclaimer"))

hero("TraceNet", t("app_sub"), ["Team ALTER", "R4C · PS05", "हिंदी · English"])
stepper(ss.step, [t("step1"), t("step2"), t("step3")])

KIND_NAME = {k: t(f"kind_{k}") for k in KINDS}


def problem_text(e: ImportProblem) -> str:
    return t(f"err_{e.key}", **e.params)


def money(x):
    return f"₹{x:,.0f}"


def show_box(key):
    st.info(f"**{t('show_lbl')}** · {t(key)}", icon="👁️")


def next_box(text):
    st.success(f"**{t('next_lbl')}** · {text}", icon="➡️")


def glossary():
    with st.expander(t("gl_title")):
        q = st.text_input(t("gl_search"), key="gl_q").strip().lower()
        lines = [x for x in (t("gl_body") + t("gl_extra")).split("\n") if x.strip()]
        st.markdown("\n".join(x for x in lines if q in x.lower()) if q else "\n".join(lines))


friendly_gang = "Gang / गिरोह"


def open_cid(cid):
    """Button callback: jump to one complaint's file."""
    ss.open_cid = cid
    ss.view = "one"


def node_lines(nodes):
    """Plain-language line for every number drawn on the money-trail picture."""
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


def trail_next_text(nodes):
    ins = [n for n in nodes if n["kind"] == "inside"]; unk = [n for n in nodes if n["kind"] == "unknown"]
    parts = []
    if ins:
        parts.append(t("tr_next_inside", n=len(ins), amt=f"{sum(n['held'] for n in ins):,.0f}"))
    if unk:
        parts.append(t("tr_next_unknown", n=len(unk)))
    if not parts:
        parts.append(t("tr_next_none"))
    return "  \n".join(parts)


def render_links(lk):
    """The 'connections between complaints' screen."""
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


# ================================================================== STEP 1 ====
if ss.step == 1:
    left, right = st.columns([3, 2])
    with left:
        st.subheader(t("upload_title"))
        st.caption(t("upload_help"))
        ups = st.file_uploader(" ", accept_multiple_files=True, type=["csv", "xlsx", "xls", "xlsm", "pdf", "txt"], label_visibility="collapsed")
        keys = []
        for f in ups or []:
            key = (f.name, f.size); keys.append(key)
            if key not in ss.parsed:
                try:
                    ss.parsed[key] = load_file(f.name, f.getvalue())
                except ImportProblem as e:
                    ss.parsed[key] = e
                except Exception as e:                       # corrupt file etc.
                    ss.parsed[key] = ImportProblem("read", name=f.name, why=str(e)[:150])
        files = []
        for key in keys:
            v = ss.parsed[key]
            if isinstance(v, ImportProblem):
                st.error(problem_text(v) if v.key != "read" else t("err_read", **v.params))
            else:
                files += v
    with right:
        with st.expander(t("what_files"), expanded=not files):
            st.markdown(t("what_files_body"))
        st.download_button("⬇ " + t("template_btn"), template_xlsx(), file_name="TraceNet_data_template.xlsx", width="stretch")
        if st.button("🧪 " + t("demo_btn"), width="stretch"):
            ss.ds = load_demo(str(HERE / "data")); ss.is_demo = True; ss.analysis = None; ss.step = 3; st.rerun()
        st.caption(t("demo_note"))

    # ---- one card per file: type + columns
    if files:
        st.subheader(t("files_found"))
    for i, fi in enumerate(files):
        ok = fi.confident
        with st.container(border=True):
            c1, c2 = st.columns([3, 2])
            c1.markdown(f"**📄 {fi.name}**  \n{'✅ ' + t('sure') if ok else '⚠️ ' + t('check_cols')}")
            new_kind = c2.selectbox(t("type_is"), KINDS, index=KINDS.index(fi.kind), format_func=KIND_NAME.get, key=f"kind{i}{fi.name}")
            if new_kind != fi.kind:
                fi.kind = new_kind; fi.mapping = detect_roles(new_kind, list(fi.df.columns))
                if new_kind == "statement" and not fi.owner:
                    fi.owner = guess_owner(fi.top_text, fi.name)
                st.rerun()
            if fi.kind == "statement":
                o1, o2 = st.columns(2)
                fi.owner = o1.text_input(t("owner_q"), fi.owner, help=t("owner_help"), key=f"own{i}{fi.name}").strip()
                fi.bank = o2.text_input(t("bank_q"), fi.bank, key=f"bank{i}{fi.name}").strip()
            with st.expander(t("cols_title"), expanded=not ok):
                opts = [t("none_opt")] + list(fi.df.columns)
                grid = st.columns(3)
                for j, r in enumerate(SYN[fi.kind]):
                    cur = fi.mapping.get(r)
                    star = " *" if r in REQUIRED[fi.kind] else ""
                    pick = grid[j % 3].selectbox(role_name(r) + star, opts, index=opts.index(cur) if cur in opts else 0, key=f"map{i}{fi.name}{fi.kind}{r}")
                    fi.mapping[r] = None if pick == opts[0] else pick
                fi.confident = all(fi.mapping.get(r) for r in REQUIRED[fi.kind]) and (
                    fi.kind != "statement" or bool((fi.mapping["debit"] and fi.mapping["credit"]) or (fi.mapping["amount"] and fi.mapping["drcr"])))
            with st.expander(t("preview")):
                st.dataframe(fi.df.head(6), width="stretch", hide_index=True)

    # ---- complaint by hand
    with st.expander("✍️ " + t("manual_title"), expanded=bool(files) and not any(f.kind == "complaints" for f in files)):
        a, b, c_, d_ = st.columns(4)
        v = a.text_input(t("m_victim"), key="mv"); amt = b.number_input(t("m_amount"), min_value=0.0, step=1000.0, key="ma")
        day = c_.date_input(t("m_date"), dt.date.today(), key="md"); tm = d_.text_input(t("m_time"), "10:00", key="mt")
        e1, e2, e3 = st.columns(3)
        ref = e1.text_input(t("m_ref"), key="mr")
        vname = e2.text_input(role_name("victim_name"), key="mn"); vphone = e3.text_input(role_name("victim_phone"), key="mp")
        if st.button(t("m_add")):
            try:
                ts = pd.Timestamp(f"{day} {tm}")
                if not v.strip() or amt <= 0: raise ValueError
                ss.manual.append(make_complaint(v, amt, ts, refs=ref, cid=f"CMP-{len(ss.manual) + 1:03d}", name=vname, phone=vphone))
                st.rerun()
            except Exception:
                st.error(t("m_bad"))
        if ss.manual:
            st.caption(t("m_added"))
            st.dataframe(pd.concat(ss.manual)[["complaint_id", "victim_account", "amount", "fraud_ts"]], hide_index=True, width="stretch")

    st.divider()
    if st.button(t("to_check"), type="primary", disabled=not files):
        ss.files = files; ss.step = 2; st.rerun()
    if not files:
        st.caption(t("need_file"))

# ================================================================== STEP 2 ====
elif ss.step == 2:
    st.subheader(t("check_title"))
    try:
        manual = pd.concat(ss.manual, ignore_index=True) if ss.manual else None
        ds0 = convert(ss.files, manual)
    except ImportProblem as e:
        st.error(problem_text(e))
        if st.button(t("back")): ss.step = 1; st.rerun()
        st.stop()
    tx = ds0.tx
    m = st.columns(5)
    m[0].metric(t("c_tx"), f"{len(tx):,}"); m[1].metric(t("c_acc"), f"{ds0.acc.account_id.nunique():,}"); m[2].metric(t("c_comp"), len(ds0.comp))
    m[3].metric(t("c_range"), f"{tx.ts.min():%d %b %Y}" if tx.ts.min().date() == tx.ts.max().date() else f"{tx.ts.min():%d %b}–{tx.ts.max():%d %b}")
    m[4].metric(t("c_cash"), tx.dst.str.startswith("CASHOUT").sum())
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

# ================================================================== STEP 3 ====
else:
    ds = ss.ds
    if ds is None:
        ss.step = 1; st.rerun()
    acc, tx, comp = ds.acc, ds.tx, ds.comp
    if ss.analysis is None or ss.analysis[0] != id(ds):
        with st.spinner("…"):
            feats = score_mules(account_features(tx, acc))
            _, rd = link_entities(acc)
            rings0 = merge_rings(rd, link_by_flow(tx, feats))
            ss.analysis = (id(ds), feats, rings0, analyse_links(ds, feats, rings0))
    _, feats, rings, lk = ss.analysis
    views = ["list", "one", "links"]
    if ss.get("view") not in views:
        ss.view = "list"
    view = st.radio(" ", views, format_func=lambda v: t("view_" + v), horizontal=True, label_visibility="collapsed", key="view")
    st.caption(t("g3_help")); glossary()
    prefix = ("demo:" if ss.is_demo else "data:")
    notes = load_notes(HERE, prefix)
    ct = complaint_table(lk)
    ct["status"] = ct.complaint_id.map(lambda c_: notes.get(c_, {}).get("status", "new"))
    if view == "links":
        render_links(lk)
        st.stop()
    if view == "list":
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
        st.stop()
    st.button(t("back_list"), on_click=lambda: ss.update(view="list"))
    comp_ids = comp.complaint_id.tolist()
    cid = ss.get("open_cid") if ss.get("open_cid") in comp_ids else comp_ids[0]
    ss.open_cid = cid
    crow = ct[ct.complaint_id == cid].iloc[0]

    FR = {"account_id": ("Account", "खाता"), "bank": ("Bank", "बैंक"), "hop": ("Steps from victim", "पीड़ित से कदम"),
          "tainted_still_held": ("Stolen money still inside (Rs)", "अभी अंदर चोरी का पैसा (रु.)"),
          "mule_score": ("Suspicion score (0-100)", "संदेह स्कोर (0-100)"), "ring": ("Gang", "गिरोह"), "action": ("What to do", "क्या करें")}
    li = 1 if lang == LANGS[0] else 0
    friendly = {k: v[li] for k, v in FR.items()}

    c = comp[comp.complaint_id == cid].iloc[0]
    seeds = list(c.seed_ids) if "seed_ids" in comp and isinstance(c.seed_ids, (list, tuple)) else []
    lag_h = crow.delay_h if pd.notna(crow.delay_h) else None
    as_of = None
    if ss.is_demo and (HERE / "data/ground_truth.csv").exists():
        with st.sidebar:
            with st.expander(t("test_title")):
                mm = evaluate(feats, pd.read_csv(HERE / "data/ground_truth.csv"))
                st.write(t("test_body", tp=mm["tp"], tot=mm["tp"] + mm["fn"], fp=mm["fp"]))

    # ---------------- complaint card
    _st = ss.get(f"st_{prefix}{cid}", notes.get(cid, {}).get("status", "new"))
    _tone = dict(new="blue", investigating="amber", frozen="teal", closed="grey").get(_st, "blue")
    _chips = [chip(t("st_" + _st), _tone)]
    if lag_h is not None:
        _chips.append(chip("⚡ " + t("in_hour").split(":")[0], "teal") if lag_h <= 1 else chip(f"⏳ {t('delay_val', h=lag_h)}", "amber"))
    _g = lk.group_of.get(cid, "")
    if crow.case:
        _chips.append(chip("🔗 " + _g, "red"))
    file_header("📁", f"{t('card_title')} · {cid}", f"{crow.victim_name or t('na')} · ₹{c.amount:,.0f} · {c.fraud_ts:%d %b %Y %H:%M}", _chips)
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
            if lag_h <= 1:
                c2.success(t("in_hour"))
            else:
                c2.warning(t("late", h=lag_h))
        c3.markdown(f"**{t('card_money')}**")
        c3.metric(t("m_lost"), money(c.amount))
        c3.metric(t("m_inside"), money(crow.inside), help=t("ch_inside")); c3.metric(t("m_cash"), money(crow.cashed), help=t("ch_cash"))
        c4.markdown(f"**{t('cl_status')}**")
        cur = notes.get(cid, {})
        skey = f"st_{prefix}{cid}"; nkey = f"nt_{prefix}{cid}"
        if skey not in ss:
            ss[skey] = cur.get("status", "new") if cur.get("status") in STATUSES else "new"
            ss[nkey] = cur.get("note", "")
        c4.selectbox(t("cl_status"), STATUSES, format_func=lambda x: t("st_" + x), key=skey, help=t("ch_status"), label_visibility="collapsed")
        c4.text_area(t("note_lbl"), key=nkey, height=70)
        if ss[skey] != cur.get("status", "new") or ss[nkey] != cur.get("note", ""):
            if save_note(HERE, prefix, cid, ss[skey], ss[nkey]):
                c4.caption("💾 " + t("note_saved"))
        gid_ = lk.group_of.get(cid, "")
        st.markdown(f"**{t('card_case')}**")
        grp = next((g for g in lk.groups if g["id"] == gid_), None)
        if grp and len(grp["complaints"]) > 1:
            others = [x for x in grp["complaints"] if x != cid]
            st.markdown(t("case_with", gid=gid_, n=len(others)))
            for col_, o in zip(st.columns(min(len(others), 6)), others[:6]):
                col_.button(t("case_open", cid=o), key=f"op_{o}", on_click=open_cid, args=(o,))
        else:
            st.caption(t("case_single"))
        st.caption(f"{t('banks_inv')}: " + (", ".join(crow.banks) or "—"))
    if ds.time_known:
        default = int(min(max((lag_h or 24) * 60, 5), 24 * 60))
        with st.expander("⏱️ " + t("when_box")):
            mins = st.slider(t("when"), 5, 24 * 60, default, 5, key=f"tt_{cid}")
            st.caption(t("when_help"))
        as_of = c.fraud_ts + pd.Timedelta(minutes=mins)

    trail = trace_funds(tx, c.victim_account, c.fraud_ts, c.amount, as_of=as_of, seed_txn_ids=seeds)
    if trail.edges.empty:
        st.info(t("nothing_moved"))
        if not (tx.src == c.victim_account).any():
            st.warning(t("note_victim_not_in_tx", cid=cid, acct=c.victim_account))
        if st.button(t("back")): ss.step = 1; st.rerun()
        st.stop()
    fl = freeze_list(trail, feats, rings)
    brief = case_brief(c, trail, fl, rings, feats)
    held = sum(trail.held.values()); cash = sum(trail.cashed.values())

    st.subheader(t(brief["headline_k"][0], **brief["headline_k"][1]))
    kpis([("🧊", t("k_held"), money(held), t("k_held_h"), "amber"), ("💸", t("k_cash"), money(cash), t("k_cash_h"), "red"),
          ("🏦", t("k_acc"), f"{len(fl[~fl.is_cashout])}", t("tab_sus"), "teal")])
    st.markdown(f"### ✅ {t('todo')}")
    for i, (key, prm) in enumerate(brief["steps_k"], 1):
        st.markdown(f"**{i}.** {t(key, **prm)}")
    if brief["gang_k"]:
        st.info(t(brief["gang_k"][0], **brief["gang_k"][1]))

    t1, t2, t3, t4, t5, t6 = st.tabs([t("tab_trail"), t("tab_act"), t("tab_sus"), t("tab_ask"), t("tab_rep"), t("tab_more")])
    with t1:
        nodes = trail_nodes(trail, feats)
        show_box("tr_show")
        st.plotly_chart(story_figure(trail, feats, nodes, t), width="stretch")
        st.markdown(f"#### {t('expl_lbl')}")
        st.markdown(t("tr_victim_line", acct=short(c.victim_account), amt=f"{c.amount:,.0f}", time=f"{c.fraud_ts:%d %b %H:%M}"))
        node_lines(nodes)
        st.caption(t("tr_warn"))
        next_box(trail_next_text(nodes))
    with t2:
        show_box("act_show"); st.caption(t("act_cols"))
        show = fl[["account_id", "bank", "hop", "tainted_still_held", "mule_score", "ring", "action"]].copy()
        show["account_id"] = show.account_id.map(pretty)
        st.dataframe(show.rename(columns=friendly), width="stretch", hide_index=True)
        st.download_button("⬇ " + t("dl_bank"), lien_file(fl, cid).to_csv(index=False), file_name=f"{cid}_bank_file.csv")
        next_box(t("act_next"))
    with t3:
        show_box("sus_show"); st.caption(t("sus_scale")); st.caption(t("sus_cap"))
        lb = feats[feats.mule_score > 0].sort_values("mule_score", ascending=False).head(30)
        if lb.empty:
            st.info(t("sus_none"))
        else:
            st.dataframe(lb[["bank", "mule_score", "reasons"]].rename(columns={"bank": friendly["bank"], "mule_score": friendly["mule_score"], "reasons": "Why / क्यों"}),
                         width="stretch")
        next_box(t("sus_next"))
        st.markdown("#### " + t("gang_cap"))
        for i, r in enumerate(rings, 1):
            st.write(f"**{t('gang_n', i=i, n=len(r))}**: " + ", ".join(r))
        if not rings:
            st.caption(t("gang_none"))
    with t4:
        show_box("rd_show")
        rounds = trace_in_rounds(tx, acc, c.victim_account, c.fraud_ts, c.amount, as_of=as_of, seed_txn_ids=seeds)
        rn = st.slider(t("wave"), 0, max(len(rounds) - 1, 0), 0) if len(rounds) > 1 else 0
        R = rounds[rn]
        a1, a2 = st.columns(2)
        a1.metric(t("w_known"), len(R["trail"].depth)); a2.metric(t("w_banks"), len(R["ask"]))
        if len(R["trail"].edges):
            rn_nodes = trail_nodes(R["trail"], feats, R["frontier"])
            st.plotly_chart(story_figure(R["trail"], feats, rn_nodes, t, R["frontier"]), width="stretch")
            st.markdown(f"#### {t('expl_lbl')}"); node_lines(rn_nodes)
        next_box(t("rd_next"))
        st.markdown(bank_requests(R, cid, c.fraud_ts))
    with t5:
        full = trace_funds(tx, c.victim_account, c.fraud_ts, c.amount, seed_txn_ids=seeds)
        rep = build_report(c, full, freeze_list(full, feats, rings), rings, feats)
        st.download_button("⬇ " + t("dl_rep"), rep, file_name=f"{cid}_report.md")
        st.markdown(rep)
    with t6:
        st.subheader(t("wl_title"))
        wl = export_watchlist(feats, rings)
        st.dataframe(wl, width="stretch", hide_index=True)
        st.download_button("⬇ " + t("dl_wl"), wl.to_csv(index=False), file_name="tracenet_watchlist.csv")
        st.subheader(t("pre_title")); st.caption(t("pre_cap"))
        q1, q2 = st.columns(2)
        names = sorted(acc.account_id)
        first = next((a for a in fl.account_id if a in names), names[0])
        target = q1.selectbox(t("pre_acc"), names, index=names.index(first))
        use_wl = q2.checkbox(t("pre_use"), value=True)
        res = precheck(acc, tx, target, c.fraud_ts, set(wl.account_id) if use_wl else (), rings)
        label = t("risk_" + res["level"]) + ": " + res["action"]
        {"HIGH": st.error, "MEDIUM": st.warning}.get(res["level"], st.success)(label)
        for r_ in res["reasons"]:
            st.write("• " + r_)
