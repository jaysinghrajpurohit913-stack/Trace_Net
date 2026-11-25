"""Importer: turns whatever the bank sent (CSV / Excel / text-PDF, transaction table or
Dr/Cr statement, complaints, KYC list) into the three tables TraceNet works on.

Flow used by the app:
    files = load_file(name, bytes)          # reads the file, guesses its type and columns
    ...user confirms / corrects type + columns + statement owner in the screen...
    ds    = convert(files, manual_complaints)   # -> Dataset(acc, tx, comp, notes)

Nothing here needs the user to know column names: every guess can be changed on screen.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .engine import is_cashout

KINDS = ["transactions", "statement", "complaints", "accounts", "domains", "iplog"]

# ------------------------------------------------------------------ column synonyms ----
# normalised header text (lower case, letters+digits only) -> role.  First = best.
SYN = {
    "transactions": {
        "txn_id":  ["txnid", "transactionid", "transactionreference", "refno", "referenceno", "utr", "utrno", "rrn", "txnref", "id"],
        "ts":      ["timestamp", "txndate", "transactiondate", "datetime", "transactiondatetime", "dateandtime", "date", "txntime", "valuedate"],
        "src":     ["src", "from", "fromaccount", "fromacc", "sender", "senderaccount", "remitter", "remitteraccount", "payer", "payeraccount",
                    "debitaccount", "debitedaccount", "source", "originator", "accountfrom"],
        "dst":     ["dst", "to", "toaccount", "toacc", "receiver", "receiveraccount", "beneficiary", "beneficiaryaccount", "beneficiaryaccountno",
                    "payee", "creditaccount", "creditedaccount", "destination", "accountto"],
        "amount":  ["amount", "amt", "transactionamount", "txnamount", "amountinr", "amountrs", "value"],
        "channel": ["channel", "mode", "paymentmode", "txntype", "transactiontype", "paymentchannel", "method", "instrument", "type"],
    },
    "statement": {
        "date":      ["txndate", "transactiondate", "date", "postingdate", "postdate", "valuedate"],
        "time":      ["time", "txntime", "transactiontime"],
        "narration": ["narration", "description", "particulars", "transactiondetails", "transactionremarks", "txnremarks", "transactiondescription", "remarks", "details"],
        "ref":       ["chqrefno", "refnochqno", "refno", "referenceno", "utr", "utrno", "txnid", "transactionid", "chequeno", "chqno", "instrumentid"],
        "debit":     ["debit", "debitamount", "debits", "withdrawal", "withdrawals", "withdrawalamt", "withdrawalamount", "dr", "drs", "debitamt"],
        "credit":    ["credit", "creditamount", "credits", "deposit", "deposits", "depositamt", "depositamount", "cr", "crs", "creditamt"],
        "amount":    ["amount", "amt", "transactionamount", "txnamount"],
        "drcr":      ["drcr", "crdr", "debitcredit", "creditdebit", "dc", "cd", "txntype", "transactiontype", "type"],
        "balance":   ["balance", "closingbalance", "runningbalance", "availablebalance", "balanceamount"],
    },
    "complaints": {
        "complaint_id":   ["complaintid", "acknowledgementno", "acknowledgementnumber", "acknowledgmentnumber", "ackno", "ackid", "ncrpid", "complaintno",
                           "complaintnumber", "caseid", "caseno", "srno", "sno"],
        "victim_account": ["victimaccount", "victimaccountno", "victimaccountnumber", "victimacc", "complainantaccount", "accountno", "accountnumber",
                           "debitedaccount", "payeraccount", "fromaccount", "account"],
        "amount":         ["amountlost", "fraudamount", "totalfraudamount", "disputedamount", "disputedamt", "amountreported", "lossamount", "amountfraud",
                           "amount", "amountinr", "amountrs"],
        "fraud_ts":       ["frauddate", "fraudtime", "fraudts", "dateoffraud", "incidentdate", "incidentdatetime", "datetimeoftransaction",
                           "transactiondate", "txndate", "datetime", "date"],
        "reported_ts":    ["reporteddate", "reporteddatetime", "reportedon", "reportedts", "complaintdate", "complaintdatetime", "dateofcomplaint", "filedon"],
        "txn_ref":        ["transactionid", "transactionids", "txnid", "utr", "utrno", "utrnumber", "referenceno", "refno", "transactionreference", "txnrefno", "rrn"],
        "first_mule":     ["firstmule", "fraudsteraccount", "suspectaccount", "beneficiaryaccount", "beneficiary", "toaccount", "receiveraccount", "creditedaccount"],
        "bank":           ["victimbank", "bank", "bankname"],
        "victim_name":    ["victimname", "complainantname", "nameofcomplainant", "nameofvictim", "complainant", "victimfullname"],
        "victim_phone":   ["victimphone", "victimmobile", "victimmobileno", "complainantmobile", "complainantphone", "complainantcontact", "victimcontact"],
        "victim_upi":     ["victimupi", "victimupiid", "victimvpa", "complainantupi"],
    },
    "domains": {
        "domain":         ["domain", "domainname", "url", "website", "host", "hostname", "fqdn", "site", "indicator", "ioc", "phishingurl", "scamdomain"],
        "ip":             ["ip", "ipaddress", "resolvedip", "hostingip", "serverip", "aaddress"],
        "registrar":      ["registrar", "registrarname", "reseller"],
        "created":        ["created", "creationdate", "createddate", "registrationdate", "registeredon", "domaincreated", "registered"],
        "expires":        ["expires", "expirydate", "expirationdate", "expiry", "registryexpirydate", "validuntil"],
        "nameservers":    ["nameservers", "nameserver", "ns", "dns"],
        "hosting":        ["hosting", "hostingprovider", "isp", "provider", "organization", "org", "asnorg", "asname", "network"],
        "asn":            ["asn", "asnumber", "autonomoussystem"],
        "country":        ["country", "countrycode", "serverlocation"],
        "ssl_issuer":     ["sslissuer", "certissuer", "issuer", "certificateissuer", "certificateauthority"],
        "ssl_first_seen": ["sslfirstseen", "certificatedate", "certfirstseen", "sslissued", "certificateissued", "certissued"],
        "first_seen":     ["firstseen", "firstobserved", "reportedon", "observedon", "dateseen", "reporteddate"],
        "last_seen":      ["lastseen", "lastobserved"],
        "complaint_id":   ["complaintid", "complaint", "caseid", "ncrp", "acknowledgementno", "linkedcomplaint", "complaintno", "linkedcomplaints"],
        "note":           ["note", "notes", "remarks", "comment", "comments"],
    },
    "iplog": {
        "ts":         ["timestamp", "time", "datetime", "eventtime", "loggedat", "date", "utctime", "accesstime", "logtime"],
        "ip":         ["ip", "ipaddress", "sourceip", "clientip", "loginip", "remoteip", "srcip"],
        "event":      ["event", "action", "activity", "eventtype", "type", "description"],
        "account_id": ["account", "accountid", "accountno", "accountnumber", "customerid", "userid"],
        "phone":      ["phone", "mobile", "mobileno", "msisdn"],
        "upi":        ["upi", "upiid", "vpa"],
        "source":     ["source", "logsource", "system", "provider"],
        "tz":         ["timezone", "tz"],
    },
    "accounts": {
        "account_id":   ["accountid", "accountno", "accountnumber", "acno", "accno", "acct", "account"],
        "bank":         ["bank", "bankname"],
        "kyc_age_days": ["kycagedays", "accountagedays", "accountage", "kycage", "ageindays"],
        "open_date":    ["accountopeningdate", "openingdate", "opendate", "dateofopening", "kycdate", "accountopendate", "openedon"],
        "device_id":    ["deviceid", "device", "imei", "deviceimei", "deviceidentifier"],
        "phone":        ["phone", "mobile", "mobileno", "phoneno", "registeredmobile", "mobilenumber", "contactno"],
        "ip":           ["ip", "ipaddress", "ipaddr", "loginip"],
    },
}
REQUIRED = {
    "transactions": ["ts", "src", "dst", "amount"],
    "statement": ["date", "narration"],           # + (debit & credit) or (amount & drcr)
    "complaints": ["victim_account", "amount"],
    "accounts": ["account_id"],
    "domains": ["domain"],
    "iplog": ["ts", "ip"],
}
_ALL_SYNS = {s for k in SYN.values() for r in k.values() for s in r}


class ImportProblem(Exception):
    """A problem the user can understand and fix. `key` is translated by the app."""
    def __init__(self, key, **params):
        super().__init__(key); self.key, self.params = key, params


def norm(x) -> str:
    return re.sub(r"[^a-z0-9]", "", str(x).lower())


# ------------------------------------------------------------------ reading files ----
def _read_csv(data: bytes) -> pd.DataFrame:
    for enc in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            text = data.decode(enc); break
        except Exception:
            continue
    first = "\n".join(text.splitlines()[:30])
    sep = max([",", ";", "\t", "|"], key=first.count)
    import csv
    rows = list(csv.reader(io.StringIO(text), delimiter=sep))      # csv module: tolerates short lines above the table
    w = max((len(r) for r in rows), default=0)
    return pd.DataFrame([r + [""] * (w - len(r)) for r in rows if any(c.strip() for c in r)])


def _read_pdf(data: bytes) -> pd.DataFrame:
    import pdfplumber
    rows, has_text = [], False
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for pno, page in enumerate(pdf.pages):
            txt = page.extract_text() or ""
            has_text |= bool(txt.strip())
            if pno == 0:                       # bank name / account number sit above the table: keep them
                for ln in txt.splitlines():
                    if sum(norm(w) in _ALL_SYNS for w in ln.split()) >= 3:
                        break
                    rows.append([ln.strip()])
            tables = page.extract_tables()
            for t in tables:
                rows += [[("" if c is None else str(c).replace("\n", " ")) for c in r] for r in t]
            if not tables:
                rows += [re.split(r"\s{2,}", ln.strip()) for ln in txt.splitlines() if ln.strip()]
    if not has_text:
        raise ImportProblem("scanned_pdf")
    w = max(len(r) for r in rows) if rows else 0
    return pd.DataFrame([r + [""] * (w - len(r)) for r in rows])


def read_sheets(name: str, data: bytes) -> dict:
    """-> {sheet_name: raw DataFrame without header}"""
    ext = name.lower().rsplit(".", 1)[-1]
    if ext in ("csv", "txt", "tsv"):
        return {"": _read_csv(data)}
    if ext in ("xlsx", "xlsm", "xls"):
        sheets = pd.read_excel(io.BytesIO(data), sheet_name=None, header=None, dtype=str)
        return {k: v for k, v in sheets.items() if len(v)}
    if ext == "pdf":
        return {"": _read_pdf(data)}
    raise ImportProblem("bad_type", name=name)


# ------------------------------------------------------------------ header + roles ----
def _find_header(raw: pd.DataFrame):
    """Banks put account details above the table. Find the real header row."""
    raw = raw.fillna("").astype(str)
    best, best_hits = 0, -1
    for i in range(min(len(raw), 60)):
        hits = sum(norm(c) in _ALL_SYNS for c in raw.iloc[i])
        if hits > best_hits:
            best, best_hits = i, hits
    top = [" ".join(x for x in raw.iloc[i] if x.strip()) for i in range(best)]
    cols, seen = [], {}
    for c in raw.iloc[best]:
        c = c.strip() or "(blank)"
        seen[c] = seen.get(c, 0) + 1
        cols.append(c if seen[c] == 1 else f"{c} ({seen[c]})")
    df = raw.iloc[best + 1:].copy(); df.columns = cols
    df = df.loc[:, [c for c in df.columns if (df[c].str.strip() != "").any()]]       # drop empty columns
    df = df[(df.apply(lambda r: "".join(r).strip(), axis=1) != "")]                   # drop empty rows
    header_norm = [norm(c) for c in df.columns]                                       # repeated header rows (PDF)
    df = df[~df.apply(lambda r: [norm(v) for v in r][:len(header_norm)] == header_norm, axis=1)]
    return df.reset_index(drop=True), top, best_hits


def detect_roles(kind: str, columns) -> dict:
    """Best guess: role -> column name (or None)."""
    cand = []
    for role, syns in SYN[kind].items():
        for col in columns:
            n = norm(col)
            if n in syns:
                cand.append((3 - 0.01 * syns.index(n), role, col))
            else:
                for s in syns:
                    if len(s) >= 6 and s in n:
                        cand.append((1 - 0.01 * syns.index(s), role, col)); break
    cand.sort(key=lambda x: -x[0])
    out, used = {r: None for r in SYN[kind]}, set()
    for _, role, col in cand:
        if out[role] is None and col not in used:
            out[role] = col; used.add(col)
    return out


def guess_kind(columns) -> str:
    score = {}
    for k in KINDS:
        m = detect_roles(k, columns)
        req = REQUIRED[k]
        s = sum(m[r] is not None for r in req)
        if k == "statement":
            s += 1 if (m["debit"] and m["credit"]) or (m["amount"] and m["drcr"]) else -2
            if m["narration"] is None: s -= 1
        if k == "transactions":
            s += 0.5 * (m["channel"] is not None)
        if k == "complaints":
            s += 0.8 * (m["complaint_id"] is not None) + 0.5 * (m["reported_ts"] is not None)
        if k == "accounts":
            s += 0.5 * sum(m[r] is not None for r in ["bank", "device_id", "phone", "ip", "kyc_age_days", "open_date"]) - 0.5
            lg = detect_roles("iplog", columns)
            if lg["ts"] and lg["ip"]:                       # a time-stamped IP list is an IP log, not an accounts list
                s -= 1.0
        if k == "domains":
            s += 0.3 * sum(m[r] is not None for r in ["registrar", "created", "nameservers", "hosting", "asn", "ssl_issuer", "expires"])
        if k == "iplog":
            s += 0.5 * (m["event"] is not None) + 0.5 * any(m[r] is not None for r in ["account_id", "phone", "upi"])
        score[k] = s / (len(req) + (1 if k == "statement" else 0))
    return max(score, key=score.get)


BANKS = ["SBI", "STATE BANK", "HDFC", "ICICI", "AXIS", "PNB", "PUNJAB NATIONAL", "KOTAK", "CANARA", "BANK OF BARODA", "BOB", "UCO", "IDFC",
         "YES BANK", "INDUSIND", "UNION BANK", "BANK OF INDIA", "CENTRAL BANK", "INDIAN BANK", "IOB", "RBL", "FEDERAL", "PAYTM", "AU SMALL",
         "BANDHAN", "IDBI", "SOUTH INDIAN", "KARNATAKA", "JANA", "EQUITAS", "FINO", "AIRTEL", "INDIA POST", "RAJASTHAN MARUDHARA", "GRAMIN"]


@dataclass
class FileInfo:
    name: str                       # "file.xlsx" or "file.xlsx > Sheet1"
    df: pd.DataFrame                # table with the real header applied
    top_text: str = ""              # lines above the table (account holder, etc.)
    kind: str = "transactions"
    mapping: dict = field(default_factory=dict)
    owner: str = ""                 # statements only: whose statement is this
    bank: str = ""
    confident: bool = True


def load_file(name: str, data: bytes) -> list[FileInfo]:
    out = []
    for sheet, raw in read_sheets(name, data).items():
        df, top, hits = _find_header(raw)
        if hits < 2 or df.empty:
            continue
        kind = guess_kind(list(df.columns))
        fi = FileInfo(name=f"{name} > {sheet}" if sheet else name, df=df, top_text=" | ".join(top), kind=kind,
                      mapping=detect_roles(kind, list(df.columns)))
        fi.confident = all(fi.mapping.get(r) for r in REQUIRED[kind])
        if kind == "statement":
            fi.confident &= bool((fi.mapping["debit"] and fi.mapping["credit"]) or (fi.mapping["amount"] and fi.mapping["drcr"]))
            fi.owner = guess_owner(fi.top_text, name)
            fi.bank = guess_bank(fi.top_text + " " + name)
        out.append(fi)
    if not out:
        raise ImportProblem("no_table", name=name)
    return out


def guess_owner(top_text: str, filename: str) -> str:
    m = re.search(r"(?:A/?C|ACCOUNT)\s*(?:NO|NUMBER|#)?\.?\s*[:\-]?\s*([0-9Xx*]{6,20})", top_text, re.I)
    if m:
        return norm_id(m.group(1))
    m = re.search(r"\d{9,18}", filename)
    return m.group(0) if m else ""


def guess_bank(text: str) -> str:
    t = text.upper()
    for b in BANKS:
        if re.search(r"\b" + re.escape(b) + r"\b", t):
            return {"STATE BANK": "SBI", "PUNJAB NATIONAL": "PNB", "BANK OF BARODA": "BOB"}.get(b, b.title() if len(b) > 4 else b)
    return ""


# ------------------------------------------------------------------ cleaning helpers ----
def norm_id(x) -> str:
    s = str(x).strip().upper()
    s = re.sub(r"\.0$", "", s)
    return re.sub(r"\s+", "", s)


def to_amount(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.upper().str.replace(r"RS\.?|INR|₹|,|\s", "", regex=True).str.replace(r"(CR|DR)\.?$", "", regex=True)
    s = s.str.replace(r"^\((.*)\)$", r"\1", regex=True)
    return pd.to_numeric(s, errors="coerce").abs()


def to_ts(series: pd.Series, time_series: pd.Series | None = None) -> pd.Series:
    s = series.astype(str).str.strip()
    if time_series is not None:
        s = s + " " + time_series.astype(str).str.strip()
    s = s.mask(s.str.lower().isin(["", "nan", "nat", "none"]))
    iso = s.str.match(r"^\d{4}-\d{2}-\d{2}", na=False)          # 2026-10-04 is year-first, never day-first
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    if iso.any():
        out[iso] = pd.to_datetime(s[iso], errors="coerce", format="mixed")
    if (~iso).any():
        out[~iso] = pd.to_datetime(s[~iso], errors="coerce", dayfirst=True, format="mixed")
    return out


def has_time(ts: pd.Series) -> bool:
    t = ts.dropna()
    return bool(len(t)) and bool(((t.dt.hour + t.dt.minute + t.dt.second) > 0).mean() > 0.2)


CASH_WORDS = {
    "ATM": r"\bATM\b|\bNWD\b|\bEAW\b|CASH\s*W(?:DL|ITHDRAW)|\bCASH\s*WDL\b|ATM-?CASH",
    "WALLET": r"PAYTM\s*WALLET|\bWALLET\b|MOBIKWIK|FREECHARGE|PHONEPE\s*WALLET|AMAZON\s*PAY\s*BALANCE|\bPPI\b",
    "CRYPTO": r"WAZIRX|COINDCX|BINANCE|ZEBPAY|COINSWITCH|MUDREX|BITBNS|\bCRYPTO\b|\bUSDT\b|\bBITCOIN\b|\bBTC\b|UNOCOIN",
    "CASH": r"\bCASH\b|\bSELF\b\s*CHQ|CASH\s*WITHDRAW",
}


def cash_kind(text) -> str | None:
    t = str(text).upper()
    for k in ("CRYPTO", "WALLET", "ATM", "CASH"):
        if re.search(CASH_WORDS[k], t):
            return k
    return None


CHANNELS = [("UPI", r"\bUPI\b|@[A-Z]{2,}"), ("IMPS", r"\bIMPS\b|\bMMT\b"), ("NEFT", r"\bNEFT\b"), ("RTGS", r"\bRTGS\b"),
            ("ATM", CASH_WORDS["ATM"]), ("POS", r"\bPOS\b|\bECOM\b"), ("CHEQUE", r"\bCHQ\b|\bCHEQUE\b|\bCLG\b")]


def channel_of(text) -> str:
    t = str(text).upper()
    for k, rx in CHANNELS:
        if re.search(rx, t):
            return k
    return "OTHER"


_STOP = set("UPI IMPS NEFT RTGS DR CR DEBIT CREDIT TO FROM BY TRF TRANSFER PAYMENT PAY OF A/C AC NO BANK LTD PVT MMT INB IB MB FT REF".split())


def counterparty(narration: str, ref: str = "") -> str:
    """Best guess of the OTHER side of a statement line: UPI id > account number > name."""
    n = str(narration).upper()
    m = re.search(r"[A-Z0-9._]{2,}@[A-Z]{2,}", n)
    if m:
        return m.group(0)
    ref = norm_id(ref)
    runs = [r for r in re.findall(r"(?<![A-Z0-9])\d{9,18}(?![A-Z0-9])", n) if r != ref]
    if len(runs) >= 2 or (len(runs) == 1 and len(runs[0]) != 12):
        runs = [r for r in runs if not (len(r) == 12 and re.search(r"(UPI|IMPS|MMT)[/\-\s]*" + r, n))] or runs
        return runs[-1]
    parts = [p.strip() for p in re.split(r"[/\-:|*]", n)]
    names = [p for p in parts if re.fullmatch(r"[A-Z][A-Z .&']{2,}", p) and not set(p.split()) <= _STOP and len(p) > 3]
    return ("NAME:" + names[0].strip()) if names else "UNKNOWN"


# ------------------------------------------------------------------ converters ----
def _txn_from_table(fi: FileInfo, notes: list) -> pd.DataFrame:
    m, d = fi.mapping, fi.df
    g = lambda r: d[m[r]] if m.get(r) in d.columns else pd.Series([""] * len(d), index=d.index)
    tx = pd.DataFrame({
        "txn_id": g("txn_id").map(norm_id) if m.get("txn_id") else "",
        "ts": to_ts(g("ts")), "src": g("src").map(norm_id), "dst": g("dst").map(norm_id),
        "amount": to_amount(g("amount")),
        "channel": g("channel").astype(str).str.upper().str.strip() if m.get("channel") else "OTHER"})
    return _finish(tx, fi.name, notes)


def _txn_from_statement(fi: FileInfo, notes: list) -> pd.DataFrame:
    m, d = fi.mapping, fi.df
    owner = norm_id(fi.owner)
    if not owner:
        raise ImportProblem("no_owner", name=fi.name)
    if m.get("debit") and m.get("credit"):
        deb, cre = to_amount(d[m["debit"]]), to_amount(d[m["credit"]])
    else:
        amt = to_amount(d[m["amount"]]); tag = d[m["drcr"]].astype(str).str.upper()
        deb = amt.where(tag.str.contains(r"DR|D\b|DEBIT|WITHDRAW", regex=True)); cre = amt.where(~tag.str.contains(r"DR|D\b|DEBIT|WITHDRAW", regex=True))
    ts = to_ts(d[m["date"]], d[m["time"]] if m.get("time") else None)
    narr = d[m["narration"]].astype(str)
    bal = to_amount(d[m["balance"]]) if m.get("balance") else pd.Series(np.nan, index=d.index)
    ref = d[m["ref"]].astype(str).map(norm_id) if m.get("ref") else pd.Series([""] * len(d), index=d.index)
    rows = []
    for i in d.index:
        is_deb = pd.notna(deb[i]) and deb[i] > 0
        is_cre = pd.notna(cre[i]) and cre[i] > 0
        if not (is_deb or is_cre):
            continue                                       # opening balance, totals, blank lines
        text, amount = narr[i], (deb[i] if is_deb else cre[i])
        kind = cash_kind(text)
        other = counterparty(text, ref[i])
        if is_deb:
            dst = f"CASHOUT:{kind}:{owner}" if kind else other
            rows.append((ref[i], ts[i], owner, dst, amount, channel_of(text), text, bal[i]))
        else:
            rows.append((ref[i], ts[i], f"CASHIN:{kind}:{owner}" if kind == "ATM" or kind == "CASH" else other, owner, amount, channel_of(text), text, bal[i]))
    tx = pd.DataFrame(rows, columns=["txn_id", "ts", "src", "dst", "amount", "channel", "narration", "balance"])
    return _finish(tx, fi.name, notes, bank_of={owner: fi.bank} if fi.bank else None)


def _finish(tx: pd.DataFrame, name: str, notes: list, bank_of=None) -> pd.DataFrame:
    n0 = len(tx)
    # cash-out nodes for transaction tables (statements already did it)
    ck = tx.channel.astype(str).map(cash_kind).fillna(tx.dst.map(cash_kind))
    mask = ck.notna() & ~tx.dst.map(is_cashout)
    tx.loc[mask, "dst"] = [f"CASHOUT:{k}:{(s if re.fullmatch(r'[A-Z ]*', str(d)) else d)}" for k, s, d in zip(ck[mask], tx.src[mask], tx.dst[mask])]
    bad = tx.ts.isna() | tx.amount.isna() | (tx.amount <= 0) | (tx.src.str.len() == 0) | (tx.dst.str.len() == 0) | (tx.src == tx.dst)
    if bad.any():
        notes.append(("warn", "rows_dropped", dict(n=int(bad.sum()), total=n0, name=name)))
    tx = tx[~bad].copy()
    if tx.channel.eq("").all() or tx.channel.eq("OTHER").all():
        pass
    tx["channel"] = tx.channel.replace("", "OTHER")
    for col, blank in (("narration", ""), ("balance", np.nan)):          # PS05 schema: narration + running balance are kept when the file has them
        if col not in tx:
            tx[col] = blank
    unk = tx.src.str.startswith(("UNKNOWN", "NAME:")).sum() + tx.dst.str.startswith(("UNKNOWN", "NAME:")).sum()
    if unk:
        notes.append(("info", "unknown_party", dict(n=int(unk), name=name)))
    tx.attrs["bank_of"] = bank_of or {}
    return tx


def _complaints(fi: FileInfo, tx: pd.DataFrame, notes: list) -> pd.DataFrame:
    m, d = fi.mapping, fi.df
    g = lambda r: d[m[r]] if m.get(r) in d.columns else pd.Series([""] * len(d), index=d.index)
    rows = []
    for k, i in enumerate(d.index, 1):
        cid = str(g("complaint_id")[i]).strip() or f"CMP-{k:03d}"
        rows.append(dict(complaint_id=cid, victim_account=norm_id(g("victim_account")[i]), amount=to_amount(pd.Series([g("amount")[i]]))[0],
                         fraud_ts=to_ts(pd.Series([g("fraud_ts")[i]]))[0], reported_ts=to_ts(pd.Series([g("reported_ts")[i]]))[0],
                         txn_ref=str(g("txn_ref")[i]), first_mule=norm_id(g("first_mule")[i]) if m.get("first_mule") else "",
                         victim_name=str(g("victim_name")[i]).strip() if m.get("victim_name") else "",
                         victim_phone=str(g("victim_phone")[i]).strip() if m.get("victim_phone") else "",
                         victim_upi=str(g("victim_upi")[i]).strip().upper() if m.get("victim_upi") else ""))
    return finalize_complaints(pd.DataFrame(rows), tx, notes)


def finalize_complaints(comp: pd.DataFrame, tx: pd.DataFrame, notes: list) -> pd.DataFrame:
    """Fill gaps using the transactions: find the victim's payment by its reference, take the time and amount from it."""
    if comp.empty:
        return comp
    comp = comp.copy()
    refs_col, fts = [], []
    amt = []
    for r in comp.itertuples():
        refs = [norm_id(x) for x in re.split(r"[,;\s/|]+", str(getattr(r, "txn_ref", ""))) if norm_id(x) not in ("", "NAN", "NONE")]
        hit = tx[(tx.txn_id.isin(refs)) & (tx.src == r.victim_account)] if refs else tx.iloc[0:0]
        if refs and hit.empty:
            notes.append(("warn", "ref_not_found", dict(cid=r.complaint_id)))
            refs = []
        ts, a = r.fraud_ts, r.amount
        if pd.isna(ts):
            ts = hit.ts.min() if len(hit) else (r.reported_ts if pd.notna(r.reported_ts) else pd.NaT)
        if (pd.isna(a) or a <= 0) and len(hit):
            a = hit.amount.sum()
        if pd.isna(ts):
            v = tx[tx.src == r.victim_account]
            ts = v.ts.min() if len(v) else pd.NaT
            if pd.notna(ts):
                notes.append(("warn", "time_guessed", dict(cid=r.complaint_id)))
        refs_col.append(hit.txn_id.tolist() if len(hit) else []); fts.append(ts); amt.append(a)
    comp["seed_ids"] = refs_col; comp["fraud_ts"] = pd.to_datetime(fts); comp["amount"] = amt
    bad = comp.fraud_ts.isna() | comp.amount.isna() | (comp.amount <= 0) | (comp.victim_account == "")
    for r in comp[bad].itertuples():
        notes.append(("warn", "complaint_skipped", dict(cid=r.complaint_id)))
    comp = comp[~bad].copy()
    for r in comp.itertuples():
        if not (tx.src == r.victim_account).any():
            notes.append(("warn", "victim_not_in_tx", dict(cid=r.complaint_id, acct=r.victim_account)))
    return comp.reset_index(drop=True)


