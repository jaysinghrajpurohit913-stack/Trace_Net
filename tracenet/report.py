import pandas as pd
from .engine import pretty


def build_report(comp_row, trail, fl, rings, feats):
    c = comp_row
    cash = sum(trail.cashed.values()); held = sum(trail.held.values())
    L = [f"# TraceNet Money-Trail Report — {c.complaint_id}", "",
         f"- Victim account: **{c.victim_account}**   |   Reported loss: **Rs {c.amount:,.0f}**",
         f"- Fraud time: {c.fraud_ts}   |   Complaint filed: {c.reported_ts if pd.notna(c.reported_ts) else 'not given'}",
         f"- Accounts touched: **{len(fl)}**   |   Max hops: **{max(trail.depth.values())}**",
         f"- Tainted money already cashed out: **Rs {cash:,.0f}**   |   Still recoverable: **Rs {held:,.0f}**", "",
         "## Fund trail (chronological)", "",
         "| Time | Hop | From | To | Channel | Tainted amount (Rs) |", "|---|---|---|---|---|---|"]
    for r in trail.edges.itertuples():
        L.append(f"| {r.ts:%d-%b %H:%M} | {r.hop} | {pretty(r.src)} | {pretty(r.dst)} | {r.channel} | {r.tainted:,.0f} |")
    L += ["", "## Recommended actions (priority order)", "",
          "| # | Account | Bank | Hop | Still held (Rs) | Mule score | Ring | Action |", "|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(fl.itertuples(), 1):
        L.append(f"| {i} | {pretty(r.account_id)} | {r.bank} | {r.hop} | {r.tainted_still_held:,.0f} | {r.mule_score} | {r.ring} | {r.action} |")
    L += ["", "## Why these accounts were flagged", ""]
    for r in fl.head(8).itertuples():
        why = feats.loc[r.account_id, "reasons"] if r.account_id in feats.index else ""
        L.append(f"- **{r.account_id}**: {why or 'Receives traced funds'}")
    rel = [x for x in rings if set(x) & set(fl.account_id)]
    if rel:
        L += ["", "## Linked network (shared device / phone / IP)", ""]
        for x in rel:
            L.append(f"- Ring of {len(x)} accounts: {', '.join(x)}")
    L += ["", "_Prototype output on synthetic data. Evidence for investigative use; not a legal determination._"]
    return "\n".join(L)


def bank_requests(rnd, complaint_id, fraud_ts):
    """Draft one request per bank for the accounts whose onward movement is unknown."""
    if not rnd["ask"]:
        return "No further requests: the trail is fully resolved with the data in hand."
    L = [f"# Round {rnd['round'] + 1} requests for {complaint_id}", ""]
    for bank, items in sorted(rnd["ask"].items()):
        L += [f"**To: Nodal Officer, {bank}**",
              f"Ref {complaint_id}. Please (1) place a lien on any remaining balance of the accounts below and "
              f"(2) share the statement from {fraud_ts:%d-%b-%Y %H:%M} onward, with beneficiary details.", ""]
        L += [f"- {a}: expected credit from this fraud Rs {amt:,.0f}" for a, amt in items] + [""]
    return "\n".join(L)
