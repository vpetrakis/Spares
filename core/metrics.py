"""
metrics.py — KPI calculation layer.
All dashboard numbers are derived here, never in the UI layer.
"""
from __future__ import annotations

from typing import Any
import pandas as pd


# ──────────────────────────────────────────────
# PIPELINE SUMMARY
# ──────────────────────────────────────────────

def pipeline_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Top-level KPI cards for the dashboard header."""
    total       = len(df)
    received    = (df["status"] == "RECEIVED").sum()
    cancelled   = (df["status"] == "CANCELLED").sum()
    active      = total - received - cancelled
    delayed     = df["sla_breach"].sum()
    total_cost  = df["cost"].sum(skipna=True)

    return {
        "total":       int(total),
        "received":    int(received),
        "active":      int(active),
        "cancelled":   int(cancelled),
        "delayed":     int(delayed),
        "total_cost":  round(float(total_cost), 2),
    }


# ──────────────────────────────────────────────
# STATUS DISTRIBUTION
# ──────────────────────────────────────────────

def status_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Count per status_label for bar/donut chart."""
    counts = (
        df.groupby("status_label")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    return counts


# ──────────────────────────────────────────────
# CATEGORY BREAKDOWN
# ──────────────────────────────────────────────

def category_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Cost and requisition count per equipment category."""
    grp = (
        df.groupby("category_name", dropna=False)
        .agg(
            count=("ta_ref", "count"),
            total_cost=("cost", "sum"),
            delayed=("sla_breach", "sum"),
        )
        .reset_index()
        .rename(columns={"category_name": "category"})
        .sort_values("total_cost", ascending=False)
    )
    grp["category"] = grp["category"].replace("", "Uncategorised")
    return grp


# ──────────────────────────────────────────────
# SUPPLIER PERFORMANCE
# ──────────────────────────────────────────────

def supplier_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Per-supplier order count, total spend, and on-time rate.
    Includes ghost-row sub-orders merged into parent.
    """
    rows = []

    # Primary supplier rows
    primary = df[df["supplier"].str.strip().ne("") & df["supplier"].notna()].copy()
    for _, row in primary.iterrows():
        rows.append({
            "supplier":   row["supplier"],
            "ta_ref":     row["ta_ref"],
            "cost":       row["cost"] if pd.notna(row["cost"]) else 0,
            "on_time":    not row["sla_breach"],
            "status":     row["status"],
        })
        # Sub-orders from ghost rows
        for sub in (row.get("sub_orders") or []):
            if sub.get("supplier"):
                rows.append({
                    "supplier":   sub["supplier"],
                    "ta_ref":     row["ta_ref"],
                    "cost":       sub.get("cost") or 0,
                    "on_time":    True,   # sub-orders are informational
                    "status":     row["status"],
                })

    if not rows:
        return pd.DataFrame(columns=["supplier", "orders", "total_cost", "on_time_pct"])

    sup_df = pd.DataFrame(rows)
    result = (
        sup_df.groupby("supplier")
        .agg(
            orders=("ta_ref", "count"),
            total_cost=("cost", "sum"),
            on_time_count=("on_time", "sum"),
        )
        .reset_index()
    )
    result["on_time_pct"] = (result["on_time_count"] / result["orders"] * 100).round(1)
    result = result.drop(columns=["on_time_count"]).sort_values("orders", ascending=False)
    return result


# ──────────────────────────────────────────────
# TIMELINE DATA
# ──────────────────────────────────────────────

def timeline_data(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly requisition count for timeline chart."""
    ts = df[df["date_requested"].notna()].copy()
    ts["month"] = ts["date_requested"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        ts.groupby("month")
        .size()
        .reset_index(name="requisitions")
        .sort_values("month")
    )
    monthly["month_label"] = monthly["month"].dt.strftime("%b %Y")
    return monthly


# ──────────────────────────────────────────────
# DELAYED ITEMS (for triage table)
# ──────────────────────────────────────────────

def delayed_items(df: pd.DataFrame) -> pd.DataFrame:
    """All SLA-breached rows, sorted by days overdue descending."""
    delayed = df[df["sla_breach"]].copy()
    if delayed.empty:
        return delayed
    return delayed.sort_values("sla_days_over", ascending=False)
