# TraceNet – developer guide

## Map (one job per file)
```
app.py                       wiring only (language, steps, router)
tracenet/config.py           EVERY threshold / weight / limit  ← change rules here
tracenet/i18n.py             all words, English + Hindi (T["key"] = (English, Hindi))
tracenet/theme.py            colours + CSS + small HTML pieces
tracenet/importer.py         any file → Dataset(acc, tx, comp, domains, iplog)   (synonym lists in SYN)
tracenet/engine.py           features, mule scoring, fund tracing, freeze list
tracenet/linking.py          complaint-to-complaint links, CASE groups, complaint_table
tracenet/intel/              digital side: model, timeutil, lookup (passive), analyse, graph, requests, evidence, timeline
tracenet/pipeline.py         run_analysis(ds) → Analysis   (the ONE place that fixes the order of steps)
tracenet/export.py           Excel + PDF case file
tracenet/ui/*.py             one screen per file; complaint_file.py has a TABS list
tests/                       pytest (fast unit tests + one slow UI smoke test)
```
Data flow: `files → importer.convert → Dataset → pipeline.run_analysis → Analysis → ui screens / export`.

## Recipes
| I want to… | Do this |
|---|---|
| change when an account counts as a mule | `config.py` (`MULE_FLAG_AT`, `MULE_POINTS`, thresholds) |
| add a mule indicator | feature in `engine._extra_features`, a points entry in `config.MULE_POINTS`, one `add(...)` line in `engine.score_mules`; a test in `tests/test_engine.py` |
| add a column / file type | synonyms in `importer.SYN`, name in `REQUIRED`/`KINDS`, a `_xxx(fi)` converter, a `kind_xxx` text in i18n |
| add a tab to the complaint page | write `def tab_xxx(ctx, f)` in `ui/complaint_file.py`, add `("tab_xxx", tab_xxx)` to `TABS`, add the text key |
| add a whole screen | new `ui/xxx_page.py` with `render(ctx, an)`, add to `ui/results.VIEWS`, router and `view_xxx` text |
| add an analysis step | a field on `pipeline.Analysis` and one line in `run_analysis` |
| add / change a text | `i18n.py` – both languages; `tests/test_i18n.py` fails if one is missing or placeholders differ |
| add a red flag for domains | `intel/analyse.domain_flags` (write the flag as a plain sentence with its evidence) |

## Checking and debugging
```
python -m pytest -q                 # everything (~1 min)
python -m pytest -q -m "not slow"   # without opening the whole app
python - <<'PY'                     # poke at the analysis without the UI
from tracenet.importer import load_demo; from tracenet.pipeline import run_analysis
an = run_analysis(load_demo("data")); print(an.table.head()); print(an.flags); print(an.corr)
PY
```
`an.dlinks` / `an.dpairs` show *why* two complaints are linked digitally; `an.feats.reasons` shows why an account is suspect; `an.lk.pairs.reasons` shows why complaints are in one CASE.

## Rules the code must keep (from the problem statement)
* Public sources only (RDAP, public DNS, CT logs, IP→ASN). **Never** connect to or scan a suspect's server (`intel/lookup.py` is the only network code).
* IP geolocation / hosting = indicative. Shared, VPN, CDN and mobile IPs are **weak** evidence and never create a strong link by themselves.
* Subscriber / login / payment records are non-public: the tool only **drafts** the lawful request (`intel/requests.py`); nothing is fetched.
* Private / documentation IPs are never sent to any lookup service.
* Demo data is synthetic (`.example` domains, documentation IP ranges). Never put real personal data in `data/`.
* All times: bank statements are local (IST); IP logs are kept as UTC and converted with `intel/timeutil.py` before comparing.
