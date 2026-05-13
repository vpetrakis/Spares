"""
core/parser.py — Marine Spares Data Engine  v2
Handles: ghost rows, hyperlinks, cancelled detection, INDEX KPIs, full state machine.
"""
from __future__ import annotations

import io
import re
import urllib.parse
from datetime import datetime, date
from typing import Optional

import openpyxl
import pandas as pd

# ── Column mapping: raw header → internal key ─────────────────────────────────
COL_MAP: dict[str, str] = {
    "NR": "nr",
    "TA REF": "ta_ref",
    "CASE": "case_code",
    " ": "seq",
    "REF": "ref_date",
    "EQUIPMENT": "equipment",
    "DESCRIPTION": "description",
    "DATE": "date_requested",
    "MESSAGE": "message",
    "ORDERED": "supplier",
    "CODE": "account_code",
    "CONFIRMATION ": "confirmation",
    "ORDER DATE": "order_date",
    "COST": "cost",
    "EST. READINESS": "est_readiness",
    "PORT ": "port",
    "AWB": "awb",
    "RCVD": "rcvd",
    "INVOICE": "invoice",
}

# ── SLA thresholds (calendar days) ────────────────────────────────────────────
SLA: dict[str, int] = {
    "supply":  7,
    "finance": 5,
    "ordered": 45,
    "transit": 21,
}

# ── Local network base path for hyperlink resolution ──────────────────────────
_HYPERLINK_BASE = r"Z:\Marine_Dept\Alexis\Spares\Hyperlinks 2026"

# ── Column ordering for final DataFrame ───────────────────────────────────────
_PRIORITY_COLS = [
    "status_label", "flag", "ta_ref", "case_code", "description", "equipment",
    "category_name", "date_requested", "supplier", "order_date", "cost",
    "est_readiness", "port", "rcvd", "account_code", "message", "confirmation",
    "awb", "invoice", "document_url", "status", "sla_breach", "sla_days_over",
    "days_in_stage", "sub_orders",
]


# ──────────────────────────────────────────────────────────────────────────────
# HYPERLINK RESOLVER
# ──────────────────────────────────────────────────────────────────────────────

def _resolve_hyperlink(raw: str) -> str:
    decoded = urllib.parse.unquote(raw)
    m = re.search(r"MODION(.+)$", decoded, re.IGNORECASE)
    if m:
        tail = m.group(1).replace("\\", "/")
        base = _HYPERLINK_BASE.replace("\\", "/")
        return f"file:///{base}/MODION{tail}"
    return decoded


# ──────────────────────────────────────────────────────────────────────────────
# STATE MACHINE
# ──────────────────────────────────────────────────────────────────────────────

def _ts(val) -> Optional[pd.Timestamp]:
    if val is None:
        return None
    if isinstance(val, (datetime, date)):
        result = pd.Timestamp(val)
        return None if pd.isnull(result) else result
    return None


