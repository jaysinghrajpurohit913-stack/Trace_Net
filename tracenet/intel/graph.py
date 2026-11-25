"""One relationship graph over everything: accounts, domains, IPs, name servers, registrars, phones, UPI ids, UTRs, complaints.

`build_graph` makes the graph. `cross_case_links` answers the question investigators ask: "which complaints are connected
through the SAME infrastructure or identifiers, even if the money did not touch the same account?"
"""
from __future__ import annotations

from itertools import combinations

import networkx as nx
import pandas as pd

from ..engine import is_cashout
from .model import Intel

# node kinds -> short label used in the picture and the tables
KIND_LABEL = {"complaint": "Complaint", "acct": "Account", "domain": "Domain", "ip": "IP address", "ns": "Name server",
              "registrar": "Registrar", "phone": "Phone", "upi": "UPI id", "utr": "UTR", "device": "Device", "host": "Hosting / network"}
PUBLIC_NS_HINTS = ("cloudflare", "awsdns", "googledomains", "domaincontrol", "azure-dns")      # shared by millions: weak


def nid(kind, value):
    return f"{kind}:{value}"


def _ns_list(s):
    return [x.strip().lower() for x in str(s).replace(";", ",").split(",") if x.strip()]


def build_graph(ds, intel: Intel, touched: dict | None = None, ips: pd.DataFrame | None = None) -> nx.Graph:
    """touched: {complaint_id: {account: amount}} from the links analysis (which accounts each complaint's money reached)."""
    G = nx.Graph()

    def add(a, b, rel, strength="strong", ref=""):
        if G.has_edge(a, b):
            G[a][b]["refs"].add(ref); return
        G.add_edge(a, b, rel=rel, strength=strength, refs={ref} if ref else set())

    weak_ip = set(ips[ips.is_vpn | ips.shared_hosting].ip) if ips is not None and len(ips) else set()

    def node(kind, value, **kw):
        n = nid(kind, value)
        if n not in G:
            weak = (kind == "ip" and value in weak_ip) or (kind == "ns" and any(h in str(value) for h in PUBLIC_NS_HINTS))
            G.add_node(n, kind=kind, value=value, weak=weak, **kw)
        return n

    comp = ds.comp
    txid = set(ds.tx.txn_id.astype(str))
    for r in comp.itertuples():
        c = node("complaint", r.complaint_id)
        v = node("acct", r.victim_account); add(c, v, "victim account")
        if getattr(r, "victim_phone", ""):
            add(c, node("phone", str(r.victim_phone)), "victim phone")
        if getattr(r, "victim_upi", ""):
            add(c, node("upi", str(r.victim_upi)), "victim UPI")
        for u in {x for x in str(getattr(r, "txn_ref", "")).replace(";", ",").split(",") if x.strip()}:
            u = u.strip().upper()
            if u in txid:
                add(c, node("utr", u), "complaint UTR", ref=f"UTR:{u}")
                t = ds.tx[ds.tx.txn_id.astype(str) == u].iloc[0]
                add(node("utr", u), node("acct", t.src), "paid from"); add(node("utr", u), node("acct", t.dst), "paid to")
    for cid, d in (touched or {}).items():
        for a in d:
            if not is_cashout(a):
                add(node("complaint", cid), node("acct", a), "money reached", strength="strong")
    # identifiers that ride on accounts (KYC phone / device / IP)
    for r in ds.acc.itertuples():
        a = nid("acct", r.account_id)
        if a not in G:
            continue
        for col, kind in (("phone", "phone"), ("device_id", "device"), ("ip", "ip")):
            raw = getattr(r, col, "")
            val = "" if pd.isna(raw) else str(raw)
            if val and val.lower() not in ("nan", "none", "<na>"):
                add(a, node(kind, val), f"account {col}", ref=f"ACC:{r.account_id}")
    # UPI ids that appear as counterparties
    for col in ("src", "dst"):
        for p in set(ds.tx[col].astype(str)):
            if "@" in p and p.upper() == p:
                u = node("upi", p)
                for q in set(ds.tx[ds.tx[col] == p][("dst" if col == "src" else "src")].astype(str)):
                    if nid("acct", q) in G:
                        add(u, nid("acct", q), "UPI paid with")
    # domains
    for r in intel.domains.itertuples():
        if not r.domain:
            if r.ip:
                ipn = node("ip", r.ip)
                if r.complaint_id:
                    for c in str(r.complaint_id).split(","):
                        if nid("complaint", c.strip()) in G: add(nid("complaint", c.strip()), ipn, "reported IP", ref=f"IP:{r.ip}")
            continue
        d = node("domain", r.domain)
        for c in [x.strip() for x in str(r.complaint_id).split(",") if x.strip()]:
            if nid("complaint", c) in G:
                add(nid("complaint", c), d, "reported by victim", ref=f"DOM:{r.domain}")
        if r.ip:
            add(d, node("ip", r.ip), "resolves to", ref=f"DOM:{r.domain}")
        for ns in _ns_list(r.nameservers):
            add(d, node("ns", ns), "name server", "weak" if any(h in ns for h in PUBLIC_NS_HINTS) else "strong", ref=f"DOM:{r.domain}")
        if r.registrar:
            add(d, node("registrar", r.registrar), "registrar", "weak", ref=f"DOM:{r.domain}")
        if r.hosting and r.ip:
            add(nid("ip", r.ip), node("host", r.hosting), "network", "weak")
    # IP log: account <-> ip (really used), phone/upi too
    for i, r in enumerate(intel.iplog.itertuples()):
        ref = f"LOG:{i + 1}"
        ipn = node("ip", r.ip)
        for kind, val in (("acct", r.account_id), ("phone", r.phone), ("upi", r.upi)):
            if val and str(val) not in ("nan", ""):
                add(node(kind, str(val)), ipn, f"logged in from ({r.event})", ref=ref)
    return G


