"""Makes made-up 'bank-style' files in sample_bank_files/ so you can practise uploading.
Run:  python make_sample_files.py"""
import os, random
import pandas as pd
from openpyxl import Workbook

random.seed(7)
OUT = "sample_bank_files"; os.makedirs(OUT, exist_ok=True)
V, M1, M2, M3, M4 = "9000111122", "5010000001", "5010000002", "5010000003", "5010000004"
V2, V3, V4, M5, M9 = "9000222233", "9000333344", "9000444455", "5010000005", "7000000009"
T = lambda hm, day=10: pd.Timestamp(f"2026-11-{day} {hm}")
case = [  # utr, time, from, to, amount, mode, narration-style
    ("412300000001", T("10:15"), V,  M1, 150000, "UPI"),
    ("412300000002", T("10:32"), M1, M2, 90000, "IMPS"),
    ("412300000003", T("10:35"), M1, M3, 58000, "IMPS"),
    ("412300000004", T("10:50"), M2, "ATM CASH WITHDRAWAL", 40000, "ATM"),
    ("412300000005", T("11:05"), M2, M4, 49500, "IMPS"),
    ("412300000006", T("11:20"), M3, "PAYTM WALLET", 57000, "UPI"),
    ("412300000007", T("09:10"), V, "SHARMA GROCERY", 2000, "UPI"),            # victim's normal payment
    # complaint 2 (same day): reuses Mule 1 and Mule 2 and the ATM
    ("412300000011", T("11:02"), V2, M1, 80000, "UPI"),
    ("412300000012", T("11:20"), M1, M2, 78000, "IMPS"),
    ("412300000013", T("11:40"), M2, "ATM CASH WITHDRAWAL", 78000, "ATM"),
    # complaint 3 (two days later): a NEW mule, but it pays Mule 3 and the same wallet
    ("412300000021", T("23:30", 12), V3, M5, 45000, "UPI"),
    ("412300000022", T("23:50", 12), M5, M3, 44000, "IMPS"),
    ("412300000023", T("00:10", 13), M3, "PAYTM WALLET", 44000, "UPI"),
    # complaint 4: unrelated gang
    ("412300000031", T("15:00", 11), V4, M9, 30000, "UPI"),
    ("412300000032", T("15:20", 11), M9, "ATM CASH WITHDRAWAL", 30000, "ATM"),
]
noise = []
for i in range(40):
    a, b = random.sample([f"60{random.randint(10000000,99999999)}" for _ in range(12)], 2)
    noise.append((f"4123{i+100:08d}", T("09:00") + pd.Timedelta(minutes=random.randint(0, 600)), a, b, random.randint(200, 9000), "UPI"))
rows = case + noise
rows.sort(key=lambda r: r[1])

# 1. one big transaction sheet (title lines on top, banks' own column names)
wb = Workbook(); ws = wb.active; ws.title = "Txn Report"
ws.append(["Consolidated transaction report - Cyber Cell Jaipur"]); ws.append(["Generated 11-Nov-2026"]); ws.append([])
ws.append(["UTR No", "Txn Date & Time", "Remitter A/c", "Beneficiary A/c", "Amount (INR)", "Mode"])
for r in rows: ws.append([r[0], r[1].strftime("%d/%m/%Y %H:%M"), r[2], r[3], f"{r[4]:,.2f}", r[5]])
wb.save(f"{OUT}/1_transactions_all_banks.xlsx")

