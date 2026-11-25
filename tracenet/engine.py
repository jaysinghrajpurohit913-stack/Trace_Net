"""TraceNet core engine: time-aware fund tracing, mule scoring, entity linking."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
import networkx as nx
from sklearn.ensemble import IsolationForest

import re

from . import config as C

CASHOUT_PREFIX = "CO"          # old demo-data prefix, kept so the demo data still works
_CASHOUT_RE = re.compile(r"^(CASHOUT[:|_]|CO\d+_)")
_BLANKS = {"", "nan", "none", "null", "na", "n/a", "-", "--", "0", "unknown"}


def is_cashout(a):
    """True for a 'money left the banking system' node (ATM, wallet, crypto, cash)."""
    return bool(_CASHOUT_RE.match(str(a)))


def short(a, n=4, limit=8):
    """Long account / complaint numbers shown as ...4321 in pictures (full number stays in hover text and tables)."""
    a = str(a)
    if is_cashout(a):
        return pretty(a, short_ids=True)
    return a if len(a) <= limit else "…" + a[-n:]


def pretty(a, short_ids=False):
    """Human label for an account id (used in pictures and reports)."""
    a = str(a)
    if a.startswith("CASHOUT:"):
        p = a.split(":")
        via = (short(p[2]) if short_ids else p[2]) if len(p) > 2 and p[2] else ""
        return f"{p[1]} cash-out" + (f" (via {via})" if via else "")
    return a


def complete_accounts(acc, tx, comp=None):
    """Make the accounts table safe for real data: add missing optional columns, add accounts
    that appear in transactions but not in the accounts file, treat blank/placeholder values
    (0, NA, '-') as 'unknown' so they never create fake gangs."""
    acc = acc.copy() if acc is not None else pd.DataFrame(columns=["account_id"])
    for c in ["kind", "bank", "kyc_age_days", "device_id", "phone", "ip"]:
        if c not in acc: acc[c] = np.nan
    acc["account_id"] = acc.account_id.astype(str).str.strip()
    ids = set(tx.src) | set(tx.dst)
    if comp is not None and len(comp): ids |= set(comp.victim_account)
    ids = {a for a in ids if not is_cashout(a)}
    missing = sorted(ids - set(acc.account_id))
    if missing:
        acc = pd.concat([acc, pd.DataFrame({"account_id": missing})], ignore_index=True)
    acc = acc.drop_duplicates("account_id").reset_index(drop=True)
    acc["bank"] = acc.bank.fillna("Unknown bank").astype(str)
    acc["kind"] = acc.kind.fillna("unknown")
    acc["kyc_age_days"] = pd.to_numeric(acc.kyc_age_days, errors="coerce")
    for c in ["device_id", "phone", "ip"]:
        v = acc[c].astype("string").str.strip()
        acc[c] = v.mask(v.str.lower().isin(_BLANKS))
    return acc


def load(data_dir):
    acc = pd.read_csv(f"{data_dir}/accounts.csv")
    tx = pd.read_csv(f"{data_dir}/transactions.csv", parse_dates=["ts"])
    comp = pd.read_csv(f"{data_dir}/complaints.csv", parse_dates=["reported_ts", "fraud_ts"])
    return acc, tx.sort_values("ts").reset_index(drop=True), comp


# ---------------------------------------------------------------- tracing ----
@dataclass
class Trail:
    edges: pd.DataFrame      # traced edges with tainted amount moved
    held: dict               # account -> tainted money still sitting there
    cashed: dict             # cash-out account -> tainted money received
    depth: dict              # account -> hop depth from victim
    seed_amount: float


def naive_reachable(tx, victim, max_hops=6):
    """Baseline: plain graph traversal ignoring time and amounts (what a naive tool does)."""
    G = nx.DiGraph(); G.add_edges_from(zip(tx.src, tx.dst))
    return set(nx.single_source_shortest_path_length(G, victim, cutoff=max_hops)) - {victim}


def trace_funds(tx, victim, fraud_ts, amount, max_hours=C.TRACE_MAX_HOURS, as_of=None, seed_txn_ids=None):
    """Follow stolen money forward in time.

    Taint accounting ('tainted-first', conservative): a transfer can only carry as much
    tainted money as the sender currently holds, and only AFTER it arrived. Once stolen
    money has arrived, outgoing transfers are assumed to use it first. This
    prevents the false trails that a plain graph traversal would produce.

    seed_txn_ids: if the complaint gives the victim's transaction reference(s), only those
    victim payments are treated as stolen money (the victim's other payments are ignored).
    Transfers with exactly the same timestamp (common when a bank gives only dates) are
    processed in as many passes as needed, so the order inside a day does not hide a trail.
    """
    end = fraud_ts + pd.Timedelta(hours=max_hours)
    if as_of is not None:                      # "where is the money right now?"
        end = min(end, pd.Timestamp(as_of))
    window = tx[(tx.ts >= fraud_ts) & (tx.ts <= end)]
    seeds = set(map(str, seed_txn_ids)) if seed_txn_ids else None
    held = {victim: float(amount)}
    depth = {victim: 0}
    rows = []

    def step(r):
        if r.src == victim and seeds is not None and str(r.txn_id) not in seeds:
            return False
        bal = held.get(r.src, 0.0)
        if bal <= 0.01:
            return False
        moved = min(bal, r.amount)
        held[r.src] = bal - moved
        held[r.dst] = held.get(r.dst, 0.0) + moved
        depth[r.dst] = min(depth.get(r.dst, 99), depth[r.src] + 1)
        rows.append(dict(ts=r.ts, src=r.src, dst=r.dst, amount=r.amount, tainted=round(moved, 2),
                         channel=r.channel, txn_id=r.txn_id, hop=depth[r.src] + 1))
        return True

    for _, grp in window.groupby("ts", sort=True):
        todo = list(grp.itertuples())
        while todo:                                   # repeat until nothing more can move
            left = [r for r in todo if not step(r)]
            if len(left) == len(todo):
                break
            todo = left
    edges = pd.DataFrame(rows)
    cashed = {a: v for a, v in held.items() if is_cashout(a) and v > 1}
    still = {a: v for a, v in held.items() if v > 1 and not is_cashout(a) and a != victim}
    return Trail(edges, still, cashed, depth, float(amount))


# ----------------------------------------------------------- mule scoring ----
def account_features(tx, acc):
    g_in = tx.groupby("dst").agg(in_amt=("amount", "sum"), in_cnt=("amount", "size"),
                                 in_peers=("src", "nunique"))
    g_out = tx.groupby("src").agg(out_amt=("amount", "sum"), out_cnt=("amount", "size"),
                                  out_peers=("dst", "nunique"))
    f = acc.set_index("account_id").join(g_in).join(g_out)
    for c in ["in_amt", "in_cnt", "in_peers", "out_amt", "out_cnt", "out_peers"]:
        f[c] = f[c].fillna(0)
    f["kyc_age_days"] = f.kyc_age_days.fillna(9999)      # unknown age = do not call it "new"
    f["passthrough"] = np.where(f.in_amt > 0, f.out_amt / f.in_amt.clip(lower=1), 0).clip(0, 1.2)

    # median minutes between receiving money and the next outgoing transfer
    hold = {}
    ins = tx.groupby("dst"); outs = tx.groupby("src")
    for a in f.index[(f.in_cnt > 0) & (f.out_cnt > 0)]:
        i_ts = ins.get_group(a).ts.values; o_ts = outs.get_group(a).ts.values
        d = []
        for t in i_ts:
            nxt = o_ts[o_ts >= t]
            if len(nxt): d.append((nxt[0] - t) / np.timedelta64(1, "m"))
        if d: hold[a] = float(np.median(d))
    f["hold_min"] = pd.Series(hold).reindex(f.index).fillna(1e4)

    # structuring: share of outgoing txns in the 40k-50k "just under limit" band is
    # approximated by the count of near-equal repeated amounts to the same receiver
    rep = tx.groupby(["src", "dst"]).size().groupby("src").max()
    f["repeat_out"] = rep.reindex(f.index).fillna(0)

    # cycle membership
    G = nx.DiGraph(); G.add_edges_from(zip(tx.src, tx.dst))
    on_cycle = set()
    for comp in nx.strongly_connected_components(G):
        if 2 < len(comp) <= 12: on_cycle |= comp
    f["in_cycle"] = f.index.isin(on_cycle).astype(int)

    _extra_features(f, tx)

    # shared identifiers
    for col in ["device_id", "phone", "ip"]:
        f[f"shared_{col}"] = f.groupby(col)[col].transform("size").fillna(1) - 1   # blanks never match
    f["shared_ids"] = f[["shared_device_id", "shared_phone", "shared_ip"]].sum(axis=1)
    return f


def _extra_features(f, tx):
    """PS05 indicators: round-figure layering, many small credits, dormant account waking up, repeated counterparties."""
    out = tx.assign(round_=(tx.amount >= C.ROUND_MIN_AMOUNT) & (tx.amount % C.ROUND_STEP == 0))
    r = out.groupby("src").agg(n=("round_", "size"), k=("round_", "sum"))
    f["round_count"] = r.k.reindex(f.index).fillna(0)
    f["round_share"] = (r.k / r.n).reindex(f.index).fillna(0)
    small = tx[tx.amount < C.SMALL_CREDIT]
    f["small_in_peers"] = small.groupby("dst").src.nunique().reindex(f.index).fillna(0)

    # dormant -> active: longest quiet spell between two events, followed by a burst within 24h
    ev = pd.concat([tx[["src", "ts"]].rename(columns={"src": "a"}), tx[["dst", "ts"]].rename(columns={"dst": "a"})]).sort_values("ts")
    awake = {}
    for a, g in ev.groupby("a"):
        if a not in f.index or len(g) < C.DORMANT_BURST + 1:
            continue
        t = g.ts.values
        gaps = np.diff(t) / np.timedelta64(1, "D")
        for i in np.where(gaps >= C.DORMANT_DAYS)[0]:
            if ((t[i + 1:] - t[i + 1]) <= np.timedelta64(24, "h")).sum() >= C.DORMANT_BURST:
                awake[a] = 1; break
    f["dormant_awake"] = pd.Series(awake).reindex(f.index).fillna(0).astype(int)

    pair = pd.concat([tx[["src", "dst"]].rename(columns={"src": "a", "dst": "b"}), tx[["dst", "src"]].rename(columns={"dst": "a", "src": "b"})])
    f["repeat_peer"] = pair.groupby(["a", "b"]).size().groupby("a").max().reindex(f.index).fillna(0)
    return f


def score_mules(f):
    """Rule score (explainable) blended with an Isolation Forest anomaly score."""
    reasons = {a: [] for a in f.index}
    rule = pd.Series(0.0, index=f.index)

    def add(mask, pts, text):
        for a in f.index[mask]:
            reasons[a].append(text)
        rule.loc[mask] += pts

    P = C.MULE_POINTS
    active = (f.in_cnt > 0) & (f.out_cnt > 0)
    add(active & (f.passthrough > C.PASSTHROUGH_RATIO) & (f.hold_min < C.FAST_HOLD_MIN), P["fast_passthrough"], "Forwards almost all the money within an hour")
    add((f.in_cnt >= 1) & (f.kyc_age_days < C.NEW_ACCOUNT_DAYS) & (f.in_amt > C.NEW_ACCOUNT_BIG_IN), P["new_big"], "New account (under 90 days) handling large amounts")
    add((f.in_peers >= C.MANY_SENDERS) & (f.out_peers <= 3) & active, P["many_senders"], "Receives money from many different people")
    add((f.out_peers >= 2) & (f.passthrough > C.PASSTHROUGH_RATIO) & active, P["splits"], "Splits the money across several accounts")
    add(f.in_cycle == 1, P["cycle"], "Money goes round in circles between accounts")
    add(f.repeat_out >= C.STRUCT_REPEATS, P["repeats"], "Repeated similar-sized transfers (to stay under limits)")
    add(f.shared_ids >= 2, P["shared_ids"], "Uses the same phone, device or internet address as other accounts")
    add((f.round_count >= C.ROUND_MIN_COUNT) & (f.round_share >= C.ROUND_SHARE) & active, P["round_figures"], "Sends round-figure amounts (layering)")
    add((f.small_in_peers >= C.SMALL_CREDIT_SENDERS) & active, P["many_small"], "Many small credits from unrelated senders")
    add((f.dormant_awake == 1) & active, P["dormant_awake"], "Was dormant, then suddenly became active")
    add((f.repeat_peer >= C.REPEAT_PEER) & active & (f.passthrough > C.PASSTHROUGH_RATIO), P["repeat_peer"], "Same counterparty again and again")
    rule = rule.clip(0, 100)

    X = f[["passthrough", "hold_min", "in_peers", "out_peers", "kyc_age_days", "shared_ids",
           "repeat_out", "in_cycle"]].copy()
    X["hold_min"] = np.log1p(X.hold_min); X["kyc_age_days"] = np.log1p(X.kyc_age_days)
    out = f.copy()
    if len(X) >= C.ML_MIN_ACCOUNTS:
        iso = IsolationForest(n_estimators=200, contamination=C.ML_CONTAMINATION, random_state=1).fit(X)
        an = -iso.score_samples(X)
        an = (an - an.min()) / (an.max() - an.min() + 1e-9) * 100
        out["mule_score"] = ((1 - C.ML_WEIGHT) * rule + C.ML_WEIGHT * an).round(1)
    else:                      # too few accounts for a meaningful anomaly model: rules only
        an = np.zeros(len(X))
        out["mule_score"] = rule.round(1)
    out["rule_score"] = rule; out["anomaly_score"] = an
    out["reasons"] = ["; ".join(reasons[a]) for a in out.index]
    return out


# ---------------------------------------------------------- entity linking ----
def link_entities(acc, min_group=2):
    """Union accounts that share a device, phone or IP -> candidate fraud rings."""
    G = nx.Graph()
    for col in ["device_id", "phone", "ip"]:
        for val, grp in acc.groupby(col):
            ids = grp.account_id.tolist()
            if len(ids) >= min_group:
                for x in ids[1:]:
                    G.add_edge(ids[0], x, via=col)
    rings = [sorted(c) for c in nx.connected_components(G) if len(c) >= 3]
    return G, sorted(rings, key=len, reverse=True)


# ----------------------------------------------------------- freeze list ----
def freeze_list(trail, scored, rings=None):
    """Rank accounts to freeze: money still inside first, then biggest tainted flow."""
    if trail.edges.empty:
        return pd.DataFrame()
    flow_in = trail.edges.groupby("dst").tainted.sum()
    accts = flow_in.index.tolist()
    df = pd.DataFrame({"account_id": accts})
    df["tainted_received"] = df.account_id.map(flow_in).round(0)
    df["tainted_still_held"] = df.account_id.map(trail.held).fillna(0).round(0)
    df["hop"] = df.account_id.map(trail.depth)
    df["mule_score"] = df.account_id.map(scored.mule_score).fillna(0)
    df["bank"] = df.account_id.map(scored.bank)
    df["is_cashout"] = df.account_id.map(is_cashout)
    ring_of = {}
    for i, r in enumerate(rings or [], 1):
        for a in r: ring_of[a] = f"RING-{i}"
    df["ring"] = df.account_id.map(ring_of).fillna("-")
    # money still inside an account always outranks everything else (it is recoverable)
    df["priority"] = (np.where(df.tainted_still_held > 1, 100, 0)
                      + df.tainted_still_held / max(trail.seed_amount, 1) * 50
                      + df.mule_score * .3 + np.where(df.ring != "-", 10, 0)).round(1)
    df["action"] = np.where(df.tainted_still_held > 1, "FREEZE NOW (funds still inside)",
                    np.where(df.is_cashout, "Trace cash-out / alert bank & merchant",
                    np.where(df.mule_score >= 40, "Freeze / KYC re-verification", "Monitor")))
    return df.sort_values("priority", ascending=False).reset_index(drop=True)


def evaluate(scored, truth, thr=C.MULE_FLAG_AT):
    t = truth.set_index("account_id")
    y = scored.index.isin(t.index[t.role.str.startswith("mule")])
    p = scored.mule_score >= thr
    tp = int((y & p).sum()); fp = int((~y & p).sum()); fn = int((y & ~p).sum())
    prec = tp / max(tp + fp, 1); rec = tp / max(tp + fn, 1)
    return dict(tp=tp, fp=fp, fn=fn, precision=round(prec, 3), recall=round(rec, 3),
                f1=round(2 * prec * rec / max(prec + rec, 1e-9), 3))


# ------------------------------------------------- partial data / rounds ----
def trace_in_rounds(tx, acc, victim, fraud_ts, amount, as_of=None, max_rounds=12, seed_txn_ids=None):
    """Simulate the real workflow: statements arrive bank by bank, not all at once.

    Round 0 knows only the victim's own statement (from the complaint). Each round we
    trace with the data we have, list the accounts whose onward movement is still
    UNKNOWN (the frontier) grouped by bank, and treat those banks' replies as arriving
    before the next round.
    """
    bank = acc.set_index("account_id").bank
    known, rounds = {victim}, []
    for r in range(max_rounds):
        vis = tx[tx.src.isin(known)]
        tr = trace_funds(vis, victim, fraud_ts, amount, as_of=as_of, seed_txn_ids=seed_txn_ids)
        frontier = [a for a in tr.depth if a not in known and not is_cashout(a)]
        got = tr.edges.groupby("dst").tainted.sum() if len(tr.edges) else {}
        ask = {}
        for a in frontier:
            ask.setdefault(bank.get(a, "?"), []).append((a, round(float(got.get(a, 0)))))
        rounds.append(dict(round=r, known=len(known), trail=tr, frontier=frontier, ask=ask,
                           unresolved=float(sum(tr.held.get(a, 0) for a in frontier))))
        if not frontier:
            break
        known |= set(frontier)
    return rounds


def link_by_flow(tx, scored, thr=C.MULE_FLAG_AT):
    """Fallback ring linking when device/phone/IP metadata is NOT available:
    suspicious accounts that pay the same beneficiary (e.g. the same cash-out point)
    or each other are grouped together."""
    cand = set(scored.index[scored.mule_score >= thr])
    G = nx.Graph()
    sub = tx[tx.src.isin(cand)]
    for dst, grp in sub.groupby("dst"):
        srcs = grp.src.unique().tolist()
        for x in srcs[1:]:
            G.add_edge(srcs[0], x, via="shared beneficiary")
    for r in sub[sub.dst.isin(cand)].itertuples():
        G.add_edge(r.src, r.dst, via="direct flow")
    return sorted([sorted(c) for c in nx.connected_components(G) if len(c) >= 3], key=len, reverse=True)


def merge_rings(*ring_lists):
    """Union overlapping rings found by different methods."""
    sets = [set(r) for rl in ring_lists for r in rl]
    merged = []
    for s in sets:
        hit = [m for m in merged if m & s]
        for m in hit: merged.remove(m); s |= m
        merged.append(s)
    return sorted([sorted(m) for m in merged], key=len, reverse=True)


# ------------------------------------------- adopted from global practice ----
def export_watchlist(scored, rings, thr=C.MULE_FLAG_AT):
    """Intelligence-sharing file for banks (idea: Suspect Registry / COSMIC-style sharing,
    but covering deeper layers, with reasons and ring ids)."""
    ring_of = {a: f"RING-{i}" for i, r in enumerate(rings, 1) for a in r}
    w = scored[scored.mule_score >= thr].copy()
    w["ring"] = [ring_of.get(a, "-") for a in w.index]
    w = w.reset_index()[["account_id", "bank", "mule_score", "ring", "reasons"]]
    return w.sort_values("mule_score", ascending=False).reset_index(drop=True)


def precheck(acc, tx, account_id, as_of, watchlist=(), rings=()):
    """Pre-payment risk check for a RECEIVING account (idea: confirmation-of-payee style
    warnings). Uses only information available BEFORE `as_of`."""
    a = acc.set_index("account_id").loc[account_id]
    hist = tx[tx.ts < as_of]
    pts, why = 0, []
    wl = set(watchlist)
    if account_id in wl:
        pts += 60; why.append("On the shared watchlist (linked to a reported fraud trail)")
    elif any(account_id in r and (set(r) & wl) for r in rings):
        pts += 40; why.append("In a ring that contains a watchlisted account")
    if pd.notna(a.kyc_age_days) and a.kyc_age_days < 90:
        pts += 15; why.append("Account opened less than 90 days ago")
    def match(col):
        return acc[col].eq(a[col]).fillna(False).astype(bool) if pd.notna(a[col]) else pd.Series(False, index=acc.index)
    same = acc[match("device_id") | match("phone") | match("ip")]
    if len(same) - 1 >= 2:
        pts += 15; why.append("Uses the same phone, device or internet address as other accounts")
    day = hist[(hist.dst == account_id) & (hist.ts >= as_of - pd.Timedelta(hours=24))]
    if day.src.nunique() >= 3 and day.amount.sum() > 40000:
        pts += 15; why.append("Received over Rs 40,000 from 3+ different senders in 24h")
    hr = hist[hist.ts >= as_of - pd.Timedelta(hours=1)]
    rin, rout = hr[hr.dst == account_id].amount.sum(), hr[hr.src == account_id].amount.sum()
    if rin > 0 and rout / rin > .9:
        pts += 25; why.append("Forwarded over 90% of recent credits within the hour")
    level = "HIGH" if pts >= 60 else "MEDIUM" if pts >= 30 else "LOW"
    action = {"HIGH": "Warn the payer and hold / delay the payment for verification",
              "MEDIUM": "Show a clear warning and add a short delay",
              "LOW": "Proceed normally"}[level]
    return dict(account_id=account_id, score=pts, level=level, action=action, reasons=why)


def lien_file(fl, complaint_id):
    """One row per account to act on, ready to hand to each bank's nodal officer."""
    d = fl[(fl.tainted_still_held > 1) | (fl.mule_score >= 40)].copy()
    d.insert(0, "complaint_id", complaint_id)
    return d[["complaint_id", "bank", "account_id", "tainted_received", "tainted_still_held", "mule_score", "ring", "action"]] \
        .sort_values(["bank", "tainted_still_held"], ascending=[True, False])