def make_complaint(victim: str, amount: float, fraud_ts, reported_ts=None, refs: str = "", cid: str = "",
                   name: str = "", phone: str = "", upi: str = "") -> pd.DataFrame:
    return pd.DataFrame([dict(complaint_id=cid or "CMP-MANUAL", victim_account=norm_id(victim), amount=float(amount),
                              fraud_ts=pd.Timestamp(fraud_ts), reported_ts=pd.Timestamp(reported_ts) if reported_ts is not None else pd.NaT,
                              txn_ref=refs, first_mule="", victim_name=name.strip(), victim_phone=phone.strip(), victim_upi=upi.strip().upper())])


def _accounts(fi: FileInfo, tx_end) -> pd.DataFrame:
    m, d = fi.mapping, fi.df
    out = pd.DataFrame({"account_id": d[m["account_id"]].map(norm_id)})
    for c in ["bank", "device_id", "phone", "ip"]:
        out[c] = d[m[c]].astype(str).str.strip() if m.get(c) else np.nan
    if m.get("kyc_age_days"):
        out["kyc_age_days"] = pd.to_numeric(d[m["kyc_age_days"]], errors="coerce")
    elif m.get("open_date"):
        out["kyc_age_days"] = (tx_end - to_ts(d[m["open_date"]])).dt.days
    return out[out.account_id != ""]