# 2. complaints (NCRP-style)
pd.DataFrame([
    {"Acknowledgement No": "31511260012345", "Complainant Name": "Rajesh Verma", "Complainant Mobile": "98290 11223", "Victim Account No": V, "Amount Lost (Rs)": "1,50,000", "Date of Fraud": "10/11/2026 10:15",
     "Complaint Date": "10/11/2026 14:30", "Transaction ID": "412300000001"},
    {"Acknowledgement No": "31511260012399", "Complainant Name": "Sunita Devi", "Complainant Mobile": "94140 55671", "Victim Account No": V2, "Amount Lost (Rs)": "80,000", "Date of Fraud": "10/11/2026 11:02",
     "Complaint Date": "10/11/2026 12:10", "Transaction ID": "412300000011"},
    {"Acknowledgement No": "31511260013011", "Complainant Name": "Kamal Soni", "Complainant Mobile": "98870 33456", "Victim Account No": V4, "Amount Lost (Rs)": "30,000", "Date of Fraud": "11/11/2026 15:00",
     "Complaint Date": "11/11/2026 16:00", "Transaction ID": "412300000031"},
    {"Acknowledgement No": "31511260014450", "Complainant Name": "Arun Saini", "Complainant Mobile": "70140 88902", "Victim Account No": V3, "Amount Lost (Rs)": "45,000", "Date of Fraud": "12/11/2026 23:30",
     "Complaint Date": "13/11/2026 09:15", "Transaction ID": "412300000021"}]
             ).to_excel(f"{OUT}/2_complaints_NCRP.xlsx", index=False)

# 3. a bank statement (CSV, Dr/Cr columns, details above the table) - Mule 1, HDFC
nm = {V2: "SUNITA DEVI", V3: "ARUN SAINI", M5: "PRIYA TRADERS", V: "RAJESH VERMA", M1: "MOHIT TRADERS", M2: "ANIL SERVICES", M3: "KAVITA ENT", M4: "DEEPAK KUMAR"}
def narr(r, owner):
    utr, t, s, d, a, mode = r
    other = d if s == owner else s
    if mode == "ATM": return "ATM WDL/ATM ID S1ABC123/JAIPUR"
    if mode == "UPI" and not str(other).isdigit(): return f"UPI-{other}-paytm@paytm-PYTM0123456-{utr}-UPI"
    return f"IMPS-{utr}-{nm.get(other, 'CUSTOMER')}-BANK-{other}-REF"
def statement(owner):
    bal, out = 1000.0, []
    for r in rows:
        if owner in (r[2], r[3]):
            dr = r[4] if r[2] == owner else ""; cr = r[4] if r[3] == owner else ""
            bal += (cr or 0) - (dr or 0)
            out.append([r[1].strftime("%d/%m/%Y"), r[1].strftime("%H:%M"), narr(r, owner), r[0], dr, cr, f"{bal:,.2f}"])
    return out
cols = ["Date", "Time", "Narration", "Chq./Ref.No.", "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"]
with open(f"{OUT}/3_statement_{M1}_HDFC.csv", "w", encoding="utf-8") as f:
    f.write("HDFC BANK LTD\nAccount Statement\nAccount No : %s\nAccount Holder : MOHIT TRADERS\n\n" % M1)
    pd.DataFrame(statement(M1), columns=cols).to_csv(f, index=False)

# 4. the same kind of statement as a PDF - Mule 2, SBI
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
doc = SimpleDocTemplate(f"{OUT}/4_statement_{M2}_SBI.pdf", pagesize=landscape(A4)); st = getSampleStyleSheet()
data = [cols] + [[Paragraph(str(c), st["BodyText"]) if i == 2 else c for i, c in enumerate(r)] for r in statement(M2)]
tb = Table(data, repeatRows=1); tb.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .5, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 8)]))
doc.build([Paragraph("STATE BANK OF INDIA - Statement of Account", st["Title"]), Paragraph(f"Account No: {M2}", st["BodyText"]), Spacer(1, 12), tb])

# 5. KYC / device list (optional file)
pd.DataFrame([{"Account Number": a, "Bank Name": b, "Account Opening Date": d, "Mobile No": p, "Device ID": dev, "IP Address": ip}
              for a, b, d, p, dev, ip in [(M1, "HDFC", "02/10/2026", "9811100001", "DEVX1", "10.1.1.9"), (M2, "SBI", "05/10/2026", "9811100002", "DEVX1", "10.1.1.9"),
                                          (M3, "PNB", "07/10/2026", "9811100003", "DEVX1", "10.1.1.7"), (M4, "Axis", "01/10/2026", "9811100004", "DEVX4", "10.1.1.7"), (M5, "Axis", "09/11/2026", "9811100005", "DEVX1", "10.1.1.9")]]
             ).to_excel(f"{OUT}/5_accounts_KYC_device.xlsx", index=False)
print("done:", sorted(os.listdir(OUT)))
