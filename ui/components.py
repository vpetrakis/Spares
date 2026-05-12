"""
components.py — Reusable Streamlit UI building blocks.
All visual chrome lives here; app.py only assembles them.
"""
from __future__ import annotations
import pandas as pd
import streamlit as st


# ──────────────────────────────────────────────
# CSS INJECTION (called once at startup)
# ──────────────────────────────────────────────

def inject_css() -> None:
    st.markdown(
        """
        <style>
        /* ── Base ── */
        .stApp { background:#0D1117; color:#E6EDF3; font-family:'Inter',sans-serif; }
        section[data-testid="stSidebar"] { background:#161B22; border-right:1px solid #30363D; }
        h1,h2,h3,h4 { color:#E6EDF3 !important; }

        /* ── KPI Cards ── */
        .kpi-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin-bottom:24px; }
        .kpi-card {
            background:#161B22; border:1px solid #30363D; border-radius:10px;
            padding:18px 16px; text-align:center;
        }
        .kpi-card .kpi-value { font-size:2rem; font-weight:700; line-height:1.1; }
        .kpi-card .kpi-label { font-size:.75rem; color:#8B949E; margin-top:4px; text-transform:uppercase; letter-spacing:.06em; }
        .kpi-card.ok   .kpi-value { color:#3FB950; }
        .kpi-card.warn .kpi-value { color:#D29922; }
        .kpi-card.danger .kpi-value { color:#F85149; }
        .kpi-card.info   .kpi-value { color:#58A6FF; }
        .kpi-card.neutral .kpi-value { color:#E6EDF3; }

        /* ── Section Headers ── */
        .section-header {
            font-size:.7rem; font-weight:600; letter-spacing:.1em;
            text-transform:uppercase; color:#8B949E;
            border-bottom:1px solid #21262D; padding-bottom:6px; margin:28px 0 14px;
        }

        /* ── Warning Banner ── */
        .warn-banner {
            background:#2D1B00; border:1px solid #D29922; border-radius:8px;
            padding:10px 14px; font-size:.82rem; color:#E3B341; margin-bottom:16px;
        }

        /* ── Delayed Row Highlight ── */
        .delayed-row { background:#2D0A0A !important; }

        /* ── Metric delta override ── */
        [data-testid="stMetricDelta"] { font-size:.75rem !important; }

        /* ── DataGrid ── */
        .stDataFrame { border:1px solid #30363D; border-radius:8px; overflow:hidden; }
        .stDataFrame th { background:#161B22 !important; color:#8B949E !important; font-size:.72rem !important; }
        .stDataFrame td { font-size:.8rem !important; }

        /* ── Tabs ── */
        .stTabs [data-baseweb="tab-list"] { background:#161B22; border-radius:8px; padding:4px; gap:4px; }
        .stTabs [data-baseweb="tab"] { border-radius:6px; color:#8B949E; font-size:.82rem; }
        .stTabs [aria-selected="true"] { background:#21262D !important; color:#E6EDF3 !important; }

        /* ── Expander ── */
        .streamlit-expanderHeader { background:#161B22 !important; border-radius:8px !important; }

        /* ── Scrollable table container ── */
        .scroll-table { overflow-x:auto; }

        /* ── Tag Pills ── */
        .tag-ok      { background:#0D4429; color:#3FB950; border-radius:12px; padding:2px 8px; font-size:.72rem; font-weight:600; }
        .tag-warn    { background:#2D1B00; color:#E3B341; border-radius:12px; padding:2px 8px; font-size:.72rem; font-weight:600; }
        .tag-danger  { background:#2D0A0A; color:#F85149; border-radius:12px; padding:2px 8px; font-size:.72rem; font-weight:600; }
        .tag-neutral { background:#21262D; color:#8B949E; border-radius:12px; padding:2px 8px; font-size:.72rem; font-weight:600; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────
# KPI CARD ROW
# ──────────────────────────────────────────────

def kpi_row(summary: dict) -> None:
    """Render the 6-card KPI header."""
    cards = [
        ("total",      summary["total"],                "Total Requisitions", "neutral"),
        ("active",     summary["active"],               "Active",             "info"),
        ("received",   summary["received"],             "Received / Onboard", "ok"),
        ("cancelled",  summary["cancelled"],            "Cancelled",          "neutral"),
        ("delayed",    summary["delayed"],              "SLA Breached",       "danger" if summary["delayed"] else "ok"),
        ("total_cost", f"${summary['total_cost']:,.0f}","Total Spend",        "info"),
    ]

    html = '<div class="kpi-grid">'
    for _, value, label, cls in cards:
        html += (
            f'<div class="kpi-card {cls}">'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-label">{label}</div>'
            f'</div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# SECTION HEADER
# ──────────────────────────────────────────────

def section(title: str) -> None:
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# DATA QUALITY WARNINGS
# ──────────────────────────────────────────────

def warnings_banner(warnings: list[str]) -> None:
    if not warnings:
        return
    items = "".join(f"<li>{w}</li>" for w in warnings)
    st.markdown(
        f'<div class="warn-banner">⚠ <strong>{len(warnings)} data quality notice(s)</strong><ul style="margin:6px 0 0 16px">{items}</ul></div>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────
# TRIAGE TABLE — delayed items
# ──────────────────────────────────────────────

def triage_table(df: pd.DataFrame) -> None:
    """Render the SLA-breach triage table with document links."""
    if df.empty:
        st.success("✅ No SLA breaches — all active requisitions are within tolerance.")
        return

    display_cols = {
        "status_label":    "Status",
        "ta_ref":          "TA Ref",
        "description":     "Description",
        "equipment":       "Equipment",
        "supplier":        "Supplier",
        "order_date":      "PO Date",
        "est_readiness":   "Est. Ready",
        "sla_days_over":   "Days Over SLA",
        "cost":            "Cost ($)",
        "document_url":    "Document",
    }
    cols_present = [c for c in display_cols if c in df.columns]
    view = df[cols_present].copy()
    view = view.rename(columns={c: display_cols[c] for c in cols_present})

    # Format dates
    for dc in ["PO Date", "Est. Ready"]:
        if dc in view.columns:
            view[dc] = pd.to_datetime(view[dc], errors="coerce").dt.strftime("%d %b %Y").fillna("—")

    if "Cost ($)" in view.columns:
        view["Cost ($)"] = view["Cost ($)"].apply(
            lambda x: f"${x:,.2f}" if pd.notna(x) and x > 0 else "—"
        )

    col_cfg = {}
    if "Document" in view.columns:
        col_cfg["Document"] = st.column_config.LinkColumn("Document", display_text="📄 Open")

    st.dataframe(
        view,
        use_container_width=True,
        hide_index=True,
        column_config=col_cfg,
    )


# ──────────────────────────────────────────────
# FULL FLEET TABLE
# ──────────────────────────────────────────────

def fleet_table(df: pd.DataFrame) -> None:
    """Full filterable requisition grid."""
    display_cols = {
        "status_label":    "Status",
        "ta_ref":          "TA Ref",
        "case_code":       "Case",
        "description":     "Description",
        "equipment":       "Equipment",
        "category_name":   "Category",
        "date_requested":  "Requested",
        "supplier":        "Supplier",
        "order_date":      "PO Date",
        "cost":            "Cost ($)",
        "est_readiness":   "Est. Ready",
        "port":            "Port",
        "rcvd":            "Received",
        "account_code":    "Code",
        "message":         "Msg Hash",
        "document_url":    "Document",
    }

    cols_present = [c for c in display_cols if c in df.columns]
    view = df[cols_present].copy().rename(columns={c: display_cols[c] for c in cols_present})

    for dc in ["Requested", "PO Date", "Est. Ready", "Received"]:
        if dc in view.columns:
            view[dc] = pd.to_datetime(view[dc], errors="coerce").dt.strftime("%d %b %Y").fillna("—")

    if "Cost ($)" in view.columns:
        view["Cost ($)"] = view["Cost ($)"].apply(
            lambda x: f"${x:,.2f}" if pd.notna(x) and x > 0 else "—"
        )

    col_cfg = {}
    if "Document" in view.columns:
        col_cfg["Document"] = st.column_config.LinkColumn("Document", display_text="📄 Open")

    st.dataframe(
        view,
        use_container_width=True,
        hide_index=True,
        column_config=col_cfg,
    )


# ──────────────────────────────────────────────
# SUPPLIER TABLE
# ──────────────────────────────────────────────

def supplier_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No supplier data available.")
        return
    view = df.copy()
    if "total_cost" in view.columns:
        view["total_cost"] = view["total_cost"].apply(lambda x: f"${x:,.2f}")
    if "on_time_pct" in view.columns:
        view["on_time_pct"] = view["on_time_pct"].apply(lambda x: f"{x:.1f}%")
    view.columns = [c.replace("_", " ").title() for c in view.columns]
    st.dataframe(view, use_container_width=True, hide_index=True)