# ------------------------------------------------------------------ the whole thing ----
@dataclass
class Dataset:
    acc: pd.DataFrame
    tx: pd.DataFrame
    comp: pd.DataFrame
    notes: list
    time_known: bool = True
    domains: pd.DataFrame = field(default_factory=lambda: __import__("tracenet.intel.model", fromlist=["x"]).empty_domains())
    iplog: pd.DataFrame = field(default_factory=lambda: __import__("tracenet.intel.model", fromlist=["x"]).empty_iplog())


def _domains(fi: FileInfo) -> pd.DataFrame:
    """Indicator rows (domains and/or IPs). A cell in the domain column that is an IP address is treated as an IP."""
    from .intel.model import tidy_domains, is_ip
    m, d = fi.mapping, fi.df
    g = lambda r: d[m[r]].astype(str) if m.get(r) in d.columns else pd.Series([""] * len(d), index=d.index)
    out = pd.DataFrame({r: g(r) for r in SYN["domains"]})
    isip = out.domain.map(is_ip)
    out.loc[isip, "ip"] = out.loc[isip, "domain"]; out.loc[isip, "domain"] = ""
    out["source"] = fi.name
    out = out[(out.domain.str.strip() != "") | (out.ip.str.strip() != "")]
    return tidy_domains(out)


