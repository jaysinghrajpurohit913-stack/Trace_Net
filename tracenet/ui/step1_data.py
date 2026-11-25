"""Step 1: add the files (any format) + complaints by hand."""
import datetime as dt

import pandas as pd
import streamlit as st

from ..importer import ImportProblem, KINDS, REQUIRED, SYN, load_file, detect_roles, guess_owner, make_complaint, load_demo
from ..templates import template_xlsx


def render(ctx):
    t, role_name, ss, HERE = ctx.t, ctx.role, ctx.ss, ctx.here
    problem_text = ctx.problem_text
    KIND_NAME = {k: t(f"kind_{k}") for k in KINDS}
    left, right = st.columns([3, 2])
    with left:
        st.subheader(t("upload_title"))
        st.caption(t("upload_help"))
        ups = st.file_uploader(" ", accept_multiple_files=True, type=["csv", "xlsx", "xls", "xlsm", "pdf", "txt"], label_visibility="collapsed")
        keys = []
        for f in ups or []:
            key = (f.name, f.size); keys.append(key)
            if key not in ss.parsed:
                try:
                    ss.parsed[key] = load_file(f.name, f.getvalue())
                except ImportProblem as e:
                    ss.parsed[key] = e
                except Exception as e:                       # corrupt file etc.
                    ss.parsed[key] = ImportProblem("read", name=f.name, why=str(e)[:150])
        files = []
        for key in keys:
            v = ss.parsed[key]
            if isinstance(v, ImportProblem):
                st.error(problem_text(v) if v.key != "read" else t("err_read", **v.params))
            else:
                files += v
    with right:
        with st.expander(t("what_files"), expanded=not files):
            st.markdown(t("what_files_body"))
        st.download_button("⬇ " + t("template_btn"), template_xlsx(), file_name="TraceNet_data_template.xlsx", width="stretch")
        if st.button("🧪 " + t("demo_btn"), width="stretch"):
            ss.ds = load_demo(str(HERE / "data")); ss.is_demo = True; ss.analysis = None; ss.step = 3; st.rerun()
        st.caption(t("demo_note"))

    # ---- one card per file: type + columns
    if files:
        st.subheader(t("files_found"))
    for i, fi in enumerate(files):
        ok = fi.confident
        with st.container(border=True):
            c1, c2 = st.columns([3, 2])
            c1.markdown(f"**📄 {fi.name}**  \n{'✅ ' + t('sure') if ok else '⚠️ ' + t('check_cols')}")
            new_kind = c2.selectbox(t("type_is"), KINDS, index=KINDS.index(fi.kind), format_func=KIND_NAME.get, key=f"kind{i}{fi.name}")
            if new_kind != fi.kind:
                fi.kind = new_kind; fi.mapping = detect_roles(new_kind, list(fi.df.columns))
                if new_kind == "statement" and not fi.owner:
                    fi.owner = guess_owner(fi.top_text, fi.name)
                st.rerun()
            if fi.kind == "statement":
                o1, o2 = st.columns(2)
                fi.owner = o1.text_input(t("owner_q"), fi.owner, help=t("owner_help"), key=f"own{i}{fi.name}").strip()
                fi.bank = o2.text_input(t("bank_q"), fi.bank, key=f"bank{i}{fi.name}").strip()
            with st.expander(t("cols_title"), expanded=not ok):
                opts = [t("none_opt")] + list(fi.df.columns)
                grid = st.columns(3)
                for j, r in enumerate(SYN[fi.kind]):
                    cur = fi.mapping.get(r)
                    star = " *" if r in REQUIRED[fi.kind] else ""
                    pick = grid[j % 3].selectbox(role_name(r) + star, opts, index=opts.index(cur) if cur in opts else 0, key=f"map{i}{fi.name}{fi.kind}{r}")
                    fi.mapping[r] = None if pick == opts[0] else pick
                fi.confident = all(fi.mapping.get(r) for r in REQUIRED[fi.kind]) and (
                    fi.kind != "statement" or bool((fi.mapping["debit"] and fi.mapping["credit"]) or (fi.mapping["amount"] and fi.mapping["drcr"])))
            with st.expander(t("preview")):
                st.dataframe(fi.df.head(6), width="stretch", hide_index=True)

    if any(f.kind == "iplog" for f in files):
        ss.log_zone = st.text_input(t("log_tz_q"), ss.get("log_zone", ""), help=t("log_tz_help"), placeholder="UTC / Asia/Kolkata").strip()

    # ---- complaint by hand
    with st.expander("✍️ " + t("manual_title"), expanded=bool(files) and not any(f.kind == "complaints" for f in files)):
        a, b, c_, d_ = st.columns(4)
        v = a.text_input(t("m_victim"), key="mv"); amt = b.number_input(t("m_amount"), min_value=0.0, step=1000.0, key="ma")
        day = c_.date_input(t("m_date"), dt.date.today(), key="md"); tm = d_.text_input(t("m_time"), "10:00", key="mt")
        e1, e2, e3 = st.columns(3)
        ref = e1.text_input(t("m_ref"), key="mr")
        vname = e2.text_input(role_name("victim_name"), key="mn"); vphone = e3.text_input(role_name("victim_phone"), key="mp")
        if st.button(t("m_add")):
            try:
                ts = pd.Timestamp(f"{day} {tm}")
                if not v.strip() or amt <= 0: raise ValueError
                ss.manual.append(make_complaint(v, amt, ts, refs=ref, cid=f"CMP-{len(ss.manual) + 1:03d}", name=vname, phone=vphone))
                st.rerun()
            except Exception:
                st.error(t("m_bad"))
        if ss.manual:
            st.caption(t("m_added"))
            st.dataframe(pd.concat(ss.manual)[["complaint_id", "victim_account", "amount", "fraud_ts"]], hide_index=True, width="stretch")

    st.divider()
    if st.button(t("to_check"), type="primary", disabled=not files):
        ss.files = files; ss.step = 2; st.rerun()
    if not files:
        st.caption(t("need_file"))
