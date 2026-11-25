"""A blank Excel template (with example rows) the user can fill and upload."""
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill


def template_xlsx() -> bytes:
    wb = Workbook()
    ws = wb.active; ws.title = "READ ME"
    for line in [
        "TraceNet data template / TraceNet डेटा टेम्पलेट",
        "",
        "Fill the sheets 'Transactions' and 'Complaints'. 'Accounts', 'Domains' and 'IP log' are optional (digital evidence).",
        "'Transactions' और 'Complaints' शीट भरें। 'Accounts' ज़रूरी नहीं है।",
        "",
        "Delete the example rows first. One row = one payment. Account numbers as text, no spaces.",
        "पहले उदाहरण वाली पंक्तियाँ मिटाएँ। एक पंक्ति = एक भुगतान। खाता नंबर बिना खाली जगह के।",
        "Cash taken out: put ATM, WALLET or CRYPTO in 'Paid to' (or in 'Mode').",
        "नकद निकासी: 'Paid to' (या 'Mode') में ATM, WALLET या CRYPTO लिखें।",
        "Your bank's own column names also work. Use this template only if the bank gave no usable file.",
        "बैंक के अपने कॉलम नाम भी चलते हैं। यह टेम्पलेट तभी लें जब बैंक की फाइल इस्तेमाल लायक न हो।",
    ]:
        ws.append([line])
    ws["A1"].font = Font(bold=True, size=13); ws.column_dimensions["A"].width = 110

    def sheet(name, head, rows):
        s = wb.create_sheet(name); s.append(head)
        for c in s[1]:
            c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="0B1F3A")
        for r in rows: s.append(r)
        for i in range(len(head)): s.column_dimensions[chr(65 + i)].width = 26
    sheet("Transactions", ["Transaction ID", "Date and Time", "Paid from (account)", "Paid to (account)", "Amount (Rs)", "Mode"],
          [["412300000001", "10/11/2026 10:15", "9000111122", "5010000001", 150000, "UPI"],
           ["412300000002", "10/11/2026 10:32", "5010000001", "5010000002", 90000, "IMPS"],
           ["412300000003", "10/11/2026 10:50", "5010000002", "ATM", 40000, "ATM"]])
    sheet("Complaints", ["Complaint ID", "Victim Account", "Amount Lost (Rs)", "Date of Fraud", "Complaint Date", "Transaction ID"],
          [["NCRP-001", "9000111122", 150000, "10/11/2026 10:15", "10/11/2026 14:30", "412300000001"]])
    sheet("Accounts", ["Account Number", "Bank", "Account Opening Date", "Mobile No", "Device ID", "IP Address"],
          [["5010000001", "HDFC", "02/10/2026", "9811100001", "DEV1", "10.1.1.9"]])
    sheet("Domains", ["Domain", "IP Address", "Registrar", "Created", "Expires", "Name Servers", "Hosting Provider", "ASN", "Country", "First Seen", "Complaint ID"],
          [["secure-kyc-update.example", "203.0.113.10", "Example Registrar", "20/09/2026", "20/12/2026", "ns1.example, ns2.example", "EXAMPLE-HOST", "AS64500", "NL", "03/10/2026 22:40", "NCRP-001"]])
    sheet("IP log", ["Timestamp", "IP Address", "Event", "Account", "Mobile", "Source"],
          [["2026-10-04T08:12:00Z", "203.0.113.77", "net_banking_login", "5010000001", "", "Bank access log (UTC)"]])
    buf = io.BytesIO(); wb.save(buf); return buf.getvalue()
