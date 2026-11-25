# TraceNet — Money-Trail Intelligence for Cyber-Fraud Investigators

**Team ALTER**  
**Rajasthan Police Hackathon 2026 (R4C)**  
**Problem Statement PS05 – Financial Crime Infrastructure & Money-Trail Analysis**

TraceNet is an investigative decision-support platform that helps cyber-fraud investigators trace stolen money across bank accounts, identify suspected mule accounts, discover links between complaints, correlate the digital infrastructure behind a fraud (domains, IPs, name servers), and prepare lawful information requests and evidence reports — in one Streamlit application, in **Hindi and English**.

**Core objective:** help investigators answer four questions quickly:

1. Where did the stolen money go?
2. Which accounts and networks should be investigated first?
3. How much money may still be available for recovery?
4. Which complaints, domains and IPs belong to the same operation?

---

## 1. Key Features

| Feature | Description |
|---|---|
| Money-trail tracing | Follows suspected stolen funds through successive transactions, time-aware, starting from a complaint or from any UTR. |
| Mule-account detection | Explainable rules (rapid in-out, many small credits, round-figure layering, dormant→active, repeated counterparties, fan-in/out, cycles) plus Isolation Forest. Every flag shows a plain-language reason. |
| Fraud-ring discovery | Connects accounts sharing devices, phones, IPs or beneficiaries. |
| Cross-complaint analysis | Scores links between complaints (Strong / Probable / Possible) and groups them into gang cases. |
| Domain intelligence | Registration age, registrar, name servers, DNS records, certificate-log history and red flags (new domain, short registration, look-alike of a bank name, shared IP / name server). |
| IP & hosting intelligence | ASN, provider, reverse DNS, VPN / proxy / shared-host hints. Geolocation is indicative only. |
| Timestamp correlation | IP-log times (UTC) are converted to local time and matched to bank transactions, with a shared-IP caveat. |
| Digital relationship graph | Domains, IPs, name servers, registrars, phones, UPI ids, accounts and UTRs across cases. Weak links (VPN, CDN, public name servers, same registrar) never merge cases on their own. |
| Case workspace | One search box for accounts, UTRs, domains, IPs, phones, UPI ids, names and complaint numbers; combined timeline; numbered evidence references; Excel and PDF case file. |
| Lawful request drafts | Letters to banks, registrars, hosting providers and ISPs with exact IP, timestamp and time zone. The legal provision is left for the investigating officer. |
| Freeze-first prioritization | Ranks accounts by suspected recoverable money and risk. |
| Bank-wise requests, lien files, watchlist | Grouped by bank, exportable. |
| Pre-payment risk check | HIGH / MEDIUM / LOW indication for a receiving account. |
| Complaint desk | Search, filters, status tracking and notes. |
| Golden-hour analysis | How recoverable funds shrink with investigation delay. |

## 2. How to Run TraceNet

### Windows

**Option A – Quick start:** extract the project and double-click `START_TraceNet.bat`.

**Option B – Manual setup** (Command Prompt in the project folder):

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

### Linux / macOS

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd tracenet_v2

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

