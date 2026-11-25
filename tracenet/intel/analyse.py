"""Explainable red flags for domains and IPs + correlation of IP-log events with bank transactions.

Every flag is a short plain sentence with the evidence in it (no black box). Flags are LEADS for the investigating officer,
not proof: shared hosting, CDNs, mobile (CGNAT) and VPN addresses are shared by many people.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from .. import config as C
from ..engine import is_cashout
from .model import IPINFO_COLS, is_ip, registrable
from .timeutil import to_local

LURE_WORDS = ("kyc", "verify", "update", "refund", "reward", "bonus", "secure", "login", "account", "upi", "pay", "wallet", "claim",
              "support", "care", "helpline", "loan", "invest", "trading", "gift", "lucky", "cashback")
BRAND_WORDS = ("sbi", "hdfc", "icici", "axis", "pnb", "kotak", "bob", "paytm", "phonepe", "gpay", "npci", "irctc", "uidai", "aadhaar",
               "incometax", "amazon", "flipkart", "airtel", "jio")


def _has(text, hints):
    t = str(text).upper()
    return any(h in t for h in hints)


def ip_table(domains: pd.DataFrame, ipinfo: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per IP seen in the indicator table (+ any looked-up details)."""
    rows = []
    for ip, g in domains[domains.ip != ""].groupby("ip"):
        rows.append(dict(ip=ip, asn=next((x for x in g.asn if x), ""), org=next((x for x in g.hosting if x), ""),
                         country=next((x for x in g.country if x), ""), rdns="", source="imported"))
    t = pd.DataFrame(rows, columns=["ip", "asn", "org", "country", "rdns", "source"])
    if ipinfo is not None and len(ipinfo):
        t = pd.concat([ipinfo, t[~t.ip.isin(ipinfo.ip)]], ignore_index=True)
    t["is_vpn"] = t.org.map(lambda x: _has(x, C.VPN_PROXY_HINTS))
    t["shared_hosting"] = t.org.map(lambda x: _has(x, C.SHARED_HOSTING_HINTS))
    return t[IPINFO_COLS].reset_index(drop=True)


def domain_flags(domains: pd.DataFrame, ips: pd.DataFrame | None = None) -> pd.DataFrame:
    """-> one row per domain: flags (list of sentences) and a simple count. Same flags in Hindi are not needed: they carry the evidence."""
    ips = ips if ips is not None else ip_table(domains)
    ipx = ips.set_index("ip") if len(ips) else pd.DataFrame(columns=IPINFO_COLS).set_index("ip")
    by_ip = domains[domains.ip != ""].groupby("ip").domain.nunique()
    by_ns = {}
    for r in domains.itertuples():
        for ns in [x.strip().lower() for x in str(r.nameservers).replace(";", ",").split(",") if x.strip()]:
            by_ns.setdefault(ns, set()).add(r.domain)
    rows = []
    for dom, g in domains[domains.domain != ""].groupby("domain"):
        r = g.iloc[0]
        flags = []
        first_use = g.first_seen.min() if g.first_seen.notna().any() else pd.NaT
        if pd.notna(r.created) and pd.notna(first_use):
            age = (first_use - r.created).days
            if 0 <= age < C.DOMAIN_NEW_DAYS:
                flags.append(f"Registered only {age} days before it was first seen in this case")
        if pd.notna(r.created) and pd.notna(r.expires) and (r.expires - r.created).days < C.DOMAIN_SHORT_LIFE_DAYS:
            flags.append(f"Short registration period ({(r.expires - r.created).days} days) - common for throw-away domains")
        if pd.notna(r.created) and pd.notna(r.ssl_first_seen) and abs((r.ssl_first_seen - r.created).days) <= 1:
            flags.append("Certificate issued on the day the domain was registered")
        words = [w for w in LURE_WORDS if w in dom] ; brands = [b for b in BRAND_WORDS if b in dom]
        if brands:
            flags.append(f"Name contains a well-known brand ({', '.join(brands)}) - possible look-alike; check it is not the real site")
        if len(words) >= 2 or (words and brands):
            flags.append(f"Name uses lure words ({', '.join(words)})")
        if re.search(r"xn--", dom):
            flags.append("Internationalised (xn--) name - may imitate another site with look-alike letters")
        for ip in {x for x in g.ip if x}:
            row = ipx.loc[ip] if ip in ipx.index else None
            if row is not None and bool(row.is_vpn):
                flags.append(f"Hosted on a VPN / proxy network ({row.org})")
            n = int(by_ip.get(ip, 0))
            if n >= 2:
                shared = row is not None and bool(row.shared_hosting)
                flags.append(f"{n} domains in this case share IP {ip}" + (" (large shared host: weak evidence)" if shared else " (strong link)"))
        for ns in [x.strip().lower() for x in str(r.nameservers).replace(";", ",").split(",") if x.strip()]:
            if len(by_ns.get(ns, ())) >= 2:
                flags.append(f"{len(by_ns[ns])} domains in this case use name server {ns}")
        rows.append(dict(domain=dom, ip=", ".join(sorted({x for x in g.ip if x})), registrar=r.registrar, created=r.created,
                         hosting=r.hosting, complaint_id=", ".join(sorted({c for c in g.complaint_id if c})), n_flags=len(flags), flags=flags))
    return pd.DataFrame(rows, columns=["domain", "ip", "registrar", "created", "hosting", "complaint_id", "n_flags", "flags"]) \
        .sort_values("n_flags", ascending=False).reset_index(drop=True)


