"""Quick plain-English demo.   python run_demo.py            -> one example case
                              python run_demo.py NCRP-20    -> a specific complaint
                              python run_demo.py --test     -> how well it detects mules (synthetic test)
For the visual version run:   streamlit run app.py"""
import sys
import pandas as pd
from tracenet.engine import *
from tracenet.summary import case_brief, brief_text

acc, tx, comp = load("data")
feats = score_mules(account_features(tx, acc))
_, rd = link_entities(acc)
rings = merge_rings(rd, link_by_flow(tx, feats))

if "--test" in sys.argv:
    truth = pd.read_csv("data/ground_truth.csv"); m = evaluate(feats, truth)
    print(f"Test on made-up data with {m['tp'] + m['fn']} planted mule accounts:")
    print(f"  Found {m['tp']} of them ({m['recall']:.0%}).  Wrongly accused innocent accounts: {m['fp']}.")
    print("  (Made-up data is easier than real data. Real-world results will differ.)")
    sys.exit()

want = [a for a in sys.argv[1:] if not a.startswith("--")]
c = (comp[comp.complaint_id == want[0]] if want else comp.iloc[[0]]).iloc[0]
trail = trace_funds(tx, c.victim_account, c.fraud_ts, c.amount)
fl = freeze_list(trail, feats, rings)
print(brief_text(case_brief(c, trail, fl, rings, feats)))
print("Available complaints:", ", ".join(comp.complaint_id))
print("Visual dashboard:  streamlit run app.py")
