"""PASSIVE public lookups for a domain or an IP. Nothing here ever connects to the suspect's own server.

Sources (all public, read-only):
  RDAP        registration data of a domain / ownership of an IP   (rdap.org -> the registry's own RDAP server)
  DNS         A, AAAA, MX, NS, TXT, CNAME and reverse DNS           (Google DNS-over-HTTPS: dns.google)
  ASN         network number + provider of an IP                    (Team Cymru, asked through DNS-over-HTTPS)
  CT logs     certificates issued for the domain + sub-domains      (crt.sh)

How it behaves
  * every call has a timeout; a failure never stops the app, it just marks the row "offline"
  * results are cached on disk (config.LOOKUP_CACHE_HOURS) so repeating a case does not repeat the traffic
  * private / documentation IPs are never sent anywhere
  * `fetch` can be replaced (tests use a fake), so this file is testable without internet
  * Geolocation and hosting are INDICATIVE only. Subscriber / login records are NOT public and are never fetched here.
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .. import config as C
from .model import is_ip, is_public_ip, norm_domain, tidy_domains

SOURCES = {
    "rdap": "RDAP (rdap.org → registry)",
    "dns": "Public DNS (dns.google DNS-over-HTTPS)",
    "asn": "Team Cymru IP→ASN (via DNS-over-HTTPS)",
    "ct": "Certificate Transparency (crt.sh)",
}
UA = {"User-Agent": "TraceNet-investigation-tool/2 (passive lookups)", "Accept": "application/json"}


def http_json(url: str, timeout: float = C.LOOKUP_TIMEOUT_S):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:          # noqa: S310 (fixed https hosts only)
        return json.loads(r.read().decode("utf-8", "replace"))


@dataclass
class LookupLog:
    """What was asked, from where, when, and what came back: this becomes evidence in the report."""
    rows: list = field(default_factory=list)

    def add(self, source, query, ok, detail=""):
        self.rows.append(dict(time_utc=pd.Timestamp.now("UTC").tz_localize(None).floor("s"), source=SOURCES.get(source, source),
                              query=query, ok=bool(ok), detail=str(detail)[:160]))

    def frame(self):
        return pd.DataFrame(self.rows, columns=["time_utc", "source", "query", "ok", "detail"])


class Cache:
    def __init__(self, folder):
        self.path = Path(folder) / "lookup_cache.json" if folder else None
        try:
            self.data = json.loads(self.path.read_text("utf-8")) if self.path and self.path.exists() else {}
        except Exception:
            self.data = {}

    def get(self, key):
        v = self.data.get(key)
        if v and time.time() - v["t"] < C.LOOKUP_CACHE_HOURS * 3600:
            return v["v"]
        return None

    def put(self, key, value):
        self.data[key] = dict(t=time.time(), v=value)
        try:
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.path.write_text(json.dumps(self.data), "utf-8")
        except Exception:
            pass


def _cached(cache, log, source, query, url, fetch):
    key = f"{source}|{query}"
    hit = cache.get(key) if cache else None
    if hit is not None:
        log.add(source, query, True, "from local cache")
        return hit
    try:
        v = fetch(url)
        if cache: cache.put(key, v)
        log.add(source, query, True)
        return v
    except Exception as e:                       # offline, blocked, not found...
        log.add(source, query, False, type(e).__name__ + ": " + str(e)[:100])
        return None


# ----------------------------------------------------------------- DNS ----
def dns_query(name, rtype, fetch, cache, log):
    url = "https://dns.google/resolve?" + urllib.parse.urlencode({"name": name, "type": rtype})
    j = _cached(cache, log, "dns", f"{name} {rtype}", url, fetch)
    return [a.get("data", "").rstrip(".").strip('"') for a in (j or {}).get("Answer", []) if a.get("type") is not None]


def dns_records(domain, fetch=http_json, cache=None, log=None):
    log = log or LookupLog()
    return {t: dns_query(domain, t, fetch, cache, log) for t in ("A", "AAAA", "MX", "NS", "TXT", "CNAME")}


def reverse_dns(ip, fetch=http_json, cache=None, log=None):
    log = log or LookupLog()
    if not is_public_ip(ip):
        return ""
    import ipaddress
    name = ipaddress.ip_address(ip).reverse_pointer
    r = dns_query(name, "PTR", fetch, cache, log)
    return r[0] if r else ""


def asn_of(ip, fetch=http_json, cache=None, log=None):
    """Team Cymru: origin AS number, then the AS name. Returns (asn, org, country)."""
    log = log or LookupLog()
    if not is_public_ip(ip) or ":" in ip:           # IPv6 not handled by this simple path
        return "", "", ""
    q = ".".join(reversed(ip.split("."))) + ".origin.asn.cymru.com"
    r = dns_query(q, "TXT", fetch, cache, log)
    if not r:
        return "", "", ""
    parts = [p.strip() for p in r[0].split("|")]
    asn, country = parts[0].split()[0], (parts[2] if len(parts) > 2 else "")
    o = dns_query(f"AS{asn}.asn.cymru.com", "TXT", fetch, cache, log)
    org = o[0].split("|")[-1].strip() if o else ""
    return f"AS{asn}", org, country


# ----------------------------------------------------------------- RDAP ----
def rdap_domain(domain, fetch=http_json, cache=None, log=None):
    log = log or LookupLog()
    j = _cached(cache, log, "rdap", domain, f"https://rdap.org/domain/{domain}", fetch)
    if not j:
        return {}
    ev = {e.get("eventAction"): e.get("eventDate") for e in j.get("events", [])}
    reg = ""
    for e in j.get("entities", []):
        if "registrar" in e.get("roles", []):
            vc = e.get("vcardArray", [None, []])[1]
            reg = next((x[3] for x in vc if x[0] == "fn"), "")
    return dict(registrar=reg, created=ev.get("registration", ""), expires=ev.get("expiration", ""),
                nameservers=", ".join(sorted(n.get("ldhName", "").lower() for n in j.get("nameservers", []))),
                status=", ".join(j.get("status", [])))


def rdap_ip(ip, fetch=http_json, cache=None, log=None):
    log = log or LookupLog()
    if not is_public_ip(ip):
        return {}
    j = _cached(cache, log, "rdap", ip, f"https://rdap.org/ip/{ip}", fetch)
    return dict(org=j.get("name", ""), country=j.get("country", ""), handle=j.get("handle", "")) if j else {}


# ----------------------------------------------------------------- CT ----
def ct_certs(domain, fetch=http_json, cache=None, log=None):
    """-> DataFrame(name, issuer, not_before) of certificates seen for domain and its sub-domains."""
    log = log or LookupLog()
    j = _cached(cache, log, "ct", domain, f"https://crt.sh/?q=%25.{urllib.parse.quote(domain)}&output=json", fetch)
    rows = []
    for c in j or []:
        for n in str(c.get("name_value", "")).splitlines():
            rows.append(dict(name=n.strip().lower().lstrip("*."), issuer=c.get("issuer_name", ""), not_before=c.get("not_before", "")))
    df = pd.DataFrame(rows, columns=["name", "issuer", "not_before"]).drop_duplicates()
    df["not_before"] = pd.to_datetime(df.not_before, errors="coerce")
    return df.sort_values("not_before").reset_index(drop=True)


def _when(x):
    """RDAP date text -> naive UTC Timestamp (NaT if unreadable)."""
    t = pd.to_datetime(x, errors="coerce", utc=True)
    return t.tz_localize(None) if pd.notna(t) else pd.NaT


# ----------------------------------------------------------------- one call for the UI ----
def enrich_domains(domains: pd.DataFrame, fetch=http_json, cache_dir=None, log: LookupLog | None = None, only_missing=True):
    """Fill the blanks of the indicator table from public sources.
    Returns (domains_df, ipinfo_df, certs_df, log). Imported values are never overwritten when only_missing=True."""
    log = log or LookupLog()
    cache = Cache(cache_dir)
    d = tidy_domains(domains)
    certs, ipinfo = [], {}
    for i, r in d.iterrows():
        if not r.domain:
            continue
        rd = rdap_domain(r.domain, fetch, cache, log)
        for col in ("registrar", "created", "expires", "nameservers"):
            if rd.get(col) and (not only_missing or d.at[i, col] in ("", None) or pd.isna(d.at[i, col])):
                d.at[i, col] = _when(rd[col]) if col in ("created", "expires") else rd[col]
        if not r.ip:
            a = dns_query(r.domain, "A", fetch, cache, log)
            if a:
                d.at[i, "ip"] = a[0]
        ct = ct_certs(r.domain, fetch, cache, log)
        if len(ct):
            ct["domain"] = r.domain; certs.append(ct)
            if not d.at[i, "ssl_issuer"]:
                d.at[i, "ssl_issuer"] = ct.iloc[0].issuer
            if pd.isna(d.at[i, "ssl_first_seen"]):
                d.at[i, "ssl_first_seen"] = _when(ct.iloc[0].not_before)
    d = tidy_domains(d)
    for ip in sorted({x for x in d.ip if x and is_ip(x)}):
        asn, org, cc = asn_of(ip, fetch, cache, log)
        ipinfo[ip] = dict(ip=ip, asn=asn, org=org, country=cc, rdns=reverse_dns(ip, fetch, cache, log), source="Cymru/DNS")
        for col, val in (("asn", asn), ("hosting", org), ("country", cc)):
            m = (d.ip == ip) & (d[col] == "")
            d.loc[m, col] = val
    from .analyse import ip_table
    return d, ip_table(d, pd.DataFrame(ipinfo.values())), (pd.concat(certs, ignore_index=True) if certs else pd.DataFrame(columns=["name", "issuer", "not_before", "domain"])), log
