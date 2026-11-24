# TraceNet — Money-Trail Intelligence for Cyber-Fraud Investigators

**Team ALTER**  
**Rajasthan Police Hackathon 2026**  
**Problem Statement PS05 – Financial Crime Infrastructure & Money-Trail Analysis**

TraceNet is an investigative decision-support platform designed to help cyber-fraud investigators trace stolen money across multiple bank accounts, identify suspicious mule accounts, discover connections between fraud complaints, and prioritize accounts where funds may still be available for recovery.

It combines transaction-flow analysis, explainable mule-account scoring, entity linking, cross-complaint intelligence, and automated investigation reports in a single Streamlit-based application.

**Core objective:** Help investigators answer three questions quickly:

1. Where did the stolen money go?
2. Which accounts and networks should be investigated first?
3. How much money may still be available for recovery?

---

## 1. Key Features

| Feature | Description |
|---|---|
| Money-trail tracing | Follows suspected stolen funds through successive transactions. |
| Mule-account detection | Identifies suspicious accounts using explainable behavioural rules and anomaly detection. |
| Fraud-ring discovery | Connects accounts sharing devices, phone numbers, or IP addresses. |
| Cross-complaint analysis | Identifies relationships between multiple fraud complaints. |
| Freeze-first prioritization | Ranks accounts based on suspected recoverable funds and risk indicators. |
| Bank-wise requests | Generates investigation requests grouped by bank. |
| Lien-file generation | Exports account-level information for bank action. |
| Watchlist export | Produces lists of high-risk accounts with reasons and ring identifiers. |
| Pre-payment risk check | Provides HIGH, MEDIUM, or LOW risk indications using available pre-payment information. |
| Investigation reports | Generates chronological transaction trails, explanations, and recommended actions. |
| Complaint management | Supports complaint entry, search, filtering, status tracking, and investigation notes. |
| Golden-hour analysis | Shows how the availability of recoverable funds changes with investigation time. |

## 2. How to Run TraceNet

### Windows

**Option A – Quick start**

1. Download or clone the repository.
2. Extract the project if downloaded as a ZIP.
3. Open the project folder.
4. Double-click `START_TraceNet.bat`.
5. Wait for dependencies to install and the application to start.
6. Open the local URL displayed in the terminal.

**Option B – Manual setup**

Open Command Prompt inside the project directory:

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

Alternatively, use:

```bash
bash start.sh
```

**Requirements:** Python 3 and an internet connection for the initial dependency installation.

## 3. How to Use TraceNet

### Step 1 – Import Data

TraceNet accepts multiple input files:

- Excel (`.xlsx`)
- CSV (`.csv`)
- Text-based PDF (`.pdf`)

The importer attempts to identify file types and map columns automatically. Users can review the detected mappings and correct them when necessary.

Investigators can also enter complaint information manually when a complaint file is unavailable.

### Step 2 – Validate and Prepare

The application displays:

- Number of transactions imported.
- Number of accounts identified.
- Number of complaints loaded.
- Import warnings and data-quality information.
- Detected column mappings.

Investigators can optionally link names or UPI identifiers to account numbers where the available records support that mapping.

### Step 3 – Investigate

The results include:

- Chronological money trails.
- Suspicious account rankings.
- Mule-account risk scores.
- Fraud-ring connections.
- Money potentially remaining in accounts.
- Bank-wise requests and lien-file exports.
- Investigation reports.

Investigators can also switch to **Connections between complaints** to examine relationships across multiple cases.

### Try the Demo

Use the application's **Try with demo data** functionality or import the sample files available in:

```text
sample_bank_files/
```

These files are intended for demonstration and testing.

## 4. System Architecture

TraceNet follows a modular architecture.

```text
                  INPUT DATA
                       |
          +------------+------------+
          |            |            |
      Bank Files   Complaints   Account/KYC Data
      CSV/Excel      NCRP        Device/Phone/IP
      Text-PDF        |
          +------------+------------+
                       |
                DATA IMPORTER
                tracenet/importer.py
                       |
             VALIDATION & MAPPING
                       |
                CORE ENGINE
                tracenet/engine.py
                       |
        +--------------+---------------+
        |              |               |
   Fund Tracing    Mule Scoring    Entity Linking
        |              |               |
        +--------------+---------------+
                       |
              CROSS-CASE ANALYSIS
              tracenet/linking.py
                       |
             PRIORITIZATION ENGINE
                       |
        +--------------+---------------+
        |              |               |
    Dashboard     Bank Requests    Reports
     app.py       Lien/Watchlist   report.py
        |              |               |
        +--------------+---------------+
                       |
              INVESTIGATOR OUTPUT
```

