"""
app.py — Marine Spares Control Tower  v2
M/V ALEXIS 2026
"""
import os, sys, io, traceback

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
    inject_css, page_header, kpi_row, section, warnings_banner,
    triage_table, fleet_table, supplier_table, stat_chip,
    status_bar, timeline_chart, cost_timeline_chart,
    sla_donut, category_treemap, supplier_chart,
    age_bar, supplier_ontime_bar,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Marine Spares — M/V Alexis 2026",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()


# ── Cache ─────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data(b: bytes):
    return parse_workbook(b)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='font-size:1.1rem;font-weight:700;color:#E6EDF3;"
        "margin-bottom:2px'>🚢 Control Tower</div>"
        "<div style='font-size:.75rem;color:#8B949E;margin-bottom:20px'>"
        "M/V ALEXIS · 2026</div>",
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "Master spares file (.xlsx)",
        type=["xlsx"],
        label_visibility="visible",
    )
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='nav-sla'>"
        "<strong>SLA Thresholds</strong><br>"
        "Supply &nbsp;&nbsp;&nbsp;→ 7 days<br>"
        "Finance &nbsp;&nbsp;→ 5 days<br>"
        "Ordered &nbsp;&nbsp;→ 45 days<br>"
        "Transit &nbsp;&nbsp;&nbsp;→ 21 days"
        "</div>",
        unsafe_allow_html=True,
    )

# ── Landing ───────────────────────────────────────────────────────────────────
if not uploaded:
    st.markdown(
        "<div style='display:flex;flex-direction:column;align-items:center;"
        "justify-content:center;min-height:60vh;text-align:center;gap:16px'>"
        "<div style='font-size:3.5rem'>🚢</div>"
        "<h2 style='color:#E6EDF3;font-weight:600;margin:0'>Marine Spares Control Tower</h2>"
        "<p style='color:#8B949E;max-width:400px;margin:0'>"
        "Upload the master spares Excel file in the sidebar to begin.</p>"
        "<div style='color:#30363D;font-size:.75rem;margin-top:8px'>"
        "M/V ALEXIS &nbsp;·&nbsp; 2026 Spares Pipeline</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.stop()

# ── Parse ─────────────────────────────────────────────────────────────────────
try:
    with st.spinner("Parsing workbook…"):
        df, index_kpis, parse_warnings = load_data(uploaded.getvalue())
except Exception as exc:
    st.error(f"**Parse error:** {exc}")
    with st.expander("Full traceback"):
        st.code(traceback.format_exc())
    st.stop()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<hr style='border-color:#21262D;margin:20px 0 16px'>",
                unsafe_allow_html=True)
    st.markdown("<div style='font-size:.7rem;font-weight:600;color:#8B949E;"
                "text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px'>"
                "Filters</div>", unsafe_allow_html=True)

    all_statuses = sorted(df["status_label"].dropna().unique().tolist())
    sel_status   = st.multiselect("Status", all_statuses, default=all_statuses, key="f_status")

    equip_opts   = sorted(df["equipment"].dropna().replace("", pd.NA).dropna().unique().tolist())
    sel_equip    = st.multiselect("Equipment", equip_opts, default=[], key="f_equip")

    cat_opts     = sorted(df["category_name"].dropna().replace("", pd.NA).dropna().unique().tolist())
    sel_cat      = st.multiselect("Category", cat_opts, default=[], key="f_cat")

    sup_opts     = sorted(df["supplier"].dropna().replace("", pd.NA).dropna().unique().tolist())
    sel_sup      = st.multiselect("Supplier", sup_opts, default=[], key="f_sup")

# ── Apply filters ─────────────────────────────────────────────────────────────
fdf = df.copy()
if sel_status: fdf = fdf[fdf["status_label"].isin(sel_status)]
if sel_equip:  fdf = fdf[fdf["equipment"].isin(sel_equip)]
if sel_cat:    fdf = fdf[fdf["category_name"].isin(sel_cat)]
if sel_sup:    fdf = fdf[fdf["supplier"].isin(sel_sup)]

# ── Metrics ───────────────────────────────────────────────────────────────────
summary    = pipeline_summary(fdf)
status_df  = status_distribution(fdf)
cat_df     = category_breakdown(fdf)
sup_df     = supplier_performance(fdf)
time_df    = timeline_data(fdf)
cost_df    = cost_by_month(fdf)
delayed_df = delayed_items(fdf)
age_df     = age_distribution(fdf)

