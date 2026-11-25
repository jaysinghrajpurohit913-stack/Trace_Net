import numpy as np
import plotly.graph_objects as go
from .engine import is_cashout, pretty, short


def _layout(trail):
    by = {}
    for a, d in trail.depth.items(): by.setdefault(d, []).append(a)
    pos = {}
    for d, nodes in by.items():
        nodes = sorted(nodes)
        for i, a in enumerate(nodes):
            pos[a] = (d, (i - (len(nodes) - 1) / 2))
    return pos


def trail_figure(trail, feats, frontier=()):
    pos = _layout(trail)
    fig = go.Figure()
    mx = max(trail.edges.tainted.max(), 1) if len(trail.edges) else 1
    for r in trail.edges.itertuples():
        (x0, y0), (x1, y1) = pos[r.src], pos[r.dst]
        fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines", hoverinfo="text",
                                 text=f"{r.src} → {r.dst}<br>Rs {r.tainted:,.0f} via {r.channel}<br>{r.ts:%d-%b %H:%M}",
                                 line=dict(width=1 + 7 * r.tainted / mx, color="rgba(200,60,60,.45)"),
                                 showlegend=False))
    xs, ys, cols, sym, txt, lab = [], [], [], [], [], []
    for a, (x, y) in pos.items():
        sc = float(feats.mule_score.get(a, 0)) if a in feats.index else 0
        held = trail.held.get(a, 0) if a != next(iter(trail.depth)) else 0
        xs.append(x); ys.append(y); lab.append(pretty(a) + (" ?" if a in frontier else ""))
        cols.append(-20 if a in frontier else sc)
        sym.append("diamond" if is_cashout(a) else ("star" if x == 0 else "circle"))
        txt.append(f"{a}<br>Mule score {sc:.0f}<br>Still holds Rs {held:,.0f}<br>"
                   + (feats.reasons.get(a, "") if a in feats.index else ""))
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text", text=lab, textposition="top center",
                             hovertext=txt, hoverinfo="text",
                             marker=dict(size=26, symbol=sym, color=cols, colorscale=[[0, "#B8C0CC"], [0.167, "#B8C0CC"], [0.1671, "#FFFFB2"], [1, "#BD0026"]], cmin=-20, cmax=100,
                                         line=dict(width=1.5, color="#222"), showscale=True,
                                         colorbar=dict(title="Mule<br>score")), showlegend=False))
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=30, b=10),
                      xaxis=dict(title="Hop distance from victim  (★ victim · ◆ cash-out)", dtick=1, zeroline=False),
                      yaxis=dict(visible=False), plot_bgcolor="white")
    return fig


# ------------------------------------------------------------------ cross-complaint pictures ----
PALETTE = ["#1F77B4", "#E4572E", "#2CA58D", "#F5A623", "#7B4FBF", "#C2185B", "#5D6D7E", "#8D6E63", "#00838F", "#9E9D24"]


def _color(i):
    return PALETTE[i % len(PALETTE)]


