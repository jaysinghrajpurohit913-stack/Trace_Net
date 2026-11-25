import io
import openpyxl
from tracenet.export import excel_bytes, pdf_bytes
from tracenet.intel.timeline import events_for
from tracenet.pipeline import trail_from_utr


def test_digital_evidence_joins_phishing_cases(an):
    g = an.lk.group_of
    assert g["NCRP-10"] == g["NCRP-20"]           # same phishing server + name servers
    assert g["NCRP-50"].startswith("SINGLE")      # only a weak (VPN / CDN) tie: must NOT be merged


def test_complaint_table_and_search_blob(an):
    t = an.table
    assert {"victim_name", "case", "inside", "cashed", "blob"} <= set(t.columns)
    assert t.blob.str.contains("m1a0").sum() >= 2


def test_utr_start(demo):
    u = demo.tx[demo.tx.src == "VIC10"].txn_id.iloc[0]
    row, trail = trail_from_utr(demo, u)
    assert row.src == "VIC10" and len(trail.edges) > 3
    assert trail_from_utr(demo, "NOPE")[0] is None


def test_timeline_has_all_lanes(an):
    ev = events_for(an, ["NCRP-10", "NCRP-11"])
    assert {"Complaint", "Bank", "Domain / IP", "IP log"} <= set(ev.lane)


def test_exports(an):
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes(an)))
    assert {"Complaints", "Domains", "IP log vs transactions", "Provider requests", "Evidence references"} <= set(wb.sheetnames)
    assert pdf_bytes(an)[:4] == b"%PDF"
