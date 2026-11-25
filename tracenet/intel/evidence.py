"""Numbered evidence references.

Every statement in a report can point to its source: a bank line (UTR), an IP-log row, an indicator row, a public lookup.
Refs are stable and human-readable:  UTR:T000123   LOG:7   DOM:secure-kyc.example   IP:203.0.113.5   LKP:12   ACC:M1A0
"""
from __future__ import annotations

import pandas as pd

from .model import Intel


def evidence_table(ds, intel: Intel, complaint_ids=None, max_rows=400) -> pd.DataFrame:
    """-> DataFrame(ref, kind, what, when, source) for the chosen complaints (or all)."""
    rows = []
    comp = ds.comp if complaint_ids is None else ds.comp[ds.comp.complaint_id.isin(complaint_ids)]
    utrs = set()
    for r in comp.itertuples():
        for u in str(getattr(r, "txn_ref", "")).replace(";", ",").split(","):
            u = u.strip().upper()
            if u:
                utrs.add(u)
        utrs |= {str(x) for x in (getattr(r, "seed_ids", None) or [])}
    t = ds.tx[ds.tx.txn_id.astype(str).isin(utrs)]
    for r in t.itertuples():
        rows.append(dict(ref=f"UTR:{r.txn_id}", kind="Bank transaction", what=f"{r.src} → {r.dst}  ₹{r.amount:,.0f} ({r.channel})", when=r.ts, source="Bank statement / transaction file"))
    for r in intel.domains.itertuples():
        if r.domain and (complaint_ids is None or not r.complaint_id or set(map(str.strip, r.complaint_id.split(","))) & set(complaint_ids)):
            rows.append(dict(ref=f"DOM:{r.domain}", kind="Domain indicator", what=f"{r.domain} → {r.ip or '?'} · registrar {r.registrar or '?'} · created {r.created:%d %b %Y}" if pd.notna(r.created) else f"{r.domain} → {r.ip or '?'}",
                             when=r.first_seen, source=r.source or "Indicator file"))
    for i, r in enumerate(intel.iplog.itertuples(), 1):
        rows.append(dict(ref=f"LOG:{i}", kind="IP-log event", what=f"{r.event} from {r.ip}" + (f" by {r.account_id}" if r.account_id else ""), when=r.ts_utc, source=(r.source or "IP log") + " (time in UTC)"))
    for i, r in enumerate(intel.lookups.itertuples(), 1):
        rows.append(dict(ref=f"LKP:{i}", kind="Public lookup", what=f"{r.query} {'OK' if r.ok else 'FAILED'}", when=r.time_utc, source=r.source))
    return pd.DataFrame(rows[:max_rows], columns=["ref", "kind", "what", "when", "source"])