def network_figure(lk, cids, show_all=False, ranked=None):
    """Complaints (squares) joined to the accounts their money went through. Accounts used by 2+ complaints are big circles.
    `ranked` (explain.shared_nodes) = the busiest accounts: they carry the numbers 1,2,3... explained under the picture."""
    import networkx as nx
    from .engine import short
    cids = list(cids)
    num = {n["acct"]: n["n"] for n in (ranked or [])}
    cnt = {}
    for c in cids:
        for a in lk.touched[c]:
            cnt[a] = cnt.get(a, 0) + 1
    keep = {a for a, k in cnt.items() if k >= 2 or show_all}
    G = nx.Graph()
    for c in cids:
        G.add_node(c)
        for a, v in lk.touched[c].items():
            if a in keep:
                G.add_edge(c, a, w=v)
    if G.number_of_nodes() == 0:
        return go.Figure()
    pos = nx.spring_layout(G, seed=3, k=1.6 / max(G.number_of_nodes(), 1) ** .5 + .2, iterations=250)
    fig = go.Figure()
    mx = max([d["w"] for _, _, d in G.edges(data=True)] + [1])
    for u, v, d in G.edges(data=True):
        fig.add_trace(go.Scatter(x=[pos[u][0], pos[v][0]], y=[pos[u][1], pos[v][1]], mode="lines", hoverinfo="text",
                                 text=f"{u} → {pretty(v)}<br>Rs {d['w']:,.0f}", showlegend=False,
                                 line=dict(width=.8 + 5 * d["w"] / mx, color="rgba(120,130,150,.40)")))
    ids = {c: i for i, c in enumerate(cids)}
    cset = set(cids)
    for r in lk.pairs[lk.pairs.a.isin(cset) & lk.pairs.b.isin(cset)].itertuples():       # links with no shared account (ring / victim reuse)
        if not any(k in ("accts", "exit") for k, _ in r.reasons) and r.a in pos and r.b in pos:
            fig.add_trace(go.Scatter(x=[pos[r.a][0], pos[r.b][0]], y=[pos[r.a][1], pos[r.b][1]], mode="lines", hoverinfo="skip", showlegend=False,
                                     line=dict(width=1.5, color="rgba(192,57,43,.6)", dash="dash")))
    bank = lk.feats.bank if "bank" in lk.feats else {}
    acc = [n for n in G.nodes if n not in cset]
    xs, ys, sz, col, sym, txt, inner, under = [], [], [], [], [], [], [], []
    for a in acc:
        k = cnt[a]; sc = float(lk.feats.mule_score.get(a, 0)) if a in lk.feats.index else 0
        xs.append(pos[a][0]); ys.append(pos[a][1]); sz.append(18 + 6 * min(k, 6) + (8 if a in num else 0)); col.append(sc)
        sym.append("diamond" if is_cashout(a) else "circle"); inner.append(str(num[a]) if a in num else "")
        b = bank.get(a, "") if a in lk.feats.index else ""
        under.append((short(a) + (f"<br>{b}" if b and not str(b).lower().startswith("unknown") else "")) if (a in num or show_all) else "")
        held = sum(lk.joint.held.get(a, {}).values())
        txt.append(f"<b>{pretty(a)}</b> {b}<br>Used in {k} complaint(s)<br>Mule score {sc:.0f}<br>Still holds Rs {held:,.0f}")
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text", text=inner, textposition="middle center", textfont=dict(size=14, color="#111", family="Arial Black"),
                             hovertext=txt, hoverinfo="text", showlegend=False,
                             marker=dict(size=sz, symbol=sym, color=col, cmin=0, cmax=100, colorscale=[[0, "#FFF3B0"], [.5, "#F5A25D"], [1, "#E0524B"]],
                                         line=dict(width=1.5, color="#222"), showscale=True,
                                         colorbar=dict(title="Suspicion<br>0–100", len=.5, thickness=12))))
    fig.add_trace(go.Scatter(x=xs, y=[y - .075 for y in ys], mode="text", text=under, textposition="bottom center", hoverinfo="skip", showlegend=False,
                             textfont=dict(size=10, color="#334155")))
    comp = lk.comp.set_index("complaint_id")
    fig.add_trace(go.Scatter(x=[pos[c][0] for c in cids], y=[pos[c][1] for c in cids], mode="markers+text", text=[short(c) for c in cids], textposition="top center",
                             showlegend=False, textfont=dict(size=11, color="#111"),
                             hovertext=[f"<b>{c}</b><br>Victim {comp.loc[c, 'victim_account']}<br>Lost Rs {comp.loc[c, 'amount']:,.0f}" for c in cids], hoverinfo="text",
                             marker=dict(size=26, symbol="square", color=[_color(ids[c]) for c in cids], line=dict(width=2, color="#111"))))
    fig.update_layout(height=580, margin=dict(l=5, r=5, t=10, b=5), plot_bgcolor="white", xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


def timeline_figure(lk, gid):
    g = next(x for x in lk.groups if x["id"] == gid)
    ev = lk.joint.events[lk.joint.events.cid.isin(g["complaints"])]
    top = [a for a in lk.shared[lk.shared.account.isin(g["shared"])].account.tolist()][:14] + [a for a in g["exits"]][:4]
    ev = ev[ev.acct.isin(top)]
    ids = {c: i for i, c in enumerate(g["complaints"])}
    comp = lk.comp.set_index("complaint_id")
    from .engine import short
    bank = lk.feats.bank if "bank" in lk.feats else {}
    ylab = lambda a: short(a) + (f" · {bank.get(a)}" if a in lk.feats.index and not str(bank.get(a, "")).lower().startswith("unknown") and not is_cashout(a) else "")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[comp.loc[c, "fraud_ts"] for c in g["complaints"]], y=["★ fraud starts"] * len(g["complaints"]), mode="markers+text",
                             text=[short(c) for c in g["complaints"]], textposition="top center", showlegend=False, hoverinfo="text",
                             marker=dict(symbol="star", size=16, color=[_color(ids[c]) for c in g["complaints"]], line=dict(width=1, color="#111"))))
    for c in g["complaints"]:
        e = ev[ev.cid == c]
        fig.add_trace(go.Scatter(x=e.ts, y=e.acct.map(ylab), mode="markers", name=short(c), hoverinfo="text",
                                 text=[f"{c} → {pretty(a)}<br>Rs {v:,.0f}<br>{t:%d-%b %H:%M}" for a, v, t in zip(e.acct, e.amount, e.ts)],
                                 marker=dict(size=[8 + 14 * (v / max(e.amount.max(), 1)) ** .5 for v in e.amount], color=_color(ids[c]), opacity=.8,
                                             line=dict(width=1, color="#222"))))
    fig.update_layout(height=max(360, 40 * (len(top) + 2)), margin=dict(l=5, r=5, t=10, b=5), plot_bgcolor="white", legend=dict(orientation="h", y=-.15),
                      yaxis=dict(autorange="reversed", gridcolor="#eee"), xaxis=dict(gridcolor="#eee"))
    return fig