### Technology Stack

| Layer | Technology |
|---|---|
| Programming language | Python |
| Application framework | Streamlit |
| Data processing | Pandas |
| Transaction graph analysis | NetworkX |
| Anomaly detection | Scikit-learn |
| Visualization | Plotly |
| Input formats | CSV, Excel, text-based PDF |
| Data storage | Local files and generated investigation records |

## 5. Core Technical Modules

| Module | Responsibility |
|---|---|
| `app.py` | Main Streamlit application and investigation interface. |
| `tracenet/engine.py` | Fund tracing, mule scoring, entity linking, prioritization, and exports. |
| `tracenet/importer.py` | File processing, column detection, mapping, and data preparation. |
| `tracenet/linking.py` | Relationships and connections across complaints. |
| `tracenet/explain.py` | Explanations for suspicious activity and investigation findings. |
| `tracenet/viz.py` | Transaction-trail and network visualizations. |
| `tracenet/report.py` | Investigation reports and bank-wise request generation. |
| `tracenet/summary.py` | Investigation summaries. |
| `tracenet/templates.py` | Reusable report and request templates. |
| `tracenet/notes.py` | Investigation notes and case-related information. |
| `tracenet/theme.py` | Application styling and interface components. |
| `tracenet/i18n.py` | Application language and text resources. |

## 6. Money-Trail Analysis

A normal transaction graph shows which accounts are connected. However, connectivity alone does not prove that money from a particular fraud travelled through every connected account.

TraceNet uses time-aware fund tracing to follow suspected stolen funds through transactions.

Its tracing logic considers:

- Transaction timestamps.
- Source and destination accounts.
- Transaction amounts.
- The arrival time of suspected stolen funds.
- The amount of suspected funds remaining at each account.
- Subsequent outgoing transactions.

This helps prevent unrelated transactions from being treated as part of the same stolen-money trail.

### Cash-out Identification

The system recognises potential cash-out destinations using indicators such as:

- ATM withdrawals.
- Cash withdrawals.
- Wallet-related transactions.
- Payment services.
- Cryptocurrency exchange references.

These indicators depend on the transaction descriptions and available input data.

### Mixed-Fund Handling

When stolen and legitimate funds are mixed in an account, TraceNet uses a conservative accounting convention: outgoing transfers are attributed to the suspected stolen balance first, until that balance is exhausted.

This is an investigative estimation method, not proof of ownership of individual funds.

## 7. Mule-Account Detection

TraceNet combines explainable behavioural rules with anomaly detection.

The behavioural indicators include:

- Rapid movement of incoming funds.
- Unusual incoming and outgoing transaction patterns.
- Fan-in and fan-out behaviour.
- Newly opened accounts.
- Transaction cycles.
- Structuring patterns.
- Shared identity and infrastructure indicators.

The implemented scoring approach combines:

- Rule-based risk score: 70%.
- Isolation Forest anomaly score: 30%.

The resulting score helps investigators prioritize accounts for further examination.

The score is a risk indicator, not a determination that an account holder has committed a crime.

## 8. Entity Linking and Fraud-Ring Discovery

Fraudulent networks may use multiple bank accounts while reusing common infrastructure.

TraceNet links accounts that share available identifiers, including:

- Device IDs.
- Phone numbers.
- IP addresses.

Accounts connected through shared identifiers can be grouped into suspected fraud rings.

When device, phone, or IP information is unavailable, the system also provides fallback linking based on shared transaction beneficiaries.

These relationships are investigative leads and require verification.

## 9. Cross-Complaint Intelligence

TraceNet can analyse multiple complaints together using a shared transaction ledger.

This helps investigators identify whether apparently separate fraud incidents may involve the same accounts or networks.

The cross-complaint analysis considers:

- Shared accounts.
- Shared cash-out destinations.
- Shared fraud-ring identifiers.
- Victim accounts appearing in another complaint's money trail.
- Similarity in complaint timing.
- Transaction-flow relationships.

Complaint pairs receive relationship scores and can be grouped into Strong, Probable, or Possible categories.

### Cross-Complaint Outputs

- New-complaint alerts.
- Complaint relationship scores.
- Shared account identification.
- Estimated money distribution across complaints.
- Network visualizations.
- Time-pattern analysis.
- Combined investigation reports.
- Consolidated bank-wise requests.

