"""Cross-complaint analysis: which complaints belong to the same gang, and why.

Steps
1. joint_trace   - follow the money of ALL complaints together on one shared ledger, so an account that
                   holds money from two complaints is split fairly (no double counting).
2. link scores   - a soft score for every pair of complaints (shared accounts, shared cash-out points,
                   same gang ring, victim reused, close in time). Not a hard rule: more evidence = stronger.
3. case groups   - complaints joined by Strong / Probable links form one CASE group.
4. patterns      - shared accounts, shared exits, gateway accounts, speed, time of day, account rotation, banks.
5. outputs       - new-complaint alert, combined report, one bank file / request per bank for the whole group.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations

import numpy as np
import pandas as pd

from . import config as C
from .engine import is_cashout, pretty, trace_funds

STRONG, PROBABLE, POSSIBLE = C.LINK_STRONG, C.LINK_PROBABLE, C.LINK_POSSIBLE      # score cut-offs (see config.py)


# ------------------------------------------------------------------ 1. joint trace ----
@dataclass
class Joint:
    events: pd.DataFrame      # ts, acct, cid, amount  (stolen money of complaint `cid` that arrived at `acct`)
    held: dict                # acct -> {cid: stolen money still inside}


def joint_trace(tx: pd.DataFrame, comp: pd.DataFrame, max_hours: int = 96) -> Joint:
    """Same idea as engine.trace_funds ('tainted-first') but for all complaints at once.
    When an account holds money from several complaints and sends some on, every complaint's share
    moves in proportion to what it put in (pro-rata)."""
    info = {}
    for r in comp.sort_values("fraud_ts").itertuples():
        seeds = getattr(r, "seed_ids", None)
        seeds = set(map(str, seeds)) if isinstance(seeds, (list, tuple, set)) and len(seeds) else None
        info[r.complaint_id] = dict(victim=r.victim_account, amt=float(r.amount), start=r.fraud_ts,
                                    end=r.fraud_ts + pd.Timedelta(hours=max_hours), seeds=seeds)
    order, ptr = list(info), 0
    held, ev = {}, []

    def step(r, ts):
        lots = held.get(r.src)
        if not lots:
            return False
        usable = {}
        for cid, a in lots.items():
            i = info[cid]
            if a <= 0.01 or ts > i["end"]:
                continue
            if r.src == i["victim"] and i["seeds"] is not None and str(r.txn_id) not in i["seeds"]:
                continue
            usable[cid] = a
        tot = sum(usable.values())
        if tot <= 0.01:
            return False
        f = min(tot, r.amount) / tot
        dst = held.setdefault(r.dst, {})
        for cid, a in usable.items():
            share = a * f
            lots[cid] = a - share
            dst[cid] = dst.get(cid, 0.0) + share
            ev.append((ts, r.dst, cid, share))
        return True

    if comp.empty:
        return Joint(pd.DataFrame(columns=["ts", "acct", "cid", "amount"]), {})
    for ts, grp in tx[tx.ts >= comp.fraud_ts.min()].groupby("ts", sort=True):
        while ptr < len(order) and info[order[ptr]]["start"] <= ts:
            cid = order[ptr]; v = held.setdefault(info[cid]["victim"], {})
            v[cid] = v.get(cid, 0.0) + info[cid]["amt"]; ptr += 1
        todo = list(grp.itertuples())
        while todo:                                   # same-time rows: repeat until nothing more can move
            left = [r for r in todo if not step(r, ts)]
            if len(left) == len(todo):
                break
            todo = left
    events = pd.DataFrame(ev, columns=["ts", "acct", "cid", "amount"])
    victim_of = {c: i["victim"] for c, i in info.items()}
    events = events[events.acct != events.cid.map(victim_of)]          # a victim getting their own money back is not a mule
    return Joint(events, held)


# ------------------------------------------------------------------ 2-4. the analysis ----
@dataclass
class Links:
    comp: pd.DataFrame
    joint: Joint
    trails: dict
    touched: dict                    # cid -> {account: money received from that complaint}
    pairs: pd.DataFrame              # a, b, score, level, reasons
    groups: list                     # list of dict (see _group)
    group_of: dict                   # cid -> group id
    shared: pd.DataFrame             # accounts used by 2+ complaints
    exits: pd.DataFrame              # cash-out points used by 2+ complaints
    split: pd.DataFrame              # account, complaint, received, still_inside   (shared accounts only)
    ring_of: dict
    feats: pd.DataFrame


def _level(score):
    return "strong" if score >= STRONG else "probable" if score >= PROBABLE else "possible" if score >= POSSIBLE else None


def analyse_links(ds, feats: pd.DataFrame, rings: list, max_hours: int = C.TRACE_MAX_HOURS, digital: dict | None = None) -> Links:
    """digital: optional {(complaint a, complaint b): (points, reasons)} from intel.graph.digital_points (shared domains / IPs / phones...)."""
    comp, tx = ds.comp.reset_index(drop=True), ds.tx
    jt = joint_trace(tx, comp, max_hours)
    trails = {}
    for r in comp.itertuples():
        seeds = getattr(r, "seed_ids", None)
        trails[r.complaint_id] = trace_funds(tx, r.victim_account, r.fraud_ts, r.amount, max_hours=max_hours,
                                             seed_txn_ids=seeds if isinstance(seeds, (list, tuple)) and len(seeds) else None)
    ev = jt.events
    touched = {c: {} for c in comp.complaint_id}
    for (cid, a), v in ev.groupby(["cid", "acct"]).amount.sum().items():
        touched[cid][a] = float(v)
    ring_of = {a: i for i, r in enumerate(rings, 1) for a in r}
    victims = dict(zip(comp.complaint_id, comp.victim_account))
    fts = dict(zip(comp.complaint_id, comp.fraud_ts))
    mule = feats.mule_score if len(feats) else pd.Series(dtype=float)

    # candidate pairs only where some evidence exists (fast even with thousands of complaints)
    by_acct, by_ring, by_victim = {}, {}, {}
    for c, d in touched.items():
        for a in d:
            by_acct.setdefault(a, set()).add(c)
            if a in ring_of:
                by_ring.setdefault(ring_of[a], set()).add(c)
    for c, v in victims.items():
        for other in by_acct.get(v, ()):
            if other != c:
                by_victim.setdefault(frozenset((c, other)), []).append(v)
    cand = set()
    for s in list(by_acct.values()) + list(by_ring.values()):
        cand |= {frozenset(p) for p in combinations(sorted(s), 2)}
    cand |= set(by_victim)
    cand |= {frozenset(k) for k in (digital or {})}

    rows = []
    for pr in cand:
        a, b = sorted(pr)
        A, B = set(touched[a]), set(touched[b])
        sa = sorted(x for x in A & B if not is_cashout(x)); se = sorted(x for x in A & B if is_cashout(x))
        pts, why = 0.0, []
        if sa:
            pts += min(sum(C.LINK_SHARED_ACCT_MULE if float(mule.get(x, 0)) >= C.MULE_FLAG_AT else C.LINK_SHARED_ACCT_OTHER for x in sa), C.LINK_SHARED_ACCT_CAP)
            why.append(("accts", dict(n=len(sa), names=", ".join(sa[:4]) + (" …" if len(sa) > 4 else ""))))
        if se:
            pts += min(C.LINK_SHARED_EXIT * len(se), C.LINK_SHARED_EXIT_CAP)
            why.append(("exit", dict(names=", ".join(pretty(x) for x in se[:3]))))
        ra = {ring_of[x] for x in A if x in ring_of}; rb = {ring_of[x] for x in B if x in ring_of}
        new_rings = (ra & rb) - {ring_of[x] for x in sa if x in ring_of}
        if new_rings:
            pts += min(C.LINK_RING * len(new_rings), C.LINK_RING_CAP)
            why.append(("ring", dict(n=len(new_rings))))
        vr = [v for v in (victims[a] if victims[a] in B else None, victims[b] if victims[b] in A else None) if v]
        if vr:
            pts += C.LINK_VICTIM_REUSED
            why.append(("victim", dict(acct=vr[0])))
        dg = (digital or {}).get((a, b)) or (digital or {}).get((b, a))
        if dg:
            pts += dg[0]; why += list(dg[1])
        gap_h = abs((fts[a] - fts[b]).total_seconds()) / 3600
        if pts > 0 and gap_h <= C.LINK_TIME_WINDOW_H:
            pts += C.LINK_TIME_BONUS
            why.append(("time", dict(h=gap_h)))
        lvl = _level(pts)
        if lvl:
            rows.append(dict(a=a, b=b, score=round(pts, 1), level=lvl, reasons=why))
    pairs = pd.DataFrame(rows, columns=["a", "b", "score", "level", "reasons"]).sort_values("score", ascending=False).reset_index(drop=True)

    # case groups: connected through Strong / Probable links
    parent = {c: c for c in comp.complaint_id}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for r in pairs[pairs.level.isin(["strong", "probable"])].itertuples():
        parent[find(r.a)] = find(r.b)
    members = {}
    for c in comp.complaint_id:
        members.setdefault(find(c), []).append(c)
    lost = dict(zip(comp.complaint_id, comp.amount))
    ordered = sorted(members.values(), key=lambda m: (-len(m), -sum(lost[x] for x in m)))
    groups, group_of = [], {}
    multi = 0
    for m in ordered:
        gid = None
        if len(m) > 1:
            multi += 1; gid = f"CASE-{multi}"
        else:
            gid = f"SINGLE-{m[0]}"
        for c in m:
            group_of[c] = gid
        groups.append(_group(gid, sorted(m, key=lambda c: fts[c]), comp, jt, trails, touched, pairs, feats, ring_of, victims))

    # shared accounts / exits / money split
    acct_rows, exit_rows, split_rows = [], [], []
    bank = feats.bank if "bank" in feats else pd.Series(dtype=object)
    first_hop = Counter(a for t in trails.values() for a, d in t.depth.items() if d == 1)
    for a, cs in by_acct.items():
        if len(cs) < 2:
            continue
        cs = sorted(cs, key=lambda c: fts[c])
        inside = {c: jt.held.get(a, {}).get(c, 0.0) for c in cs}
        recv = {c: touched[c][a] for c in cs}
        if is_cashout(a):
            exit_rows.append(dict(account=a, n=len(cs), complaints=", ".join(cs), total=sum(recv.values())))
            continue
        evs = ev[ev.acct == a]
        acct_rows.append(dict(account=a, bank=bank.get(a, "?"), n=len(cs), complaints=", ".join(cs), total=sum(recv.values()),
                              inside=sum(inside.values()), score=float(mule.get(a, 0)), ring=f"RING-{ring_of[a]}" if a in ring_of else "-",
                              first_use=evs.ts.min(), last_use=evs.ts.max(), first_hop_in=first_hop.get(a, 0), group=group_of[cs[0]]))
        for c in cs:
            split_rows.append(dict(account=a, complaint=c, received=recv[c], still_inside=inside[c]))
    shared = pd.DataFrame(acct_rows, columns=["account", "bank", "n", "complaints", "total", "inside", "score", "ring", "first_use",
                                              "last_use", "first_hop_in", "group"]).sort_values(["n", "total"], ascending=False).reset_index(drop=True)
    exits = pd.DataFrame(exit_rows, columns=["account", "n", "complaints", "total"]).sort_values(["n", "total"], ascending=False).reset_index(drop=True)
    split = pd.DataFrame(split_rows, columns=["account", "complaint", "received", "still_inside"])
    return Links(comp, jt, trails, touched, pairs, groups, group_of, shared, exits, split, ring_of, feats)


def _group(gid, cids, comp, jt, trails, touched, pairs, feats, ring_of, victims):
    c = comp.set_index("complaint_id").loc[cids]
    accts = sorted({a for x in cids for a in touched[x] if not is_cashout(a)})
    exits = sorted({a for x in cids for a in touched[x] if is_cashout(a)})
    inside = sum(v for a in accts for cid, v in jt.held.get(a, {}).items() if cid in cids)
    cashed = sum(v for a in exits for cid, v in jt.held.get(a, {}).items() if cid in cids)
    cnt = Counter(a for x in cids for a in touched[x])
    shared = [a for a, k in cnt.items() if k >= 2]
    sub = pairs[pairs.a.isin(cids) & pairs.b.isin(cids) & pairs.level.isin(["strong", "probable"])]
    speeds = []
    for x in cids:
        e = trails[x].edges
        if len(e):
            co = e[e.dst.map(is_cashout)]
            if len(co):
                speeds.append((co.ts.min() - c.loc[x, "fraud_ts"]).total_seconds() / 60)
    ts = c.fraud_ts.sort_values()
    first_seen = jt.events[jt.events.cid.isin(cids) & ~jt.events.acct.map(is_cashout)].groupby("acct").ts.min()
    banks = Counter(feats.bank.get(a, "Unknown bank") if len(feats) else "Unknown bank" for a in accts)
    return dict(id=gid, complaints=cids, accounts=accts, exits=exits, shared=sorted(shared), lost=float(c.amount.sum()), inside=float(inside),
                cashed=float(cashed), start=ts.iloc[0], end=ts.iloc[-1],
                gap_h=float(np.mean(np.diff(ts.values).astype("timedelta64[m]").astype(float)) / 60) if len(ts) > 1 else None,
                strong=int((sub.level == "strong").sum()), probable=int((sub.level == "probable").sum()),
                rings=sorted({ring_of[a] for a in accts if a in ring_of}), banks=dict(banks.most_common()),
                speed_min=float(np.median(speeds)) if speeds else None, hours=Counter(int(h) for h in c.fraud_ts.dt.hour),
                new_per_day=first_seen.dt.date.value_counts().sort_index().to_dict(), victims=[victims[x] for x in cids])


# ------------------------------------------------------------------ 5. outputs ----
def alert_for(lk: Links, cid: str) -> dict:
    """What a newly arrived complaint is connected to. Only complaints that arrived EARLIER are considered."""
    comp = lk.comp.set_index("complaint_id")
    arrival = (comp.reported_ts.fillna(comp.fraud_ts) if "reported_ts" in comp else comp.fraud_ts)
    mine = arrival[cid]
    p = lk.pairs[((lk.pairs.a == cid) | (lk.pairs.b == cid))]
    rows = []
    for r in p.itertuples():
        o = r.b if r.a == cid else r.a
        if arrival[o] <= mine:
            rows.append(dict(other=o, score=r.score, level=r.level, reasons=r.reasons))
    near = pd.DataFrame(rows, columns=["other", "score", "level", "reasons"])
    accts = [a for a in lk.touched[cid] if any(a in lk.touched[o] for o in near.other)] if len(near) else []
    inside = {a: sum(lk.joint.held.get(a, {}).values()) for a in accts if not is_cashout(a)}
    return dict(cid=cid, links=near, shared_accounts=accts, inside=sum(inside.values()), group=lk.group_of.get(cid))


def group_bank_file(lk: Links, gid: str) -> pd.DataFrame:
    """One row per account to act on across the WHOLE group, ready for each bank's nodal officer."""
    g = next(x for x in lk.groups if x["id"] == gid)
    cids = set(g["complaints"])
    rows = []
    for a in g["accounts"]:
        mine = [c for c in g["complaints"] if a in lk.touched[c]]
        held = sum(v for c, v in lk.joint.held.get(a, {}).items() if c in cids)
        score = float(lk.feats.mule_score.get(a, 0)) if a in lk.feats.index else 0.0
        act = "FREEZE NOW (funds still inside)" if held > 1 else "Freeze / KYC re-verification" if (score >= 40 or len(mine) >= 2) else "Monitor"
        rows.append(dict(bank=lk.feats.bank.get(a, "Unknown bank") if a in lk.feats.index else "Unknown bank", account_id=a,
                         complaints=" ; ".join(mine), n_complaints=len(mine), received=round(sum(lk.touched[c][a] for c in mine)),
                         still_held=round(held), mule_score=score, ring=f"RING-{lk.ring_of[a]}" if a in lk.ring_of else "-", action=act))
    df = pd.DataFrame(rows, columns=["bank", "account_id", "complaints", "n_complaints", "received", "still_held", "mule_score", "ring", "action"])
    df = df[df.action != "Monitor"]
    return df.sort_values(["bank", "still_held"], ascending=[True, False]).reset_index(drop=True)


