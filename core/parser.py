"""
core/parser.py — Marine Spares Data Engine  v4
Fixes vs v3:
  - _norm_code: str(x).strip() — handles raw int/float from Pandas 3.x ArrowDtype
  - Ghost row detection: only fires when ta_ref IS None (rows with ta_ref always kept)
  - Hyperlink resolution: also checks cell VALUE for embedded path strings
  - invoice / non-date columns: protected from to_datetime crash
  - OF-26-2569 pattern: NR=None + SEQ=None + TA REF present → valid requisition
  - Vessel name extracted from row 1 for multi-vessel support
"""
from __future__ import annotations

import io
import re
import urllib.parse
from datetime import datetime, date
from typing import Optional

import openpyxl
import pandas as pd

# ── Column mapping ─────────────────────────────────────────────────────────────
COL_MAP: dict[str, str] = {
    "NR":             "nr",
    "TA REF":         "ta_ref",
    "CASE":           "case_code",
    " ":              "seq",
    "REF":            "ref_date",
    "EQUIPMENT":      "equipment",
    "DESCRIPTION":    "description",
    "DATE":           "date_requested",
    "MESSAGE":        "message",
    "ORDERED":        "supplier",
    "CODE":           "account_code",
    "CONFIRMATION ":  "confirmation",
    "ORDER DATE":     "order_date",
    "COST":           "cost",
    "EST. READINESS": "est_readiness",
    "PORT ":          "port",
    "AWB":            "awb",
    "RCVD":           "rcvd",
    "INVOICE":        "invoice",
}

SLA: dict[str, int] = {
    "supply":  7,
    "finance": 5,
    "ordered": 45,
    "transit": 21,
}

_HYPERLINK_BASE = r"Z:\Marine_Dept\Alexis\Spares\Hyperlinks 2026"

_PRIORITY_COLS = [
    "vessel", "status_label", "flag", "ta_ref", "case_code", "description",
    "equipment", "category_name", "date_requested", "supplier", "order_date",
    "cost", "cost_raw", "is_cancelled",
    "est_readiness", "port", "rcvd", "account_code", "message", "confirmation",
    "awb", "invoice", "document_url", "status", "sla_breach", "sla_days_over",
    "days_in_stage", "sub_orders",
]

# Regex for embedded path strings in cell values
_PATH_RE = re.compile(r"(\.\.[\\/].*\.(?:doc|pdf|xls|xlsx|docx))", re.IGNORECASE)


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _resolve_hyperlink(raw: str) -> str:
    """Convert relative UNC / encoded path to file:/// URL."""
    decoded = urllib.parse.unquote(raw)
    m = re.search(r"MODION(.+)$", decoded, re.IGNORECASE)
    if m:
        tail = m.group(1).replace("\\", "/")
        base = _HYPERLINK_BASE.replace("\\", "/")
        return f"file:///{base}/MODION{tail}"
    return decoded


def _extract_path_from_value(val: object) -> Optional[str]:
    """If a cell VALUE contains an embedded path string, extract it."""
    if val is None:
        return None
    s = str(val)
    m = _PATH_RE.search(s)
    return _resolve_hyperlink(m.group(1)) if m else None


def _ts(val) -> Optional[pd.Timestamp]:
    """Safely coerce any value to Timestamp; returns None for NaT/None/bad."""
    if val is None:
        return None
    try:
        result = pd.Timestamp(val)
        return None if pd.isnull(result) else result
    except Exception:
        return None


def _is_cancelled(confirmation: object) -> bool:
    return "CANCEL" in str(confirmation or "").upper()


def _norm_code(x: object) -> str:
    """
    Normalise account_code to string.
    Handles: int (5513), float (5513.0), str ('5513'), str ('5517C'), None/NaN.
    IMPORTANT: accepts any type — does NOT assume str input (Pandas 3.x ArrowDtype).
    """
    if x is None:
        return ""
    s = str(x).strip()
    if s in ("", "None", "nan", "NaN", "<NA>"):
        return ""
    try:
        # Pure-integer codes: 5513.0 → "5513"
        f = float(s)
        if f == int(f):
            return str(int(f))
        return s
    except (ValueError, OverflowError):
        return s


# ──────────────────────────────────────────────────────────────────────────────
# STATE MACHINE
# ──────────────────────────────────────────────────────────────────────────────

