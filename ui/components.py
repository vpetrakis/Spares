"""
ui/components.py — Premium Streamlit component library  v3
Design philosophy: precision over decoration, signal over noise.
"""
from __future__ import annotations
import pandas as pd
import streamlit as st


# ──────────────────────────────────────────────────────────────────────────────
# CSS — the entire visual system in one injection
# ──────────────────────────────────────────────────────────────────────────────

def inject_css() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ═══ RESET & BASE ═══════════════════════════════════════════════════════ */
    *, *::before, *::after { box-sizing: border-box; }
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    .stApp {
        background: #080C10;
        color: #CDD9E5;
    }
    .block-container {
        padding: 2rem 2.5rem 6rem !important;
        max-width: 1440px !important;
    }

    /* ═══ SIDEBAR ════════════════════════════════════════════════════════════ */
    section[data-testid="stSidebar"] {
        background: #0D1117;
        border-right: 1px solid #1C2128;
        width: 260px !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding: 1.75rem 1.25rem !important;
    }
    /* Sidebar logo area */
    .sb-logo {
        display: flex; align-items: center; gap: 10px;
        padding-bottom: 20px; border-bottom: 1px solid #1C2128;
        margin-bottom: 20px;
    }
    .sb-logo .sb-icon {
        width: 36px; height: 36px; background: linear-gradient(135deg,#1B4F8A,#0D2D5C);
        border-radius: 9px; display: flex; align-items: center; justify-content: center;
        font-size: 1.1rem; border: 1px solid #2D4A7A;
        box-shadow: 0 0 12px rgba(27,79,138,0.3);
    }
    .sb-logo .sb-title { font-size: .88rem; font-weight: 600; color: #CDD9E5; line-height:1.2; }
    .sb-logo .sb-sub   { font-size: .7rem;  color: #768390; }

    /* Sidebar section label */
    .sb-section {
        font-size: .62rem; font-weight: 600; letter-spacing: .13em;
        text-transform: uppercase; color: #444C56;
        margin: 20px 0 8px;
    }
    /* SLA reference card */
    .sla-card {
        background: #0D1117; border: 1px solid #1C2128; border-radius: 8px;
        padding: 10px 12px; margin-top: 8px;
    }
    .sla-card .sla-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 3px 0; font-size: .72rem; color: #768390;
        border-bottom: 1px solid #1C2128;
    }
    .sla-card .sla-row:last-child { border-bottom: none; }
    .sla-card .sla-row .sla-val  { color: #58A6FF; font-weight: 600; font-family: 'JetBrains Mono', monospace; }

    /* ═══ MULTISELECT / SELECT / INPUTS ══════════════════════════════════════ */
    [data-baseweb="select"] > div {
        background: #0D1117 !important;
        border-color: #1C2128 !important;
        border-radius: 7px !important;
    }
    [data-baseweb="select"] > div:hover { border-color: #30363D !important; }
    [data-baseweb="tag"] {
        background: #1B3A5C !important;
        color: #58A6FF !important;
        border-radius: 4px !important;
    }
    [data-baseweb="popover"] { background: #0D1117 !important; border: 1px solid #1C2128 !important; }
    [data-baseweb="menu"] ul { background: #0D1117 !important; }
    [role="option"] { background: #0D1117 !important; color: #CDD9E5 !important; }
    [role="option"]:hover { background: #1C2128 !important; }

    /* ═══ FILE UPLOADER ══════════════════════════════════════════════════════ */
    [data-testid="stFileUploader"] section {
        background: #0D1117 !important;
        border: 1px dashed #2D4A7A !important;
        border-radius: 10px !important;
        transition: border-color .2s, background .2s;
    }
    [data-testid="stFileUploader"] section:hover {
        background: #0F1923 !important;
        border-color: #58A6FF !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] { color: #768390 !important; }

    /* ═══ PAGE HEADER ════════════════════════════════════════════════════════ */
    .page-header {
        display: flex; align-items: center; gap: 16px;
        padding: 0 0 22px 0;
        border-bottom: 1px solid #1C2128;
        margin-bottom: 26px;
    }
    .page-header-icon {
        width: 48px; height: 48px;
        background: linear-gradient(135deg,#1B4F8A 0%,#0D2D5C 100%);
        border-radius: 12px; display: flex; align-items: center;
        justify-content: center; font-size: 1.4rem;
        border: 1px solid #2D4A7A;
        box-shadow: 0 4px 20px rgba(27,79,138,0.25);
        flex-shrink: 0;
    }
    .page-header-text h1 {
        font-size: 1.3rem !important; font-weight: 600 !important;
        color: #CDD9E5 !important; margin: 0 !important;
        letter-spacing: -.01em; line-height: 1.2 !important;
    }
    .page-header-text .sub {
        font-size: .72rem; color: #768390; margin-top: 3px;
    }
    .filter-badge {
        margin-left: auto;
        background: #1B2D1B; border: 1px solid #2D5C2D;
        border-radius: 20px; padding: 5px 14px;
        font-size: .72rem; color: #3FB950; font-weight: 500;
        white-space: nowrap;
    }

    /* ═══ KPI GRID ═══════════════════════════════════════════════════════════ */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 10px;
        margin-bottom: 30px;
    }
    @media (max-width: 1200px) { .kpi-grid { grid-template-columns: repeat(4, 1fr); } }
    @media (max-width: 700px)  { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }

    .kpi {
        background: #0D1117;
        border: 1px solid #1C2128;
        border-radius: 10px;
        padding: 16px 14px 12px;
        position: relative;
        overflow: hidden;
        cursor: default;
        transition: border-color .18s, transform .18s, box-shadow .18s;
    }
    .kpi:hover {
        border-color: var(--kpi-color, #30363D);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.3), 0 0 0 1px var(--kpi-color, #30363D);
    }
    .kpi::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: var(--kpi-color, #1C2128);
    }
    .kpi::after {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(ellipse at top left, rgba(var(--kpi-rgb, 88,166,255), 0.04) 0%, transparent 60%);
        pointer-events: none;
    }
    .kpi .kpi-val {
        font-size: 1.65rem; font-weight: 700; line-height: 1;
        letter-spacing: -.025em;
        color: var(--kpi-color, #CDD9E5);
    }
    .kpi .kpi-lbl {
        font-size: .63rem; font-weight: 600; color: #444C56;
        text-transform: uppercase; letter-spacing: .08em;
        margin-top: 6px;
    }
    .kpi .kpi-sub {
        font-size: .68rem; color: #444C56; margin-top: 2px;
    }

    .kpi-blue   { --kpi-color:#58A6FF; --kpi-rgb:88,166,255; }
    .kpi-green  { --kpi-color:#3FB950; --kpi-rgb:63,185,80;  }
    .kpi-red    { --kpi-color:#F85149; --kpi-rgb:248,81,73;  }
    .kpi-amber  { --kpi-color:#D29922; --kpi-rgb:210,153,34; }
    .kpi-purple { --kpi-color:#BC8CFF; --kpi-rgb:188,140,255;}
    .kpi-muted  { --kpi-color:#444C56; --kpi-rgb:68,76,86;   }
    .kpi-teal   { --kpi-color:#39D353; --kpi-rgb:57,211,83;  }

    /* ═══ SECTION LABEL ══════════════════════════════════════════════════════ */
    .sec {
        display: flex; align-items: center; gap: 8px;
        font-size: .63rem; font-weight: 600; letter-spacing: .12em;
        text-transform: uppercase; color: #444C56;
        border-bottom: 1px solid #1C2128;
        padding-bottom: 8px;
        margin: 28px 0 14px;
    }
    .sec::before {
        content: '';
        display: inline-block; width: 3px; height: 12px;
        background: #1B4F8A; border-radius: 2px;
    }

    /* ═══ TABS ═══════════════════════════════════════════════════════════════ */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 1px solid #1C2128 !important;
        gap: 0; padding: 0;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 0 !important;
        color: #444C56 !important;
        font-size: .8rem !important;
        font-weight: 500 !important;
        padding: 10px 20px !important;
        border-bottom: 2px solid transparent !important;
        transition: color .15s, border-color .15s;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #768390 !important; }
    .stTabs [aria-selected="true"] {
        color: #58A6FF !important;
        border-bottom: 2px solid #58A6FF !important;
    }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 24px !important; }

    /* ═══ DATAFRAMES ══════════════════════════════════════════════════════════ */
    .stDataFrame {
        border: 1px solid #1C2128 !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    .stDataFrame thead tr th {
        background: #0D1117 !important;
        color: #444C56 !important;
        font-size: .65rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: .08em !important;
        border-bottom: 1px solid #1C2128 !important;
        padding: 10px 12px !important;
    }
    .stDataFrame tbody tr td {
        font-size: .78rem !important;
        color: #CDD9E5 !important;
        border-color: #1C2128 !important;
        padding: 8px 12px !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stDataFrame tbody tr:hover td { background: rgba(88,166,255,0.03) !important; }
    .stDataFrame tbody tr:nth-child(even) td { background: rgba(0,0,0,0.15) !important; }

    /* ═══ EXPANDER ════════════════════════════════════════════════════════════ */
    .streamlit-expanderHeader {
        background: #0D1117 !important;
        border: 1px solid #1C2128 !important;
        border-radius: 8px !important;
        font-size: .8rem !important;
        color: #768390 !important;
    }
    .streamlit-expanderHeader:hover { border-color: #30363D !important; color: #CDD9E5 !important; }
    .streamlit-expanderContent {
        background: #0D1117 !important;
        border: 1px solid #1C2128 !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
        padding: 12px !important;
    }

    /* ═══ ALERTS ══════════════════════════════════════════════════════════════ */
    .stAlert { border-radius: 8px !important; font-size: .82rem !important; }
    [data-testid="stNotification"] { border-radius: 8px !important; }

    /* ═══ BUTTONS ═════════════════════════════════════════════════════════════ */
    .stDownloadButton > button {
        background: #0D1117 !important;
        border: 1px solid #1C2128 !important;
        color: #768390 !important;
        border-radius: 7px !important;
        font-size: .75rem !important;
        padding: 6px 16px !important;
        font-family: 'Inter', sans-serif !important;
        transition: border-color .15s, color .15s, box-shadow .15s;
    }
    .stDownloadButton > button:hover {
        border-color: #58A6FF !important;
        color: #58A6FF !important;
        box-shadow: 0 0 8px rgba(88,166,255,0.15) !important;
    }

    /* ═══ SPINNER ═════════════════════════════════════════════════════════════ */
    .stSpinner > div { border-top-color: #58A6FF !important; }

    /* ═══ SCROLLBAR ═══════════════════════════════════════════════════════════ */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #1C2128; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #30363D; }

    /* ═══ QUALITY BANNER ══════════════════════════════════════════════════════ */
    .q-banner {
        background: #1A1400;
        border: 1px solid #3D3000;
        border-left: 3px solid #D29922;
        border-radius: 0 8px 8px 0;
        padding: 10px 16px;
        font-size: .78rem; color: #D29922;
        margin-bottom: 18px;
        display: flex; align-items: flex-start; gap: 10px;
    }
    .q-banner ul { margin: 4px 0 0 14px; padding: 0; color: #957020; }

    /* ═══ STAT CHIP ═══════════════════════════════════════════════════════════ */
    .stat-chip {
        background: #0D1117;
        border: 1px solid #1C2128;
        border-radius: 8px;
        padding: 14px;
        text-align: center;
    }
    .stat-chip .chip-val {
        font-size: 1.4rem; font-weight: 700;
        letter-spacing: -.02em;
    }
    .stat-chip .chip-lbl {
        font-size: .63rem; color: #444C56;
        text-transform: uppercase; letter-spacing: .08em;
        margin-top: 4px;
    }

    /* ═══ LANDING PAGE ════════════════════════════════════════════════════════ */
    .landing {
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        min-height: 65vh; text-align: center; gap: 0;
    }
    .landing-icon {
        font-size: 3rem;
        background: linear-gradient(135deg,#1B4F8A,#0D2D5C);
        width: 80px; height: 80px; border-radius: 20px;
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 20px;
        border: 1px solid #2D4A7A;
        box-shadow: 0 8px 32px rgba(27,79,138,0.3);
    }
    .landing h2 { font-size: 1.5rem; color: #CDD9E5; margin: 0 0 8px; font-weight: 600; }
    .landing p  { color: #444C56; font-size: .88rem; max-width: 380px; margin: 0; line-height: 1.6; }

    /* ═══ CANCELLED BADGE ═════════════════════════════════════════════════════ */
    .cancelled-badge {
        display: inline-flex; align-items: center; gap: 5px;
        background: rgba(68,76,86,0.2); border: 1px solid #2D333B;
        border-radius: 4px; padding: 2px 8px;
        font-size: .7rem; color: #768390;
        font-family: 'JetBrains Mono', monospace;
    }
    </style>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# PAGE HEADER
# ──────────────────────────────────────────────────────────────────────────────

def page_header(filtered: int = 0, total: int = 0) -> None:
    badge = ""
    if 0 < filtered < total:
        badge = f'<div class="filter-badge">⚡ {filtered} of {total} shown</div>'
    st.markdown(
        f"""<div class="page-header">
              <div class="page-header-icon">🚢</div>
              <div class="page-header-text">
                <h1>Marine Spares Control Tower</h1>
                <div class="sub">M/V ALEXIS &nbsp;·&nbsp; 2026 Spares Pipeline</div>
              </div>
              {badge}
            </div>""",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# KPI ROW
# ──────────────────────────────────────────────────────────────────────────────

def kpi_row(s: dict) -> None:
    delay_cls = "kpi-red" if s["delayed"] > 0 else "kpi-green"
    cards = [
        ("kpi-blue",   str(s["total"]),                      "Total",         "requisitions"),
        ("kpi-teal",   str(s["received"]),                   "Received",      "onboard"),
        ("kpi-blue",   str(s["active"]),                     "Active",        "in pipeline"),
        ("kpi-muted",  str(s["cancelled"]),                  "Cancelled",     "excluded from budget"),
        (delay_cls,    str(s["delayed"]),                    "SLA Breach",    "action needed" if s["delayed"] else "all clear"),
        ("kpi-purple", f"${s['total_cost']:,.0f}",           "Budget Spend",  "excl. cancelled"),
        ("kpi-amber",  f"{s.get('avg_age', 0):.0f}d",       "Avg Stage Age", "active items"),
    ]
    html = '<div class="kpi-grid">'
    for cls, val, lbl, sub in cards:
        html += (f'<div class="kpi {cls}">'
                 f'<div class="kpi-val">{val}</div>'
                 f'<div class="kpi-lbl">{lbl}</div>'
                 f'<div class="kpi-sub">{sub}</div>'
                 f'</div>')
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# SECTION LABEL
# ──────────────────────────────────────────────────────────────────────────────

def section(title: str) -> None:
    st.markdown(f'<div class="sec">{title}</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# DATA QUALITY BANNER
# ──────────────────────────────────────────────────────────────────────────────

def warnings_banner(warnings: list[str]) -> None:
    if not warnings:
        return
    items = "".join(f"<li>{w}</li>" for w in warnings)
    st.markdown(
        f'<div class="q-banner">⚠<div>'
        f'<strong>{len(warnings)} data notice(s)</strong>'
        f'<ul>{items}</ul></div></div>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# STAT CHIP
# ──────────────────────────────────────────────────────────────────────────────

def stat_chip(label: str, value: str, color: str = "#58A6FF") -> None:
    st.markdown(
        f'<div class="stat-chip">'
        f'<div class="chip-val" style="color:{color}">{value}</div>'
        f'<div class="chip-lbl">{label}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR WIDGET
# ──────────────────────────────────────────────────────────────────────────────

def sidebar_header() -> None:
    st.markdown(
        '<div class="sb-logo">'
        '<div class="sb-icon">🚢</div>'
        '<div><div class="sb-title">Control Tower</div>'
        '<div class="sb-sub">M/V ALEXIS · 2026</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )


def sidebar_sla_card() -> None:
    st.markdown(
        '<div class="sb-section">SLA Thresholds</div>'
        '<div class="sla-card">'
        '<div class="sla-row"><span>Supply</span><span class="sla-val">7d</span></div>'
        '<div class="sla-row"><span>Finance</span><span class="sla-val">5d</span></div>'
        '<div class="sla-row"><span>Ordered</span><span class="sla-val">45d</span></div>'
        '<div class="sla-row"><span>Transit</span><span class="sla-val">21d</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# DATA TABLES
# ──────────────────────────────────────────────────────────────────────────────

def _fmt_dates(view: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in view.columns:
            view[c] = pd.to_datetime(view[c], errors="coerce").dt.strftime("%d %b %Y").fillna("—")
    return view


def _fmt_cost(view: pd.DataFrame, col: str = "Cost (USD)") -> pd.DataFrame:
    if col in view.columns:
        view[col] = view[col].apply(lambda x: f"${x:,.2f}" if pd.notna(x) and x > 0 else "—")
    return view


def triage_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.success("✅ All active requisitions are within SLA thresholds.")
        return
    col_map = {
        "status_label":"Status","ta_ref":"TA Ref","description":"Description",
        "equipment":"Equipment","supplier":"Supplier","order_date":"PO Date",
        "est_readiness":"Est. Ready","sla_days_over":"Days Over","cost":"Cost (USD)",
        "document_url":"Document",
    }
    cols = [c for c in col_map if c in df.columns]
    view = df[cols].rename(columns=col_map).copy()
    view = _fmt_dates(view, ["PO Date","Est. Ready"])
    view = _fmt_cost(view)
    cfg  = {}
    if "Document" in view.columns:
        cfg["Document"] = st.column_config.LinkColumn("Document", display_text="📄 Open")
    st.dataframe(view, use_container_width=True, hide_index=True, column_config=cfg)


def fleet_table(df: pd.DataFrame) -> None:
    col_map = {
        "status_label":"Status","ta_ref":"TA Ref","case_code":"Case",
        "description":"Description","equipment":"Equipment",
        "category_name":"Category","date_requested":"Requested",
        "supplier":"Supplier","order_date":"PO Date","cost":"Cost (USD)",
        "est_readiness":"Est. Ready","port":"Port","rcvd":"Received",
        "account_code":"Code","document_url":"Document",
    }
    cols = [c for c in col_map if c in df.columns]
    view = df[cols].rename(columns=col_map).copy()
    view = _fmt_dates(view, ["Requested","PO Date","Est. Ready","Received"])
    view = _fmt_cost(view)
    cfg  = {}
    if "Document" in view.columns:
        cfg["Document"] = st.column_config.LinkColumn("Document", display_text="📄 Open")
    st.dataframe(view, use_container_width=True, hide_index=True, column_config=cfg)


def cancelled_table(df: pd.DataFrame) -> None:
    """Shows cancelled rows with their original cost for audit."""
    col_map = {
        "ta_ref":"TA Ref","description":"Description","equipment":"Equipment",
        "supplier":"Supplier","confirmation":"Cancellation Note",
        "cost_raw":"Original Cost",
    }
    cols = [c for c in col_map if c in df.columns]
    view = df[cols].rename(columns=col_map).copy()
    if "Original Cost" in view.columns:
        view["Original Cost"] = view["Original Cost"].apply(
            lambda x: f"${x:,.2f}" if pd.notna(x) and x > 0 else "—")
    st.dataframe(view, use_container_width=True, hide_index=True)


def supplier_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No supplier data.")
        return
    view = df.rename(columns={
        "supplier":"Supplier","orders":"Orders",
        "total_cost":"Total Spend","on_time_pct":"On-Time %",
    }).copy()
    if "Total Spend" in view.columns:
        view["Total Spend"] = view["Total Spend"].apply(lambda x: f"${x:,.2f}")
    if "On-Time %" in view.columns:
        view["On-Time %"] = view["On-Time %"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(view, use_container_width=True, hide_index=True)
