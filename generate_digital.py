"""Adds the DIGITAL layer to the made-up demo data (all fictional; domains end in .example, IPs are documentation ranges):
   * case 5: round-figure layering + a dormant account that wakes up   -> data/*.csv (appended, safe to run twice)
   * data/domains.csv : phishing domains + IPs the victims reported
   * data/ip_log.csv  : IP-log events (UTC) for some mule accounts

   python generate_digital.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).parent / "data"
rng = np.random.default_rng(7)
acc = pd.read_csv(OUT / "accounts.csv"); tx = pd.read_csv(OUT / "transactions.csv", parse_dates=["ts"])
comp = pd.read_csv(OUT / "complaints.csv"); gt = pd.read_csv(OUT / "ground_truth.csv")

if "NCRP-50" not in set(comp.complaint_id):
    banks = acc.bank.unique().tolist()
    start = pd.Timestamp("2026-10-22 02:10")
    ids = ["VIC50", "M5A0", "M5B0", "M5B1", "M5B2", "M5B3", "CO5_ATM", "CO5_WALLET"]
    new_acc = [dict(account_id=a, kind=("victim" if a.startswith("VIC") else "cashout" if a.startswith("CO") else "mule"), bank=rng.choice(banks),
                    kyc_age_days=int(rng.integers(1000, 3000) if a.startswith("VIC") else rng.integers(10, 80)),
                    device_id=f"DEV_RING5_{i % 2}" if a.startswith("M5") else f"DEV{rng.integers(10**5, 10**6)}",
                    phone=f"9{rng.integers(10**8, 10**9)}", ip=f"{rng.integers(11, 220)}.{rng.integers(0, 255)}.{rng.integers(0, 255)}.{rng.integers(1, 254)}")
               for i, a in enumerate(ids)]
    rows = []
    def add(s, d, amt, t, ch): rows.append(dict(ts=t, src=s, dst=d, amount=float(amt), channel=ch))
    add("VIC50", "M5A0", 200000, start, "UPI")
    # M5B1 was quiet for weeks (one tiny credit on 3 Oct) and wakes up now
    add("AC0100", "M5B1", 450, pd.Timestamp("2026-10-03 11:00"), "UPI")
    for k, b in enumerate(["M5B0", "M5B1", "M5B2", "M5B3"]):
        add("M5A0", b, 50000, start + pd.Timedelta(minutes=12 + 4 * k), "IMPS")                       # round figures
    for k, b in enumerate(["M5B0", "M5B1", "M5B2", "M5B3"]):
        t = start + pd.Timedelta(minutes=45 + 6 * k)
        add(b, "CO5_ATM", 25000, t, "IMPS"); add(b, "CO5_WALLET", 25000, t + pd.Timedelta(minutes=3), "IMPS")
    t5 = pd.DataFrame(rows)
    # three more round-figure transfers so the layering pattern is clear
    for k in range(3):
        add("M5A0", "M5B0", 10000, start + pd.Timedelta(minutes=70 + 5 * k), "IMPS")
    t5 = pd.DataFrame(rows)
    tx2 = pd.concat([tx.drop(columns="txn_id"), t5]).sort_values("ts").reset_index(drop=True)
    tx2.insert(0, "txn_id", [f"T{i:06d}" for i in range(len(tx2))])
    # txn ids of the old rows changed: complaints only use victim account + time, so remap by position is not needed
    tx2.to_csv(OUT / "transactions.csv", index=False)
    pd.concat([acc, pd.DataFrame(new_acc)]).drop_duplicates("account_id").to_csv(OUT / "accounts.csv", index=False)
    comp = pd.concat([comp, pd.DataFrame([dict(complaint_id="NCRP-50", case=5, victim_account="VIC50", amount=200000, reported_ts=start + pd.Timedelta(hours=7),
                                              fraud_ts=start, first_mule="M5A0", victim_name="Meena Kanwar", victim_phone="9414055500")])])
    comp.to_csv(OUT / "complaints.csv", index=False)
    pd.concat([gt, pd.DataFrame([dict(account_id=a, case=5, role="mule_L2" if "B" in a else "mule_L1") for a in ids if a.startswith("M5")]
                                + [dict(account_id=a, case=5, role="cashout") for a in ids if a.startswith("CO")])]).to_csv(OUT / "ground_truth.csv", index=False)
    tx = tx2

# ---------------------------------------------------------------- domains ----
D = lambda **k: dict(dict(domain="", ip="", registrar="", created="", expires="", nameservers="", hosting="", asn="", country="", ssl_issuer="",
                          ssl_first_seen="", first_seen="", last_seen="", complaint_id="", note=""), **k)
domains = [
    D(domain="secure-kyc-update.example", ip="203.0.113.10", registrar="NameBazaar Pvt Ltd", created="2026-09-20", expires="2026-12-20",
      nameservers="ns1.fastdns.example, ns2.fastdns.example", hosting="CHEAPVPS-LLC", asn="AS64500", country="NL", ssl_issuer="Let's Encrypt",
      ssl_first_seen="2026-09-20", first_seen="2026-10-03 22:40", last_seen="2026-10-12", complaint_id="NCRP-10, NCRP-11", note="Link sent by SMS as 'KYC expired'"),
    D(domain="kyc-verify-sbi.example", ip="203.0.113.10", registrar="NameBazaar Pvt Ltd", created="2026-09-20", expires="2026-12-20",
      nameservers="ns1.fastdns.example, ns2.fastdns.example", hosting="CHEAPVPS-LLC", asn="AS64500", country="NL", ssl_issuer="Let's Encrypt",
      ssl_first_seen="2026-09-21", first_seen="2026-10-08 20:15", complaint_id="NCRP-20", note="Fake bank page"),
    D(domain="upi-refund-claim.example", ip="198.51.100.44", registrar="NameBazaar Pvt Ltd", created="2026-09-20", expires="2026-12-20",
      nameservers="ns1.fastdns.example, ns3.fastdns.example", hosting="SMALLHOST-INC", asn="AS64501", country="US", ssl_issuer="Let's Encrypt",
      ssl_first_seen="2026-09-22", first_seen="2026-10-18 18:30", complaint_id="NCRP-40", note="Refund scam - different server, same name server and registration batch"),
    D(domain="hdfc-rewards-portal.example", ip="192.0.2.99", registrar="Global Domains LLC", created="2026-08-01", expires="2027-08-01",
      nameservers="ns1.cloudflare.example", hosting="CLOUDFLARENET", asn="AS64502", country="US", ssl_issuer="Google Trust Services",
      ssl_first_seen="2026-08-01", first_seen="2026-10-13 21:00", complaint_id="NCRP-30", note="Behind a CDN"),
    D(domain="sbi-reward-points.example", ip="192.0.2.99", registrar="Other Registry Co", created="2026-10-05", expires="2026-11-05",
      nameservers="ns2.cloudflare.example", hosting="CLOUDFLARENET", asn="AS64502", country="US", ssl_issuer="Google Trust Services",
      ssl_first_seen="2026-10-05", first_seen="2026-10-22 02:00", complaint_id="NCRP-50", note="Behind the same CDN: weak link only"),
    D(ip="203.0.113.77", hosting="M247 VPN SERVICES", asn="AS64503", country="RO", first_seen="2026-10-04 05:00", complaint_id="NCRP-10", note="IP seen in the victim's bank alert"),
]
pd.DataFrame(domains).to_csv(OUT / "domains.csv", index=False)

# ---------------------------------------------------------------- IP log (UTC) ----
def first_credit(a):
    g = tx[tx.dst == a].sort_values("ts"); return g.ts.iloc[0] if len(g) else None
logs = []
for a, vpn in [("M1A0", "203.0.113.77"), ("M1A1", "203.0.113.77"), ("M1B0", "203.0.113.77"), ("M2A0", "198.51.100.200"), ("M5A0", "203.0.113.77")]:
    t = first_credit(a)
    if t is None: continue
    ist = t + pd.Timedelta(minutes=int(rng.integers(2, 9)))
    utc = ist - pd.Timedelta(hours=5, minutes=30)
    logs.append(dict(timestamp=utc.strftime("%Y-%m-%dT%H:%M:%SZ"), ip=vpn, event="net_banking_login", account=a, phone="", source="Bank access log (UTC)"))
t = first_credit("M1A2")
if t is not None:                               # identified by phone only + a different time notation
    phone = acc.set_index("account_id").phone.get("M1A2")
    utc = t + pd.Timedelta(minutes=3) - pd.Timedelta(hours=5, minutes=30)
    logs.append(dict(timestamp=utc.strftime("%Y-%m-%d %H:%M:%S +00:00"), ip="203.0.113.77", event="otp_request", account="", phone=phone, source="SMS gateway log (UTC)"))
t = first_credit("M3A0")                         # an event far from any transaction (should be classed 'far')
if t is not None:
    logs.append(dict(timestamp=(t - pd.Timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ"), ip="198.51.100.201", event="net_banking_login", account="M3A0", phone="", source="Bank access log (UTC)"))
pd.DataFrame(logs).to_csv(OUT / "ip_log.csv", index=False)
print("case5 + domains.csv + ip_log.csv written:", len(domains), "indicators,", len(logs), "log events")