The scoring weights and relationship thresholds are maintained in:

```text
tracenet/linking.py
```

## 10. Freeze-First Prioritization

TraceNet generates a prioritized list of accounts requiring investigation.

The prioritization considers:

1. Suspected money still available in an account.
2. Mule-account risk score.
3. Fraud-ring membership.
4. Transaction-flow relationships.

The purpose is to help investigators focus on potentially recoverable funds before they move further through the financial network.

TraceNet generates recommendations and supporting information. Actual account freezing and lien execution remain decisions and actions of authorized investigators and banks.

## 11. Additional Investigation Capabilities

### Rounds Mode

Simulates investigation as bank statements arrive in successive rounds.

It identifies unknown accounts, organizes requests by bank, and supports further investigation as additional information becomes available.

### Watchlist Export

Exports high-risk accounts with their risk explanations and suspected fraud-ring identifiers.

### Pre-Payment Check

The `precheck` functionality provides HIGH, MEDIUM, or LOW risk indications using available information about the receiving account before a payment.

This is currently an application-level capability; integration with banking applications or payment systems is not included.

### Lien-File Generation

Generates bank-specific CSV files containing account information intended to support the investigation and referral process.

### Complaint Desk

The complaint interface supports:

- Manual complaint entry.
- Complaint search.
- Bank, date, amount, and status filters.
- Complaint-level investigation.
- Investigation notes.
- Status tracking.

Available statuses include:

- New.
- Investigation ongoing.
- Money frozen.
- Closed.

The application also supports searching using complaint identifiers, victim information, account numbers, and related case information where those fields are available in the imported data.

## 12. Supported Input Data

TraceNet supports different types of financial records.

| Input | Information | Important fields |
|---|---|---|
| Transaction table | Multiple accounts and payments | Date/time, source account, destination account, amount |
| Bank statement | Individual account activity | Date, narration, debit, credit |
| Complaint records | Fraud complaint information | Victim account, fraud amount, fraud date/time |
| Account/KYC records | Account and infrastructure information | Account number, bank, phone, device ID, IP, opening date |

Optional transaction fields include:

- Transaction ID.
- UTR.
- Payment mode.

The application attempts to map equivalent column names automatically.

For blank or unsupported bank formats, investigators can use the available templates and map their data into the supported structure.

### Input Limitations

- Scanned or image-only PDFs are not supported by the current text-based PDF importer.
- Some bank statements identify counterparties only through names or UPI identifiers.
- Incomplete timestamps can make transaction ordering within the same day uncertain.
- The quality of results depends on the completeness and accuracy of supplied records.

## 13. Demo Data and Benchmark Results

The repository includes synthetic datasets and sample bank files for demonstration.

The benchmark described in the project documentation uses:

- 14 complaints.
- Four simulated laundering styles.
- 36 planted mule accounts.
- 600 normal accounts in a separate pre-payment risk test.

### Reported Synthetic Benchmark Results

| Metric | Reported result |
|---|---:|
| Mule detection precision | 100% |
| Mule detection recall | 94% |
| Mule detection F1-score | 0.97 |
| Planted mule accounts detected | 34 / 36 |
| Cross-complaint planted cases recovered | 4 / 4 |
| Incorrect cross-complaint links in that demo | 0 |

The reported mule detection results use a score threshold of 40.

### Golden-Hour Simulation

The synthetic benchmark reports the following recoverable share when tracing begins at different times:

| Investigation delay | Simulated recoverable share |
|---|---:|
| 15 minutes | 100% |
| 1 hour | 53% |
| 3 hours | 3% |

These results illustrate how delays can affect the availability of funds in the simulated transaction network.

**Important:** All these figures are based on synthetic data and controlled demonstrations. They are not real-world detection rates, recovery guarantees, or validated operational performance. Actual results would depend on real banking data, data quality, bank response times, and operational conditions.

## 14. Running the Demo and Tests

The repository includes:

```text
generate_data.py
make_sample_files.py
run_demo.py
```

### Run the Demo

Activate your virtual environment and install dependencies:

```bash
pip install -r requirements.txt
```

Launch the application:

```bash
streamlit run app.py
```

Use the demo-data option inside the application to explore the investigation workflow.

### Run the Demo Test

```bash
python run_demo.py --test
```

The packaged synthetic test reports detection of 34 out of 36 planted mule accounts in the documented run.

Test results can vary if datasets, parameters, or code are modified.

## 15. Repository Structure

