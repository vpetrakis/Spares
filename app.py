"""
app.py — Marine Spares Control Tower  v3
M/V ALEXIS 2026

Architecture:
  core/parser.py   — data extraction + state machine
  core/metrics.py  — all KPI calculations (cancelled excluded from budget)
  ui/components.py — CSS design system + Streamlit components
  ui/charts.py     — Plotly chart factory
"""
import os, sys, traceback

try:
    _ROOT = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _ROOT = os.path.abspath(os.getcwd())

for _p in [_ROOT, "/mount/src/spares"]:
    _p = os.path.abspath(_p)
    if os.path.isdir(os.path.join(_p, "core")) and _p not in sys.path:
        sys.path.insert(0, _p)

import pandas as pd
import streamlit as st

from core import (
    parse_workbook, pipeline_summary, status_distribution,
    category_breakdown, supplier_performance, timeline_data,
    delayed_items, age_distribution, cost_by_month,
)
from ui import (
    inject_css, page_header, kpi_row, section, warnings_banner, stat_chip,
    sidebar_header, sidebar_sla_card,
    triage_table, fleet_table, cancelled_table, supplier_table,
    status_bar, timeline_chart, cost_timeline_chart,
    sla_donut, category_treemap,
    supplier_chart, age_bar, supplier_ontime_bar,
)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Marine Spares — M/V Alexis 2026",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()


# ─────────────────────────────────────────────────────────────────────────────
# CACHED PARSER
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data(b: bytes):
    return parse_workbook(b)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    sidebar_header()

    uploaded = st.file_uploader(
        "Master spares file",
        type=["xlsx"],
        label_visibility="collapsed",
    )

    sidebar_sla_card()

# ─────────────────────────────────────────────────────────────────────────────
# LANDING
# ─────────────────────────────────────────────────────────────────────────────
if not uploaded:
    st.markdown(
        '<div class="landing">'
        '<div class="landing-icon">🚢</div>'
        '<h2>Marine Spares Control Tower</h2>'
        '<p>Upload the ALEXIS master spares file (.xlsx) in the sidebar to launch the dashboard.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# PARSE
# ─────────────────────────────────────────────────────────────────────────────
try:
    with st.spinner("Parsing workbook…"):
        df, index_kpis, parse_warnings = load_data(uploaded.getvalue())
except Exception as exc:
    st.error(f"**Parse error:** {exc}")
    with st.expander("Full traceback"):
        st.code(traceback.format_exc())
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR FILTERS  (rendered after data is available)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="sb-section" style="margin-top:20px">Filters</div>',
        unsafe_allow_html=True,
    )
    all_statuses = sorted(df["status_label"].dropna().unique().tolist())
    sel_status   = st.multiselect("Status", all_statuses,
                                  default=all_statuses, key="f_status",
                                  label_visibility="collapsed")

    st.markdown('<div class="sb-section">Equipment</div>', unsafe_allow_html=True)
    equip_opts = sorted(df["equipment"].dropna().replace("", pd.NA).dropna().unique().tolist())
    sel_equip  = st.multiselect("Equipment", equip_opts,
                                default=[], key="f_equip",
                                label_visibility="collapsed")

    st.markdown('<div class="sb-section">Category</div>', unsafe_allow_html=True)
    cat_opts = sorted(df["category_name"].dropna().replace("", pd.NA).dropna().unique().tolist())
    sel_cat  = st.multiselect("Category", cat_opts,
                              default=[], key="f_cat",
                              label_visibility="collapsed")

    st.markdown('<div class="sb-section">Supplier</div>', unsafe_allow_html=True)
    sup_opts = sorted(df["supplier"].dropna().replace("", pd.NA).dropna().unique().tolist())
    sel_sup  = st.multiselect("Supplier", sup_opts,
                              default=[], key="f_sup",
                              label_visibility="collapsed")

# ─────────────────────────────────────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────────────────────────────────────
fdf = df.copy()
if sel_status: fdf = fdf[fdf["status_label"].isin(sel_status)]
if sel_equip:  fdf = fdf[fdf["equipment"].isin(sel_equip)]
if sel_cat:    fdf = fdf[fdf["category_name"].isin(sel_cat)]
if sel_sup:    fdf = fdf[fdf["supplier"].isin(sel_sup)]

