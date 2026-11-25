"""Screens of the app. Each file draws ONE screen and exposes  render(ctx[, an]).

common.py          Ctx: translator, session, small shared widgets (boxes, glossary, open-a-complaint)
step1_data.py      1 Add data
step2_check.py     2 Check
results.py         3 Result: runs the analysis once, shows the view switch, calls the screens below
complaints.py      list + search
complaint_file.py  one complaint: card, picture, actions  (tabs listed in TABS: add a tab = add a function there)
links_page.py      connections between complaints (gangs)
digital_page.py    domains / IPs / hosting, IP-log correlation, digital links, provider letters
workspace_page.py  search everything, UTR trail, unified timeline, evidence, PDF/Excel export
"""
