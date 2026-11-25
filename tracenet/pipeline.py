"""The ONE place that runs the whole analysis, in order. The UI calls run_analysis(); tests call it too.

    data (Dataset)  ->  mule features/scores -> rings -> complaint links -> digital intel -> cross-case digital links -> final links

Adding a new analysis step = add a field to Analysis and one line in run_analysis.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .engine import account_features, score_mules, link_entities, link_by_flow, merge_rings, trace_funds
from .intel.analyse import correlate_iplog, domain_flags, ip_table
from .intel.graph import build_graph, cross_case_links, digital_points, pair_summary
from .intel.model import Intel, empty_domains
from .linking import Links, analyse_links, complaint_table


@dataclass
class Analysis:
    ds: object
    feats: pd.DataFrame
    rings: list
    lk: Links
    intel: Intel
    flags: pd.DataFrame                  # domain red flags
    corr: pd.DataFrame                   # IP-log events matched to bank transactions
    graph: object                        # networkx relationship graph (all entity types)
    dlinks: pd.DataFrame                 # complaint pairs sharing digital things (one row per shared thing)
    dpairs: pd.DataFrame                 # the same, one row per complaint pair
    table: pd.DataFrame = field(default_factory=pd.DataFrame)   # one row per complaint (list + search page)


def run_analysis(ds, intel: Intel | None = None, log_zone: str = "") -> Analysis:
    feats = score_mules(account_features(ds.tx, ds.acc))
    _, ring_data = link_entities(ds.acc)
    rings = merge_rings(ring_data, link_by_flow(ds.tx, feats))
    lk0 = analyse_links(ds, feats, rings)                              # money only: needed to know which accounts each complaint touched

    intel = intel or Intel(domains=ds.domains, iplog=ds.iplog)
    ips = intel.ips if len(intel.ips) else ip_table(intel.domains if len(intel.domains) else empty_domains())
    intel = Intel(domains=intel.domains, iplog=intel.iplog, ips=ips, certs=intel.certs, lookups=intel.lookups)
    G = build_graph(ds, intel, lk0.touched, ips)
    dl = cross_case_links(G)
    lk = analyse_links(ds, feats, rings, digital=digital_points(dl)) if len(dl) else lk0
    return Analysis(ds=ds, feats=feats, rings=rings, lk=lk, intel=intel, flags=domain_flags(intel.domains, ips) if len(intel.domains) else pd.DataFrame(),
                    corr=correlate_iplog(intel.iplog, ds.tx, ds.acc, ips, log_zone), graph=G, dlinks=dl, dpairs=pair_summary(dl) if len(dl) else pd.DataFrame(),
                    table=complaint_table(lk))


def trail_from_utr(ds, utr: str):
    """Start from ONE payment (UTR / transaction reference) - e.g. a victim's. Returns (row, trail) or (None, None) if not found."""
    u = str(utr).strip().upper()
    hit = ds.tx[ds.tx.txn_id.astype(str).str.upper() == u]
    if hit.empty:
        return None, None
    r = hit.iloc[0]
    return r, trace_funds(ds.tx, r.src, r.ts, float(r.amount), seed_txn_ids=[r.txn_id])
