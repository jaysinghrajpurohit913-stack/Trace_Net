"""Downloadable case files: one Excel workbook and one PDF for the chosen complaints (or all).

Both are built from the same `Analysis` object and list the evidence references (UTR:..., DOM:..., LOG:...) so every
statement can be traced back to its source row. English only (these go to banks / courts)."""
from __future__ import annotations

import io
from xml.sax.saxutils import escape

import pandas as pd

from .engine import pretty
from .intel.evidence import evidence_table
from .intel.requests import drafts_for
from .linking import group_bank_file

DISCLAIMER = ("Leads for investigators, not proof. Based only on the data supplied. IP geolocation and hosting details are indicative; "
              "shared, mobile (CGNAT) and VPN addresses cannot identify a person. Subscriber, login and other non-public records must be "
              "obtained only through the applicable lawful process. TraceNet performs passive public lookups only and does not probe any server.")


def _cids(an, cids):
    return list(cids) if cids else an.ds.comp.complaint_id.tolist()


def _flat(df):
    """Excel-safe copy: lists -> text, timezone-free datetimes."""
    d = df.copy()
    for c in d.columns:
        if d[c].map(lambda v: isinstance(v, (list, tuple, set, dict))).any():
            d[c] = d[c].map(lambda v: "; ".join(map(str, v)) if isinstance(v, (list, tuple, set)) else str(v))
    return d


def sheets(an, cids=None) -> dict:
    cids = _cids(an, cids)
    t = an.table[an.table.complaint_id.isin(cids)]
    out = {"Complaints": _flat(t.drop(columns=["blob", "mules"], errors="ignore"))}
    suspects = an.feats[an.feats.mule_score >= 40].sort_values("mule_score", ascending=False)
    touched = {a for c in cids for a in an.lk.touched[c]}
    s = suspects[suspects.index.isin(touched)]
    out["Suspected mules"] = s[["bank", "mule_score", "reasons"]].reset_index().rename(columns={"index": "account_id"})
    groups = sorted({an.lk.group_of[c] for c in cids if not an.lk.group_of[c].startswith("SINGLE")})
    bank = [group_bank_file(an.lk, g).assign(case=g) for g in groups]
    out["Bank actions"] = pd.concat(bank, ignore_index=True) if bank else pd.DataFrame(columns=["bank", "account_id", "action"])
    if len(an.lk.shared):
        out["Shared accounts"] = an.lk.shared[an.lk.shared.account.isin(touched)].drop(columns=["first_use", "last_use"], errors="ignore")
    if len(an.intel.domains):
        out["Domains"] = _flat(an.flags)
        out["IPs"] = an.intel.ips
    if len(an.corr):
        out["IP log vs transactions"] = an.corr
    if len(an.dpairs):
        out["Digital links"] = an.dpairs[an.dpairs.a.isin(cids) | an.dpairs.b.isin(cids)]
    d = drafts_for(an.intel, an.intel.ips, an.corr, cids)
    if d:
        out["Provider requests"] = pd.DataFrame([dict(type=x["kind"], to=x["to"], about=x["subject"], draft=x["text"]) for x in d])
    out["Evidence references"] = evidence_table(an.ds, an.intel, cids)
    out["Read me"] = pd.DataFrame({"note": [DISCLAIMER]})
    return out


def excel_bytes(an, cids=None) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, df in sheets(an, cids).items():
            d = _flat(df)
            for c in d.columns:
                if str(d[c].dtype).startswith("datetime"):
                    d[c] = d[c].dt.strftime("%Y-%m-%d %H:%M")
            d.to_excel(xw, sheet_name=name[:31], index=False)
            ws = xw.sheets[name[:31]]
            for i, c in enumerate(d.columns, 1):
                ws.column_dimensions[ws.cell(1, i).column_letter].width = min(max(12, int(d[c].astype(str).str.len().quantile(.9) if len(d) else 12) + 2), 60)
            ws.freeze_panes = "A2"
    return buf.getvalue()


