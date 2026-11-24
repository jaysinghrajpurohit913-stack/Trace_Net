"""Look and feel: one stylesheet + a few small HTML pieces (hero, stepper, KPI cards, chips).
Only presentation; no analysis logic lives here."""
import html
import streamlit as st

CSS = """
<style>
:root{
  --bg:#eef4f2; --surface:#ffffff; --ink:#0d2b2b; --muted:#5b7473; --line:#d9e6e2;
  --brand:#0f8a6d; --brand2:#18b394; --brand-soft:#dcf5ee; --deep:#082322; --deep2:#0d3a37;
  --amber:#e8a317; --amber-soft:#fff3d6; --red:#e5484d; --red-soft:#ffe3e4; --blue:#2f6fed; --blue-soft:#e3edff;
  --shadow:0 1px 2px rgba(8,35,34,.06),0 8px 24px rgba(8,35,34,.07);
}
html,body,[class*="css"]{font-family:"Inter","Segoe UI","Noto Sans Devanagari","Nirmala UI",system-ui,sans-serif;letter-spacing:0}
[data-testid="stAppViewContainer"]{background:radial-gradient(1200px 500px at 85% -10%,#d3f1e7 0,transparent 60%),var(--bg);color:var(--ink)}
[data-testid="stHeader"]{background:transparent}
.main .block-container{max-width:1500px;padding-top:1.2rem;padding-bottom:4rem}
h1,h2,h3,h4{color:var(--ink);letter-spacing:-.01em}
h3{font-weight:700} h4{font-weight:650}
/* sidebar */
[data-testid="stSidebar"]{background:linear-gradient(180deg,var(--deep) 0,var(--deep2) 100%);border-right:0}
[data-testid="stSidebar"] *{color:#d6efe8}
[data-testid="stSidebar"] [data-testid="stButton"]>button{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.16);border-radius:10px;font-weight:600;transition:.2s}
[data-testid="stSidebar"] [data-testid="stButton"]>button:hover{background:rgba(24,179,148,.25);border-color:var(--brand2)}
/* hero */
.tn-hero{position:relative;overflow:hidden;border-radius:20px;padding:26px 30px;margin:0 0 18px;color:#eafff8;
  background:radial-gradient(600px 260px at 90% 0,rgba(24,179,148,.55),transparent 65%),radial-gradient(500px 300px at 0 120%,rgba(47,111,237,.35),transparent 60%),linear-gradient(135deg,#06201f,#0d3a37 60%,#0b4a3f);
  box-shadow:0 14px 40px rgba(8,35,34,.25)}
.tn-hero:before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.05) 1px,transparent 1px);background-size:34px 34px;mask-image:linear-gradient(90deg,transparent,#000 70%);-webkit-mask-image:linear-gradient(90deg,transparent,#000 70%)}
.tn-hero .row{position:relative;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.tn-logo{width:54px;height:54px;border-radius:16px;display:grid;place-items:center;font-size:28px;background:linear-gradient(135deg,#18b394,#0f8a6d);box-shadow:0 0 0 6px rgba(24,179,148,.18),0 8px 20px rgba(0,0,0,.3);animation:pulse 3.2s ease-in-out infinite}
@keyframes pulse{50%{box-shadow:0 0 0 12px rgba(24,179,148,.05),0 8px 20px rgba(0,0,0,.3)}}
.tn-hero h1{margin:0;font-size:2rem;font-weight:800;color:#fff;letter-spacing:-.02em;padding:0}
.tn-hero p{margin:.15rem 0 0;color:#a9d9cc;font-size:.95rem;max-width:760px}
.tn-badges{margin-left:auto;display:flex;gap:8px;flex-wrap:wrap}
.tn-badge{padding:5px 12px;border-radius:999px;font-size:.74rem;font-weight:600;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.18);color:#d9fff3}
/* stepper */
.tn-steps{display:flex;gap:0;align-items:center;background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:12px 18px;margin-bottom:18px;box-shadow:var(--shadow)}
.tn-step{display:flex;align-items:center;gap:10px;flex:1;font-weight:600;color:var(--muted);font-size:.95rem}
.tn-step .dot{width:32px;height:32px;border-radius:50%;display:grid;place-items:center;font-weight:700;background:#e8f0ee;color:var(--muted);flex:none}
.tn-step.done .dot{background:var(--brand);color:#fff}.tn-step.done{color:var(--ink)}
.tn-step.now .dot{background:linear-gradient(135deg,var(--brand2),var(--brand));color:#fff;box-shadow:0 0 0 5px rgba(24,179,148,.2)}.tn-step.now{color:var(--ink)}
.tn-step+.tn-step:before{content:"";height:2px;flex:1;max-width:90px;margin-right:10px;background:var(--line)}
.tn-step.done+.tn-step:before,.tn-step.now:before{background:var(--brand)}
/* KPI cards */
.tn-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:6px 0 16px}
.tn-kpi{position:relative;background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:16px 18px;box-shadow:var(--shadow);transition:transform .18s,box-shadow .18s;overflow:hidden}
.tn-kpi:hover{transform:translateY(-3px);box-shadow:0 12px 30px rgba(8,35,34,.13)}
.tn-kpi:before{content:"";position:absolute;left:0;top:0;bottom:0;width:5px;background:var(--c,var(--brand))}
.tn-kpi .l{font-size:.78rem;font-weight:650;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;display:flex;gap:6px;align-items:center}
.tn-kpi .v{font-size:1.75rem;font-weight:800;margin-top:4px;color:var(--ink);letter-spacing:-.02em}
.tn-kpi .s{font-size:.8rem;color:var(--muted);margin-top:2px}
.tn-kpi .ic{position:absolute;right:14px;top:10px;font-size:1.6rem;opacity:.9}
.tn-kpi.teal{--c:var(--brand)}.tn-kpi.amber{--c:var(--amber)}.tn-kpi.red{--c:var(--red)}.tn-kpi.blue{--c:var(--blue)}
/* chips */
.tn-chip{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:999px;font-size:.8rem;font-weight:650;margin:0 6px 6px 0;border:1px solid transparent}
.tn-chip.teal{background:var(--brand-soft);color:#0a6a54;border-color:#b6e8da}.tn-chip.amber{background:var(--amber-soft);color:#8a5a00;border-color:#f6dd9c}
.tn-chip.red{background:var(--red-soft);color:#a3262b;border-color:#f8c1c3}.tn-chip.blue{background:var(--blue-soft);color:#1f4fb8;border-color:#bdd1fb}.tn-chip.grey{background:#eaf0ef;color:#46605e;border-color:#d4e0de}
/* file header */
.tn-file{display:flex;align-items:center;gap:14px;flex-wrap:wrap;background:linear-gradient(135deg,#ffffff,#eefaf6);border:1px solid var(--line);border-radius:18px;padding:16px 20px;margin:8px 0 12px;box-shadow:var(--shadow)}
.tn-file .id{font-size:1.5rem;font-weight:800;letter-spacing:-.02em}.tn-file .sub{color:var(--muted);font-size:.88rem}
.tn-file .ic{font-size:2rem}
/* native widgets */
[data-testid="stMetric"]{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:12px 16px;box-shadow:var(--shadow)}
[data-testid="stMetricLabel"]{color:var(--muted);font-weight:650}[data-testid="stMetricValue"]{font-weight:800;letter-spacing:-.02em}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:var(--shadow)}
[data-testid="stVerticalBlockBorderWrapper"]{border-color:var(--line);border-radius:16px;background:var(--surface);box-shadow:var(--shadow)}
[data-testid="stExpander"]{border-color:var(--line);border-radius:14px;background:var(--surface)}
[data-testid="stExpander"] summary{font-weight:650}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-baseweb="select"]>div{border-radius:12px!important}
[data-testid="stTextInput"] input{padding:.7rem .9rem;font-size:1rem;border:1.5px solid var(--line);background:#fff}
[data-testid="stTextInput"] input:focus{border-color:var(--brand2);box-shadow:0 0 0 4px rgba(24,179,148,.16)}
[data-testid="stFileUploader"] section{border:2px dashed #7fd3bd;border-radius:16px;background:linear-gradient(135deg,#fff,#effaf6)}
[data-testid="stBaseButton-primary"]{background:linear-gradient(135deg,var(--brand2),var(--brand));border:0;border-radius:12px;font-weight:700;padding:.55rem 1.2rem;box-shadow:0 6px 16px rgba(15,138,109,.35);transition:.18s}
[data-testid="stBaseButton-primary"]:hover{transform:translateY(-1px);box-shadow:0 10px 22px rgba(15,138,109,.45)}
[data-testid="stBaseButton-secondary"]{border-radius:12px;border:1px solid var(--line);font-weight:600;background:#fff;transition:.18s}
[data-testid="stBaseButton-secondary"]:hover{border-color:var(--brand2);color:var(--brand);transform:translateY(-1px)}
[data-testid="stRadio"] [role="radiogroup"]{gap:8px}
/* top view switch = segmented control */
.st-key-view [role="radiogroup"]{background:#dfece8;padding:5px;border-radius:14px;display:inline-flex;gap:2px}
.st-key-view label{padding:8px 18px;border-radius:10px;margin:0!important;cursor:pointer;transition:.15s}
.st-key-view label:has(input:checked){background:#fff;box-shadow:0 2px 8px rgba(8,35,34,.15);font-weight:700;color:var(--brand)}
.st-key-view label>div:first-child{display:none}
[data-testid="stSidebar"] [data-testid="stExpander"]{background:rgba(255,255,255,.06);border-color:rgba(255,255,255,.16)}
[data-testid="stSidebar"] [data-testid="stExpander"] *{color:#d6efe8!important}
[data-testid="stTabs"] [role="tablist"]{gap:6px;border-bottom:1px solid var(--line)}
[data-testid="stTabs"] [role="tab"]{padding:.7rem 1rem;font-weight:650;color:var(--muted);border-radius:10px 10px 0 0}
[data-testid="stTabs"] [role="tab"]:hover{background:var(--brand-soft)}
[data-testid="stTabs"] [aria-selected="true"]{color:var(--brand)}
[data-testid="stAlert"]{border-radius:14px;border:1px solid var(--line)}
.stPlotlyChart{background:#fff;border:1px solid var(--line);border-radius:16px;padding:8px;box-shadow:var(--shadow)}
[data-testid="stCaptionContainer"]{color:var(--muted)}
hr{border-color:var(--line)}
@media(max-width:760px){.tn-hero{padding:18px}.tn-hero h1{font-size:1.5rem}.tn-badges{margin-left:0}.tn-step span.t{display:none}.tn-kpi .v{font-size:1.4rem}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def _e(x):
    return html.escape(str(x))


def hero(title, sub, badges=()):
    b = "".join(f'<span class="tn-badge">{_e(x)}</span>' for x in badges)
    st.markdown(f'<div class="tn-hero"><div class="row"><div class="tn-logo">🔎</div><div><h1>{_e(title)}</h1><p>{_e(sub)}</p></div>'
                f'<div class="tn-badges">{b}</div></div></div>', unsafe_allow_html=True)


def stepper(step, labels):
    parts = []
    for i, lab in enumerate(labels, 1):
        cls = "done" if step > i else ("now" if step == i else "")
        parts.append(f'<div class="tn-step {cls}"><div class="dot">{"✓" if step > i else i}</div><span class="t">{_e(lab)}</span></div>')
    st.markdown(f'<div class="tn-steps">{"".join(parts)}</div>', unsafe_allow_html=True)


def kpis(items):
    """items: (icon, label, value, sub, tone) tuples -> a row of cards."""
    cards = "".join(f'<div class="tn-kpi {_e(tone)}"><div class="ic">{ic}</div><div class="l">{_e(lab)}</div><div class="v">{_e(val)}</div>'
                    f'<div class="s">{_e(sub)}</div></div>' for ic, lab, val, sub, tone in items)
    st.markdown(f'<div class="tn-kpis">{cards}</div>', unsafe_allow_html=True)


def chip(text, tone="grey"):
    return f'<span class="tn-chip {tone}">{_e(text)}</span>'


def file_header(icon, cid, sub, chips):
    st.markdown(f'<div class="tn-file"><div class="ic">{icon}</div><div><div class="id">{_e(cid)}</div><div class="sub">{_e(sub)}</div></div>'
                f'<div style="margin-left:auto">{"".join(chips)}</div></div>', unsafe_allow_html=True)
