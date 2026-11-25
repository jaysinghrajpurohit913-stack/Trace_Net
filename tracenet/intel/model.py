"""Table layouts for the digital side. Every table the app passes around has exactly these columns."""
import ipaddress
import re
from dataclasses import dataclass, field

import pandas as pd

DOMAIN_COLS = ["domain", "ip", "registrar", "created", "expires", "nameservers", "hosting", "asn", "country", "ssl_issuer",
               "ssl_first_seen", "first_seen", "last_seen", "complaint_id", "source", "note"]
IPLOG_COLS = ["ts_utc", "ip", "event", "account_id", "phone", "upi", "source", "tz"]
IPINFO_COLS = ["ip", "asn", "org", "country", "rdns", "is_vpn", "shared_hosting", "source"]


def empty_domains() -> pd.DataFrame:
    return pd.DataFrame(columns=DOMAIN_COLS)


def empty_iplog() -> pd.DataFrame:
    return pd.DataFrame(columns=IPLOG_COLS)


def is_ip(x) -> bool:
    try:
        ipaddress.ip_address(str(x).strip())
        return True
    except ValueError:
        return False


def is_public_ip(x) -> bool:
    """Private / documentation-style addresses are kept in the data but never sent to a lookup service."""
    try:
        a = ipaddress.ip_address(str(x).strip())
    except ValueError:
        return False
    return a.is_global


def norm_domain(x) -> str:
    s = str(x).strip().lower()
    s = re.sub(r"^[a-z]+://", "", s)
    s = s.split("/")[0].split("?")[0].split(":")[0].strip(".")
    return s[4:] if s.startswith("www.") else s


def registrable(domain: str) -> str:
    """Last two labels (good enough for grouping; co.in style endings keep three)."""
    p = domain.split(".")
    if len(p) >= 3 and p[-2] in ("co", "com", "org", "net", "gov", "ac") and len(p[-1]) == 2:
        return ".".join(p[-3:])
    return ".".join(p[-2:]) if len(p) >= 2 else domain


def tidy_domains(df: pd.DataFrame) -> pd.DataFrame:
    """Make any partly-filled indicator table follow DOMAIN_COLS."""
    out = df.copy()
    for c in DOMAIN_COLS:
        if c not in out:
            out[c] = pd.NaT if c in ("created", "expires", "ssl_first_seen", "first_seen", "last_seen") else ""
    out["domain"] = out.domain.map(lambda x: norm_domain(x) if str(x).strip() else "")
    out["ip"] = out.ip.astype(str).str.strip().replace({"nan": "", "None": ""})
    for c in ("created", "expires", "ssl_first_seen", "first_seen", "last_seen"):
        out[c] = pd.to_datetime(out[c], errors="coerce")
        if getattr(out[c].dt, "tz", None) is not None:
            out[c] = out[c].dt.tz_convert("UTC").dt.tz_localize(None)
    for c in ("registrar", "nameservers", "hosting", "asn", "country", "ssl_issuer", "complaint_id", "source", "note"):
        out[c] = out[c].fillna("").astype(str).replace({"nan": ""})
    return out[DOMAIN_COLS].reset_index(drop=True)


@dataclass
class Intel:
    """Everything digital about a case, in one object."""
    domains: pd.DataFrame = field(default_factory=empty_domains)
    iplog: pd.DataFrame = field(default_factory=empty_iplog)
    ips: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=IPINFO_COLS))
    certs: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=["name", "issuer", "not_before", "domain"]))
    lookups: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=["time_utc", "source", "query", "ok", "detail"]))

    @property
    def empty(self) -> bool:
        return self.domains.empty and self.iplog.empty
