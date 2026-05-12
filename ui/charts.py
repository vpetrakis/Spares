"""
charts.py — All Plotly visualisations.
Returns fig objects; rendering is done in app.py via st.plotly_chart.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Shared theme ─────────────────────────────
DARK_BG     = "#0D1117"
CARD_BG     = "#161B22"
BORDER      = "#30363D"
TEXT_PRIMARY   = "#E6EDF3"
TEXT_MUTED  = "#8B949E"
GREEN  = "#3FB950"
AMBER  = "#E3B341"
RED    = "#F85149"
BLUE   = "#58A6FF"
PURPLE = "#BC8CFF"

STATUS_COLORS = {
    "🟢 Received":       GREEN,
    "🔵 Pending Supply": BLUE,
    "🟠 Ordered":        "#F0883E",
    "🟡 In Transit":     AMBER,
    "🔴 Transit Overdue":RED,
    "🔴 Supply Overdue": RED,
    "🔴 Order Overdue":  RED,
    "✖ Cancelled":       TEXT_MUTED,
    "⚪ Unknown":         BORDER,
}

LAYOUT_DEFAULTS = dict(
    paper_bgcolor=CARD_BG,
    plot_bgcolor=CARD_BG,
    font_color=TEXT_PRIMARY,
    font_family="Inter, sans-serif",
    margin=dict(l=16, r=16, t=36, b=16),
)


def _apply(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(**LAYOUT_DEFAULTS, title=dict(text=title, font_size=13, font_color=TEXT_MUTED))
    fig.update_xaxes(gridcolor=BORDER, zerolinecolor=BORDER)
    fig.update_yaxes(gridcolor=BORDER, zerolinecolor=BORDER)
    return fig


# ──────────────────────────────────────────────
# STATUS DISTRIBUTION BAR
# ──────────────────────────────────────────────

def status_bar(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart: count per pipeline status."""
    colors = [STATUS_COLORS.get(s, BLUE) for s in df["status_label"]]
    fig = go.Figure(go.Bar(
        x=df["count"],
        y=df["status_label"],
        orientation="h",
        marker_color=colors,
        text=df["count"],
        textposition="outside",
        textfont_color=TEXT_PRIMARY,
    ))
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title=dict(text="Pipeline status distribution", font_size=13, font_color=TEXT_MUTED),
        yaxis=dict(automargin=True, tickfont_color=TEXT_PRIMARY),
        xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
        height=max(250, len(df) * 44),
        showlegend=False,
    )
    return fig


# ──────────────────────────────────────────────
# CATEGORY COST TREEMAP
# ──────────────────────────────────────────────

def category_treemap(df: pd.DataFrame) -> go.Figure:
    """Treemap of total cost per equipment category."""
    data = df[df["total_cost"] > 0].copy()
    if data.empty:
        return _empty_fig("No cost data available")
    fig = px.treemap(
        data,
        path=["category"],
        values="total_cost",
        color="total_cost",
        color_continuous_scale=[[0, CARD_BG], [0.5, BLUE], [1, PURPLE]],
        custom_data=["count", "delayed"],
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>$%{value:,.0f}",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Cost: $%{value:,.2f}<br>"
            "Requisitions: %{customdata[0]}<br>"
            "Delayed: %{customdata[1]}<extra></extra>"
        ),
    )
    fig.update_layout(**LAYOUT_DEFAULTS, title=dict(text="Spend by category", font_size=13, font_color=TEXT_MUTED))
    fig.update_coloraxes(showscale=False)
    return fig


# ──────────────────────────────────────────────
# TIMELINE LINE CHART
# ──────────────────────────────────────────────

def timeline_chart(df: pd.DataFrame) -> go.Figure:
    """Monthly requisition volume line chart."""
    if df.empty:
        return _empty_fig("No timeline data")
    fig = go.Figure(go.Scatter(
        x=df["month_label"],
        y=df["requisitions"],
        mode="lines+markers+text",
        line=dict(color=BLUE, width=2),
        marker=dict(color=BLUE, size=7),
        text=df["requisitions"],
        textposition="top center",
        textfont_color=TEXT_PRIMARY,
        fill="tozeroy",
        fillcolor="rgba(88,166,255,0.08)",
    ))
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title=dict(text="Requisitions per month", font_size=13, font_color=TEXT_MUTED),
        xaxis=dict(gridcolor=BORDER, tickfont_color=TEXT_MUTED),
        yaxis=dict(gridcolor=BORDER, tickfont_color=TEXT_MUTED, dtick=1),
        height=280,
    )
    return fig


# ──────────────────────────────────────────────
# SUPPLIER BAR
# ──────────────────────────────────────────────

def supplier_bar(df: pd.DataFrame) -> go.Figure:
    """Grouped bar: orders vs spend per supplier."""
    if df.empty:
        return _empty_fig("No supplier data")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Orders",
        x=df["supplier"],
        y=df["orders"],
        marker_color=BLUE,
        yaxis="y",
    ))
    fig.add_trace(go.Bar(
        name="Total Cost ($)",
        x=df["supplier"],
        y=df["total_cost"],
        marker_color=PURPLE,
        yaxis="y2",
    ))
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title=dict(text="Supplier: order volume vs spend", font_size=13, font_color=TEXT_MUTED),
        yaxis=dict(title="Orders", gridcolor=BORDER, tickfont_color=TEXT_MUTED),
        yaxis2=dict(title="Cost ($)", overlaying="y", side="right",
                    gridcolor=BORDER, tickfont_color=TEXT_MUTED),
        barmode="group",
        legend=dict(bgcolor="rgba(0,0,0,0)", font_color=TEXT_MUTED),
        height=300,
    )
    return fig


# ──────────────────────────────────────────────
# SLA OVERDUE GAUGE
# ──────────────────────────────────────────────

def sla_gauge(delayed: int, total: int) -> go.Figure:
    pct = round(delayed / total * 100, 1) if total else 0
    color = GREEN if pct < 10 else AMBER if pct < 25 else RED
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number=dict(suffix="%", font_color=color, font_size=28),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor=TEXT_MUTED, tickfont_color=TEXT_MUTED),
            bar=dict(color=color, thickness=0.25),
            bgcolor=CARD_BG,
            bordercolor=BORDER,
            steps=[
                dict(range=[0, 10],  color="#0D4429"),
                dict(range=[10, 25], color="#2D1B00"),
                dict(range=[25, 100],color="#2D0A0A"),
            ],
        ),
        title=dict(text="SLA breach rate", font_color=TEXT_MUTED, font_size=13),
    ))
    fig.update_layout(
        paper_bgcolor=CARD_BG,
        font_color=TEXT_PRIMARY,
        margin=dict(l=24, r=24, t=40, b=24),
        height=220,
    )
    return fig


# ──────────────────────────────────────────────
# HELPER
# ──────────────────────────────────────────────

def _empty_fig(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, x=0.5, y=0.5, showarrow=False, font_color=TEXT_MUTED)
    fig.update_layout(**LAYOUT_DEFAULTS, height=200)
    return fig
