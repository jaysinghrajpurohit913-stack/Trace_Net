"""Synthetic data generator for TraceNet.

Creates a realistic-looking (but 100% fake) banking dataset:
  * ~600 normal accounts with everyday UPI/IMPS/NEFT traffic
  * 4 planted cyber-fraud cases (victims -> mule layers -> cash-out), each with a
    different laundering style, so detection can be evaluated against ground truth.
No real personal or bank data is used anywhere.
"""
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(7)
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)
T0 = pd.Timestamp("2026-10-01 00:00:00")
BANKS = ["SBI", "HDFC", "ICICI", "PNB", "BoB", "Axis", "Kotak", "Canara", "UCO", "IDFC"]
CHANNELS = ["UPI", "IMPS", "NEFT"]

accounts, txns = [], []


def add_account(aid, kind, age_days, device=None, phone=None, ip=None):
    accounts.append(dict(
        account_id=aid, kind=kind, bank=rng.choice(BANKS), kyc_age_days=int(age_days),
        device_id=device or f"DEV{rng.integers(10**5, 10**6)}",
        phone=phone or f"9{rng.integers(10**8, 10**9)}",
        ip=ip or f"{rng.integers(11,220)}.{rng.integers(0,255)}.{rng.integers(0,255)}.{rng.integers(1,254)}"))


def add_txn(src, dst, amt, ts, ch=None):
    txns.append(dict(ts=ts, src=src, dst=dst, amount=round(float(amt), 2),
                     channel=ch or rng.choice(CHANNELS)))


# ---- normal population ----------------------------------------------------
normal = [f"AC{i:04d}" for i in range(1, 601)]
for a in normal:
    add_account(a, "normal", rng.integers(200, 4000))
for _ in range(9000):
    s, d = rng.choice(normal, 2, replace=False)
    ts = T0 + pd.Timedelta(minutes=int(rng.integers(0, 30 * 24 * 60)))
    add_txn(s, d, min(rng.lognormal(7, 1.1), 80000), ts)
# a few legit busy merchants (fan-in but slow pass-through) -> hard negatives
merchants = normal[:6]
for m in merchants:
    for _ in range(120):
        s = rng.choice(normal[6:])
        add_txn(s, m, rng.lognormal(6, .6), T0 + pd.Timedelta(minutes=int(rng.integers(0, 43200))))

# ---- planted fraud cases ----------------------------------------------------
cases, labels = [], []


def mule(aid, case, layer, ring_dev=None, ring_phone=None, ring_ip=None):
    add_account(aid, "mule", rng.integers(5, 60), ring_dev, ring_phone, ring_ip)
    labels.append(dict(account_id=aid, case=case, role=f"mule_L{layer}"))


def cashout(aid, case, ctype):
    add_account(aid, "cashout", rng.integers(5, 40))
    labels.append(dict(account_id=aid, case=case, role="cashout"))


