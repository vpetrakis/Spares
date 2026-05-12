"""
app.py — Marine Spares Control Tower
M/V ALEXIS 2026
"""
import os
import sys
import io
import traceback

# ── Bulletproof sys.path for Streamlit Cloud + local dev
# Strategy: try __file__, fall back to cwd, then also try /mount/src/* pattern
try:
    _ROOT = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _ROOT = os.path.abspath(os.getcwd())

for _candidate in [_ROOT] + [
    p for p in [
        os.path.join(_ROOT, ".."),
        "/mount/src/spares",
    ] if os.path.isdir(os.path.join(p, "core"))
]:
    _candidate = os.path.abspath(_candidate)
    if _candidate not in sys.path:
        sys.path.insert(0, _candidate)

import pandas as pd
import streamlit as st

from core import (
    parse_workbook,
    pipeline_summary,
    status_distribution,
    category_breakdown,
    supplier_performance,
    timeline_data,
    delayed_items,
)
from ui import (
    inject_css,
    kpi_row,
    section,
    warnings_banner,
    triage_table,
    fleet_table,
    supplier_table,
    status_bar,
    category_treemap,
    timeline_chart,
    supplier_bar,
    sla_gauge,
)

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Marine Spares Control Tower — M/V Alexis",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()


@st.cache_data(show_spinner=False)
def load_data(file_bytes: bytes):
    return parse_workbook(file_bytes)


# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🚢 Control Tower")
    st.markdown("**M/V ALEXIS — 2026 Spares**")
    st.markdown("---")
    uploaded = st.file_uploader(
        "Upload master spares file",
        type=["xlsx"],
        help="Drop the ALEXIS_-_2026.xlsx (or any year equivalent) here.",
    )
    st.markdown("---")
    st.markdown(
        "<small style='color:#8B949E'>Pipeline SLA thresholds<br>"
        "Supply: 7 days · Finance: 5 days<br>"
        "Ordered: 45 days · Transit: 21 days</small>",
        unsafe_allow_html=True,
    )