streamlit run app.py
```

or simply `bash start.sh`.

**Requirements:** Python 3.10+ and internet access for the first dependency install. The optional public-lookup button also needs internet; everything else works offline.

## 3. How to Use TraceNet

### Step 1 – Import data
Excel (`.xlsx`), CSV and text-based PDF. Files can be dropped in any order and any column naming; the importer detects what each file is and maps columns automatically. You can correct the mapping, or type a complaint in by hand.

### Step 2 – Check
Shows transactions, accounts and complaints found, warnings, detected mappings, and the number of domains / IP-log rows. You can optionally link names or UPI ids to account numbers.

### Step 3 – Investigate
Five views: **Complaints** (searchable list) · **One complaint** (card, money trail, mules, actions, notes) · **Connections** between complaints · **Domains & IPs** · **Case workspace**.

### Try the demo
Click **Try with demo data**, or import the files in `sample_bank_files/`.

## 4. System Architecture

```text
                    INPUT DATA
      Bank files · Complaints · KYC/Device · Domains · IP log
                         |
                  tracenet/importer.py      (any file → one common schema)
                         |
                 tracenet/pipeline.py       (the ONE place that fixes the order of steps)
                         |
      +------------------+-------------------+
      |                  |                   |
 engine.py          linking.py          intel/ (passive digital evidence)
 trace · mule       complaint ↔         domains · IPs · time match ·
 score · freeze     complaint, CASEs    graph · requests · timeline
      |                  |                   |
      +------------------+-------------------+
                         |
              ui/*.py  (one screen per file)   export.py (Excel / PDF)
                         |
                INVESTIGATOR OUTPUT
```

### Technology stack

| Layer | Technology |
|---|---|
| Language | Python 3 |
| Application | Streamlit |
| Data | Pandas, NumPy |
| Graphs | NetworkX |
| Anomaly detection | scikit-learn |
| Visualization | Plotly |
| Input | CSV, Excel, text-based PDF (pdfplumber) |
| Reports | openpyxl, reportlab |
| Tests | pytest, Streamlit AppTest |

## 5. Core Technical Modules

| Module | Responsibility |
|---|---|
| `app.py` | Wiring only: language, steps, router. |
| `tracenet/config.py` | **Every** threshold, weight and limit. |
| `tracenet/importer.py` | File detection, column mapping, common schema. |
| `tracenet/engine.py` | Fund tracing, mule scoring, ring linking, freeze list. |
| `tracenet/linking.py` | Complaint-to-complaint links, CASE groups, complaint table. |
| `tracenet/pipeline.py` | `run_analysis()` → one `Analysis` object. |
| `tracenet/intel/` | Domain/IP lookups (passive), time correlation, relationship graph, evidence references, lawful request drafts, timeline. |
| `tracenet/explain.py`, `summary.py`, `report.py` | Plain-language explanations, briefs, bank-wise requests. |
| `tracenet/export.py` | Excel and PDF case file. |
| `tracenet/viz.py` | Money-trail and relationship pictures. |
| `tracenet/ui/` | One file per screen. |
| `tracenet/theme.py`, `i18n.py` | Look and feel; all words in English + Hindi. |
| `tracenet/notes.py` | Status and investigation notes. |

## 6. Money-Trail Analysis

A plain transaction graph only shows who is connected; it does not prove that stolen money passed through every connected account. TraceNet traces **time-aware**: transaction timestamps, arrival time of suspected funds, the amount remaining at each account, and the outgoing transfers that follow. Unrelated transactions are not treated as part of the trail.

**Cash-out identification:** ATM / cash withdrawals, wallets, payment services and crypto-exchange references, based on narration text.

**Mixed-fund handling:** outgoing transfers are attributed to the suspected stolen balance first until it is exhausted. This is an investigative estimation convention, not proof of ownership of individual funds, and it can over-estimate stolen funds.

## 7. Mule-Account Detection

Explainable indicators: rapid in-out movement, many small credits from different senders, round-figure layering, dormant account suddenly active, repeated counterparties, fan-in / fan-out, cycles, structuring, shared identity or infrastructure.

Scoring: rule-based risk 70% + Isolation Forest anomaly 30%. An account is flagged at a score of 40 (`config.MULE_FLAG_AT`). The score is a risk indicator, **not** a finding that the account holder committed a crime.

## 8. Entity Linking and Fraud Rings

Accounts sharing device IDs, phone numbers or IP addresses are grouped into suspected rings. When none of these are available, shared beneficiaries are used as a fallback. All links are leads that need verification.

## 9. Cross-Complaint and Digital Intelligence

Complaint pairs are scored from: shared accounts, shared cash-out destinations, shared rings, a victim account appearing in another trail, timing similarity, money-flow links — and **digital links**: shared domains, name servers, IPs, phones, UPI ids, devices.

| Evidence | Treatment |
|---|---|
| Same domain / phone / UPI / device | Strong |
| Shared name server, registrar, hosting | Weak (needs support) |
| VPN, proxy, CDN, shared-host IP | Weak, never merges cases alone |

Levels: Strong ≥ 6, Probable ≥ 3, Possible ≥ 1.5 (editable in `config.py`).

## 10. Digital Evidence — What Is and Is Not Done

**Done (public, passive sources only):** RDAP/WHOIS, DNS A/AAAA/MX/NS/TXT/CNAME over public DNS-over-HTTPS, certificate-transparency logs, IP→ASN. Results are cached and the tool works offline.

**Not done, by design:**
- No access to real bank systems, no account freezing.
- No active scanning or probing of any third-party server.
- No subscriber, login or non-public records — the tool only **drafts** the lawful request. Such records come only through legal process.
- Private and documentation IP ranges are never sent to any lookup service.
- IP geolocation is indicative only; shared / dynamic IPs are flagged as weak evidence.

**Time handling:** bank statements are local time (IST); IP logs are stored as UTC and converted before comparison; all letters state both.

Historical DNS is only used if you import it; there is no free passive source for it.

## 11. Freeze-First Prioritization

Ranking uses: suspected money still in the account, mule score, ring membership and flow relationships. TraceNet produces recommendations; freezing and lien actions remain with authorised investigators and banks.

## 12. Supported Input Data

| Input | Information | Key fields |
|---|---|---|
| Transaction table | Many accounts and payments | Date/time, from, to, amount |
| Bank statement | One account's activity | Date, narration, debit, credit, balance, UTR |
| Complaint records | NCRP-style complaints | Victim account, amount, fraud time, (name, phone, UPI) |
| Account / KYC | Account infrastructure | Account, bank, phone, device, IP, opening date |
| Domains / IPs | Phishing infrastructure | Domain, IP, registrar, name server, dates |
| IP log | Who connected when | Timestamp, IP, account / phone |

### Input limitations
- Scanned / image-only PDFs are not supported (OCR needed first).
- Some statements identify counterparties only by name or UPI id; use the alias box.
- Incomplete timestamps make same-day ordering uncertain.
- Results depend on completeness and accuracy of the records.

## 13. Demo Data and Benchmark

Synthetic data only: 5 complaints, 5 laundering styles, 41 planted mule accounts, 6 domain indicators on `.example` names with documentation-range IPs.

| Metric | Result (`python run_demo.py --test`) |
|---|---:|
| Planted mule accounts found | 38 / 41 (93%) |
| Innocent accounts wrongly flagged | 1 |
| Phishing complaints joined into one case via shared domain | NCRP-10 + NCRP-20 |
| Case kept separate (only a VPN IP in common) | NCRP-50 |

**Important:** these figures come from synthetic data and controlled demonstrations. They are not real-world detection rates or recovery guarantees. Real results depend on real banking data, data quality and bank response times.

## 14. Running the Demo and Tests

```bash
pip install -r requirements.txt
streamlit run app.py          # the app
python run_demo.py --test     # synthetic detection check
pip install -r requirements-dev.txt
python -m pytest -q           # unit + UI smoke tests (~1 min)
```

Developer guide: [`DEVELOPING.md`](DEVELOPING.md).

## 15. Repository Structure

```text
TraceNet/
├── app.py
├── README.md
├── DEVELOPING.md
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── .gitignore
├── .streamlit/config.toml
│
├── tracenet/
│   ├── config.py        engine.py     importer.py   linking.py
│   ├── pipeline.py      explain.py    summary.py    report.py
│   ├── export.py        viz.py        templates.py  notes.py
│   ├── theme.py         i18n.py
│   ├── intel/           model · timeutil · lookup · analyse · graph
│   │                    evidence · requests · timeline
│   └── ui/              common · step1_data · step2_check · results
│                        complaints · complaint_file · links_page
│                        digital_page · workspace_page
│
├── tests/
├── assets/              rounds.png · trail.png · stats.json
├── data/                synthetic: transactions, accounts, complaints,
│                        domains, ip_log, ground_truth (.csv)
├── sample_bank_files/   1_transactions · 2_complaints · 3_statement (CSV)
│                        4_statement (PDF) · 5_accounts_KYC · 6_domains_IPs
│                        7_ip_log
│
├── generate_data.py · generate_digital.py · make_sample_files.py
├── run_demo.py
├── START_TraceNet.bat
└── start.sh
```

`data/` and `sample_bank_files/` must contain synthetic or approved data only.

## 16. Real-World Context

Cyber-fraud money moves across many accounts and banks within hours, and the phishing infrastructure behind it is often reused across victims. Recovery depends on how quickly the next account in the chain is identified and the bank is contacted — and on proving that separate complaints belong to one operation. TraceNet is built around that operational problem. Initiatives like the Indian Suspect Registry and Singapore's COSMIC show the value of sharing financial-crime intelligence; TraceNet's watchlist export and entity linking explore related ideas at prototype level, without any integration with those systems.

## 17. Assumptions and Limitations

1. **Bank response:** further records come from banks through authorised channels; TraceNet cannot obtain them itself.
2. **Infrastructure data:** ring detection is stronger with reliable device, phone and IP data.
3. **Incomplete records** reduce tracing accuracy.
4. **Mixed funds:** the conservative convention can overestimate stolen funds.
5. **Cash-out:** once money leaves the traceable network, recovery is harder.
6. **Scanned documents** need OCR first.
7. **No live bank API** and no account freezing.
8. **Public lookups** are untested at scale against the live internet and depend on third-party services being reachable.
9. **Decision authority:** scores and reports are leads, not legal proof.

## 18. Security and Data Handling

- Use synthetic data for demonstrations; never commit real complainant or banking data.
- Never publish passwords, API keys or credentials; keep `.env` files out of version control.
- `case_notes.json` and `.tracenet_cache/` are local runtime files and are git-ignored.
- Restrict access to any deployment that handles real records; add access control, audit logging, retention policy and encryption before operational use.

## 19. Future Scope

- Secure integration with authorised banking and cybercrime data channels
- OCR for scanned statements
- Real-time monitoring where authorised feeds exist
- Graph-based anomaly detection
- Role-based access and audit trails
- Centralised case management
- Validation on appropriately anonymised real data

These are proposed extensions, not existing functionality.

## 20. Project Objective

To cut the time and manual effort needed to understand a cyber-fraud money trail: time-aware tracing, explainable mule detection, ring and cross-complaint discovery, digital-evidence correlation and ready-to-use reports and requests.

**Trace the money. Connect the cases. Prioritize the action.**

---

**Team ALTER** · Rajasthan Police Hackathon 2026 · PS05 – Financial Crime Infrastructure & Money-Trail Analysis
