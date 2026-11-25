"""One event list across bank money, complaints, domains and IP logs (all on the bank's local clock)."""
import pandas as pd

from ..engine import is_cashout, pretty, short
from .timeutil import to_local


def events_for(an, cids) -> pd.DataFrame:
    """-> DataFrame(when, lane, label, ref) for the chosen complaints. Lanes: Complaint | Bank | Domain / IP | IP log."""
    rows = []
    comp = an.ds.comp[an.ds.comp.complaint_id.isin(cids)]
    accts = set()
    for r in comp.itertuples():
        rows.append(dict(when=r.fraud_ts, lane="Complaint", label=f"{r.complaint_id}: fraud, ₹{r.amount:,.0f} taken from {short(r.victim_account)}", ref=f"UTR:{getattr(r, 'txn_ref', '')}" if str(getattr(r, "txn_ref", "")) not in ("", "nan") else ""))
        if pd.notna(r.reported_ts):
            rows.append(dict(when=r.reported_ts, lane="Complaint", label=f"{r.complaint_id}: complaint filed", ref=""))
        tr = an.lk.trails[r.complaint_id]
        accts |= set(an.lk.touched[r.complaint_id])
        for e in tr.edges.itertuples():
            if e.hop == 1 or is_cashout(e.dst):
                what = f"cash-out via {pretty(e.dst, short_ids=True)}" if is_cashout(e.dst) else f"money reaches {short(e.dst)}"
                rows.append(dict(when=e.ts, lane="Bank", label=f"{r.complaint_id}: {what} (₹{e.tainted:,.0f})", ref=f"UTR:{e.txn_id}"))
    d = an.intel.domains
    if len(d):
        for r in d.itertuples():
            ids = {x.strip() for x in str(r.complaint_id).split(",") if x.strip()}
            if ids & set(cids) and pd.notna(r.first_seen):
                rows.append(dict(when=r.first_seen, lane="Domain / IP", label=f"first seen: {r.domain or r.ip} ({r.ip or ''})", ref=f"DOM:{r.domain}" if r.domain else f"IP:{r.ip}"))
            if ids & set(cids) and pd.notna(r.created) and r.domain:
                rows.append(dict(when=r.created, lane="Domain / IP", label=f"domain registered: {r.domain}", ref=f"DOM:{r.domain}"))
    if len(an.intel.iplog):
        lg = an.intel.iplog.copy(); lg["when"] = to_local(lg.ts_utc); lg["n"] = range(1, len(lg) + 1)
        ph = an.ds.acc.drop_duplicates("phone").set_index("phone").account_id.to_dict() if "phone" in an.ds.acc else {}
        lg["acct"] = lg.account_id.where(lg.account_id != "", lg.phone.map(ph).fillna(""))
        for r in lg[lg.acct.isin(accts)].itertuples():
            rows.append(dict(when=r.when, lane="IP log", label=f"{r.event} from {r.ip} by {short(r.acct)}", ref=f"LOG:{r.n}"))
    return pd.DataFrame(rows, columns=["when", "lane", "label", "ref"]).sort_values("when").reset_index(drop=True)
