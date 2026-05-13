"""
ui/charts.py — Premium Plotly chart factory  v3
All figures use explicit layout dicts — no **_BASE spread to avoid kwarg conflicts.
"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ── Design tokens ──────────────────────────────────────────────────────────────
BG      = "#080C10"
CARD    = "#0D1117"
CARD2   = "#1C2128"
BORDER  = "#1C2128"
BORDER2 = "#14191F"
TEXT    = "#CDD9E5"
MUTED   = "#444C56"
MUTED2  = "#768390"
GREEN   = "#3FB950"
AMBER   = "#D29922"
RED     = "#F85149"
BLUE    = "#58A6FF"
PURPLE  = "#BC8CFF"
ORANGE  = "#F0883E"
NAVY    = "#1B4F8A"

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

_FONT = dict(family="Inter, sans-serif", color=TEXT, size=12)


def _base_layout(height: int = 300, title: str = "",
                 margin: tuple = (0, 0, 40, 0)) -> dict:
    """Return a fresh layout dict. No **spread = no kwarg conflicts."""
    l, r, t, b = margin
    out = dict(
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        font=_FONT,
        height=height,
        margin=dict(l=l, r=r, t=t, b=b),
        hoverlabel=dict(
            bgcolor=CARD2, bordercolor=BORDER,
            font=dict(family="Inter, sans-serif", size=12, color=TEXT),
        ),
    )
    if title:
        out["title"] = dict(
            text=title,
            font=dict(size=11, color=MUTED2, family="Inter, sans-serif"),
            x=0, xanchor="left", pad=dict(l=2),
        )
    return out


def _grid(fig: go.Figure) -> go.Figure:
    fig.update_xaxes(gridcolor=BORDER2, zerolinecolor=BORDER2,
                     showline=False, tickfont=dict(color=MUTED, size=10))
    fig.update_yaxes(gridcolor=BORDER2, zerolinecolor=BORDER2,
                     showline=False, tickfont=dict(color=MUTED, size=10))
    return fig


def _empty(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(**_base_layout(height=160))
    fig.add_annotation(
        text=msg, x=0.5, y=0.5, showarrow=False,
        xref="paper", yref="paper",
        font=dict(color=MUTED2, size=12, family="Inter, sans-serif"),
    )
    return fig


# ── STATUS BAR ────────────────────────────────────────────────────────────────

def status_bar(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No status data")
    df = df.sort_values("count")
    colors = [STATUS_COLOR.get(s, BLUE) for s in df["status_label"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["count"], y=df["status_label"], orientation="h",
        marker=dict(
            color=colors,
            line=dict(width=0),
            opacity=0.9,
        ),
        text=[f" {v}" for v in df["count"]],
        textposition="outside",
        textfont=dict(color=TEXT, size=12, family="Inter, sans-serif"),
        hovertemplate="<b>%{y}</b><br>Count: %{x}<extra></extra>",
        cliponaxis=False,
    ))
    fig.update_layout(
        **_base_layout(height=max(200, len(df) * 54), title="Pipeline status",
                       margin=(0, 40, 36, 0)),
        yaxis=dict(automargin=True, tickfont=dict(size=11, color=TEXT),
                   gridcolor=BORDER2, zerolinecolor=BORDER2),
        xaxis=dict(gridcolor=BORDER2, zerolinecolor=BORDER2,
                   tickfont=dict(color=MUTED, size=10)),
        showlegend=False, bargap=0.38,
    )
    return fig


# ── TIMELINE ──────────────────────────────────────────────────────────────────

def timeline_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No timeline data")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["month_label"], y=df["requisitions"],
        mode="lines+markers",
        line=dict(color=BLUE, width=2.5, shape="spline"),
        marker=dict(
            color=CARD, size=8,
            line=dict(color=BLUE, width=2.5),
        ),
        fill="tozeroy",
        fillcolor="rgba(27,79,138,0.12)",
        hovertemplate="<b>%{x}</b><br>%{y} requisitions<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(height=240, title="Requisitions by month",
                       margin=(0, 20, 36, 0)),
        xaxis=dict(gridcolor=BORDER2, zerolinecolor=BORDER2,
                   tickfont=dict(color=MUTED2, size=10)),
        yaxis=dict(gridcolor=BORDER2, zerolinecolor=BORDER2,
                   tickfont=dict(color=MUTED, size=10), dtick=1),
    )
    return fig


# ── COST TIMELINE ─────────────────────────────────────────────────────────────

def cost_timeline_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No spend data (excluded cancelled)")
    max_cost = df["cost"].max()
    colors = [
        f"rgba({int(88 + (188-88)*v/max_cost)},{int(166 + (140-166)*v/max_cost)},{int(255 + (255-255)*v/max_cost)},0.85)"
        for v in df["cost"]
    ]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["month_label"], y=df["cost"],
        marker=dict(color=colors, line=dict(width=0)),
        text=["$" + f"{v:,.0f}" for v in df["cost"]],
        textposition="outside",
        textfont=dict(color=MUTED2, size=10),
        hovertemplate="<b>%{x}</b><br>Spend: $%{y:,.2f}<extra></extra>",
        cliponaxis=False,
    ))
    fig.update_layout(
        **_base_layout(height=240, title="Monthly spend — excl. cancelled",
                       margin=(0, 20, 36, 0)),
        xaxis=dict(gridcolor=BORDER2, zerolinecolor=BORDER2,
                   tickfont=dict(color=MUTED2, size=10)),
        yaxis=dict(gridcolor=BORDER2, zerolinecolor=BORDER2,
                   tickfont=dict(color=MUTED, size=10), tickprefix="$"),
        bargap=0.35,
    )
    return fig


# ── SLA DONUT ─────────────────────────────────────────────────────────────────

def sla_donut(delayed: int, total: int) -> go.Figure:
    ok    = max(0, total - delayed)
    pct   = round(delayed / total * 100, 1) if total else 0
    color = GREEN if pct == 0 else AMBER if pct < 20 else RED

    fig = go.Figure(go.Pie(
        values=[max(delayed, 0.001), ok],   # avoid zero-pie render bug
        labels=["Breached", "On Track"],
        hole=0.74,
        marker=dict(
            colors=[color, CARD2],
            line=dict(width=2, color=CARD),
        ),
        textinfo="none",
        hovertemplate="%{label}: <b>%{value}</b><extra></extra>",
        sort=False,
        direction="clockwise",
    ))
    fig.add_annotation(
        text=f"<b>{pct:.0f}%</b>",
        x=0.5, y=0.58,
        font=dict(size=30, color=color, family="Inter, sans-serif"),
        showarrow=False,
    )
    fig.add_annotation(
        text="breach rate",
        x=0.5, y=0.38,
        font=dict(size=10, color=MUTED2, family="Inter, sans-serif"),
        showarrow=False,
    )
    fig.update_layout(
        paper_bgcolor=CARD, plot_bgcolor=CARD,
        font=_FONT,
        height=210,
        margin=dict(l=0, r=0, t=10, b=10),
        showlegend=False,
        hoverlabel=dict(bgcolor=CARD2, bordercolor=BORDER, font=_FONT),
    )
    return fig


# ── CATEGORY TREEMAP ──────────────────────────────────────────────────────────

def category_treemap(df: pd.DataFrame) -> go.Figure:
    data = df[df["total_cost"] > 0].copy()
    if data.empty:
        return _empty("No cost data (all cancelled?)")
    fig = px.treemap(
        data, path=["category"], values="total_cost",
        color="total_cost",
        color_continuous_scale=[
            [0.0, "#0D1117"],
            [0.3, "#0D2D5C"],
            [0.7, "#1B4F8A"],
            [1.0, "#58A6FF"],
        ],
        custom_data=["count","delayed"],
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>$%{value:,.0f}",
        textfont=dict(family="Inter, sans-serif", size=11, color=TEXT),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Spend: $%{value:,.2f}<br>"
            "Req: %{customdata[0]}<br>"
            "Delayed: %{customdata[1]}"
            "<extra></extra>"
        ),
        marker=dict(line=dict(width=2, color=BG)),
    )
    fig.update_layout(
        paper_bgcolor=CARD, plot_bgcolor=CARD,
        font=_FONT,
        height=270,
        margin=dict(l=0, r=0, t=36, b=0),
        title=dict(
            text="Spend by category — excl. cancelled",
            font=dict(size=11, color=MUTED2, family="Inter, sans-serif"),
            x=0, xanchor="left", pad=dict(l=2),
        ),
        coloraxis_showscale=False,
        hoverlabel=dict(bgcolor=CARD2, bordercolor=BORDER, font=_FONT),
    )
    return fig


# ── SUPPLIER CHART ────────────────────────────────────────────────────────────

def supplier_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No supplier data")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Orders", x=df["supplier"], y=df["orders"],
        marker=dict(color=BLUE, line=dict(width=0), opacity=0.85),
        yaxis="y",
        hovertemplate="%{x}<br>Orders: <b>%{y}</b><extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Spend (USD)", x=df["supplier"], y=df["total_cost"],
        marker=dict(color=PURPLE, line=dict(width=0), opacity=0.85),
        yaxis="y2",
        hovertemplate="%{x}<br>Spend: <b>$%{y:,.0f}</b><extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(height=300, title="Supplier — orders & spend",
                       margin=(0, 60, 40, 0)),
        barmode="group", bargap=0.28, bargroupgap=0.06,
        yaxis=dict(title="Orders", gridcolor=BORDER2,
                   tickfont=dict(color=MUTED, size=10), title_font=dict(color=MUTED2)),
        yaxis2=dict(title="Spend (USD)", overlaying="y", side="right",
                    gridcolor=BORDER2, tickprefix="$",
                    tickfont=dict(color=MUTED, size=10), title_font=dict(color=MUTED2)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=MUTED2, size=11),
                    orientation="h", y=1.1, x=0),
        xaxis=dict(tickfont=dict(color=TEXT, size=11), gridcolor=BORDER2),
    )
    return fig


# ── AGE BAR ───────────────────────────────────────────────────────────────────

def age_bar(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No active items")
    df = df.sort_values("days_in_stage", ascending=True).tail(15)
    colors = [STATUS_COLOR.get(s, BLUE) for s in df["status_label"]]
    short  = (df["description"].str[:30]
              + df["description"].apply(lambda x: "…" if len(str(x)) > 30 else ""))
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["days_in_stage"], y=short,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0), opacity=0.85),
        text=[f" {int(v)}d" for v in df["days_in_stage"]],
        textposition="outside",
        textfont=dict(color=MUTED2, size=10),
        hovertemplate="%{y}<br>Days in stage: <b>%{x}</b><extra></extra>",
        cliponaxis=False,
    ))
    fig.update_layout(
        **_base_layout(height=max(200, len(df) * 40),
                       title="Days in current stage — active items",
                       margin=(0, 50, 36, 0)),
        yaxis=dict(automargin=True, tickfont=dict(size=10, color=TEXT),
                   gridcolor=BORDER2, zerolinecolor=BORDER2),
        xaxis=dict(gridcolor=BORDER2, zerolinecolor=BORDER2,
                   tickfont=dict(color=MUTED, size=10)),
        showlegend=False, bargap=0.32,
    )
    return fig


# ── SUPPLIER ON-TIME BAR ──────────────────────────────────────────────────────

def supplier_ontime_bar(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No supplier data")
    colors = [
        GREEN if v >= 90 else AMBER if v >= 70 else RED
        for v in df["on_time_pct"]
    ]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["on_time_pct"], y=df["supplier"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0), opacity=0.85),
        text=[f" {v:.0f}%" for v in df["on_time_pct"]],
        textposition="outside",
        textfont=dict(color=TEXT, size=11),
        hovertemplate="%{y}: <b>%{x:.1f}%</b><extra></extra>",
        cliponaxis=False,
    ))
    fig.update_layout(
        **_base_layout(height=max(160, len(df) * 54),
                       title="On-time delivery rate",
                       margin=(0, 40, 36, 0)),
        xaxis=dict(range=[0, 118], gridcolor=BORDER2, zerolinecolor=BORDER2,
                   tickfont=dict(color=MUTED, size=10), ticksuffix="%"),
        yaxis=dict(automargin=True, tickfont=dict(color=TEXT, size=11),
                   gridcolor=BORDER2, zerolinecolor=BORDER2),
        showlegend=False, bargap=0.38,
    )
    return fig