def hour_figure(hours):
    xs = list(range(24))
    fig = go.Figure(go.Bar(x=xs, y=[hours.get(h, 0) for h in xs], marker_color=["#2B3A67" if (h < 6 or h >= 22) else "#E4572E" for h in xs]))
    fig.update_layout(height=240, margin=dict(l=5, r=5, t=10, b=5), plot_bgcolor="white", xaxis=dict(dtick=2, title="Hour of day"), yaxis=dict(title="Frauds", dtick=1))
    return fig


def split_figure(lk, gid):
    g = next(x for x in lk.groups if x["id"] == gid)
    d = lk.split[lk.split.complaint.isin(g["complaints"]) & lk.split.account.isin(g["shared"])]
    order = d.groupby("account").received.sum().sort_values(ascending=False).head(12).index.tolist()
    ids = {c: i for i, c in enumerate(g["complaints"])}
    fig = go.Figure()
    for c in g["complaints"]:
        e = d[(d.complaint == c) & d.account.isin(order)].set_index("account").reindex(order)
        fig.add_trace(go.Bar(x=order, y=e.received.fillna(0), name=c, marker_color=_color(ids[c])))
    fig.update_layout(barmode="stack", height=340, margin=dict(l=5, r=5, t=10, b=5), plot_bgcolor="white", yaxis=dict(title="Stolen money received (Rs)"),
                      legend=dict(orientation="h", y=-.25))
    return fig


# ------------------------------------------------------------------ story-style money trail ----
KIND_STYLE = {   # kind -> (colour, symbol, number colour)
    "victim": ("#2B6CB0", "star", "#FFFFFF"), "inside": ("#F59E0B", "circle", "#1F2937"), "passed": ("#94A3B8", "circle", "#1F2937"),
    "cash": ("#DC2626", "diamond", "#FFFFFF"), "unknown": ("#FFFFFF", "circle", "#475569")}


def _lab(a, bank):
    from .engine import short
    return short(a) + (f" · {bank}" if bank and not str(bank).lower().startswith("unknown") else "")


