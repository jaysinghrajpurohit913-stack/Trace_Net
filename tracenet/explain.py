"""Turns a trail / a group of complaints into numbered, plain-language items.
The same numbers are drawn on the pictures (viz.py) and explained below them (app.py)."""
import pandas as pd

from .engine import is_cashout


def _bank(feats, a):
    return str(feats.bank.get(a, "")) if len(feats) and a in feats.index else ""


def trail_nodes(trail, feats, frontier=()):
    """Accounts the stolen money reached, numbered in the order they received it.
    kind: inside (still holds money) | passed (empty, passed on) | cash (left the banks) | unknown (bank has not replied)."""
    e = trail.edges
    if e is None or e.empty:
        return []
    victim = next(iter(trail.depth))
    first_in = e.groupby("dst").ts.min()
    recv = e.groupby("dst").tainted.sum()
    first_out = e.groupby("src").ts.min()
    order = sorted([a for a in trail.depth if a != victim and a in first_in.index], key=lambda a: (first_in[a], str(a)))
    out = []
    for i, a in enumerate(order, 1):
        held = float(trail.held.get(a, 0) or 0)
        if is_cashout(a):
            kind = "cash"
        elif a in frontier:
            kind = "unknown"
        elif held > 1:
            kind = "inside"
        else:
            kind = "passed"
        delay = (first_out[a] - first_in[a]).total_seconds() / 60 if a in first_out.index else None
        score = float(feats.mule_score.get(a, 0)) if len(feats) and a in feats.index else 0.0
        out.append(dict(n=i, acct=a, kind=kind, recv=float(recv[a]), held=held, t=first_in[a], delay=delay, bank="" if kind == "cash" else _bank(feats, a),
                        hop=int(trail.depth[a]), score=score))
    return out


def shared_nodes(lk, cids, top=8):
    """The accounts / cash-out points used by the most complaints, numbered 1..top."""
    cnt, tot = {}, {}
    for c in cids:
        for a, v in lk.touched[c].items():
            cnt[a] = cnt.get(a, 0) + 1
            tot[a] = tot.get(a, 0.0) + v
    ranked = sorted([a for a, k in cnt.items() if k >= 2], key=lambda a: (-cnt[a], -tot[a]))[:top]
    out = []
    for i, a in enumerate(ranked, 1):
        inside = sum(v for c, v in lk.joint.held.get(a, {}).items() if c in cids)
        out.append(dict(n=i, acct=a, is_exit=is_cashout(a), k=cnt[a], total=tot[a], inside=float(inside),
                        score=float(lk.feats.mule_score.get(a, 0)) if a in lk.feats.index else 0.0, bank=_bank(lk.feats, a)))
    return out
