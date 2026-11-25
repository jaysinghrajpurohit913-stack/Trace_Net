import pandas as pd
from tracenet import config as C
from tracenet.engine import evaluate, trace_funds


def test_demo_detection_quality(an):
    m = evaluate(an.feats, pd.read_csv("data/ground_truth.csv"))
    assert m["tp"] >= 34 and m["fp"] <= 3, m


def test_ps05_indicators_fire_on_case5(an):
    f = an.feats
    assert f.loc["M5A0", "round_share"] >= C.ROUND_SHARE
    assert f.loc["M5B1", "dormant_awake"] == 1
    assert "round-figure" in f.loc["M5A0", "reasons"].lower() or f.loc["M5A0", "round_count"] >= 3


def test_trace_never_creates_money(demo):
    for r in demo.comp.itertuples():
        t = trace_funds(demo.tx, r.victim_account, r.fraud_ts, r.amount)
        assert sum(t.cashed.values()) + sum(v for v in t.held.values()) <= r.amount * 1.001


def test_all_thresholds_live_in_config():
    import re, pathlib
    src = pathlib.Path("tracenet/engine.py").read_text()
    assert not re.search(r"thr=\d", src), "default thresholds must come from tracenet/config.py"