def story_figure(trail, feats, nodes, t, frontier=(), victim_label=""):
    """Left to right: victim -> step 1 accounts -> step 2 ... -> cash-out. Number inside each circle = order of arrival.
    Colour = what is true NOW (still inside / passed on / cashed out / unknown). Arrow text = stolen money moved."""
    import pandas as pd
    from .engine import short
    e = trail.edges
    victim = next(iter(trail.depth))
    pos, cols = {}, {}
    for nd in nodes:
        cols.setdefault(nd["hop"], []).append(nd["acct"])
    pos[victim] = (0, 0)
    for hop, accs in cols.items():
        for i, a in enumerate(accs):
            pos[a] = (hop, -(i - (len(accs) - 1) / 2) * 1.0)
    rows = max([len(v) for v in cols.values()] + [1])
    fig = go.Figure()
    # arrows with amounts
    agg = e.groupby(["src", "dst"]).agg(tainted=("tainted", "sum"), ts=("ts", "min")).reset_index()
    mx = max(agg.tainted.max(), 1)
    for r in agg.itertuples():
        if r.src not in pos or r.dst not in pos:
            continue
        (x0, y0), (x1, y1) = pos[r.src], pos[r.dst]
        sx, sy = x0 + (x1 - x0) * .13, y0 + (y1 - y0) * .13
        ex, ey = x0 + (x1 - x0) * .87, y0 + (y1 - y0) * .87
        fig.add_annotation(x=ex, y=ey, ax=sx, ay=sy, xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.2,
                           arrowwidth=1.2 + 4.5 * r.tainted / mx, arrowcolor="rgba(71,85,105,.55)")
        fig.add_annotation(x=(x0 + x1) / 2, y=(y0 + y1) / 2, text=f"₹{r.tainted:,.0f}", showarrow=False, font=dict(size=11, color="#334155"),
                           bgcolor="rgba(255,255,255,.88)", borderpad=1)
    # nodes grouped by kind so the legend explains the colours
    allnodes = [dict(n="★", acct=victim, kind="victim", bank="", recv=0, held=0, score=0)] + nodes
    legend = {"victim": t("leg_victim"), "inside": t("leg_inside"), "passed": t("leg_passed"), "cash": t("leg_cash"), "unknown": t("leg_unknown")}
    for kind in ["victim", "inside", "passed", "cash", "unknown"]:
        ns = [n for n in allnodes if n["kind"] == kind]
        if not ns:
            continue
        col, sym, tcol = KIND_STYLE[kind]
        hover = []
        for n in ns:
            if kind == "victim":
                hover.append(f"{victim}<br>{t('fig_victim')}")
            else:
                hover.append(f"<b>{n['n']}. {pretty(n['acct'])}</b> {n['bank']}<br>{t('hv_got')}: ₹{n['recv']:,.0f}<br>{t('hv_inside')}: ₹{n['held']:,.0f}<br>{t('hv_score')}: {n['score']:.0f}/100")
        fig.add_trace(go.Scatter(x=[pos[n["acct"]][0] for n in ns], y=[pos[n["acct"]][1] for n in ns], mode="markers+text", name=legend[kind],
                                 text=[str(n["n"]) if kind != "unknown" else f"{n['n']}?" for n in ns], textposition="middle center",
                                 textfont=dict(color=tcol, size=15, family="Arial Black"), hovertext=hover, hoverinfo="text",
                                 marker=dict(size=40 if kind != "victim" else 46, color=col, symbol=sym, line=dict(width=3 if kind == "inside" else 1.8, color="#111827"))))
    lab, lx, ly = [], [], []
    for n in allnodes:
        x, y = pos[n["acct"]]
        if n["kind"] == "victim":
            txt = f"<b>{t('fig_victim')}</b><br>{short(victim)}"
        else:
            warn = " ⚠" if n["score"] >= 40 and n["kind"] != "cash" else ""
            txt = f"<b>{_lab(n['acct'], n['bank'])}</b>{warn}<br>₹{n['recv']:,.0f}"
        lab.append(txt); lx.append(x); ly.append(y - .26)
    fig.add_trace(go.Scatter(x=lx, y=ly, mode="text", text=lab, textposition="bottom center", hoverinfo="skip", showlegend=False, textfont=dict(size=11, color="#111827")))
    hops = sorted({0} | set(cols))
    fig.update_layout(height=int(190 * rows + 170), margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="white",
                      xaxis=dict(tickvals=hops, ticktext=[t("fig_victim") if h == 0 else f"{t('fig_step')} {h}" for h in hops], side="top", showgrid=True,
                                 gridcolor="#EEF2F7", zeroline=False, range=[-.5, max(hops) + .5], tickfont=dict(size=13, color="#334155")),
                      yaxis=dict(visible=False, range=[-(rows / 2) - .9, rows / 2 + .3]),
                      legend=dict(orientation="h", y=-.02, yanchor="top", font=dict(size=12)))
    return fig


# ------------------------------------------------------------- relationship graph (all entity types) ----
GRAPH_STYLE = {   # kind -> (colour, symbol, English label)
    "complaint": ("#2f6fed", "star", "Complaint"), "acct": ("#e8a317", "circle", "Account"), "domain": ("#8b5cf6", "square", "Domain"),
    "ip": ("#0f8a6d", "diamond", "IP address"), "ns": ("#14b8a6", "triangle-up", "Name server"), "registrar": ("#94a3b8", "triangle-down", "Registrar"),
    "phone": ("#ec4899", "pentagon", "Phone"), "upi": ("#f97316", "hexagon", "UPI id"), "utr": ("#64748b", "cross", "UTR"),
    "device": ("#a855f7", "x", "Device"), "host": ("#cbd5e1", "circle-open", "Hosting / network"),
}