def evidence_nodes(G: nx.Graph, cid: str) -> dict:
    """{node: how it was reached} for ONE complaint, by explicit rules (no loose graph walking):
         its reported domains  -> the domain, its IP(s), name servers, registrar
         its reported IPs / victim phone / victim UPI
         the accounts its money reached -> their KYC phone / device / IP and the IPs they logged in from."""
    c = nid("complaint", cid)
    out = {}
    if c not in G:
        return out
    for m in G.neighbors(c):
        k = G.nodes[m]["kind"]
        if k == "domain":
            out[m] = "reported domain"
            for x in G.neighbors(m):
                if G.nodes[x]["kind"] in ("ip", "ns", "registrar"):
                    out.setdefault(x, f"of domain {G.nodes[m]['value']}")
        elif k in ("ip", "phone", "upi"):
            out[m] = "reported by victim"
        elif k == "acct" and G[c][m]["rel"] == "money reached":
            for x in G.neighbors(m):
                if G.nodes[x]["kind"] in ("ip", "phone", "device", "upi"):
                    out.setdefault(x, f"used by account {G.nodes[m]['value']}")
    return out


def cross_case_links(G: nx.Graph) -> pd.DataFrame:
    """One row per (complaint pair, shared node). strength is 'weak' when the shared thing is shared by huge numbers of people
    anyway (VPN / big hosting IP, public name server, same registrar): shown, but never counted as strong evidence."""
    comps = sorted(n.split(":", 1)[1] for n, d in G.nodes(data=True) if d["kind"] == "complaint")
    reach = {c: evidence_nodes(G, c) for c in comps}
    rows = []
    for a, b in combinations(comps, 2):
        for n in set(reach[a]) & set(reach[b]):
            d = G.nodes[n]
            rows.append(dict(a=a, b=b, kind=d["kind"], value=d["value"], strength="weak" if d.get("weak") or d["kind"] == "registrar" else "strong",
                             via_a=reach[a][n], via_b=reach[b][n]))
    df = pd.DataFrame(rows, columns=["a", "b", "kind", "value", "strength", "via_a", "via_b"])
    return df.sort_values(["a", "b", "strength", "kind"]).reset_index(drop=True)


def pair_summary(links: pd.DataFrame) -> pd.DataFrame:
    """One row per complaint pair: how many strong / weak shared things, of which kinds, and a short readable list."""
    rows = []
    for (a, b), g in links.groupby(["a", "b"]):
        strong = g[g.strength == "strong"]
        rows.append(dict(a=a, b=b, strong=len(strong), weak=len(g) - len(strong),
                         kinds=", ".join(sorted({KIND_LABEL[k] for k in strong.kind})) or "-",
                         what="; ".join(f"{KIND_LABEL[k]} {v}" for k, v in zip(g.kind, g.value))[:300]))
    return pd.DataFrame(rows, columns=["a", "b", "strong", "weak", "kinds", "what"]).sort_values(["strong", "weak"], ascending=False).reset_index(drop=True)


def digital_points(links: pd.DataFrame) -> dict:
    """{(a,b): (points, [(reason key, params)])}: what shared digital evidence adds to the complaint link score (see config.LINK_DIGITAL_*)."""
    from .. import config as C
    out = {}
    for r in pair_summary(links).itertuples():
        pts = min(C.LINK_DIGITAL_STRONG * min(r.strong, 3) + C.LINK_DIGITAL_WEAK * min(r.weak, 2), C.LINK_DIGITAL_CAP)
        if pts > 0:
            out[(r.a, r.b)] = (pts, [("digital", dict(n=r.strong + r.weak, names=r.what[:140]))])
    return out


def graph_view(G: nx.Graph, around: list[str], depth: int = 2) -> nx.Graph:
    """Small readable sub-graph: everything within `depth` steps of the chosen nodes (money-only accounts are kept but trimmed)."""
    keep = set()
    for n in around:
        if n in G:
            keep |= set(nx.single_source_shortest_path_length(G, n, cutoff=depth))
    return G.subgraph(keep).copy()