def group_report(lk: Links, gid: str) -> str:
    g = next(x for x in lk.groups if x["id"] == gid)
    comp = lk.comp.set_index("complaint_id")
    L = [f"# TraceNet Combined Case Report: {gid}", "",
         f"- Complaints: **{len(g['complaints'])}**   |   Total reported loss: **Rs {g['lost']:,.0f}**",
         f"- Active between {g['start']:%d-%b %H:%M} and {g['end']:%d-%b %H:%M}",
         f"- Stolen money still inside accounts: **Rs {g['inside']:,.0f}**   |   Already cashed out: **Rs {g['cashed']:,.0f}**",
         f"- Accounts used: **{len(g['accounts'])}** (shared by 2+ complaints: **{len(g['shared'])}**)   |   Cash-out points: **{len(g['exits'])}**", ""]
    L += ["## Complaints in this case", "", "| Complaint | Victim account | Lost (Rs) | Fraud time |", "|---|---|---|---|"]
    for c in g["complaints"]:
        L.append(f"| {c} | {comp.loc[c, 'victim_account']} | {comp.loc[c, 'amount']:,.0f} | {comp.loc[c, 'fraud_ts']:%d-%b %H:%M} |")
    p = lk.pairs[lk.pairs.a.isin(g["complaints"]) & lk.pairs.b.isin(g["complaints"])]
    L += ["", "## Why these complaints are linked", ""]
    for r in p.itertuples():
        txt = "; ".join(_reason_en(k, d) for k, d in r.reasons)
        L.append(f"- {r.a} and {r.b}: **{r.level}** (score {r.score}). {txt}")
    if g["shared"]:
        L += ["", "## Accounts used by more than one complaint", "", "| Account | Bank | Complaints | Total received (Rs) | Still inside (Rs) | Mule score |", "|---|---|---|---|---|---|"]
        for r in lk.shared[lk.shared.account.isin(g["shared"])].itertuples():
            L.append(f"| {r.account} | {r.bank} | {r.complaints} | {r.total:,.0f} | {r.inside:,.0f} | {r.score:.0f} |")
    if g["exits"]:
        L += ["", "## Cash-out points", ""] + [f"- {pretty(x)}" for x in g["exits"]]
    L += ["", "## Pattern", ""]
    if g["speed_min"] is not None:
        L.append(f"- Median time from fraud to first cash-out: **{g['speed_min']:.0f} minutes**")
    if g["gap_h"] is not None:
        L.append(f"- Average gap between complaints: **{g['gap_h']:.1f} hours**")
    top_h = ", ".join(f"{h:02d}:00 ({n})" for h, n in sorted(g["hours"].items(), key=lambda x: -x[1])[:3])
    L.append(f"- Most frauds started around: {top_h}")
    L.append("- Banks involved: " + ", ".join(f"{b} ({n})" for b, n in g["banks"].items()))
    bf = group_bank_file(lk, gid)
    L += ["", "## One request per bank (whole case)", ""]
    for b, d in bf.groupby("bank"):
        L.append(f"**To: Nodal Officer, {b}**  Please place a lien on any balance and share statements for: " +
                 ", ".join(f"{r.account_id} (complaints {r.complaints})" for r in d.itertuples()))
        L.append("")
    L += ["_Prototype output. Evidence for investigative use; not a legal determination._"]
    return "\n".join(L)


