"""Digital-infrastructure intelligence (domains, IPs, hosting) and how it ties to the money trail.

model.py     table layouts + small helpers (is_ip, normalising)
timeutil.py  one place for time zones: everything is stored as UTC and shown as local (IST by default)
lookup.py    PASSIVE public lookups only (RDAP, DNS-over-HTTPS, Certificate Transparency); cached; works offline
analyse.py   explainable red flags for domains / IPs, and IP-log <-> transaction timestamp correlation
graph.py     one relationship graph over accounts, domains, IPs, phones, UPI ids, UTRs and complaints
requests.py  drafts of lawful information requests (bank / registrar / hosting / ISP)
evidence.py  numbered evidence references used by the workspace and the reports
"""
