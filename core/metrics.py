"""
core/metrics.py — KPI calculation layer  v3
Rule: ALL budget/cost metrics use df where is_cancelled==False.
      Cancelled rows appear ONLY in the cancelled audit section.
"""
from __future__ import annotations
from typing import Any
import pandas as pd


def _active(df: pd.DataFrame) -> pd.DataFrame:
    """Return non-cancelled rows. Used as base for all financial metrics."""
    return df[~df["is_cancelled"]].copy()


def pipeline_summary(df: pd.DataFrame) -> dict[str, Any]:
    total      = len(df)
    received   = int((df["status"] == "RECEIVED").sum())
    cancelled  = int((df["status"] == "CANCELLED").sum())
    active     = total - received - cancelled
    delayed    = int(df["sla_breach"].sum())                    # cancelled never breach
    # Budget = cost of non-cancelled rows only
    budget_df  = _active(df)
    total_cost = round(float(budget_df["cost"].sum(skipna=True)), 2)
    avg_age    = (
        round(float(df["days_in_stage"].dropna().mean()), 1)
        if df["days_in_stage"].notna().any() else 0.0
    )
    return dict(
        total=total, received=received, active=active,
        cancelled=cancelled, delayed=delayed,
        total_cost=total_cost, avg_age=avg_age,
    )


def status_distribution(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("status_label").size()
          .reset_index(name="count")
          .sort_values("count", ascending=False)
    )


def category_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Cost breakdown excludes cancelled rows."""
    base = _active(df)
    grp = (
        base.groupby("category_name", dropna=False)
            .agg(count=("ta_ref","count"), total_cost=("cost","sum"),
                 delayed=("sla_breach","sum"))
            .reset_index()
            .rename(columns={"category_name": "category"})
            .sort_values("total_cost", ascending=False)
    )
    grp["category"] = grp["category"].replace("", "Uncategorised")
    return grp


def supplier_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Supplier metrics exclude cancelled orders."""
    base = _active(df)
    rows = []
    primary = base[base["supplier"].str.strip().ne("") & base["supplier"].notna()]
    for _, row in primary.iterrows():
        rows.append(dict(
            supplier=row["supplier"], ta_ref=row["ta_ref"],
            cost=row["cost"] if pd.notna(row["cost"]) else 0,
            on_time=not row["sla_breach"],
        ))
        for sub in (row.get("sub_orders") or []):
            if sub.get("supplier"):
                rows.append(dict(
                    supplier=sub["supplier"], ta_ref=row["ta_ref"],
                    cost=sub.get("cost") or 0, on_time=True,
                ))
    if not rows:
        return pd.DataFrame(columns=["supplier","orders","total_cost","on_time_pct"])
    sup = pd.DataFrame(rows)
    result = (
        sup.groupby("supplier")
           .agg(orders=("ta_ref","count"), total_cost=("cost","sum"),
                on_time_count=("on_time","sum"))
           .reset_index()
    )
    result["on_time_pct"] = (result["on_time_count"] / result["orders"] * 100).round(1)
    return result.drop(columns=["on_time_count"]).sort_values("total_cost", ascending=False)


def timeline_data(df: pd.DataFrame) -> pd.DataFrame:
    """Requisition timeline includes all rows (volume, not cost)."""
    ts = df[df["date_requested"].notna()].copy()
    if ts.empty:
        return pd.DataFrame(columns=["month_label","requisitions"])
    ts["month"] = ts["date_requested"].dt.to_period("M").dt.to_timestamp()
    monthly = (ts.groupby("month").size()
                 .reset_index(name="requisitions")
                 .sort_values("month"))
    monthly["month_label"] = monthly["month"].dt.strftime("%b %Y")
    return monthly


def delayed_items(df: pd.DataFrame) -> pd.DataFrame:
    delayed = df[df["sla_breach"]].copy()
    return delayed.sort_values("sla_days_over", ascending=False) if not delayed.empty else delayed


def age_distribution(df: pd.DataFrame) -> pd.DataFrame:
    active = df[
        ~df["status"].isin(["RECEIVED","CANCELLED"]) & df["days_in_stage"].notna()
    ].copy()
    if active.empty:
        return pd.DataFrame(columns=["ta_ref","description","days_in_stage","status_label"])
    return (active[["ta_ref","description","days_in_stage","status_label"]]
            .sort_values("days_in_stage", ascending=False))


def cost_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly spend excludes cancelled."""
    base = _active(df)
    ts   = base[base["order_date"].notna() & base["cost"].notna() & (base["cost"] > 0)].copy()
    if ts.empty:
        return pd.DataFrame(columns=["month_label","cost"])
    ts["month"] = ts["order_date"].dt.to_period("M").dt.to_timestamp()
    monthly = (ts.groupby("month")["cost"].sum().reset_index().sort_values("month"))
    monthly["month_label"] = monthly["month"].dt.strftime("%b %Y")
    return monthly