# ─────────────────────────────────────────────────────────────────────────────
# METRICS  (all computed on filtered data; cancelled excluded from budget)
# ─────────────────────────────────────────────────────────────────────────────
summary    = pipeline_summary(fdf)
status_df  = status_distribution(fdf)
cat_df     = category_breakdown(fdf)
sup_df     = supplier_performance(fdf)
time_df    = timeline_data(fdf)
cost_df    = cost_by_month(fdf)
delayed_df = delayed_items(fdf)
age_df     = age_distribution(fdf)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
page_header(filtered=len(fdf), total=len(df))
warnings_banner(parse_warnings)
kpi_row(summary)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
t_ov, t_tr, t_fl, t_su, t_ca = st.tabs([
    "📊  Overview",
    "🔥  Triage",
    "🔍  Full Fleet",
    "🏭  Suppliers",
    "📦  Categories",
])


# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with t_ov:
    # Row 1 — Status bar (left) + SLA donut (right)
    c_bar, c_donut = st.columns([3, 1], gap="medium")
    with c_bar:
        section("Pipeline status")
        st.plotly_chart(status_bar(status_df),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key="ov_status_bar")
    with c_donut:
        section("SLA health")
        st.plotly_chart(sla_donut(summary["delayed"], summary["total"]),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key="ov_sla_donut")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        stat_chip("Avg stage age",
                  f"{summary.get('avg_age', 0):.0f}d", "#D29922")

    # Row 2 — Timeline + Spend
    c_tl, c_sp = st.columns(2, gap="medium")
    with c_tl:
        section("Requisitions per month")
        st.plotly_chart(timeline_chart(time_df),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key="ov_timeline")
    with c_sp:
        section("Monthly spend — excl. cancelled")
        st.plotly_chart(cost_timeline_chart(cost_df),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key="ov_cost")

    # Row 3 — Treemap + INDEX ledger
    c_tree, c_idx = st.columns([2, 1], gap="medium")
    with c_tree:
        section("Spend by category — excl. cancelled")
        st.plotly_chart(category_treemap(cat_df),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key="ov_treemap")
    with c_idx:
        section("INDEX ledger")
        if index_kpis:
            idx_rows = [
                {
                    "Category": v["category_name"].replace(" Spares","").replace(" SPARES","").strip(),
                    "Case":     v["case_code"],
                    "Rcvd":     v["requisitions_received"] or "—",
                    "Spend":    f"${v['cost']:,.0f}" if v["cost"] else "—",
                }
                for v in index_kpis.values() if v["category_name"]
            ]
            st.dataframe(pd.DataFrame(idx_rows),
                         use_container_width=True, hide_index=True)
        else:
            st.info("No INDEX sheet found.")


# ══════════════════════════════════════════════════════════════════════════════
# TRIAGE
# ══════════════════════════════════════════════════════════════════════════════
with t_tr:
    if summary["delayed"] == 0:
        st.success(
            "✅ All active requisitions are within SLA thresholds. "
            "Fleet supply chain is operating normally."
        )
    else:
        st.error(
            f"⚠️  **{summary['delayed']} requisition(s) have breached SLA.**  "
            f"Review the triage table and take action."
        )

    section("SLA breach triage")
    triage_table(delayed_df)

    # Age bar — all active items
    if not age_df.empty:
        section("Stage age — all active items")
        st.plotly_chart(age_bar(age_df),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key="tr_age_bar")

    # Cancelled audit — separated, clearly labelled, cost_raw shown
    cancelled_df = fdf[fdf["is_cancelled"]].copy()
    if not cancelled_df.empty:
        section(f"Cancelled requisitions — {len(cancelled_df)} item(s)")
        st.markdown(
            '<div style="font-size:.75rem;color:#444C56;margin:-8px 0 10px;">'
            '⚠ Cancelled orders are <strong>excluded from all budget calculations</strong>. '
            'Original cost shown below for audit purposes only.</div>',
            unsafe_allow_html=True,
        )
        with st.expander("Show cancelled requisitions"):
            cancelled_table(cancelled_df)