def _iplog(fi: FileInfo, zone: str = "") -> pd.DataFrame:
    """IP-log events. Times with their own offset (Z, +00:00) are respected; plain times are taken as `zone` (default India)."""
    from .intel.model import IPLOG_COLS
    from .intel.timeutil import parse_utc
    m, d = fi.mapping, fi.df
    g = lambda r: d[m[r]].astype(str).str.strip() if m.get(r) in d.columns else pd.Series([""] * len(d), index=d.index)
    tzcol = g("tz")
    ts = parse_utc(g("ts"), zone or (tzcol[tzcol != ""].iloc[0] if (tzcol != "").any() else ""))
    out = pd.DataFrame({"ts_utc": ts, "ip": g("ip"), "event": g("event").replace("", "event"), "account_id": g("account_id").map(norm_id).replace("NAN", ""),
                        "phone": g("phone").replace("nan", ""), "upi": g("upi").str.upper().replace("NAN", ""), "source": g("source").replace("", fi.name),
                        "tz": zone or "UTC/own offset"})
    return out[out.ts_utc.notna() & (out.ip != "")][IPLOG_COLS].reset_index(drop=True)


def convert(files: list[FileInfo], manual: pd.DataFrame | None = None, log_zone: str = "") -> Dataset:
    from .engine import complete_accounts
    notes, txs, accs, comps, bank_of = [], [], [], [], {}
    for fi in files:
        if fi.kind == "transactions":
            t = _txn_from_table(fi, notes)
        elif fi.kind == "statement":
            t = _txn_from_statement(fi, notes)
        else:
            continue
        bank_of.update(t.attrs.get("bank_of", {})); txs.append(t)
    if not txs:
        raise ImportProblem("no_transactions")
    tx = pd.concat(txs, ignore_index=True)
    # the same payment appears in the sender's and the receiver's statement: keep one
    has_id = tx.txn_id.astype(str).str.len() > 0
    keyed = tx[has_id].drop_duplicates(["txn_id", "src", "dst", "amount"])
    tx = pd.concat([keyed, tx[~has_id].drop_duplicates(["ts", "src", "dst", "amount"])], ignore_index=True)
    tx["ts_order"] = np.arange(len(tx))
    tx = tx.sort_values(["ts", "ts_order"], kind="stable").drop(columns="ts_order").reset_index(drop=True)
    miss = tx.txn_id.astype(str).str.len() == 0
    tx.loc[miss, "txn_id"] = [f"R{i:06d}" for i in range(int(miss.sum()))]
    time_known = has_time(tx.ts)
    if not time_known:
        notes.append(("warn", "no_time", {}))
    doms, logs = [], []
    for fi in files:
        if fi.kind == "domains":
            doms.append(_domains(fi))
        elif fi.kind == "iplog":
            logs.append(_iplog(fi, log_zone))
        elif fi.kind == "accounts":
            accs.append(_accounts(fi, tx.ts.max()))
        elif fi.kind == "complaints":
            comps.append(_complaints(fi, tx, notes))
    if manual is not None and len(manual):
        comps.append(finalize_complaints(manual, tx, notes))
    comp = pd.concat(comps, ignore_index=True) if comps else pd.DataFrame(
        columns=["complaint_id", "victim_account", "amount", "fraud_ts", "reported_ts", "txn_ref", "first_mule", "seed_ids",
                 "victim_name", "victim_phone", "victim_upi"])
    acc = pd.concat(accs, ignore_index=True).drop_duplicates("account_id") if accs else pd.DataFrame(columns=["account_id"])
    if bank_of:
        extra = pd.DataFrame({"account_id": list(bank_of), "bank": list(bank_of.values())})
        acc = pd.concat([acc, extra[~extra.account_id.isin(acc.account_id)]], ignore_index=True)
        if "bank" in acc:
            acc["bank"] = acc.bank.fillna(acc.account_id.map(bank_of))
    acc = complete_accounts(acc, tx, comp)
    if len(comp) and "seed_ids" not in comp:
        comp["seed_ids"] = [[] for _ in range(len(comp))]
    from .intel.model import empty_domains, empty_iplog
    return Dataset(acc=acc, tx=tx, comp=comp, notes=notes, time_known=time_known,
                   domains=pd.concat(doms, ignore_index=True) if doms else empty_domains(),
                   iplog=pd.concat(logs, ignore_index=True) if logs else empty_iplog())