```text
TraceNet/
│
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── .streamlit/
│   └── config.toml
│
├── tracenet/
│   ├── __init__.py
│   ├── engine.py
│   ├── importer.py
│   ├── linking.py
│   ├── explain.py
│   ├── viz.py
│   ├── report.py
│   ├── summary.py
│   ├── templates.py
│   ├── notes.py
│   ├── theme.py
│   └── i18n.py
│
├── assets/
│   ├── rounds.png
│   ├── trail.png
│   └── stats.json
│
├── data/
│   ├── transactions.csv
│   ├── accounts.csv
│   ├── complaints.csv
│   └── ground_truth.csv
│
├── sample_bank_files/
│   ├── 1_transactions_all_banks.xlsx
│   ├── 2_complaints_NCRP.xlsx
│   ├── 3_statement_5010000001_HDFC.csv
│   ├── 4_statement_5010000002_SBI.pdf
│   └── 5_accounts_KYC_device.xlsx
│
├── generate_data.py
├── make_sample_files.py
├── run_demo.py
├── START_TraceNet.bat
└── start.sh
```

The `data/` and `sample_bank_files/` directories contain demonstration datasets. They should contain synthetic or otherwise approved data only.

## 16. Real-World Context

Cyber-fraud investigations often involve rapid transfers across multiple accounts, multiple banks, and different payment channels.

The effectiveness of fund recovery can depend on how quickly investigators identify the next account in the transaction chain and communicate with the relevant financial institution.

TraceNet is designed around this operational challenge by combining transaction tracing, account prioritization, cross-complaint intelligence, and bank-wise reporting.

The Indian Suspect Registry and international initiatives such as Singapore's COSMIC demonstrate the importance of sharing financial-crime intelligence across institutions.

TraceNet explores related capabilities through watchlist exports, entity linking, and investigation reports. These are prototype-level capabilities and do not represent direct integration with those systems.

## 17. Assumptions and Limitations

TraceNet is an investigative decision-support prototype.

The following assumptions and limitations are important:

1. **Bank response:** Further transaction details may depend on information supplied by banks through authorized channels. TraceNet cannot independently obtain unavailable banking records.
2. **Infrastructure data:** Fraud-ring detection is stronger when reliable device, phone, and IP information is available.
3. **Incomplete records:** Missing timestamps, transaction identifiers, or counterparty information can reduce tracing accuracy.
4. **Mixed funds:** The current conservative attribution convention can overestimate the amount of stolen funds in some mixed-fund scenarios.
5. **Cash-out:** Once funds leave the traceable financial network, recovery may become more difficult.
6. **Scanned documents:** Image-only PDF statements require OCR or another preprocessing step and are not supported by the current importer.
7. **Bank integration:** The current prototype does not provide direct live bank API integration or execute account freezes.
8. **Decision authority:** Risk scores and reports are investigative leads, not legal proof of wrongdoing.

## 18. Security and Data Handling

Financial investigation records can contain highly sensitive personal and financial information.

For demonstrations:

- Use synthetic sample datasets.
- Never commit real complainant information or confidential banking records.
- Never publish passwords, API keys, or access credentials.
- Keep `.env` files and local configuration secrets outside version control.
- Restrict access to any deployment that processes real financial information.
- Apply appropriate access controls, audit logging, retention policies, and encryption before any operational deployment.

The current project is a local application prototype. Its data-handling and access-control model must be strengthened before deployment with real investigation records.

## 19. Future Scope

Potential improvements include:

- Secure integration with authorized banking and cybercrime data channels.
- OCR support for scanned bank statements.
- Real-time transaction monitoring where authorized data feeds are available.
- More advanced graph-based anomaly detection.
- Improved multilingual investigation reports.
- Role-based investigator access and audit trails.
- Secure centralized case management.
- Integration with authorized watchlist and intelligence-sharing systems.
- Further validation using appropriately anonymized real-world datasets.

These are proposed extensions, not claims of existing functionality.

## 20. Project Objective

TraceNet aims to reduce the time and manual effort required to understand complex money trails in cyber-fraud investigations.

By bringing together time-aware fund tracing, explainable mule detection, fraud-ring discovery, cross-complaint analysis, and prioritized investigation outputs, it provides investigators with a structured starting point for following stolen money and identifying accounts that may require urgent attention.

**Trace the money. Connect the cases. Prioritize the action.**

---

**Team ALTER**  
Rajasthan Police Hackathon 2026  
PS05 – Financial Crime Infrastructure & Money-Trail Analysis