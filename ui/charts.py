"""
ui/charts.py — Premium Plotly chart factory  v2
Every function returns a go.Figure ready for st.plotly_chart(..., key=<unique>).
"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ── Design tokens ──────────────────────────────────────────────────────────────
BG       = "#0D1117"
CARD     = "#161B22"
CARD2    = "#1C2128"
BORDER   = "#30363D"
BORDER2  = "#21262D"
TEXT     = "#E6EDF3"
MUTED    = "#8B949E"
GREEN    = "#3FB950"
AMBER    = "#D29922"
RED      = "#F85149"
BLUE     = "#58A6FF"
PURPLE   = "#BC8CFF"
ORANGE   = "#F0883E"
TEAL     = "#39D353"

STATUS_COLOR: dict[str, str] = {
    "🟢 Received":        GREEN,
    "🔵 Pending Supply":  BLUE,
    "🟠 Ordered":         ORANGE,
    "🟡 In Transit":      AMBER,
    "🔴 Transit Overdue": RED,
    "🔴 Supply Overdue":  RED,
    "🔴 Order Overdue":   RED,
    "✖ Cancelled":        MUTED,
    "⚪ Unknown":          BORDER,
}

_BASE = dict(
    paper_bgcolor=CARD, plot_bgcolor=CARD,
    font=dict(family="Inter, sans-serif", color=TEXT, size=12),
    margin=dict(l=0, r=0, t=40, b=0),
)

def _fig(title: str = "", height: int = 300) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        **_BASE,
        height=height,
        title=dict(text=title, font=dict(size=12, color=MUTED), x=0, xanchor="left", pad=dict(l=4)),
    )
    return fig

def _grid(fig: go.Figure) -> go.Figure:
    fig.update_xaxes(gridcolor=BORDER2, zerolinecolor=BORDER2, showline=False)
    fig.update_yaxes(gridcolor=BORDER2, zerolinecolor=BORDER2, showline=False)
    return fig


# ── Status horizontal bar ──────────────────────────────────────────────────────

def status_bar(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No status data")
    df = df.sort_values("count")
    colors = [STATUS_COLOR.get(s, BLUE) for s in df["status_label"]]
    fig = _fig("Pipeline status", height=max(220, len(df) * 52))
    fig.add_trace(go.Bar(
        x=df["count"], y=df["status_label"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"  {v}" for v in df["count"]],
        textposition="outside",
        textfont=dict(color=TEXT, size=13, family="Inter, sans-serif"),
        hovertemplate="%{y}: <b>%{x}</b><extra></extra>",
    ))
    fig.update_layout(
        yaxis=dict(automargin=True, tickfont=dict(size=12, color=TEXT)),
        xaxis=dict(gridcolor=BORDER2, zerolinecolor=BORDER2, tickfont=dict(color=MUTED)),
        showlegend=False,
        bargap=0.35,
    )
    return fig


# ── Timeline area chart ────────────────────────────────────────────────────────

def timeline_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No timeline data")
    fig = _fig("Requisitions by month", height=260)
    fig.add_trace(go.Scatter(
        x=df["month_label"], y=df["requisitions"],
        mode="lines+markers",
        line=dict(color=BLUE, width=2.5, shape="spline"),
        marker=dict(color=BLUE, size=7, line=dict(color=BG, width=2)),
        fill="tozeroy",
        fillcolor="rgba(88,166,255,0.07)",
        hovertemplate="%{x}: <b>%{y} req.</b><extra></extra>",
    ))
    _grid(fig)
    fig.update_xaxes(tickfont=dict(color=MUTED, size=11))
    fig.update_yaxes(tickfont=dict(color=MUTED, size=11), dtick=1)
    return fig


# ── Cost by month bar ──────────────────────────────────────────────────────────

def cost_timeline_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No spend data")
    fig = _fig("Monthly spend (USD)", height=240)
    fig.add_trace(go.Bar(
        x=df["month_label"], y=df["cost"],
        marker=dict(
            color=df["cost"],
            colorscale=[[0, CARD2], [0.4, BLUE], [1, PURPLE]],
            showscale=False,
            line=dict(width=0),
        ),
        text=["$" + f"{v:,.0f}" for v in df["cost"]],
        textposition="outside",
        textfont=dict(color=MUTED, size=10),
        hovertemplate="%{x}: <b>$%{y:,.0f}</b><extra></extra>",
    ))
    _grid(fig)
    fig.update_xaxes(tickfont=dict(color=MUTED, size=11))
    fig.update_yaxes(tickfont=dict(color=MUTED, size=11), tickprefix="$")
    return fig


# ── SLA donut gauge ────────────────────────────────────────────────────────────

def sla_donut(delayed: int, total: int) -> go.Figure:
    ok    = max(0, total - delayed)
    pct   = round(delayed / total * 100, 1) if total else 0
    color = GREEN if pct == 0 else AMBER if pct < 20 else RED

    fig = go.Figure(go.Pie(
        values=[delayed, ok],
        labels=["Delayed", "On Track"],
        hole=0.72,
        marker=dict(colors=[color, BORDER2], line=dict(width=0)),
        textinfo="none",
        hovertemplate="%{label}: <b>%{value}</b><extra></extra>",
        sort=False,
    ))
    fig.add_annotation(
        text=f"<b>{pct}%</b>",
        x=0.5, y=0.55, font=dict(size=28, color=color, family="Inter, sans-serif"),
        showarrow=False,
    )
    fig.add_annotation(
        text="breach rate",
        x=0.5, y=0.35, font=dict(size=11, color=MUTED, family="Inter, sans-serif"),
        showarrow=False,
    )
    base_no_margin = {k:v for k,v in _BASE.items() if k != 'margin'}
    fig.update_layout(
        **base_no_margin, height=220,
        showlegend=False,
        margin=dict(l=0, r=0, t=8, b=0),
    )
    return fig


# ── Category treemap ───────────────────────────────────────────────────────────

def category_treemap(df: pd.DataFrame, key_suffix: str = "") -> go.Figure:
    data = df[df["total_cost"] > 0].copy()
    if data.empty:
        return _empty("No cost data")
    fig = px.treemap(
        data, path=["category"], values="total_cost",
        color="total_cost",
        color_continuous_scale=[[0, CARD2], [0.5, "#1e4a8a"], [1, PURPLE]],
        custom_data=["count", "delayed"],
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>$%{value:,.0f}",
        textfont=dict(family="Inter, sans-serif", size=12),
        hovertemplate=(
            "<b>%{label}</b><br>Spend: $%{value:,.2f}"
            "<br>Requisitions: %{customdata[0]}"
            "<br>Delayed: %{customdata[1]}<extra></extra>"
        ),
        marker=dict(line=dict(width=1.5, color=BG)),
    )
    base_no_margin = {k:v for k,v in _BASE.items() if k != 'margin'}
    fig.update_layout(
        **base_no_margin, height=260,
        title=dict(text="Spend by category", font=dict(size=12, color=MUTED),
                   x=0, xanchor="left", pad=dict(l=4)),
        margin=dict(l=0, r=0, t=36, b=0),
        coloraxis_showscale=False,
    )
    return fig


# ── Supplier grouped bar ───────────────────────────────────────────────────────

def supplier_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No supplier data")
    fig = _fig("Supplier: orders & spend", height=300)
    fig.add_trace(go.Bar(
        name="Orders", x=df["supplier"], y=df["orders"],
        marker=dict(color=BLUE, line=dict(width=0)),
        yaxis="y",
        hovertemplate="%{x}<br>Orders: <b>%{y}</b><extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Spend ($)", x=df["supplier"], y=df["total_cost"],
        marker=dict(color=PURPLE, line=dict(width=0)),
        yaxis="y2",
        hovertemplate="%{x}<br>Spend: <b>$%{y:,.0f}</b><extra></extra>",
    ))
    fig.update_layout(
        barmode="group", bargap=0.25, bargroupgap=0.08,
        yaxis=dict(title="Orders", gridcolor=BORDER2, tickfont=dict(color=MUTED)),
        yaxis2=dict(title="Spend ($)", overlaying="y", side="right",
                    gridcolor=BORDER2, tickfont=dict(color=MUTED), tickprefix="$"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=MUTED, size=11),
                    orientation="h", y=1.12, x=0),
    )
    fig.update_xaxes(tickfont=dict(color=TEXT, size=12))
    return fig


# ── Age distribution bar ───────────────────────────────────────────────────────

def age_bar(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No active items")
    df = df.sort_values("days_in_stage", ascending=True).tail(15)
    colors = [STATUS_COLOR.get(s, BLUE) for s in df["status_label"]]
    short_desc = df["description"].str[:28] + df["description"].apply(lambda x: "…" if len(str(x)) > 28 else "")
    fig = _fig("Days in current stage (active items)", height=max(220, len(df) * 40))
    fig.add_trace(go.Bar(
        x=df["days_in_stage"], y=short_desc, orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"  {int(v)}d" for v in df["days_in_stage"]],
        textposition="outside",
        textfont=dict(color=MUTED, size=10),
        hovertemplate="%{y}<br>Days: <b>%{x}</b><extra></extra>",
    ))
    fig.update_layout(
        yaxis=dict(automargin=True, tickfont=dict(size=10, color=TEXT)),
        xaxis=dict(gridcolor=BORDER2, zerolinecolor=BORDER2, tickfont=dict(color=MUTED)),
        showlegend=False, bargap=0.3,
    )
    return fig


# ── On-time rate horizontal bars ───────────────────────────────────────────────

def supplier_ontime_bar(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No supplier data")
    colors = [GREEN if v >= 90 else AMBER if v >= 70 else RED for v in df["on_time_pct"]]
    fig = _fig("Supplier on-time rate (%)", height=max(160, len(df) * 52))
    fig.add_trace(go.Bar(
        x=df["on_time_pct"], y=df["supplier"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"  {v:.0f}%" for v in df["on_time_pct"]],
        textposition="outside",
        textfont=dict(color=TEXT, size=12),
        hovertemplate="%{y}: <b>%{x:.1f}%</b><extra></extra>",
    ))
    fig.update_layout(
        xaxis=dict(range=[0, 115], gridcolor=BORDER2, zerolinecolor=BORDER2,
                   tickfont=dict(color=MUTED), ticksuffix="%"),
        yaxis=dict(automargin=True, tickfont=dict(color=TEXT, size=12)),
        showlegend=False, bargap=0.35,
    )
    return fig


# ── Helper ────────────────────────────────────────────────────────────────────

def _empty(msg: str) -> go.Figure:
    fig = _fig(height=180)
    fig.add_annotation(
        text=msg, x=0.5, y=0.5, showarrow=False,
        font=dict(color=MUTED, size=13, family="Inter, sans-serif"),
        xref="paper", yref="paper",
    )
    return fig