# ── Header ────────────────────────────────────────────────────────────────────
page_header(filtered=len(fdf), total=len(df))
warnings_banner(parse_warnings)
kpi_row(summary)

# ── Tabs ──────────────────────────────────────────────────────────────────────
t_overview, t_triage, t_fleet, t_suppliers, t_categories = st.tabs([
    "📊  Overview",
    "🔥  Triage",
    "🔍  Full Fleet",
    "🏭  Suppliers",
    "📦  Categories",
])


# ════════════════════════════════════════════════════════════════════
# OVERVIEW
# ════════════════════════════════════════════════════════════════════
with t_overview:

    # ── Row 1: status bar + SLA donut ─────────────────────────────
    col_bar, col_donut = st.columns([3, 1], gap="medium")
    with col_bar:
        section("Pipeline status", margin_top=False)
        st.plotly_chart(status_bar(status_df),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key="ov_status_bar")
    with col_donut:
        section("SLA health", margin_top=False)
        st.plotly_chart(sla_donut(summary["delayed"], summary["total"]),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key="ov_sla_donut")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        stat_chip("Avg stage age", f"{summary.get('avg_age',0):.0f} days", "#D29922")

    # ── Row 2: timeline + spend ───────────────────────────────────
    col_tl, col_sp = st.columns(2, gap="medium")
    with col_tl:
        section("Requisitions per month")
        st.plotly_chart(timeline_chart(time_df),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key="ov_timeline")
    with col_sp:
        section("Monthly spend (USD)")
        st.plotly_chart(cost_timeline_chart(cost_df),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key="ov_cost_timeline")

    # ── Row 3: category treemap + index ledger ────────────────────
    col_tree, col_idx = st.columns([2, 1], gap="medium")
    with col_tree:
        section("Spend by category")
        st.plotly_chart(category_treemap(cat_df),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key="ov_treemap")
    with col_idx:
        section("INDEX ledger")
        if index_kpis:
            idx_rows = [
                {
                    "Category": kpi["category_name"].replace(" SPARES","").strip(),
                    "Case":     kpi["case_code"],
                    "Received": kpi["requisitions_received"] or "—",
                    "Spend":    f"${kpi['cost']:,.0f}" if kpi["cost"] else "—",
                }
                for kpi in index_kpis.values()
                if kpi["category_name"]
            ]
            st.dataframe(pd.DataFrame(idx_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No INDEX sheet found.")


# ════════════════════════════════════════════════════════════════════
# TRIAGE
# ════════════════════════════════════════════════════════════════════
with t_triage:
    if summary["delayed"] == 0:
        st.success("✅ All active requisitions are within SLA thresholds. Fleet supply chain is healthy.")
    else:
        st.error(
            f"⚠️ **{summary['delayed']} requisition(s) breached SLA.** "
            f"Review the table below and take immediate action."
        )

    section("SLA breach triage", margin_top=False)
    triage_table(delayed_df)

    # Age bar for all active items
    if not age_df.empty:
        section("Stage age — all active items")
        st.plotly_chart(age_bar(age_df),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key="tr_age_bar")

    # Cancelled items
    cancelled_df = fdf[fdf["status"] == "CANCELLED"]
    if not cancelled_df.empty:
        section(f"Cancelled items — {len(cancelled_df)}")
        with st.expander("Show cancelled requisitions"):
            view_cols = [c for c in ["ta_ref","description","equipment",
                                     "supplier","confirmation","cost"] if c in cancelled_df.columns]
            vw = cancelled_df[view_cols].rename(columns={
                "ta_ref":"TA Ref","description":"Description","equipment":"Equipment",
                "supplier":"Supplier","confirmation":"Cancellation Note","cost":"Cost (USD)",
            })
            if "Cost (USD)" in vw.columns:
                vw["Cost (USD)"] = vw["Cost (USD)"].apply(
                    lambda x: f"${x:,.2f}" if pd.notna(x) and x > 0 else "—")
            st.dataframe(vw, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════
# FULL FLEET
# ════════════════════════════════════════════════════════════════════
with t_fleet:
    c_hd, c_dl = st.columns([3, 1])
    with c_hd:
        section(f"All requisitions — {len(fdf)} records", margin_top=False)
    with c_dl:
        st.markdown("<div style='padding-top:28px'>", unsafe_allow_html=True)
        csv_cols = [c for c in fdf.columns if c != "sub_orders"]
        csv_data = fdf[csv_cols].copy()
        for dc in ["date_requested","order_date","est_readiness","rcvd","ref_date","invoice"]:
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
        with st.expander("🔗 Split orders (multi-supplier requisitions)"):
            for _, row in fdf[fdf["sub_orders"].apply(
                    lambda x: isinstance(x, list) and len(x) > 0)].iterrows():
                st.markdown(f"**{row['ta_ref']}** — {row['description']}")
                for sub in row["sub_orders"]:
                    od = pd.Timestamp(sub["order_date"]).strftime("%d %b %Y") \
                         if sub.get("order_date") else "—"
                    cost = f"${sub.get('cost', 0):,.2f}" if sub.get("cost") else "—"
                    st.markdown(
                        f"&nbsp;&nbsp;&nbsp;└ **{sub.get('supplier','—')}** &nbsp;·&nbsp; "
                        f"PO: {od} &nbsp;·&nbsp; Cost: {cost}",
                        unsafe_allow_html=True,
                    )

    fleet_table(fdf)


# ════════════════════════════════════════════════════════════════════
# SUPPLIERS
# ════════════════════════════════════════════════════════════════════
with t_suppliers:
    if sup_df.empty:
        st.info("No supplier data available for current filter.")
    else:
        col_main, col_side = st.columns([3, 1], gap="medium")
        with col_main:
            section("Order volume & spend", margin_top=False)
            st.plotly_chart(supplier_chart(sup_df),
                            use_container_width=True,
                            config={"displayModeBar": False},
                            key="su_chart")
            section("On-time delivery rate")
            st.plotly_chart(supplier_ontime_bar(sup_df),
                            use_container_width=True,
                            config={"displayModeBar": False},
                            key="su_ontime")
        with col_side:
            section("Scorecard", margin_top=False)
            supplier_table(sup_df)
            section("Totals")
            stat_chip("Total suppliers", str(len(sup_df)), "#58A6FF")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            stat_chip("Total spend",
                      f"${sup_df['total_cost'].sum():,.0f}", "#BC8CFF")


# ════════════════════════════════════════════════════════════════════
# CATEGORIES
# ════════════════════════════════════════════════════════════════════
with t_categories:
    col_t, col_tbl = st.columns([2, 1], gap="medium")
    with col_t:
        section("Spend by category", margin_top=False)
        st.plotly_chart(category_treemap(cat_df),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key="ca_treemap")
    with col_tbl:
        section("Category breakdown", margin_top=False)
        view = cat_df.rename(columns={
            "category":"Category","count":"Req.","total_cost":"Spend","delayed":"Delayed"}).copy()
        view["Spend"] = view["Spend"].apply(lambda x: f"${x:,.0f}" if x > 0 else "—")
        st.dataframe(view, use_container_width=True, hide_index=True)

    section("Drill-down by category")
    all_cats = sorted(fdf["category_name"].dropna().replace("", pd.NA).dropna().unique().tolist())
    if all_cats:
        chosen   = st.selectbox("Select category", all_cats, key="cat_drill")
        cat_view = fdf[fdf["category_name"] == chosen]
        c1, c2, c3 = st.columns(3)
        with c1: stat_chip("Requisitions", str(len(cat_view)))
        with c2: stat_chip("Total spend",
                           f"${cat_view['cost'].sum(skipna=True):,.0f}", "#BC8CFF")
        with c3: stat_chip("Delayed", str(int(cat_view["sla_breach"].sum())),
                           "#F85149" if cat_view["sla_breach"].any() else "#3FB950")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        fleet_table(cat_view)
    else:
        st.info("No categorised requisitions in current selection.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;color:#21262D;font-size:.7rem;"
    "padding:48px 0 16px;border-top:1px solid #21262D;margin-top:48px'>"
    "Marine Spares Control Tower &nbsp;·&nbsp; M/V Alexis 2026 &nbsp;·&nbsp; Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