def run_case(cid, n_victims, victim_amt, n_l1, n_l2, n_l3, style, start_hours, shared):
    start = T0 + pd.Timedelta(hours=start_hours)
    ring_dev = [f"DEV_RING{cid}_{i}" for i in range(2)]
    ring_phone = f"9{cid}00000{cid}1"
    ring_ip = f"103.77.{cid}.14"
    pick = lambda: (rng.choice(ring_dev) if shared and rng.random() < .8 else None,
                    ring_phone if shared and rng.random() < .4 else None,
                    ring_ip if shared and rng.random() < .6 else None)
    L1 = [f"M{cid}A{i}" for i in range(n_l1)]
    L2 = [f"M{cid}B{i}" for i in range(n_l2)]
    L3 = [f"M{cid}C{i}" for i in range(n_l3)]
    CO = [f"CO{cid}_ATM", f"CO{cid}_WALLET", f"CO{cid}_CRYPTO"][: max(2, min(3, n_l3))]
    for a in L1: mule(a, cid, 1, *pick())
    for a in L2: mule(a, cid, 2, *pick())
    for a in L3: mule(a, cid, 3, *pick())
    for a in CO: cashout(a, cid, a.split("_")[1])
    victims = []
    for v in range(n_victims):
        va = f"VIC{cid}{v}"
        add_account(va, "victim", rng.integers(500, 3000))
        victims.append(va)
        amt = victim_amt * rng.uniform(.6, 1.4)
        t = start + pd.Timedelta(minutes=int(rng.integers(0, 90)))
        dst = L1[v % n_l1]
        add_txn(va, dst, amt, t, "UPI")
        cases.append(dict(complaint_id=f"NCRP-{cid}{v}", case=cid, victim_account=va,
                          amount=round(amt, 2), reported_ts=t + pd.Timedelta(hours=int(rng.integers(2, 20))),
                          fraud_ts=t, first_mule=dst))
    # layering: every layer forwards ~97-99% within minutes, splitting across the next layer
    def forward(src_layer, dst_layer, t_lo, t_hi):
        for a in src_layer:
            inflow = sum(x["amount"] for x in txns if x["dst"] == a and x["ts"] >= start)
            if inflow <= 0: continue
            k = min(len(dst_layer), 2 if style != "chain" else 1)
            targets = rng.choice(dst_layer, k, replace=False)
            last_in = max(x["ts"] for x in txns if x["dst"] == a and x["ts"] >= start)
            for d in targets:
                add_txn(a, d, inflow * .97 / k, last_in + pd.Timedelta(minutes=int(rng.integers(t_lo, t_hi))))
    forward(L1, L2, 3, 25)
    forward(L2, L3, 3, 25)
    if style == "circular":                      # round-tripping inside the ring
        add_txn(L3[0], L2[0], 4000, start + pd.Timedelta(hours=3), "IMPS")
        add_txn(L2[0], L1[0], 3500, start + pd.Timedelta(hours=4), "IMPS")
        add_txn(L1[0], L3[0], 3000, start + pd.Timedelta(hours=5), "IMPS")
    # cash-out
    for a in L3:
        inflow = sum(x["amount"] for x in txns if x["dst"] == a and x["ts"] >= start)
        last_in = max([x["ts"] for x in txns if x["dst"] == a and x["ts"] >= start] or [start])
        if style == "structuring":               # many sub-threshold withdrawals
            n = 8
            for j in range(n):
                add_txn(a, CO[j % len(CO)], min(inflow * .96 / n, 49000), last_in + pd.Timedelta(minutes=10 + 12 * j), "IMPS")
        else:
            for j, c in enumerate(CO[:2]):
                add_txn(a, c, inflow * .96 / 2, last_in + pd.Timedelta(minutes=int(rng.integers(5, 40))), "IMPS")


run_case(1, 4, 120000, 3, 4, 3, "layered", 24 * 3, True)
run_case(2, 3, 250000, 2, 3, 3, "structuring", 24 * 8, True)
run_case(3, 5, 60000, 4, 4, 4, "circular", 24 * 13, True)
run_case(4, 2, 480000, 2, 2, 2, "chain", 24 * 18, False)   # harder: no shared devices

acc = pd.DataFrame(accounts).drop_duplicates("account_id")
tx = pd.DataFrame(txns).sort_values("ts").reset_index(drop=True)
tx.insert(0, "txn_id", [f"T{i:06d}" for i in range(len(tx))])
acc.to_csv(OUT / "accounts.csv", index=False)
tx.to_csv(OUT / "transactions.csv", index=False)
pd.DataFrame(cases).to_csv(OUT / "complaints.csv", index=False)
pd.DataFrame(labels).to_csv(OUT / "ground_truth.csv", index=False)
print(f"accounts={len(acc)} txns={len(tx)} complaints={len(cases)} planted_fraud_accts={len(labels)}")