# ------------------------------------------------- IP log <-> transactions ----
def correlate_iplog(iplog: pd.DataFrame, tx: pd.DataFrame, acc: pd.DataFrame, ips: pd.DataFrame | None = None,
                    zone: str = "") -> pd.DataFrame:
    """For every IP-log event that names an account (or a phone we can map to an account) find the closest bank transaction
    of that account. IP-log times are UTC and are converted to the bank's local clock first.

    class: 'same moment' (within config.IP_LOG_MATCH_MINUTES), 'nearby' (within IP_LOG_NEAR_MINUTES), else 'far'.
    caveat: shows when the same IP is used by several accounts (shared / mobile / VPN addresses cannot name a person)."""
    cols = ["when_local", "ip", "event", "account_id", "txn_id", "txn_time", "txn_dir", "txn_amount", "gap_min", "class", "caveat", "source"]
    if iplog.empty or tx.empty:
        return pd.DataFrame(columns=cols)
    log = iplog.copy()
    log["when_local"] = to_local(log.ts_utc, zone)
    ph = acc.dropna(subset=["phone"]).drop_duplicates("phone").set_index("phone").account_id.to_dict() if "phone" in acc else {}
    log["account_id"] = np.where(log.account_id.astype(str).str.len() > 0, log.account_id, log.phone.map(ph).fillna(""))
    per_ip = log[log.account_id != ""].groupby("ip").account_id.nunique()
    vpn = set(ips[ips.is_vpn].ip) if ips is not None and len(ips) else set()
    shared = set(ips[ips.shared_hosting].ip) if ips is not None and len(ips) else set()
    ev = pd.concat([tx.assign(acct=tx.src, dir="debit"), tx.assign(acct=tx.dst, dir="credit")])
    ev = ev[~ev.acct.map(lambda a: is_cashout(a) or str(a).startswith("CASHIN"))]
    by = {a: g.sort_values("ts") for a, g in ev.groupby("acct")}
    rows = []
    for r in log.itertuples():
        g = by.get(r.account_id)
        if g is None or pd.isna(r.when_local):
            continue
        gap = (g.ts - r.when_local).dt.total_seconds() / 60
        i = gap.abs().idxmin()
        m = g.loc[i]; gm = float(gap[i])
        cls = "same moment" if abs(gm) <= C.IP_LOG_MATCH_MINUTES else "nearby" if abs(gm) <= C.IP_LOG_NEAR_MINUTES else "far"
        cav = []
        if per_ip.get(r.ip, 0) >= 2:
            cav.append(f"IP used by {int(per_ip[r.ip])} accounts")
        if r.ip in vpn: cav.append("VPN / proxy address")
        if r.ip in shared: cav.append("large shared host")
        rows.append(dict(when_local=r.when_local, ip=r.ip, event=r.event, account_id=r.account_id, txn_id=m.txn_id, txn_time=m.ts, txn_dir=m.dir,
                         txn_amount=m.amount, gap_min=round(gm, 1), **{"class": cls}, caveat="; ".join(cav), source=r.source))
    return pd.DataFrame(rows, columns=cols).sort_values("gap_min", key=abs).reset_index(drop=True)
