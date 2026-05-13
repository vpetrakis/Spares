"""
ui/components.py — Premium Streamlit component library  v2
"""
from __future__ import annotations
import pandas as pd
import streamlit as st


# ──────────────────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────────────────

def inject_css() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* ── Reset & base ─────────────────────────────────────────────────── */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    .stApp { background: #0D1117; color: #E6EDF3; }
    .block-container { padding: 1.5rem 2rem 4rem !important; max-width: 1400px !important; }

    /* ── Sidebar ──────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: #0D1117;
        border-right: 1px solid #21262D;
    }
    section[data-testid="stSidebar"] .block-container { padding: 1.5rem 1rem !important; }

    /* ── Page header strip ────────────────────────────────────────────── */
    .page-header {
        display: flex; align-items: center; gap: 14px;
        padding: 0 0 20px 0; border-bottom: 1px solid #21262D; margin-bottom: 24px;
    }
    .page-header .vessel-badge {
        background: #161B22; border: 1px solid #30363D; border-radius: 8px;
        padding: 6px 14px; font-size: .78rem; color: #8B949E; letter-spacing: .04em;
        text-transform: uppercase; font-weight: 500;
    }
    .page-header h1 {
        font-size: 1.35rem !important; font-weight: 600 !important;
        color: #E6EDF3 !important; margin: 0 !important; line-height: 1 !important;
    }

    /* ── KPI grid ─────────────────────────────────────────────────────── */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 10px; margin-bottom: 28px;
    }
    @media (max-width: 1100px) { .kpi-grid { grid-template-columns: repeat(4, 1fr); } }
    @media (max-width: 700px)  { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }

    .kpi {
        background: #161B22; border: 1px solid #21262D; border-radius: 10px;
        padding: 16px 14px 14px; position: relative; overflow: hidden;
        transition: border-color .15s;
    }
    .kpi:hover { border-color: #30363D; }
    .kpi::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: var(--accent, #30363D);
    }
    .kpi .val {
        font-size: 1.75rem; font-weight: 700; line-height: 1; letter-spacing: -.02em;
        color: var(--accent, #E6EDF3);
    }
    .kpi .lbl {
        font-size: .68rem; font-weight: 500; color: #8B949E; margin-top: 5px;
        text-transform: uppercase; letter-spacing: .07em;
    }
    .kpi .sub {
        font-size: .7rem; color: #8B949E; margin-top: 2px;
    }

    /* accent colours */
    .kpi-blue   { --accent: #58A6FF; }
    .kpi-green  { --accent: #3FB950; }
    .kpi-red    { --accent: #F85149; }
    .kpi-amber  { --accent: #D29922; }
    .kpi-purple { --accent: #BC8CFF; }
    .kpi-muted  { --accent: #8B949E; }
    .kpi-teal   { --accent: #39D353; }

    /* ── Section label ────────────────────────────────────────────────── */
    .sec-label {
        font-size: .65rem; font-weight: 600; letter-spacing: .12em;
        text-transform: uppercase; color: #8B949E;
        border-bottom: 1px solid #21262D; padding-bottom: 7px;
        margin: 32px 0 14px;
    }

    /* ── Tabs ─────────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent; gap: 2px; border-bottom: 1px solid #21262D !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent; border-radius: 0; color: #8B949E;
        font-size: .82rem; font-weight: 500; padding: 8px 18px;
        border-bottom: 2px solid transparent !important;
    }
    .stTabs [aria-selected="true"] {
        background: transparent !important; color: #E6EDF3 !important;
        border-bottom: 2px solid #58A6FF !important;
    }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 20px !important; }

    /* ── DataFrames ───────────────────────────────────────────────────── */
    .stDataFrame { border: 1px solid #21262D !important; border-radius: 8px; overflow: hidden; }
    .stDataFrame thead tr th {
        background: #161B22 !important; color: #8B949E !important;
        font-size: .7rem !important; font-weight: 600 !important;
        text-transform: uppercase; letter-spacing: .06em;
        border-bottom: 1px solid #21262D !important;
    }
    .stDataFrame tbody tr:nth-child(even) td { background: rgba(22,27,34,.5) !important; }
    .stDataFrame tbody tr:hover td { background: #1C2128 !important; }
    .stDataFrame tbody td { font-size: .8rem !important; border-color: #21262D !important; }

    /* ── File uploader ────────────────────────────────────────────────── */
    [data-testid="stFileUploader"] {
        background: #161B22 !important; border: 1px dashed #30363D !important;
        border-radius: 10px !important;
    }

    /* ── Expander ─────────────────────────────────────────────────────── */
    .streamlit-expanderHeader {
        background: #161B22 !important; border-radius: 8px !important;
        border: 1px solid #21262D !important; font-size: .82rem !important;
    }
    .streamlit-expanderContent { border-color: #21262D !important; }

    /* ── Alerts ───────────────────────────────────────────────────────── */
    .stAlert { border-radius: 8px !important; }

    /* ── Multiselect ──────────────────────────────────────────────────── */
    [data-baseweb="select"] { background: #161B22 !important; border-color: #30363D !important; }
    [data-baseweb="tag"] { background: #21262D !important; }

    /* ── Download button ──────────────────────────────────────────────── */
    .stDownloadButton button {
        background: #161B22 !important; border: 1px solid #30363D !important;
        color: #8B949E !important; border-radius: 7px !important;
        font-size: .78rem !important; padding: 6px 16px !important;
    }
    .stDownloadButton button:hover {
        border-color: #58A6FF !important; color: #58A6FF !important;
    }

    /* ── Quality banner ───────────────────────────────────────────────── */
    .q-banner {
        background: #1C1600; border: 1px solid #D29922; border-radius: 8px;
        padding: 10px 16px; font-size: .8rem; color: #E3B341; margin-bottom: 20px;
        display: flex; align-items: flex-start; gap: 10px;
    }
    .q-banner ul { margin: 4px 0 0 16px; padding: 0; }
    .q-banner li { margin-bottom: 2px; }

    /* ── Sidebar nav items ────────────────────────────────────────────── */
    .nav-sla {
        background: #161B22; border: 1px solid #21262D; border-radius: 8px;
        padding: 10px 12px; font-size: .75rem; color: #8B949E; line-height: 1.7;
    }
    .nav-sla strong { color: #E6EDF3; }

    /* ── Spinner ──────────────────────────────────────────────────────── */
    .stSpinner > div { border-top-color: #58A6FF !important; }

    /* ── Scrollbar ────────────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0D1117; }
    ::-webkit-scrollbar-thumb { background: #30363D; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #8B949E; }
    </style>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# PAGE HEADER
# ──────────────────────────────────────────────────────────────────────────────

def page_header(vessel: str = "M/V ALEXIS", year: str = "2026",
                filtered: int = 0, total: int = 0) -> None:
    filter_badge = ""
    if filtered < total:
        filter_badge = (f"<span style='background:#2D1B00;border:1px solid #D29922;"
                        f"border-radius:6px;padding:4px 10px;font-size:.72rem;"
                        f"color:#E3B341;margin-left:auto'>⚡ {filtered} of {total} shown</span>")
    st.markdown(
        f"""<div class="page-header">
              <span style='font-size:1.8rem;line-height:1'>🚢</span>
              <div>
                <h1>Marine Spares Control Tower</h1>
                <div style='font-size:.75rem;color:#8B949E;margin-top:3px'>
                  {vessel} &nbsp;·&nbsp; {year} Spares Pipeline
                </div>
              </div>
              {filter_badge}
            </div>""",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# KPI CARDS
# ──────────────────────────────────────────────────────────────────────────────

def kpi_row(s: dict) -> None:
    delay_cls = "kpi-red" if s["delayed"] > 0 else "kpi-green"
    cards = [
        ("kpi-blue",   str(s["total"]),                    "Total Requisitions", ""),
        ("kpi-teal",   str(s["received"]),                 "Received / Onboard",  "fleet secured"),
        ("kpi-blue",   str(s["active"]),                   "Active",              "in pipeline"),
        ("kpi-muted",  str(s["cancelled"]),                "Cancelled",           "terminal"),
        (delay_cls,    str(s["delayed"]),                  "SLA Breached",        "needs action" if s["delayed"] else "all on track"),
        ("kpi-purple", f"${s['total_cost']:,.0f}",         "Total Spend",         "USD"),
        ("kpi-amber",  f"{s.get('avg_age', 0):.0f}d",     "Avg Stage Age",       "active items"),
    ]
    html = '<div class="kpi-grid">'
    for cls, val, lbl, sub in cards:
        html += (f'<div class="kpi {cls}">'
                 f'<div class="val">{val}</div>'
                 f'<div class="lbl">{lbl}</div>'
                 + (f'<div class="sub">{sub}</div>' if sub else "")
                 + '</div>')
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# SECTION LABEL
# ──────────────────────────────────────────────────────────────────────────────

def section(title: str, margin_top: bool = True) -> None:
    mt = "margin-top:32px" if margin_top else "margin-top:0"
    st.markdown(f'<div class="sec-label" style="{mt}">{title}</div>',
                unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# DATA QUALITY BANNER
# ──────────────────────────────────────────────────────────────────────────────

def warnings_banner(warnings: list[str]) -> None:
    if not warnings:
        return
    items = "".join(f"<li>{w}</li>" for w in warnings)
    st.markdown(
        f'<div class="q-banner"><span>⚠</span><div>'
        f'<strong>{len(warnings)} data quality notice(s)</strong>'
        f'<ul>{items}</ul></div></div>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# TRIAGE TABLE
# ──────────────────────────────────────────────────────────────────────────────

def triage_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.success("✅ All active requisitions are within SLA.")
        return
    col_map = {
        "status_label": "Status", "ta_ref": "TA Ref",
        "description": "Description", "equipment": "Equipment",
        "supplier": "Supplier", "order_date": "PO Date",
        "est_readiness": "Est. Ready", "sla_days_over": "Days Over",
        "cost": "Cost (USD)", "document_url": "Document",
    }
    cols = [c for c in col_map if c in df.columns]
    view = df[cols].rename(columns=col_map).copy()
    for dc in ["PO Date", "Est. Ready"]:
        if dc in view.columns:
            view[dc] = pd.to_datetime(view[dc], errors="coerce").dt.strftime("%d %b %Y").fillna("—")
    if "Cost (USD)" in view.columns:
        view["Cost (USD)"] = view["Cost (USD)"].apply(
            lambda x: f"${x:,.2f}" if pd.notna(x) and x > 0 else "—")
    cfg = {}
    if "Document" in view.columns:
        cfg["Document"] = st.column_config.LinkColumn("Document", display_text="📄 Open")
    st.dataframe(view, use_container_width=True, hide_index=True, column_config=cfg)


# ──────────────────────────────────────────────────────────────────────────────
# FLEET TABLE
# ──────────────────────────────────────────────────────────────────────────────

def fleet_table(df: pd.DataFrame, key: str = "fleet") -> None:
    col_map = {
        "status_label": "Status", "ta_ref": "TA Ref", "case_code": "Case",
        "description": "Description", "equipment": "Equipment",
        "category_name": "Category", "date_requested": "Requested",
        "supplier": "Supplier", "order_date": "PO Date", "cost": "Cost (USD)",
        "est_readiness": "Est. Ready", "port": "Port", "rcvd": "Received",
        "account_code": "Code", "document_url": "Document",
    }
    cols = [c for c in col_map if c in df.columns]
    view = df[cols].rename(columns=col_map).copy()
    for dc in ["Requested", "PO Date", "Est. Ready", "Received"]:
        if dc in view.columns:
            view[dc] = pd.to_datetime(view[dc], errors="coerce").dt.strftime("%d %b %Y").fillna("—")
    if "Cost (USD)" in view.columns:
        view["Cost (USD)"] = view["Cost (USD)"].apply(
            lambda x: f"${x:,.2f}" if pd.notna(x) and x > 0 else "—")
    cfg = {}
    if "Document" in view.columns:
        cfg["Document"] = st.column_config.LinkColumn("Document", display_text="📄 Open")
    st.dataframe(view, use_container_width=True, hide_index=True, column_config=cfg)


# ──────────────────────────────────────────────────────────────────────────────
# SUPPLIER TABLE
# ──────────────────────────────────────────────────────────────────────────────

def supplier_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No supplier data.")
        return
    view = df.rename(columns={
        "supplier": "Supplier", "orders": "Orders",
        "total_cost": "Total Spend", "on_time_pct": "On-Time %",
    }).copy()
    if "Total Spend" in view.columns:
        view["Total Spend"] = view["Total Spend"].apply(lambda x: f"${x:,.2f}")
    if "On-Time %" in view.columns:
        view["On-Time %"] = view["On-Time %"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(view, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────────────
# STAT CHIP (inline metric for use inside columns)
# ──────────────────────────────────────────────────────────────────────────────

def stat_chip(label: str, value: str, color: str = "#58A6FF") -> None:
    st.markdown(
        f'<div style="background:#161B22;border:1px solid #21262D;border-radius:8px;'
        f'padding:12px 14px;text-align:center;">'
        f'<div style="font-size:1.4rem;font-weight:700;color:{color}">{value}</div>'
        f'<div style="font-size:.68rem;color:#8B949E;text-transform:uppercase;'
        f'letter-spacing:.07em;margin-top:3px">{label}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
