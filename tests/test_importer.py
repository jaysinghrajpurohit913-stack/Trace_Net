import glob
import pandas as pd
from tracenet.importer import load_file, convert, load_demo
from tracenet.intel.timeutil import parse_utc, to_local


def _files():
    out = []
    for f in sorted(glob.glob("sample_bank_files/*")):
        out += load_file(f.split("/")[-1], open(f, "rb").read())
    return out


def test_sample_files_are_recognised():
    kinds = {f.kind for f in _files()}
    assert {"transactions", "complaints", "statement", "accounts", "domains", "iplog"} <= kinds


def test_convert_keeps_digital_tables_and_narration():
    ds = convert(_files(), None, "")
    assert len(ds.domains) == 2 and len(ds.iplog) == 2
    assert {"narration", "balance"} <= set(ds.tx.columns)
    assert ds.comp.victim_name.str.len().gt(0).all()


def test_demo_loads_digital_layer(demo):
    assert len(demo.domains) >= 5 and len(demo.iplog) >= 5


def test_timezone_normalisation():
    s = pd.Series(["2026-10-04T07:38:00Z", "2026-10-04 13:08", "04/10/2026 13:08:00 +05:30", "04/10/2026 07:38 UTC"])
    u = parse_utc(s)
    assert u.nunique() == 1 and u.iloc[0] == pd.Timestamp("2026-10-04 07:38")
    assert to_local(u).iloc[0] == pd.Timestamp("2026-10-04 13:08")
