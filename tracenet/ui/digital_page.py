"""Digital trail: domains, IPs, hosting, IP-log vs bank time match, links between complaints, lawful-request drafts."""
import pandas as pd
import streamlit as st

from ..intel.lookup import enrich_domains, LookupLog, SOURCES
from ..intel.model import Intel
from ..intel.requests import drafts_for
from ..theme import kpis
from ..viz import graph_figure, corr_figure


def _lookups(ctx, an):
    t, ss = ctx.t, ctx.ss
    with st.expander("🔎 " + t("dg_lookup_title")):
        st.caption(t("dg_lookup_body"))
        st.markdown("\n".join(f"- {v}" for v in SOURCES.values()))
        if st.button(t("dg_lookup_btn"), key="run_lookup"):
            with st.spinner("…"):
                d, ips, certs, log = enrich_domains(an.intel.domains, cache_dir=ctx.here / ".tracenet_cache")
            ss.intel = Intel(domains=d, iplog=an.intel.iplog, ips=ips, certs=certs, lookups=log.frame())
            ok = int(ss.intel.lookups.ok.sum()) if len(ss.intel.lookups) else 0
            (st.success if ok else st.warning)(t("dg_lookup_done", ok=ok, n=len(ss.intel.lookups)))
            st.rerun()
        if len(an.intel.lookups):
            st.dataframe(an.intel.lookups, hide_index=True, width="stretch")


def render(ctx, an):
    t, ss = ctx.t, ctx.ss
    st.subheader(t("dg_title")); st.info(t("dg_rules"), icon="⚖️")
    if an.intel.empty:
        st.warning(t("dg_none"))
        st.markdown(t("dg_none_how"))
        return
    d, flags, corr = an.intel.domains, an.flags, an.corr
    kpis([("🌐", t("dg_k_dom"), f"{d.domain.replace('', pd.NA).nunique()}", t("dg_k_dom_s", n=d.ip.replace('', pd.NA).nunique()), "teal"),
          ("🚩", t("dg_k_flag"), f"{int((flags.n_flags > 0).sum()) if len(flags) else 0}", t("dg_k_flag_s"), "amber"),
          ("⏱️", t("dg_k_corr"), f"{int((corr['class'] == 'same moment').sum()) if len(corr) else 0}", t("dg_k_corr_s", n=len(corr)), "red"),
          ("🔗", t("dg_k_links"), f"{len(an.dpairs)}", t("dg_k_links_s"), "blue")])
    _lookups(ctx, an)
    tabs = st.tabs([t("dg_t_dom"), t("dg_t_corr"), t("dg_t_links"), t("dg_t_graph"), t("dg_t_req")])
    with tabs[0]:
        ctx.show_box("dg_dom_show")
        if len(flags):
            for r in flags.itertuples():
                with st.container(border=True):
                    st.markdown(f"**{r.domain}** → `{r.ip or '?'}` · {r.registrar or '?'} · {r.hosting or '?'} " + (f"· 🧾 {r.complaint_id}" if r.complaint_id else ""))
                    for fl in r.flags:
                        st.markdown(f"- 🚩 {fl}")
                    if not r.flags:
                        st.caption(t("dg_noflag"))
        st.markdown("#### " + t("dg_ips"))
        st.dataframe(an.intel.ips, hide_index=True, width="stretch")
        if len(an.intel.certs):
            st.markdown("#### " + t("dg_certs")); st.dataframe(an.intel.certs, hide_index=True, width="stretch")
        ctx.next_box(t("dg_dom_next"))
    with tabs[1]:
        ctx.show_box("dg_corr_show")
        if corr.empty:
            st.info(t("dg_corr_none"))
        else:
            st.plotly_chart(corr_figure(corr), width="stretch")
            st.dataframe(corr, hide_index=True, width="stretch")
            st.caption(t("dg_corr_caveat"))
    with tabs[2]:
        ctx.show_box("dg_links_show")
        if an.dpairs.empty:
            st.info(t("dg_links_none"))
        else:
            same = {frozenset(g["complaints"]) for g in an.lk.groups}
            p = an.dpairs.copy()
            p["money_case"] = [any({r.a, r.b} <= s for s in same) and "yes" or "no" for r in p.itertuples()]
            p["group_now"] = [an.lk.group_of.get(r.a) == an.lk.group_of.get(r.b) and "same case" or "different" for r in p.itertuples()]
            st.dataframe(p, hide_index=True, width="stretch")
            st.caption(t("dg_links_cap"))
            with st.expander(t("dg_links_detail")):
                st.dataframe(an.dlinks, hide_index=True, width="stretch")
    with tabs[3]:
        ctx.show_box("dg_graph_show")
        ids = an.ds.comp.complaint_id.tolist()
        pick = st.multiselect(t("dg_graph_pick"), ids, default=ids[:1], key="gr_pick")
        g1, g2 = st.columns(2)
        hide_weak = g1.checkbox(t("dg_graph_weak"), value=False)
        detail = g1.checkbox(t("dg_graph_detail"), value=False)
        depth = g2.slider(t("dg_graph_depth"), 1, 3, 2)
        if pick:
            st.plotly_chart(graph_figure(an.graph, [f"complaint:{c}" for c in pick], depth, hide_weak, only_shared=not detail), width="stretch")
        st.caption(t("dg_graph_cap"))
    with tabs[4]:
        ctx.show_box("dg_req_show")
        dr = drafts_for(an.intel, an.intel.ips, an.corr)
        if not dr:
            st.info(t("dg_req_none"))
        else:
            i = st.selectbox(t("dg_req_pick"), range(len(dr)), format_func=lambda k: f"{dr[k]['kind'].upper()} · {dr[k]['to']} · {dr[k]['subject']}")
            st.code(dr[i]["text"], language=None)
            st.download_button("⬇ " + t("dg_req_dl"), dr[i]["text"], file_name=f"request_{dr[i]['kind']}_{i + 1}.txt")
