# TraceNet — Money-Trail Intelligence for Cyber-Fraud Investigators
Team **ALTER** · Rajasthan Police Hackathon 2026 · **PS05 – Financial Crime Infrastructure & Money-Trail Analysis**

TraceNet follows stolen money hop-by-hop through a transaction graph, scores mule accounts,
links accounts that share devices/phones/IPs into fraud rings, and gives investigators a
**freeze-first list** plus an auto-generated trail report.

## Use it (3 steps)  ·  इस्तेमाल (3 कदम)
**Start:** double-click `START_TraceNet.bat` (Windows) or run `bash start.sh` (Mac/Linux). The first time it installs what it needs; after that it opens in your browser.
**शुरू करें:** `START_TraceNet.bat` पर डबल-क्लिक करें (Windows) या `bash start.sh` चलाएँ। पहली बार ज़रूरी चीज़ें अपने आप इंस्टॉल होती हैं; फिर ब्राउज़र में खुल जाता है।

1. **Add data / डेटा डालें** – drop the files from the banks (Excel, CSV, or text-PDF). TraceNet guesses what each file is and which column is which. Fix only what is wrong. No complaint file? Type the complaint in by hand.
2. **Check / जाँचें** – see how many payments, accounts and complaints were read, and any warnings in plain words. Optionally join a name or UPI id to an account number.
3. **Result / नतीजा** – a numbered "what to do now" list, the money-trail picture, who to freeze first, the gang, ready-made requests for each bank, and a report.

Want to practise first? Click **Try with demo data**, or upload the files in `sample_bank_files/` (they look like real bank files).

## Reading the pictures  ·  चित्र कैसे पढ़ें
Every picture has **one line above it** (what it shows) and **an action box below it** (what to do next). The money-trail picture runs left to right: victim ★ → Step 1 → Step 2 → … → cash-out. The **number in each circle** is the order in which accounts received the money, and the **colour** says what is true now: orange = money still inside (freeze it), grey = passed on, red diamond = cash-out, white `?` = bank has not replied. Each number is explained in plain words under the picture. Pictures show account numbers shortened (…4321) with the bank name; the tables and the 'What to do now' steps use the full number, so use those for letters to banks. A glossary (mule, freeze/lien, step, gang ring, golden hour, KYC, UTR…) is at the top of the result page.

