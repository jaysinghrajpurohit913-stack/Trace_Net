"""Plain-language case brief: what happened, where the money is, what to do now."""
import pandas as pd
from .engine import pretty


def rs(x):
    return f"Rs {x:,.0f}"


def case_brief(c, trail, fl, rings, feats):
    cash = sum(trail.cashed.values())
    held = {a: v for a, v in trail.held.items() if v > 1}
    mules = fl[~fl.is_cashout]
    out = dict(title=f"Case {c.complaint_id}")
    kk = []          # the same steps as (translation key, parameters) so the app can show them in Hindi or English
    out["headline"] = (f"{rs(c.amount)} was stolen from account {c.victim_account}. "
                       f"It was passed through {len(mules)} accounts in {max(trail.depth.values())} steps.")
    out["headline_k"] = ("br_headline", dict(amt=f"{c.amount:,.0f}", acct=c.victim_account, n=len(mules), s=max(trail.depth.values())))
    if not len(mules):
        out["headline"] = f"{rs(c.amount)} was stolen from account {c.victim_account}. No onward payments were found in the data yet."
        out["headline_k"] = ("br_headline_none", dict(amt=f"{c.amount:,.0f}", acct=c.victim_account))
    out["facts"] = [
        f"Already taken out as cash/wallet/crypto: {rs(cash)}",
        f"Still sitting inside bank accounts: {rs(sum(held.values()))}",
        f"Accounts that touched the stolen money: {len(mules)}",
    ]
    if pd.notna(c.reported_ts):
        out["facts"].append(f"Complaint was filed {(c.reported_ts - c.fraud_ts).total_seconds() / 3600:.0f} hours after the fraud")
    steps = []
    for r in fl[fl.tainted_still_held > 1].head(5).itertuples():
        steps.append(f"Ask {r.bank} to freeze account {r.account_id} NOW. About {rs(r.tainted_still_held)} of the stolen money is still inside.")
        kk.append(("br_freeze", dict(bank=r.bank, acct=r.account_id, amt=f"{r.tainted_still_held:,.0f}")))
    rest = fl[(fl.tainted_still_held <= 1) & (~fl.is_cashout) & (fl.mule_score >= 40)]
    for bank, g in rest.groupby("bank"):
        steps.append(f"Ask {bank} to hold/verify and send statements for: {', '.join(g.account_id)}. They look like mule accounts (money passed through them).")
        kk.append(("br_hold", dict(bank=bank, accts=", ".join(g.account_id))))
    co = fl[fl.is_cashout]
    if len(co):
        steps.append(f"Money left the banking system through: {', '.join(pretty(a) for a in co.account_id)}. Ask these cash-out points for their records (CCTV, KYC, withdrawal details).")
        kk.append(("br_cash", dict(names=", ".join(pretty(a) for a in co.account_id))))
    trail_accts = set(fl.account_id)
    bigger = [r for r in rings if set(r) & trail_accts]
    out["gang"] = None; out["gang_k"] = None
    if bigger:
        r = max(bigger, key=len); extra = [a for a in r if a not in trail_accts]
        out["gang"] = (f"These accounts look connected to a larger gang of {len(r)} accounts (they share devices, phones or the same cash-out points)."
                       + (f" Other accounts in this gang to check against other complaints: {', '.join(extra[:6])}." if extra else ""))
        steps.append("Check whether other complaints involve the same gang accounts, then combine them into one case.")
        out["gang_k"] = ("br_gang", dict(n=len(r), extra=(", ".join(extra[:6]))))
        kk.append(("br_gang_check", {}))
    out["steps"] = steps; out["steps_k"] = kk
    sus = []
    for r in mules.sort_values("mule_score", ascending=False).head(6).itertuples():
        why = feats.loc[r.account_id, "reasons"] if r.account_id in feats.index else ""
        sus.append((r.account_id, r.bank, r.mule_score, why or "Received stolen money"))
    out["suspicious"] = sus
    return out


def brief_text(d):
    L = ["=" * 72, d["title"], "=" * 72, "", d["headline"], "", "KEY FACTS"]
    L += [f"  - {x}" for x in d["facts"]]
    L += ["", "WHAT TO DO NOW (in this order)"]
    L += [f"  {i}. {x}" for i, x in enumerate(d["steps"], 1)]
    if d["gang"]: L += ["", "GANG", f"  {d['gang']}"]
    L += ["", "MOST SUSPICIOUS ACCOUNTS (score out of 100)"]
    L += [f"  - {a} ({b}) score {s:.0f}: {w}" for a, b, s, w in d["suspicious"]]
    L += ["", "Mule account = an account used only to pass stolen money along.",
          "Note: based only on the data provided. Treat as a lead for investigators, not proof.", ""]
    return "\n".join(L)