def load_demo(data_dir="data") -> Dataset:
    """The bundled made-up data, in the same Dataset shape."""
    from .engine import load, complete_accounts
    acc, tx, comp = load(data_dir)
    comp = comp.copy(); comp["seed_ids"] = [[] for _ in range(len(comp))]
    ds = Dataset(acc=complete_accounts(acc, tx, comp), tx=tx, comp=comp, notes=[], time_known=True)
    from pathlib import Path
    for fname, attr, fn in (("domains.csv", "domains", _domains), ("ip_log.csv", "iplog", _iplog)):
        f = Path(data_dir) / fname
        if f.exists():                                   # the digital demo layer goes through the same importer as real files
            fi = load_file(fname, f.read_bytes())[0]
            setattr(ds, attr, fn(fi))
    return ds


# ------------------------------------------------------------------ unmatched parties ----
def unlinked_parties(ds: Dataset, top=25) -> pd.DataFrame:
    """Names / UPI ids from statements that could not be tied to an account number.
    The investigator can say 'this UPI id is account 5010000003' and the trail joins up."""
    t = pd.concat([ds.tx[["src", "amount"]].rename(columns={"src": "party"}), ds.tx[["dst", "amount"]].rename(columns={"dst": "party"})])
    t = t[t.party.str.startswith(("NAME:", "UNKNOWN")) | t.party.str.contains("@")]
    if t.empty:
        return pd.DataFrame(columns=["party", "times", "amount"])
    g = t.groupby("party").amount.agg(times="size", amount="sum").reset_index().sort_values("amount", ascending=False).head(top)
    return g.reset_index(drop=True)


def apply_aliases(ds: Dataset, alias: dict) -> Dataset:
    """alias = {'RAMESH@OKAXIS': '5010000003'}  -> rename in transactions and rebuild accounts."""
    alias = {norm_id(k): norm_id(v) for k, v in alias.items() if str(v).strip()}
    if not alias:
        return ds
    from .engine import complete_accounts
    tx = ds.tx.copy(); tx["src"] = tx.src.replace(alias); tx["dst"] = tx.dst.replace(alias)
    tx = tx[tx.src != tx.dst].reset_index(drop=True)
    acc = ds.acc[~ds.acc.account_id.isin(alias)]
    import dataclasses
    return dataclasses.replace(ds, acc=complete_accounts(acc, tx, ds.comp), tx=tx)         # keeps domains / IP log too
