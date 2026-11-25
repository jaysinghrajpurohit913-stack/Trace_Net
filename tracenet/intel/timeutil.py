"""Time zones in one place.

Rule: bank statements are naive local time (India, config.DEFAULT_TZ). IP logs from providers are often UTC ("Z", "+00:00").
Internally an IP-log time is kept as UTC; to compare with a bank time we convert it to local time first.
"""
import re

import pandas as pd

from .. import config as C

_EXPLICIT = re.compile(r"(Z|UTC|GMT|[+-]\d{2}:?\d{2})\s*$", re.I)
ALIASES = {"IST": "Asia/Kolkata", "UTC": "UTC", "GMT": "UTC", "Z": "UTC"}


def tz_name(x: str) -> str:
    x = str(x or "").strip()
    return ALIASES.get(x.upper(), x) or C.DEFAULT_TZ


def parse_utc(series: pd.Series, assume_tz: str = "") -> pd.Series:
    """Text -> naive UTC timestamps. Text with its own offset keeps it; naive text is taken as `assume_tz` (default India)."""
    zone = tz_name(assume_tz)
    out = []
    for v in series.astype(str).str.strip():
        if not v or v.lower() in ("nan", "nat", "none"):
            out.append(pd.NaT); continue
        try:
            if _EXPLICIT.search(v):
                iso = bool(re.match(r"^\d{4}-\d{2}-\d{2}", v))
                t = pd.to_datetime(re.sub(r"\s*(UTC|GMT)$", "Z", v, flags=re.I), dayfirst=not iso, utc=True)
            else:
                iso = bool(re.match(r"^\d{4}-\d{2}-\d{2}", v))
                t = pd.to_datetime(v, dayfirst=not iso).tz_localize(zone, ambiguous="NaT", nonexistent="shift_forward")
            out.append(t.tz_convert("UTC").tz_localize(None))
        except Exception:
            out.append(pd.NaT)
    return pd.Series(pd.to_datetime(out), index=series.index)


def to_local(utc: pd.Series, zone: str = "") -> pd.Series:
    """Naive UTC -> naive local time (same clock as the bank statements)."""
    return utc.dt.tz_localize("UTC").dt.tz_convert(tz_name(zone)).dt.tz_localize(None)


def fmt_both(ts_local, zone: str = "") -> str:
    """'04 Oct 2026 13:08:00 IST (07:38:00 UTC)' for letters and reports."""
    z = tz_name(zone)
    t = pd.Timestamp(ts_local).tz_localize(z)
    u = t.tz_convert("UTC")
    short = "IST" if z == "Asia/Kolkata" else z
    return f"{t:%d %b %Y %H:%M:%S} {short} ({u:%H:%M:%S} UTC)"