def _compute_state(row: dict, now: pd.Timestamp) -> dict:
    rcvd       = _ts(row.get("rcvd"))
    est_ready  = _ts(row.get("est_readiness"))
    order_date = _ts(row.get("order_date"))
    date_req   = _ts(row.get("date_requested"))
    confirm    = str(row.get("confirmation") or "").upper()

    if "CANCEL" in confirm:
        return dict(status="CANCELLED", status_label="✖ Cancelled",
                    flag="CANCELLED", days_in_stage=None, sla_breach=False, sla_days_over=0)

    if rcvd is not None:
        return dict(status="RECEIVED", status_label="🟢 Received",
                    flag="OK", days_in_stage=int((now - rcvd).days),
                    sla_breach=False, sla_days_over=0)

    if est_ready is not None:
        overdue = int((now - est_ready).days)
        breach  = overdue > 0
        return dict(
            status="OVERDUE_TRANSIT" if breach else "IN_TRANSIT",
            status_label="🔴 Transit Overdue" if breach else "🟡 In Transit",
            flag="DELAYED" if breach else "OK",
            days_in_stage=abs(overdue),
            sla_breach=breach,
            sla_days_over=overdue if breach else 0,
        )

    if order_date is not None:
        days  = int((now - order_date).days)
        breach = days > SLA["ordered"]
        return dict(
            status="OVERDUE_ORDERED" if breach else "ORDERED",
            status_label="🔴 Order Overdue" if breach else "🟠 Ordered",
            flag="DELAYED" if breach else "OK",
            days_in_stage=days,
            sla_breach=breach,
            sla_days_over=max(0, days - SLA["ordered"]),
        )

    if date_req is not None:
        days  = int((now - date_req).days)
        breach = days > SLA["supply"]
        return dict(
            status="OVERDUE_SUPPLY" if breach else "PENDING_SUPPLY",
            status_label="🔴 Supply Overdue" if breach else "🔵 Pending Supply",
            flag="DELAYED" if breach else "OK",
            days_in_stage=days,
            sla_breach=breach,
            sla_days_over=max(0, days - SLA["supply"]),
        )

    return dict(status="UNKNOWN", status_label="⚪ Unknown",
                flag="ERROR", days_in_stage=None, sla_breach=False, sla_days_over=0)


# ──────────────────────────────────────────────────────────────────────────────
# INDEX SHEET PARSER
# ──────────────────────────────────────────────────────────────────────────────

def _parse_index(ws) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for row in ws.iter_rows(min_row=4, values_only=True):
        padded = (list(row) + [None] * 10)[:10]
        name, case, code = padded[0], padded[1], padded[2]
        cost, rcvd_count, processed = padded[5], padded[7], padded[9]
        if code is None:
            continue
        code_str = _norm_code(code)
        if not code_str:
            continue
        result[code_str] = {
            "category_name":          str(name).strip() if name else "",
            "case_code":              str(case).strip() if case else "",
            "cost":                   float(cost) if cost else 0.0,
            "requisitions_received":  int(rcvd_count) if rcvd_count else 0,
            "requisitions_processed": int(processed) if processed else 0,
        }
    return result


# ──────────────────────────────────────────────────────────────────────────────
# VESSEL NAME EXTRACTOR
# ──────────────────────────────────────────────────────────────────────────────

def _extract_vessel(ws) -> str:
    """Read vessel name from row 1, col A (e.g. 'M/V ALEXIS - SPARE CASES 2026')."""
    cell = ws.cell(row=1, column=1).value
    if not cell:
        return ""
    s = str(cell)
    # Pattern: "M/V <NAME> - SPARE..." → extract <NAME>
    m = re.match(r"M/V\s+(.+?)\s*[-–]", s, re.IGNORECASE)
    return m.group(1).strip().title() if m else s.strip()


# ──────────────────────────────────────────────────────────────────────────────
# MAIN PARSER
# ──────────────────────────────────────────────────────────────────────────────