## Connections between complaints  ·  शिकायतों के बीच जुड़ाव
In step 3 switch to **"Connections between complaints"**. TraceNet follows all complaints together on one shared ledger (so an account holding money from two victims is split fairly, nothing counted twice) and gives every pair of complaints a soft score:
same account (more points for mule-like ones) · same cash-out point · same gang ring (phone/device/IP) · a victim's account used to pass on another's money · frauds close in time.
Strong/Probable links join complaints into a **CASE group**. You get: a **new-complaint alert** (is today's complaint linked to earlier ones, and what is still inside the shared accounts), a **network picture**, **shared accounts + money split**, **time pattern** (speed to cash-out, night-time, gap between complaints, new accounts per day), and a **combined report + one bank file** for the whole case.
On the demo data it recovers the 4 planted cases exactly (14 complaints, no wrong links). Weights live in `tracenet/linking.py` (`STRONG`, `PROBABLE`, `POSSIBLE`).

## What data can I feed in?  ·  कौन-सा डेटा चलेगा?
Any of these, mixed together, in Excel / CSV / text-PDF (not scanned pictures):

| File | What it has | Needed columns (any name that means the same) |
|---|---|---|
| **Transaction table** | one row per payment, many accounts | date-time, paid-from account, paid-to account, amount (optional: transaction id/UTR, mode) |
| **Bank statement** | one account's passbook | date, narration/details, debit and credit (or amount + Dr/Cr). You tell it whose account it is |
| **Complaints (NCRP)** | one row per complaint | victim account, amount, date-time of fraud (optional: complaint id, reported time, transaction id of the victim's payment) |
| **Account details** (optional) | KYC / device info | account number (optional: bank, mobile, device id, IP, account opening date) |

Cash taken out is recognised from the words ATM, CASH WITHDRAWAL, WALLET / PAYTM / MOBIKWIK, crypto exchange names, in the mode or the "paid to" / narration.
If you have nothing usable from the bank, download the blank Excel template inside the app and paste the data in. The exact internal format is in "Plugging in real data" below.

**Honest limits:** scanned/photo PDFs cannot be read (ask the bank for Excel/CSV). In a statement the other side is often only a name or UPI id; use the "join names" box in step 2 to tie it to an account number. If the data has only dates and no time, the order of payments inside one day is a best guess (the app warns you).

## What it does
| Module | File | What |
|---|---|---|
| Time-aware tracing | `tracenet/engine.py::trace_funds` | Taint accounting: a transfer can only carry tainted money the sender already holds, after it arrived. Avoids false trails of plain graph traversal. |
| Mule scoring | `engine.py::score_mules` | Explainable rules (rapid pass-through, fan-in/out, new account, cycles, structuring, shared IDs) blended 70/30 with an Isolation Forest anomaly score. |
| Entity linking | `engine.py::link_entities` | Union of accounts sharing device / phone / IP → fraud rings. |
| Freeze-first list | `engine.py::freeze_list` | Money still inside an account ranks first (recoverable), then mule score and ring membership. |
| Report | `tracenet/report.py` | Chronological trail, actions, reasons, linked network. |
| Rounds mode | `engine.py::trace_in_rounds` | Simulates statements arriving bank by bank; lists unknown accounts grouped by bank and drafts one request per bank (`report.py::bank_requests`). |
| Fallback linking | `engine.py::link_by_flow` | Groups suspicious accounts that share beneficiaries when device/phone/IP data is missing. |
| Watchlist export | `engine.py::export_watchlist` | Shareable list of high-risk accounts with reasons and ring ids (Suspect Registry / COSMIC idea, deeper layers). |
| Pre-payment check | `engine.py::precheck` | HIGH/MEDIUM/LOW warning for a receiving account using only pre-payment information (confirmation-of-payee idea). |
| Lien file | `engine.py::lien_file` | Per-bank CSV of accounts to act on (FinCEN-style complete, fast referral). |
| Dashboard | `app.py` | "Investigate as of" slider shows the golden-hour effect. |

## Results on the synthetic benchmark (14 complaints, 4 laundering styles)
- Mule detection: precision 100%, recall 94%, F1 0.97 (34/36 planted mules at score ≥ 40)
- Recoverable share of stolen money if traced at 15 min / 1 h / 3 h: **100% / 53% / 3%**
- Honest caveat: synthetic data is easier than real data; real-bank tuning is future work.

## Plugging in real data
Use the app (step 1). Internally everything becomes three tables:
`transactions` (`txn_id, ts, src, dst, amount, channel`), `accounts` (`account_id, bank, kyc_age_days, device_id, phone, ip`) and
`complaints` (`complaint_id, victim_account, amount, fraud_ts, reported_ts, seed_ids`). Cash-out points are accounts named `CASHOUT:<ATM|WALLET|CRYPTO|CASH>:<detail>`.

## Real-world context (why this matters)
- India, FY2023-24 to 2025-26: Rs 56,087 cr reported on NCRP, Rs 9,079 cr lien-marked (~16%), Rs 206 cr refunded (MHA/PIB).
- Rajasthan 2025: Rs 768.7 cr lost, Rs 179.15 cr frozen (~23%), 1.28 lakh complaints.
- Practitioners put the real golden hour at about 60 minutes; the Suspect Registry shares Layer 1 mule accounts, TraceNet follows funds beyond Layer 1.
- Prototype numbers above are from synthetic data, not real bank data.

## Assumptions (stated openly)
1. Banks reply with next-hop details (e.g. via CFCFRMS); reply time is outside TraceNet's control.
2. Without device/phone/IP data, rings fall back to shared beneficiaries.
3. Mixed funds: money leaving an account after stolen money arrives is counted as stolen first, until the stolen balance is used up. This is a conservative convention (it may over-flag small later payments), so output is investigative evidence, not proof.
4. TraceNet recommends; investigators and banks decide and act. It cannot undo cash-out.

## Adopted from global practice (and honest limits)
| Practice (where) | In TraceNet | Status |
|---|---|---|
| Cross-bank intelligence sharing (India Suspect Registry, Singapore COSMIC) | Watchlist export with reasons | Built; needs a bank/legal channel |
| Pre-payment warnings (Australia/UK confirmation of payee) | `precheck` risk levels | Built as a function; needs bank app integration |
| Fast, complete referral (US FinCEN Rapid Response Program) | Per-bank requests, lien file, golden-hour clock | Built |
| Network analytics, behaviour patterns (bank vendors, MuleHunter.AI) | Ring linking, rules + anomaly | Built |
| Mandatory reimbursement, crypto forensics, graph neural nets | Not adopted | Out of scope for this stage |

Test on synthetic data: with no watchlist, 9 of 14 first-hop mules get MEDIUM and 5 stay LOW (the ring without shared devices is hardest); 0 of 600 normal accounts were flagged. With a watchlist built from the same trails all 14 are HIGH, but that is hindsight and only helps if the gang reuses accounts.

## Finding a complaint (new)
Step 3 now opens on **All complaints**: one row per complaint (victim, phone, when it happened, when it was filed, delay, amount, status, gang case, money still inside / cashed out).
- **Search box**: complaint/acknowledgement no., victim name, phone, UPI id, account number (victim *or* any mule on the trail), bank, CASE-id. Part of a number is enough. The "Matched on" column tells you why a row appeared.
- **Filters**: bank, fraud date, amount, status. Hover the **?** on a column heading for its meaning.
- Click a row, then **Open analysis** → the **Complaint file**: card (who / when / how much / status + note / gang case with buttons to the sibling complaints), then the picture and what-to-do tabs.
- Status (new / investigation ongoing / money frozen / closed) and your note are saved in `case_notes.json` next to the app.
- Victim name / phone / UPI are read from the complaints file if it has such columns (e.g. "Complainant Name", "Complainant Mobile"); otherwise the card says "not in the file".
- The glossary at the top has a search box.

## Look and feel
All styling lives in `tracenet/theme.py` (colours at the top of `CSS`, a few HTML pieces: hero, stepper, KPI cards, chips) and `.streamlit/config.toml`. Change a colour there and the whole app follows. No logic is in that file.
