"""Every tunable number in TraceNet lives here, so a rule can be changed in ONE place.

Nothing in this file imports anything else from tracenet (no circular imports) and nothing here does any work.
To check what a threshold does, search for its name, e.g.  grep -rn MULE_FLAG_AT tracenet/
"""

# ------------------------------------------------------------------ tracing ----
TRACE_MAX_HOURS = 96            # follow stolen money for at most this long after the fraud
GOLDEN_HOUR = 1.0               # a complaint filed within this many hours is "golden hour"

# -------------------------------------------------------------- mule scoring ----
MULE_FLAG_AT = 40               # score (0-100) at or above which an account is called a suspected mule
ML_MIN_ACCOUNTS = 30            # below this many accounts the anomaly model is skipped (rules only)
ML_WEIGHT = 0.3                 # share of the final score that comes from the anomaly model
ML_CONTAMINATION = 0.06

PASSTHROUGH_RATIO = 0.9         # "forwards almost all the money" = at least this share leaves again
FAST_HOLD_MIN = 60              # ... within this many minutes
NEW_ACCOUNT_DAYS = 90
NEW_ACCOUNT_BIG_IN = 40_000
MANY_SENDERS = 3
STRUCT_REPEATS = 4              # same sender->receiver pair this many times = repeated similar transfers
ROUND_MIN_AMOUNT = 5_000        # round-figure test only for amounts at least this big
ROUND_STEP = 1_000              # ... that are exact multiples of this
ROUND_SHARE = 0.6               # share of outgoing transfers that are round figures
ROUND_MIN_COUNT = 3
SMALL_CREDIT = 5_000            # "small" credit
SMALL_CREDIT_SENDERS = 5        # this many different senders of small credits
DORMANT_DAYS = 14               # quiet for this long, then suddenly busy = "dormant account woke up"
DORMANT_BURST = 3               # busy = this many transactions within 24h after the quiet spell
REPEAT_PEER = 5                 # same counterparty this many times (any direction)

# points added to the rule score for each indicator (rule score is capped at 100)
MULE_POINTS = dict(fast_passthrough=30, new_big=15, many_senders=10, splits=10, cycle=15, repeats=15, shared_ids=20,
                   round_figures=12, many_small=10, dormant_awake=15, repeat_peer=5)

# ------------------------------------------------------- linking complaints ----
LINK_STRONG = 6.0
LINK_PROBABLE = 3.0
LINK_POSSIBLE = 1.5
LINK_SHARED_ACCT_MULE = 3.0     # points per shared account that looks like a mule ...
LINK_SHARED_ACCT_OTHER = 1.5    # ... and per other shared account
LINK_SHARED_ACCT_CAP = 9.0
LINK_SHARED_EXIT = 2.0
LINK_SHARED_EXIT_CAP = 4.0
LINK_RING = 2.0
LINK_RING_CAP = 4.0
LINK_VICTIM_REUSED = 2.0
LINK_TIME_BONUS = 0.5
LINK_TIME_WINDOW_H = 24
LINK_DIGITAL_STRONG = 2.0       # shared domain / IP / name server / phone / device / UPI (not weak)
LINK_DIGITAL_WEAK = 0.5         # shared VPN / big-host IP, public name server, same registrar
LINK_DIGITAL_CAP = 4.0

# ---------------------------------------------------------------- pre-check ----
PRECHECK_HIGH = 60
PRECHECK_MEDIUM = 30

# ---------------------------------------------------- digital (domain / IP) ----
IP_LOG_MATCH_MINUTES = 30       # an IP-log event this close to a transaction is "the same moment"
IP_LOG_NEAR_MINUTES = 180       # ... and this close is "nearby"
DOMAIN_NEW_DAYS = 90            # domain registered less than this long before first use = "freshly registered"
DOMAIN_SHORT_LIFE_DAYS = 400    # registration length shorter than this is common for throw-away domains
LOOKUP_TIMEOUT_S = 8            # per passive lookup
LOOKUP_CACHE_HOURS = 24 * 7

# Hosting / network names that are shared by thousands of customers: a shared IP here is NOT strong evidence
SHARED_HOSTING_HINTS = ("CLOUDFLARE", "AMAZON", "AWS", "GOOGLE", "MICROSOFT", "AZURE", "DIGITALOCEAN", "OVH", "HETZNER",
                        "LINODE", "AKAMAI", "FASTLY", "GODADDY", "NAMECHEAP", "HOSTINGER", "CONTABO", "VULTR")
VPN_PROXY_HINTS = ("VPN", "PROXY", "TOR EXIT", "M247", "NORDVPN", "EXPRESSVPN", "PROTON", "MULLVAD", "PIA ", "PRIVATE INTERNET ACCESS")

# time zone the bank statements are in unless told otherwise (India)
DEFAULT_TZ = "Asia/Kolkata"