if not uploaded:
    st.markdown(
        """
        <div style='text-align:center;padding:80px 0 40px'>
          <div style='font-size:4rem'>🚢</div>
          <h2 style='color:#E6EDF3;margin:16px 0 8px'>Marine Spares Control Tower</h2>
          <p style='color:#8B949E;font-size:1rem'>
            Upload the master spares Excel file using the sidebar to begin.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

try:
    with st.spinner("Parsing workbook…"):
        df, index_kpis, warnings = load_data(uploaded.getvalue())
except Exception as exc:
    st.error(f"**Parse error:** {exc}")
    with st.expander("Full traceback"):
        st.code(traceback.format_exc())
    st.stop()

# ──────────────────────────────────────────────
# SIDEBAR FILTERS
# ──────────────────────────────────────────────

with st.sidebar:
    st.markdown("---")
    st.markdown("#### Filters")
    status_options = sorted(df["status_label"].dropna().unique().tolist())
    sel_status = st.multiselect("Status", status_options, default=status_options)
    equip_options = sorted(df["equipment"].dropna().replace("", pd.NA).dropna().unique().tolist())
    sel_equip = st.multiselect("Equipment", equip_options, default=[])
    cat_options = sorted(df["category_name"].dropna().replace("", pd.NA).dropna().unique().tolist())
    sel_cat = st.multiselect("Category", cat_options, default=[])
    supplier_options = sorted(df["supplier"].dropna().replace("", pd.NA).dropna().unique().tolist())
    sel_supplier = st.multiselect("Supplier", supplier_options, default=[])

filtered = df.copy()
if sel_status:
    filtered = filtered[filtered["status_label"].isin(sel_status)]
if sel_equip:
    filtered = filtered[filtered["equipment"].isin(sel_equip)]
if sel_cat:
    filtered = filtered[filtered["category_name"].isin(sel_cat)]
if sel_supplier:
    filtered = filtered[filtered["supplier"].isin(sel_supplier)]

summary    = pipeline_summary(filtered)
status_df  = status_distribution(filtered)
cat_df     = category_breakdown(filtered)
sup_df     = supplier_performance(filtered)
time_df    = timeline_data(filtered)
delayed_df = delayed_items(filtered)

# ──────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────

col_title, col_meta = st.columns([3, 1])
with col_title:
    st.markdown("## 🚢 Marine Spares Control Tower — M/V ALEXIS 2026")
with col_meta:
    if len(filtered) < len(df):
        st.markdown(
            f"<div style='text-align:right;padding-top:12px;color:#E3B341;font-size:.82rem'>"
            f"⚡ Showing {len(filtered)} of {len(df)} requisitions</div>",
            unsafe_allow_html=True,
        )

warnings_banner(warnings)
kpi_row(summary)

# ──────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────

tab_overview, tab_triage, tab_fleet, tab_suppliers, tab_categories = st.tabs([
    "📊 Overview", "🔥 Triage", "🔍 Full Fleet", "🏭 Suppliers", "📦 Categories",
])

with tab_overview:
    col_l, col_r = st.columns([2, 1])
    with col_l:
        section("Pipeline Status Distribution")
        st.plotly_chart(status_bar(status_df), use_container_width=True, config={"displayModeBar": False}, key="chart_status_bar")
        section("Requisition Volume Timeline")
        st.plotly_chart(timeline_chart(time_df), use_container_width=True, config={"displayModeBar": False}, key="chart_timeline")
    with col_r:
        section("SLA Health")
        st.plotly_chart(sla_gauge(summary["delayed"], summary["total"]), use_container_width=True, config={"displayModeBar": False}, key="chart_sla_gauge")
        section("Spend by Category")
        st.plotly_chart(category_treemap(cat_df), use_container_width=True, config={"displayModeBar": False}, key="chart_treemap_overview")
    if index_kpis:
        section("Category Ledger (from INDEX sheet)")
        idx_rows = []
        for code, kpi in index_kpis.items():
            idx_rows.append({
                "Code": code,
                "Category": kpi["category_name"],
                "Case": kpi["case_code"],
                "Cost (Index)": f"${kpi['cost']:,.2f}" if kpi["cost"] else "—",
                "Req. Received": kpi["requisitions_received"] or "—",
                "Req. Processed": kpi["requisitions_processed"] or "—",
            })
        st.dataframe(pd.DataFrame(idx_rows), use_container_width=True, hide_index=True)

with tab_triage:
    if summary["delayed"] == 0:
        st.success("✅ All active requisitions are within SLA. Fleet supply chain is healthy.")
    else:
        st.error(f"⚠️ **{summary['delayed']} requisition(s) have breached SLA thresholds.** Immediate action required.")
    section(f"SLA Breach Triage — {summary['delayed']} item(s)")
    triage_table(delayed_df)
    cancelled_df = filtered[filtered["status"] == "CANCELLED"]
    if not cancelled_df.empty:
        section(f"Cancelled Requisitions — {len(cancelled_df)} item(s)")
        with st.expander("Show cancelled items"):
            view_cols = [c for c in ["ta_ref", "description", "equipment", "supplier", "confirmation", "cost"] if c in cancelled_df.columns]
            st.dataframe(
                cancelled_df[view_cols].rename(columns={
                    "ta_ref": "TA Ref", "description": "Description",
                    "equipment": "Equipment", "supplier": "Supplier",
                    "confirmation": "Cancellation Note", "cost": "Cost ($)",
                }),
                use_container_width=True, hide_index=True,
            )

with tab_fleet:
    section(f"All Requisitions — {len(filtered)} records")
    has_suborders = filtered["sub_orders"].apply(lambda x: len(x) > 0 if isinstance(x, list) else False).any()
    if has_suborders:
        with st.expander("🔗 Split orders (multi-supplier requisitions)"):
            for _, row in filtered[filtered["sub_orders"].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)].iterrows():
                st.markdown(f"**{row['ta_ref']}** — {row['description']}")
                for sub in row["sub_orders"]:
                    st.markdown(
                        f"&nbsp;&nbsp;&nbsp;└ Supplier: **{sub.get('supplier', '—')}** | "
                        f"PO: {pd.Timestamp(sub['order_date']).strftime('%d %b %Y') if sub.get('order_date') else '—'} | "
                        f"Cost: ${sub.get('cost', 0):,.2f}",
                        unsafe_allow_html=True,
                    )
    fleet_table(filtered)
    csv_cols = [c for c in filtered.columns if c not in ("sub_orders",)]
    csv_data = filtered[csv_cols].copy()
    for dc in ["date_requested", "order_date", "est_readiness", "rcvd", "ref_date", "invoice"]:
        if dc in csv_data.columns:
            csv_data[dc] = pd.to_datetime(csv_data[dc], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    st.download_button(
        "⬇ Export filtered data as CSV",
        csv_data.to_csv(index=False).encode("utf-8"),
        file_name="alexis_spares_export.csv",
        mime="text/csv",
    )

with tab_suppliers:
    section("Supplier Intelligence")
    if sup_df.empty:
        st.info("No supplier data available for current filter selection.")
    else:
        col_chart, col_table = st.columns([2, 1])
        with col_chart:
            st.plotly_chart(supplier_bar(sup_df), use_container_width=True, config={"displayModeBar": False}, key="chart_supplier_bar")
        with col_table:
            section("Supplier Scorecard")
            supplier_table(sup_df)

with tab_categories:
    section("Category Breakdown")
    col_tree, col_tbl = st.columns([2, 1])
    with col_tree:
        st.plotly_chart(category_treemap(cat_df), use_container_width=True, config={"displayModeBar": False}, key="chart_treemap_categories")
    with col_tbl:
        view = cat_df.copy()
        view["total_cost"] = view["total_cost"].apply(lambda x: f"${x:,.2f}")
        view.columns = ["Category", "Count", "Total Cost", "Delayed"]
        st.dataframe(view, use_container_width=True, hide_index=True)
    section("Drill-down by category")
    all_cats = sorted(filtered["category_name"].dropna().replace("", pd.NA).dropna().unique().tolist())
    if all_cats:
        chosen = st.selectbox("Select category to inspect", all_cats)
        cat_view = filtered[filtered["category_name"] == chosen]
        fleet_table(cat_view)
    else:
        st.info("No categorised requisitions in current selection.")

st.markdown(
    "<div style='text-align:center;color:#30363D;font-size:.72rem;padding:32px 0 8px'>"
    "Marine Spares Control Tower · M/V Alexis 2026 · Built with Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
