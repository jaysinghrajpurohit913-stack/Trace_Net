"""Case workspace: search everything, start from a UTR, one timeline, evidence references, PDF / Excel download."""
import pandas as pd
import streamlit as st

from ..explain import trail_nodes
from ..export import excel_bytes, pdf_bytes
from ..intel.evidence import evidence_table
from ..intel.timeline import events_for
from ..pipeline import trail_from_utr
from ..viz import events_figure, story_figure
from .complaint_file import node_lines
from ..engine import freeze_list


def search_everything(an, q):
    """Substring search over every node of the relationship graph + complaint ids. -> DataFrame(kind, value, complaints)."""
    q = q.strip().lower()
    rows = []
    G = an.graph
    for n, d in G.nodes(data=True):
        if d["kind"] == "complaint" or q not in str(d["value"]).lower():
            continue
        comps = sorted({G.nodes[m]["value"] for m in G.neighbors(n) if G.nodes[m]["kind"] == "complaint"} |
                       {G.nodes[x]["value"] for m in G.neighbors(n) for x in G.neighbors(m) if G.nodes[x]["kind"] == "complaint"})
        rows.append(dict(kind=d["kind"], value=d["value"], complaints=", ".join(comps)))
    for r in an.table[an.table.blob.str.contains(q, regex=False)].itertuples():
        rows.append(dict(kind="complaint", value=r.complaint_id, complaints=r.complaint_id))
    return pd.DataFrame(rows, columns=["kind", "value", "complaints"]).drop_duplicates().head(80)


def render(ctx, an, prefix, notes):
    t, ss = ctx.t, ctx.ss
    st.subheader(t("ws_title")); st.caption(t("ws_help"))
    q = st.text_input(t("ws_search"), placeholder=t("ws_search_ph"), key="ws_q")
    if q.strip():
        r = search_everything(an, q)
        st.markdown(f"**{t('ws_found', n=len(r))}**")
        if len(r):
            st.dataframe(r, hide_index=True, width="stretch")
            first = next((c.strip() for c in ", ".join(r.complaints).split(",") if c.strip()), None)
            if first:
                st.button(t("case_open", cid=first), on_click=ctx.open_complaint, args=(first,))
    with st.expander("🧾 " + t("ws_utr_title"), expanded=False):
        u = st.text_input(t("ws_utr"), key="ws_utr").strip()
        if u:
            row, trail = trail_from_utr(an.ds, u)
            if row is None:
                st.warning(t("ws_utr_none"))
            else:
                st.success(t("ws_utr_found", src=row.src, dst=row.dst, amt=f"{row.amount:,.0f}", ts=f"{row.ts:%d %b %Y %H:%M}"))
                fl = freeze_list(trail, an.feats, an.rings)
                nodes = trail_nodes(trail, an.feats)
                st.plotly_chart(story_figure(trail, an.feats, nodes, t), width="stretch")
                node_lines(ctx, nodes)
    ids = an.ds.comp.complaint_id.tolist()
    groups = sorted({g for g in an.lk.group_of.values() if not g.startswith("SINGLE")})
    scope = st.selectbox(t("ws_scope"), ["all"] + groups + ids, format_func=lambda x: t("ws_all") if x == "all" else x, key="ws_scope")
    cids = ids if scope == "all" else ([c for c, g in an.lk.group_of.items() if g == scope] if scope in groups else [scope])
    ev = events_for(an, cids)
    st.markdown("#### " + t("ws_timeline")); st.caption(t("ws_timeline_help"))
    if len(ev):
        st.plotly_chart(events_figure(ev), width="stretch")
        with st.expander(t("ws_timeline_tbl")):
            st.dataframe(ev, hide_index=True, width="stretch")
    st.markdown("#### " + t("ws_evidence")); st.caption(t("ws_evidence_help"))
    st.dataframe(evidence_table(an.ds, an.intel, cids), hide_index=True, width="stretch")
    st.markdown("#### " + t("ws_export"))
    c1, c2 = st.columns(2)
    if c1.button("📊 " + t("ws_make_xlsx"), key="mk_x"):
        ss.ws_x = excel_bytes(an, cids)
    if c2.button("📄 " + t("ws_make_pdf"), key="mk_p"):
        ss.ws_p = pdf_bytes(an, cids)
    if ss.get("ws_x"):
        c1.download_button("⬇ Excel", ss.ws_x, file_name="TraceNet_workspace.xlsx")
    if ss.get("ws_p"):
        c2.download_button("⬇ PDF", ss.ws_p, file_name="TraceNet_workspace.pdf")