def _reason_en(k, d):
    return {"accts": "shares {n} account(s): {names}", "exit": "same cash-out point: {names}", "ring": "accounts belong to the same gang ring ({n})",
            "victim": "victim account {acct} was used to pass the other complaint's money", "time": "frauds within {h:.0f} hours of each other",
            "digital": "shared digital evidence ({n}): {names}"}[k].format(**d)


def complaint_table(lk: Links) -> pd.DataFrame:
    """One row per complaint: who, when, how much, where the money is now, which case group. Feeds the list + search page.
    'inside' / 'cashed' come from the joint ledger, so a shared account is never counted twice."""
    comp = lk.comp
    victim_of = dict(zip(comp.complaint_id, comp.victim_account))
    inside = dict.fromkeys(comp.complaint_id, 0.0); cashed = dict.fromkeys(comp.complaint_id, 0.0)
    for a, lots in lk.joint.held.items():
        for cid, v in lots.items():
            if v <= 1 or cid not in inside:
                continue
            if is_cashout(a):
                cashed[cid] += v
            elif a != victim_of[cid]:
                inside[cid] += v
    group_size = {g["id"]: len(g["complaints"]) for g in lk.groups}
    rows = []
    for r in comp.itertuples():
        mules = sorted(a for a in lk.touched[r.complaint_id] if not is_cashout(a))
        banks = sorted({str(lk.feats.bank.get(a, "")) for a in mules if a in lk.feats.index} - {"", "Unknown bank", "nan"})
        gid = lk.group_of.get(r.complaint_id, "")
        g = getattr(r, "victim_name", "") or ""
        delay = (r.reported_ts - r.fraud_ts).total_seconds() / 3600 if pd.notna(getattr(r, "reported_ts", pd.NaT)) else float("nan")
        rows.append(dict(complaint_id=r.complaint_id, victim_name=str(g) if str(g) != "nan" else "", victim_phone=str(getattr(r, "victim_phone", "") or ""),
                         victim_upi=str(getattr(r, "victim_upi", "") or ""), victim_account=r.victim_account, amount=float(r.amount), fraud_ts=r.fraud_ts,
                         reported_ts=getattr(r, "reported_ts", pd.NaT), delay_h=delay, case=gid if group_size.get(gid, 1) > 1 else "",
                         inside=inside[r.complaint_id], cashed=cashed[r.complaint_id], banks=banks, mules=mules,
                         first_mule=str(getattr(r, "first_mule", "") or ""),
                         utr=" ".join(x for x in str(getattr(r, "txn_ref", "") or "").replace(";", " ").replace(",", " ").split() if x.lower() != "nan")))
    df = pd.DataFrame(rows)
    df["delay_h"] = pd.to_numeric(df.delay_h, errors="coerce"); df["reported_ts"] = pd.to_datetime(df.reported_ts)
    df["blob"] = (df.complaint_id + " " + df.victim_name + " " + df.victim_phone + " " + df.victim_upi + " " + df.victim_account + " " + df.first_mule + " " +
                  df.mules.map(" ".join) + " " + df.banks.map(" ".join) + " " + df.case + " " + df.utr).str.lower()
    return df