def pdf_bytes(an, cids=None, title="TraceNet Case Workspace Report") -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    cids = _cids(an, cids)
    ss = getSampleStyleSheet()
    H1, H2, B = ss["Title"], ss["Heading2"], ParagraphStyle("b", parent=ss["BodyText"], fontSize=9, leading=12)
    small = ParagraphStyle("s", parent=B, fontSize=7.5, leading=9)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=14 * mm, rightMargin=14 * mm, topMargin=12 * mm, bottomMargin=12 * mm, title=title)

    def table(df, widths=None, max_rows=40):
        d = _flat(df).head(max_rows).copy()
        for c in d.columns:
            if str(d[c].dtype).startswith("datetime"):
                d[c] = d[c].dt.strftime("%d %b %H:%M")
        fmt = lambda v: f"{v:,.0f}" if isinstance(v, float) and abs(v) >= 100 else (f"{v:.1f}" if isinstance(v, float) else str(v))
        rows = [[Paragraph(f"<b>{escape(str(c))}</b>", small) for c in d.columns]] + [[Paragraph(escape(fmt(v))[:220], small) for v in r] for r in d.itertuples(index=False)]
        t = Table(rows, repeatRows=1, colWidths=widths)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dcf5ee")), ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#b8cfc9")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return t

    tb = an.table[an.table.complaint_id.isin(cids)]
    S = [Paragraph(escape(title), H1), Paragraph(f"Complaints covered: {len(cids)} &nbsp;|&nbsp; Total reported loss: Rs {tb.amount.sum():,.0f} &nbsp;|&nbsp; "
                                              f"Still inside accounts: Rs {tb.inside.sum():,.0f} &nbsp;|&nbsp; Already cashed out: Rs {tb.cashed.sum():,.0f}", B), Spacer(1, 4),
         Paragraph(escape(DISCLAIMER), small), Spacer(1, 8), Paragraph("1. Complaints", H2),
         table(tb[["complaint_id", "victim_name", "victim_phone", "fraud_ts", "reported_ts", "amount", "case", "inside", "cashed"]])]
    sus = an.feats[(an.feats.mule_score >= 40) & an.feats.index.isin({a for c in cids for a in an.lk.touched[c]})].sort_values("mule_score", ascending=False)
    S += [Paragraph("2. Suspected mule accounts (why each was flagged)", H2),
          table(sus[["bank", "mule_score", "reasons"]].reset_index().rename(columns={"index": "account"}), [35 * mm, 25 * mm, 18 * mm, 170 * mm])]
    groups = sorted({an.lk.group_of[c] for c in cids if not an.lk.group_of[c].startswith("SINGLE")})
    if groups:
        S.append(Paragraph("3. Gang cases (complaints joined by shared accounts, cash-out points and digital evidence)", H2))
        for g in groups:
            gg = next(x for x in an.lk.groups if x["id"] == g)
            S.append(Paragraph(f"<b>{g}</b>: {', '.join(gg['complaints'])} — loss Rs {gg['lost']:,.0f}; still inside Rs {gg['inside']:,.0f}; cash-out points: {len(gg['exits'])}", B))
    if len(an.intel.domains):
        S += [PageBreak(), Paragraph("4. Domains and hosting (public / supplied data)", H2),
              table(an.flags[["domain", "ip", "registrar", "created", "hosting", "complaint_id", "flags"]], [48 * mm, 28 * mm, 35 * mm, 20 * mm, 32 * mm, 22 * mm, 80 * mm])]
    if len(an.corr):
        S += [Paragraph("5. IP-log events matched to bank transactions (IP-log time converted from UTC to IST)", H2),
              table(an.corr[["when_local", "ip", "event", "account_id", "txn_id", "gap_min", "class", "caveat"]])]
    if len(an.dpairs):
        S += [Paragraph("6. Complaints connected through shared digital evidence", H2), table(an.dpairs, [22 * mm, 22 * mm, 14 * mm, 14 * mm, 55 * mm, 140 * mm])]
    ev = evidence_table(an.ds, an.intel, cids)
    S += [PageBreak(), Paragraph("7. Evidence references", H2), table(ev, [45 * mm, 32 * mm, 110 * mm, 30 * mm, 50 * mm], max_rows=120)]
    doc.build(S)
    return buf.getvalue()