def graph_figure(G, around, depth=2, hide_weak=False, max_nodes=70, kinds=None, only_shared=True):
    """Readable sub-graph around chosen nodes. Nodes coloured by type; dashed lines = weak evidence (shared VPN / big host / registrar)."""
    import networkx as nx
    keep = {}
    for n in around:
        if n in G:
            for m, d in nx.single_source_shortest_path_length(G, n, cutoff=depth).items():
                keep[m] = min(keep.get(m, 9), d)
    if kinds:
        keep = {m: d for m, d in keep.items() if G.nodes[m]["kind"] in kinds or m in around}
    if hide_weak:
        keep = {m: d for m, d in keep.items() if not G.nodes[m].get("weak") or m in around}
    nodes = sorted(keep, key=lambda m: (keep[m], -G.degree(m)))[:max_nodes]
    H = G.subgraph(nodes)
    if only_shared:       # simple view: drop identifiers that connect to just ONE thing (they only add clutter)
        leaf = [n for n in H if H.degree(n) <= 1 and H.nodes[n]["kind"] in ("phone", "device", "ip", "upi", "ns", "registrar", "host", "utr") and n not in around]
        H = H.subgraph([n for n in H if n not in leaf])
    fig = go.Figure()
    if len(H) == 0:
        return fig
    pos = nx.spring_layout(H, seed=4, k=1.4 / max(len(H) ** .5, 1))
    for weak in (False, True):
        xs, ys = [], []
        for a, b, d in H.edges(data=True):
            if (d.get("strength") == "weak") == weak:
                xs += [pos[a][0], pos[b][0], None]; ys += [pos[a][1], pos[b][1], None]
        if xs:
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", hoverinfo="none", showlegend=False,
                                     line=dict(color="#b6c7c3" if weak else "#6b8782", width=1 if weak else 1.6, dash="dot" if weak else "solid")))
    for kind, (col, sym, lab) in GRAPH_STYLE.items():
        ns = [n for n in H if H.nodes[n]["kind"] == kind]
        if not ns:
            continue
        txt = [(short(H.nodes[n]["value"]) if kind in ("acct",) and len(str(H.nodes[n]["value"])) > 10 else str(H.nodes[n]["value"]))[:26] for n in ns]
        hov = [f"<b>{lab}</b><br>{H.nodes[n]['value']}" + ("<br><i>weak: shared by many</i>" if H.nodes[n].get("weak") else "") + f"<br>{H.degree(n)} connections" for n in ns]
        fig.add_trace(go.Scatter(x=[pos[n][0] for n in ns], y=[pos[n][1] for n in ns], mode="markers+text", text=txt, textposition="top center", name=lab, hovertext=hov, hoverinfo="text",
                                 textfont=dict(size=10), marker=dict(color=col, symbol=sym, size=[26 if n in around else 17 for n in ns], line=dict(color="white", width=1.5))))
    fig.update_layout(height=620, margin=dict(l=5, r=5, t=10, b=5), xaxis=dict(visible=False), yaxis=dict(visible=False), plot_bgcolor="white",
                      legend=dict(orientation="h", y=-0.02), hoverlabel=dict(font_size=13))
    return fig


def corr_figure(corr):
    """IP-log events vs the nearest bank transaction of the same account (minutes apart)."""
    if corr.empty:
        return go.Figure()
    d = corr.copy(); d["lab"] = d.account_id + " · " + d.ip
    colors = d["class"].map({"same moment": "#e5484d", "nearby": "#e8a317", "far": "#94a3b8"})
    fig = go.Figure(go.Bar(y=d.lab, x=d.gap_min, orientation="h", marker_color=colors, hovertext=d.caveat.replace("", "no caveat"),
                           text=[f"{g:+.0f} min" for g in d.gap_min], textposition="outside"))
    fig.update_layout(height=max(260, 34 * len(d) + 80), margin=dict(l=5, r=30, t=10, b=30), plot_bgcolor="white", yaxis=dict(autorange="reversed"),
                      xaxis=dict(title="minutes between the IP-log event and the bank transaction (negative = log came first)", zeroline=True, zerolinecolor="#334"))
    return fig


def events_figure(ev):
    """One timeline with a lane per kind of evidence: complaints, bank money, domains, IP log."""
    lanes = ["Complaint", "Bank", "Domain / IP", "IP log"]
    col = {"Complaint": "#2f6fed", "Bank": "#e8a317", "Domain / IP": "#8b5cf6", "IP log": "#0f8a6d"}
    fig = go.Figure()
    for ln in lanes:
        d = ev[ev.lane == ln]
        if len(d):
            fig.add_trace(go.Scatter(x=d.when, y=[ln] * len(d), mode="markers", name=ln, hovertext=d.label, hoverinfo="text+x",
                                     marker=dict(size=13, color=col[ln], line=dict(color="white", width=1))))
    fig.update_layout(height=330, margin=dict(l=5, r=5, t=10, b=5), plot_bgcolor="white", yaxis=dict(categoryorder="array", categoryarray=lanes[::-1]),
                      legend=dict(orientation="h", y=-0.2))
    return fig