def _compute_state(row: dict, now: pd.Timestamp) -> dict:
    """
    Deterministic 8-state pipeline.

    Priority order:
      1. CANCELLED  — CONFIRMATION contains 'CANCEL' (terminal, never a delay)
      2. RECEIVED   — RCVD date present
      3. OVERDUE_TRANSIT / IN_TRANSIT — EST. READINESS present
      4. OVERDUE_ORDERED / ORDERED    — ORDER DATE present
      5. OVERDUE_SUPPLY / PENDING_SUPPLY — DATE present
      6. UNKNOWN
    """
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
            status        = "OVERDUE_TRANSIT" if breach else "IN_TRANSIT",
            status_label  = "🔴 Transit Overdue" if breach else "🟡 In Transit",
            flag          = "DELAYED" if breach else "OK",
            days_in_stage = abs(overdue),
            sla_breach    = breach,
            sla_days_over = overdue if breach else 0,
        )

    if order_date is not None:
        days  = int((now - order_date).days)
        breach = days > SLA["ordered"]
        return dict(
            status        = "OVERDUE_ORDERED" if breach else "ORDERED",
            status_label  = "🔴 Order Overdue" if breach else "🟠 Ordered",
            flag          = "DELAYED" if breach else "OK",
            days_in_stage = days,
            sla_breach    = breach,
            sla_days_over = max(0, days - SLA["ordered"]),
        )

    if date_req is not None:
        days  = int((now - date_req).days)
        breach = days > SLA["supply"]
        return dict(
            status        = "OVERDUE_SUPPLY" if breach else "PENDING_SUPPLY",
            status_label  = "🔴 Supply Overdue" if breach else "🔵 Pending Supply",
            flag          = "DELAYED" if breach else "OK",
            days_in_stage = days,
            sla_breach    = breach,
            sla_days_over = max(0, days - SLA["supply"]),
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
        result[str(code).strip()] = {
            "category_name":          str(name).strip() if name else "",
            "case_code":              str(case).strip() if case else "",
            "cost":                   float(cost) if cost else 0.0,
            "requisitions_received":  int(rcvd_count) if rcvd_count else 0,
            "requisitions_processed": int(processed) if processed else 0,
        }
    return result


# ──────────────────────────────────────────────────────────────────────────────
# MAIN PARSER
# ──────────────────────────────────────────────────────────────────────────────

def parse_workbook(file_bytes: bytes) -> tuple[pd.DataFrame, dict, list[str]]:
    """
    Parse the ALEXIS spares workbook.

    Returns:
        df          — one row per requisition (ghost rows merged into parent)
        index_kpis  — category KPI dict from INDEX sheet
        warnings    — non-fatal data quality messages
    """
    warnings: list[str] = []
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)

    # ── Locate sheets ─────────────────────────────────────────────────────────
    spares_name = next((s for s in wb.sheetnames if "SPARES" in s.upper()), None)
    index_name  = next((s for s in wb.sheetnames if "INDEX"  in s.upper()), None)
    if not spares_name:
        raise ValueError("Cannot find a SPARES sheet in this workbook.")

    ws      = wb[spares_name]
    index_kpis = _parse_index(wb[index_name]) if index_name else {}

    # ── Find header row ───────────────────────────────────────────────────────
    header_row = None
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=20, values_only=True)):
        if row and "TA REF" in row:
            header_row = i + 1
            break
    if header_row is None:
        raise ValueError("Cannot find header row containing 'TA REF'.")

    # {col_index → normalised_key}
    col_idx: dict[int, str] = {}
    for i, cell in enumerate(ws[header_row]):
        if cell.value is not None:
            raw_h = str(cell.value)
            col_idx[i] = COL_MAP.get(raw_h, raw_h.lower().replace(" ", "_").strip())

    # ── Read rows ─────────────────────────────────────────────────────────────
    records: list[dict] = []

    for row in ws.iter_rows(min_row=header_row + 1):
        raw: dict = {}
        for i, cell in enumerate(row):
            if i not in col_idx:
                continue
            raw[col_idx[i]] = cell.value
            if cell.hyperlink and cell.hyperlink.target:
                raw[f"__hl_{col_idx[i]}"] = cell.hyperlink.target

        ta_ref = raw.get("ta_ref")
        seq    = raw.get("seq")

        # Ghost row: no TA REF, no seq, but has supplier/order_date/cost
        if (ta_ref is None and seq is None
                and (raw.get("supplier") or raw.get("order_date") or raw.get("cost"))):
            if records:
                parent = records[-1]
                parent.setdefault("sub_orders", []).append({
                    "supplier":   raw.get("supplier"),
                    "order_date": raw.get("order_date"),
                    "cost":       raw.get("cost"),
                })
                if raw.get("cost") is not None:
                    parent["cost"] = (parent.get("cost") or 0.0) + float(raw["cost"])
                warnings.append(
                    f"Split order merged → {parent.get('ta_ref', '?')} "
                    f"(supplier: {raw.get('supplier')}, cost: {raw.get('cost')})"
                )
            else:
                warnings.append(f"Orphan ghost row ignored: {raw}")
            continue

        # Skip blank rows
        data_vals = [v for k, v in raw.items() if not k.startswith("__hl_")]
        if not any(v is not None for v in data_vals):
            continue

        if ta_ref is None:
            warnings.append(f"Row without TA REF skipped (seq={seq})")
            continue

        # Resolve hyperlink from MESSAGE column
        hl_raw = raw.pop("__hl_message", None)
        raw["document_url"] = _resolve_hyperlink(str(hl_raw)) if hl_raw else None

        # Remove any other raw hyperlink keys
        for k in [k for k in list(raw) if k.startswith("__hl_")]:
            raw.pop(k)

        raw.setdefault("sub_orders", [])
        records.append(raw)

    if not records:
        raise ValueError("No valid requisition rows found.")

    # ── Build DataFrame ───────────────────────────────────────────────────────
    df = pd.DataFrame(records)

    # Date coercion
    for col in ["date_requested", "order_date", "est_readiness", "rcvd", "ref_date", "invoice"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Numeric coercion
    for col in ["cost", "seq", "nr"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # String coercion + cleanup
    str_cols = ["ta_ref", "case_code", "equipment", "description", "message",
                "supplier", "account_code", "confirmation", "port", "awb"]
    for col in str_cols:
        if col in df.columns:
            df[col] = (df[col].astype(str).str.strip()
                       .replace({"None": "", "nan": "", "NaN": ""}))

    # Normalise account_code (5513.0 → "5513")
    if "account_code" in df.columns:
        def _norm_code(x: str) -> str:
            x = x.strip()
            if x in ("", "None", "nan"):
                return x
            try:
                return str(int(float(x)))
            except (ValueError, OverflowError):
                return x
        df["account_code"] = df["account_code"].apply(_norm_code)

    # Category enrichment from INDEX sheet
    df["category_name"] = df["account_code"].map(
        lambda c: index_kpis.get(c, {}).get("category_name", "")
    ) if "account_code" in df.columns else ""

    # ── State machine ─────────────────────────────────────────────────────────
    now = pd.Timestamp(datetime.now())
    states = [_compute_state(r, now) for r in df.to_dict("records")]
    df = pd.concat([df, pd.DataFrame(states)], axis=1)

    # ── Column ordering ───────────────────────────────────────────────────────
    ordered = [c for c in _PRIORITY_COLS if c in df.columns]
    rest    = [c for c in df.columns if c not in ordered]
    return df[ordered + rest], index_kpis, warnings