# ══════════════════════════════════════════════════════════════════════════════
# FULL FLEET
# ══════════════════════════════════════════════════════════════════════════════
with t_fl:
    c_hd, c_dl = st.columns([4, 1])
    with c_hd:
        section(f"All requisitions — {len(fdf)} records")
    with c_dl:
        st.markdown("<div style='padding-top:30px'>", unsafe_allow_html=True)
        csv_cols  = [c for c in fdf.columns if c not in ("sub_orders",)]
        csv_data  = fdf[csv_cols].copy()
        date_cols = ["date_requested","order_date","est_readiness","rcvd","ref_date","invoice"]
        for dc in date_cols:
            if dc in csv_data.columns:
                csv_data[dc] = pd.to_datetime(csv_data[dc], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
        st.download_button(
            "⬇ Export CSV",
            csv_data.to_csv(index=False).encode("utf-8"),
            file_name="alexis_spares_2026.csv",
            mime="text/csv",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Split orders disclosure
    has_sub = fdf["sub_orders"].apply(lambda x: isinstance(x, list) and len(x) > 0).any()
    if has_sub:
        with st.expander("🔗 Split orders — multi-supplier requisitions"):
            split_rows = fdf[fdf["sub_orders"].apply(
                lambda x: isinstance(x, list) and len(x) > 0)]
            for _, row in split_rows.iterrows():
                st.markdown(
                    f"<div style='font-size:.82rem;color:#CDD9E5;margin-bottom:4px'>"
                    f"<strong>{row['ta_ref']}</strong> — {row['description']}</div>",
                    unsafe_allow_html=True,
                )
                for sub in row["sub_orders"]:
                    od   = (pd.Timestamp(sub["order_date"]).strftime("%d %b %Y")
                            if sub.get("order_date") else "—")
                    cost = f"${sub.get('cost', 0):,.2f}" if sub.get("cost") else "—"
                    st.markdown(
                        f"<div style='font-size:.75rem;color:#444C56;padding-left:16px;margin-bottom:2px'>"
                        f"└ <strong style='color:#768390'>{sub.get('supplier','—')}</strong>"
                        f" &nbsp;·&nbsp; PO: {od}"
                        f" &nbsp;·&nbsp; Cost: {cost}</div>",
                        unsafe_allow_html=True,
                    )

    fleet_table(fdf)


# ══════════════════════════════════════════════════════════════════════════════
# SUPPLIERS
# ══════════════════════════════════════════════════════════════════════════════
with t_su:
    if sup_df.empty:
        st.info("No supplier data available for the current filter selection.")
    else:
        c_main, c_side = st.columns([3, 1], gap="medium")
        with c_main:
            section("Order volume & spend")
            st.plotly_chart(supplier_chart(sup_df),
                            use_container_width=True,
                            config={"displayModeBar": False},
                            key="su_chart")
            section("On-time delivery rate")
            st.plotly_chart(supplier_ontime_bar(sup_df),
                            use_container_width=True,
                            config={"displayModeBar": False},
                            key="su_ontime")
        with c_side:
            section("Scorecard")
            supplier_table(sup_df)
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            stat_chip("Suppliers", str(len(sup_df)), "#58A6FF")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            stat_chip("Total spend",
                      f"${sup_df['total_cost'].sum():,.0f}", "#BC8CFF")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORIES
# ══════════════════════════════════════════════════════════════════════════════
with t_ca:
    c_tree, c_tbl = st.columns([2, 1], gap="medium")
    with c_tree:
        section("Spend by category — excl. cancelled")
        st.plotly_chart(category_treemap(cat_df),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key="ca_treemap")
    with c_tbl:
        section("Breakdown")
        vw = cat_df.rename(columns={
            "category":"Category","count":"Req",
            "total_cost":"Spend (USD)","delayed":"Delayed",
        }).copy()
        vw["Spend (USD)"] = vw["Spend (USD)"].apply(
            lambda x: f"${x:,.0f}" if x > 0 else "—")
        st.dataframe(vw, use_container_width=True, hide_index=True)

    section("Drill-down by category")
    all_cats = sorted(
        fdf["category_name"].dropna().replace("", pd.NA).dropna().unique().tolist()
    )
    if all_cats:
        chosen   = st.selectbox("Category", all_cats, key="cat_drill",
                                label_visibility="collapsed")
        cat_view = fdf[fdf["category_name"] == chosen]
        c1, c2, c3 = st.columns(3)
        with c1: stat_chip("Requisitions", str(len(cat_view)))
        with c2:
            cat_spend = cat_view[~cat_view["is_cancelled"]]["cost"].sum(skipna=True)
            stat_chip("Spend (excl. cancelled)", f"${cat_spend:,.0f}", "#BC8CFF")
        with c3:
            stat_chip("Delayed",
                      str(int(cat_view["sla_breach"].sum())),
                      "#F85149" if cat_view["sla_breach"].any() else "#3FB950")
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        fleet_table(cat_view)
    else:
        st.info("No categorised requisitions in current selection.")

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;color:#1C2128;font-size:.68rem;"
    "padding:56px 0 20px;margin-top:48px;border-top:1px solid #1C2128'>"
    "Marine Spares Control Tower &nbsp;·&nbsp; M/V Alexis 2026 &nbsp;·&nbsp; "
    "Cancelled orders excluded from all budget metrics"
    "</div>",
    unsafe_allow_html=True,
)