def parse_workbook(file_bytes: bytes) -> tuple[pd.DataFrame, dict, list[str]]:
    """
    Parse any Marine Spares workbook (ALEXIS, STEFANOS T, MINOAN SEA, …).

    Guarantees:
      - Cancelled rows → cost=NaN, cost_raw=original  (budget safe)
      - Ghost rows (split orders, NR/SEQ=None but TA REF present) → kept as records
      - account_code normalised from any type (int/float/str) without crash
      - Embedded path strings in MESSAGE cell values resolved as document_url
      - Non-date 'invoice' strings (e.g. '60 DAYS') silently ignored

    Returns:
        df          — one row per requisition
        index_kpis  — category KPI dict from INDEX sheet
        warnings    — non-fatal data quality messages
    """
    warnings: list[str] = []
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)

    spares_name = next((s for s in wb.sheetnames if "SPARES" in s.upper()), None)
    index_name  = next((s for s in wb.sheetnames if "INDEX"  in s.upper()), None)
    if not spares_name:
        raise ValueError("Cannot find a SPARES sheet in this workbook.")

    ws         = wb[spares_name]
    index_kpis = _parse_index(wb[index_name]) if index_name else {}
    vessel     = _extract_vessel(ws)

    # ── Locate header row ─────────────────────────────────────────────────────
    header_row = None
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=20, values_only=True)):
        if row and "TA REF" in row:
            header_row = i + 1
            break
    if header_row is None:
        raise ValueError("Cannot find header row containing 'TA REF'.")

    col_idx: dict[int, str] = {}
    for i, cell in enumerate(ws[header_row]):
        if cell.value is not None:
            raw_h = str(cell.value)
            col_idx[i] = COL_MAP.get(raw_h, raw_h.lower().replace(" ", "_").strip())

    # ── Read data rows ─────────────────────────────────────────────────────────
    records: list[dict] = []

    for row in ws.iter_rows(min_row=header_row + 1):
        raw: dict = {}
        for i, cell in enumerate(row):
            if i not in col_idx:
                continue
            raw[col_idx[i]] = cell.value
            # Capture hyperlink object target
            if cell.hyperlink and cell.hyperlink.target:
                raw[f"__hl_{col_idx[i]}"] = cell.hyperlink.target

        ta_ref = raw.get("ta_ref")
        seq    = raw.get("seq")

        # ── Ghost row: ONLY when ta_ref is truly absent ────────────────────
        # Rows with ta_ref present (even if NR/SEQ missing) are valid requisitions.
        if (ta_ref is None and seq is None
                and (raw.get("supplier") or raw.get("order_date") or raw.get("cost"))):
            if records:
                parent   = records[-1]
                sub_cost = raw.get("cost")
                parent.setdefault("sub_orders", []).append({
                    "supplier":   raw.get("supplier"),
                    "order_date": raw.get("order_date"),
                    "cost":       sub_cost,
                })
                if sub_cost is not None and not parent.get("_cancelled_flag", False):
                    parent["cost"] = (parent.get("cost") or 0.0) + float(sub_cost)
                warnings.append(
                    f"Split order merged → {parent.get('ta_ref','?')} "
                    f"(supplier: {raw.get('supplier')}, cost: {sub_cost})"
                )
            else:
                warnings.append(f"Orphan ghost row ignored: {raw}")
            continue

        # Skip fully blank rows
        data_vals = [v for k, v in raw.items() if not k.startswith("__hl_")]
        if not any(v is not None for v in data_vals):
            continue

        # Rows without ta_ref that are not ghost rows → skip with warning
        if ta_ref is None:
            warnings.append(f"Row without TA REF skipped (seq={seq}, nr={raw.get('nr')})")
            continue

        # ── Document URL resolution ────────────────────────────────────────
        # Priority 1: hyperlink object on MESSAGE cell
        # Priority 2: embedded path string in MESSAGE cell value
        hl_obj = raw.pop("__hl_message", None)
        if hl_obj:
            raw["document_url"] = _resolve_hyperlink(str(hl_obj))
        else:
            embedded = _extract_path_from_value(raw.get("message"))
            raw["document_url"] = embedded  # None if no path found

        # Remove all other __hl_ keys
        for k in [k for k in list(raw) if k.startswith("__hl_")]:
            raw.pop(k)

        # ── Cancelled detection ────────────────────────────────────────────
        raw["_cancelled_flag"] = _is_cancelled(raw.get("confirmation"))
        raw["vessel"]          = vessel
        raw.setdefault("sub_orders", [])
        records.append(raw)

    if not records:
        raise ValueError("No valid requisition rows found.")

    df = pd.DataFrame(records)

    # ── Date coercion (protected) ──────────────────────────────────────────
    # 'invoice' may contain strings like '60 DAYS' — coerce with errors='coerce'
    for col in ["date_requested", "order_date", "est_readiness", "rcvd", "ref_date", "invoice"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed")

    # ── Numeric coercion ───────────────────────────────────────────────────
    for col in ["cost", "seq", "nr"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── String coercion ────────────────────────────────────────────────────
    str_cols = ["ta_ref", "case_code", "equipment", "description", "message",
                "supplier", "confirmation", "port", "awb", "vessel"]
    for col in str_cols:
        if col in df.columns:
            df[col] = (df[col].astype(str).str.strip()
                       .replace({"None": "", "nan": "", "NaN": ""}))

    # ── account_code normalisation ─────────────────────────────────────────
    # _norm_code accepts any type — no astype(str) prerequisite needed
    if "account_code" in df.columns:
        df["account_code"] = df["account_code"].apply(_norm_code)
    else:
        df["account_code"] = ""

    # ── Cancelled cost isolation ───────────────────────────────────────────
    df["is_cancelled"] = df["_cancelled_flag"].fillna(False).astype(bool)
    df["cost_raw"]     = pd.to_numeric(df.get("cost"), errors="coerce").copy()
    df.loc[df["is_cancelled"], "cost"] = float("nan")
    df = df.drop(columns=["_cancelled_flag"])

    # ── Category enrichment ───────────────────────────────────────────────
    df["category_name"] = df["account_code"].apply(
        lambda c: index_kpis.get(c, {}).get("category_name", "")
    )

    # ── State machine ─────────────────────────────────────────────────────
    now    = pd.Timestamp(datetime.now())
    states = [_compute_state(r, now) for r in df.to_dict("records")]
    df     = pd.concat([df, pd.DataFrame(states)], axis=1)

    # ── Final column order ────────────────────────────────────────────────
    ordered = [c for c in _PRIORITY_COLS if c in df.columns]
    rest    = [c for c in df.columns    if c not in ordered]
    return df[ordered + rest], index_kpis, warnings
