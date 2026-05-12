"""
parser.py — Marine Spares Data Engine
Handles: ghost rows (split orders), hyperlinks, cancelled states,
         INDEX sheet KPIs, supplier extraction, full state machine.
"""
from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional

import openpyxl
import pandas as pd


# ──────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────

# Columns exactly as they appear in row 3 of the workbook
EXPECTED_HEADERS = [
    "NR", "TA REF", "CASE", " ", "REF", "EQUIPMENT", "DESCRIPTION",
    "DATE", "MESSAGE", "ORDERED", "CODE", "CONFIRMATION ",
    "ORDER DATE", "COST", "EST. READINESS", "PORT ", "AWB",
    "RCVD", "INVOICE",
]

# Normalised names we use internally
COL_MAP = {
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

# SLA thresholds (calendar days per stage)
SLA = {
    "supply": 7,
    "finance": 5,
    "ordered": 45,
    "transit": 21,
}

# INDEX sheet category definitions (row 4-13, cols A/B/C)
INDEX_CATEGORIES = {
    "5511":  {"name": "Main Engine Spares",                 "case": "ME"},
    "5512":  {"name": "Diesel Generator Spares",            "case": "DG"},
    "5513":  {"name": "Auxiliary Machineries Spares",       "case": "AX"},
    "5514":  {"name": "Deck Machineries Spares",            "case": "DK"},
    "5516":  {"name": "Boiler Spares",                      "case": "BL"},
    "5517":  {"name": "Various Spares",                     "case": "VA"},
    "5517A": {"name": "Engine Room Automation Spares",      "case": "AT"},
    "5517B": {"name": "Cargo Holds / Systems Spares",       "case": "CS"},
    "5517C": {"name": "Electrical System Spares",           "case": "EL"},
    "5521M": {"name": "Docking Related Spares",             "case": "DD"},
}

HYPERLINK_BASE = r"Z:\Marine_Dept\Alexis\Spares\Hyperlinks 2026"


# ──────────────────────────────────────────────
# HYPERLINK RESOLVER
# ──────────────────────────────────────────────

def _resolve_hyperlink(raw: str) -> str:
    """Convert relative UNC hyperlink to a usable file:/// URL."""
    decoded = urllib.parse.unquote(raw)
    # Pattern: ..\..\SPARES' HYPERLINKS 2026\MODION\...
    match = re.search(r"MODION(.+)$", decoded, re.IGNORECASE)
    if match:
        tail = match.group(1).replace("\\", "/")
        base = HYPERLINK_BASE.replace("\\", "/")
        return f"file:///{base}/MODION{tail}"
    return decoded


# ──────────────────────────────────────────────
# STATE MACHINE
# ──────────────────────────────────────────────

def _compute_state(row: dict, today: datetime) -> dict:
    """
    7-state pipeline with SLA breach detection.

    States (ordered by pipeline progression):
      CANCELLED  → CONFIRMATION contains 'CANCEL' keyword (terminal)
      RECEIVED   → RCVD date present
      IN_TRANSIT → EST. READINESS present, not yet received
      ORDERED    → ORDER DATE present, no est. readiness
      FINANCE    → (would need SENT TO FINANCE col — not in current sheet)
      PENDING    → DATE present, nothing further
      UNKNOWN    → no date at all
    """
    def _d(val):
        if val is None:
            return None
        if isinstance(val, (datetime, date)):
            return pd.Timestamp(val)
        return None

    now = pd.Timestamp(today)

    rcvd       = _d(row.get("rcvd"))
    est_ready  = _d(row.get("est_readiness"))
    order_date = _d(row.get("order_date"))
    date_req   = _d(row.get("date_requested"))
    confirm    = str(row.get("confirmation") or "").upper()

    # ── TERMINAL: CANCELLED ───────────────────
    if "CANCEL" in confirm:
        return {
            "status": "CANCELLED",
            "status_label": "✖ Cancelled",
            "flag": "CANCELLED",
            "days_in_stage": None,
            "sla_breach": False,
            "sla_days_over": 0,
        }

    # ── RECEIVED ─────────────────────────────
    if rcvd is not None:
        return {
            "status": "RECEIVED",
            "status_label": "🟢 Received",
            "flag": "OK",
            "days_in_stage": (now - rcvd).days,
            "sla_breach": False,
            "sla_days_over": 0,
        }

    # ── IN TRANSIT ───────────────────────────
    if est_ready is not None:
        overdue = (now - est_ready).days
        breach = overdue > 0
        return {
            "status": "OVERDUE_TRANSIT" if breach else "IN_TRANSIT",
            "status_label": "🔴 Transit Overdue" if breach else "🟡 In Transit",
            "flag": "DELAYED" if breach else "OK",
            "days_in_stage": abs(overdue),
            "sla_breach": breach,
            "sla_days_over": overdue if breach else 0,
        }

    # ── ORDERED (awaiting delivery date) ─────
    if order_date is not None:
        days = (now - order_date).days
        breach = days > SLA["ordered"]
        return {
            "status": "OVERDUE_ORDERED" if breach else "ORDERED",
            "status_label": "🔴 Order Overdue" if breach else "🟠 Ordered",
            "flag": "DELAYED" if breach else "OK",
            "days_in_stage": days,
            "sla_breach": breach,
            "sla_days_over": max(0, days - SLA["ordered"]),
        }

    # ── PENDING SUPPLY ────────────────────────
    if date_req is not None:
        days = (now - date_req).days
        breach = days > SLA["supply"]
        return {
            "status": "OVERDUE_SUPPLY" if breach else "PENDING_SUPPLY",
            "status_label": "🔴 Supply Overdue" if breach else "🔵 Pending Supply",
            "flag": "DELAYED" if breach else "OK",
            "days_in_stage": days,
            "sla_breach": breach,
            "sla_days_over": max(0, days - SLA["supply"]),
        }

    return {
        "status": "UNKNOWN",
        "status_label": "⚪ Unknown",
        "flag": "ERROR",
        "days_in_stage": None,
        "sla_breach": False,
        "sla_days_over": 0,
    }


# ──────────────────────────────────────────────
# INDEX SHEET PARSER
# ──────────────────────────────────────────────

def _parse_index(ws) -> dict:
    """
    Extract KPIs from the INDEX sheet.
    Returns dict keyed by account_code string.
    """
    result = {}
    for row in ws.iter_rows(min_row=4, values_only=True):
        name, case, code, _, _, cost, _, rcvd_count, _, processed = (
            (list(row) + [None] * 10)[:10]
        )
        if code is None:
            continue
        code_str = str(code).strip()
        result[code_str] = {
            "category_name": str(name).strip() if name else "",
            "case_code": str(case).strip() if case else "",
            "cost": float(cost) if cost else 0.0,
            "requisitions_received": int(rcvd_count) if rcvd_count else 0,
            "requisitions_processed": int(processed) if processed else 0,
        }
    return result


# ──────────────────────────────────────────────
# MAIN PARSER
# ──────────────────────────────────────────────

def parse_workbook(file_bytes: bytes) -> tuple[pd.DataFrame, dict, list[str]]:
    """
    Parse the Marine Spares workbook completely.

    Returns:
        df          – One row per requisition (ghost rows merged into parent)
        index_kpis  – Dict of category KPIs from INDEX sheet
        warnings    – List of non-fatal data quality warnings
    """
    import io
    warnings: list[str] = []
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)

    # ── locate sheets ─────────────────────────
    spares_sheet = next(
        (s for s in wb.sheetnames if "SPARES" in s.upper()), None
    )
    index_sheet = next(
        (s for s in wb.sheetnames if "INDEX" in s.upper()), None
    )
    if not spares_sheet:
        raise ValueError("Cannot find a SPARES sheet in this workbook.")

    ws_spares = wb[spares_sheet]
    index_kpis = _parse_index(wb[index_sheet]) if index_sheet else {}

    # ── locate header row ─────────────────────
    header_row_idx = None
    for i, row in enumerate(ws_spares.iter_rows(min_row=1, max_row=20, values_only=True)):
        if row and "TA REF" in row:
            header_row_idx = i + 1  # 1-based
            break
    if header_row_idx is None:
        raise ValueError("Cannot find header row containing 'TA REF'.")

    # Build header index  {col_index: normalised_key}
    raw_headers = [cell.value for cell in ws_spares[header_row_idx]]
    col_index: dict[int, str] = {}
    for idx, h in enumerate(raw_headers):
        if h is not None:
            stripped = str(h)
            norm = COL_MAP.get(stripped, stripped.lower().replace(" ", "_").strip())
            col_index[idx] = norm

    # ── read all rows with hyperlinks ─────────
    records: list[dict] = []
    prev_ta_ref: Optional[str] = None

    for row in ws_spares.iter_rows(min_row=header_row_idx + 1):
        raw = {col_index[i]: cell.value for i, cell in enumerate(row) if i in col_index}

        # Collect hyperlinks from MESSAGE column (col 8 = index I)
        for i, cell in enumerate(row):
            if i in col_index and cell.hyperlink and cell.hyperlink.target:
                raw[col_index[i] + "_hyperlink_raw"] = cell.hyperlink.target

        ta_ref = raw.get("ta_ref")
        seq    = raw.get("seq")

        # ── GHOST ROW DETECTION ───────────────
        # A ghost row has no TA REF but has at least one of: supplier, order_date, cost
        # It belongs to the previous requisition (split order from multiple suppliers)
        is_ghost = (
            ta_ref is None
            and seq is None
            and (
                raw.get("supplier") is not None
                or raw.get("order_date") is not None
                or raw.get("cost") is not None
            )
        )

        if is_ghost:
            if records:
                parent = records[-1]
                # Merge additional supplier and cost into parent as a sub-order
                sub_orders = parent.setdefault("sub_orders", [])
                sub_orders.append({
                    "supplier":   raw.get("supplier"),
                    "order_date": raw.get("order_date"),
                    "cost":       raw.get("cost"),
                })
                # Accumulate total cost
                if raw.get("cost") is not None:
                    parent["cost"] = (parent.get("cost") or 0) + raw["cost"]
                warnings.append(
                    f"Ghost row merged into {parent.get('ta_ref', '?')} "
                    f"(supplier: {raw.get('supplier')}, cost: {raw.get('cost')})"
                )
            else:
                warnings.append(f"Orphan ghost row ignored: {raw}")
            continue

        # Skip completely empty rows
        if not any(v for k, v in raw.items() if not k.endswith("_hyperlink_raw")):
            continue

        # Require at minimum a TA REF
        if ta_ref is None:
            warnings.append(f"Row without TA REF skipped: seq={seq}")
            continue

        # ── HYPERLINK RESOLUTION ──────────────
        hl_raw = raw.pop("message_hyperlink_raw", None)
        if hl_raw:
            raw["document_url"] = _resolve_hyperlink(str(hl_raw))
        else:
            raw["document_url"] = None

        raw.setdefault("sub_orders", [])
        prev_ta_ref = ta_ref
        records.append(raw)

    if not records:
        raise ValueError("No valid requisition rows found in workbook.")

    # ── BUILD DATAFRAME ───────────────────────
    df = pd.DataFrame(records)

    # ── TYPE COERCION ─────────────────────────
    date_cols = ["date_requested", "order_date", "est_readiness", "rcvd", "ref_date", "invoice"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    numeric_cols = ["cost", "seq", "nr"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    str_cols = ["ta_ref", "case_code", "equipment", "description", "message",
                "supplier", "account_code", "confirmation", "port", "awb"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace("None", "").replace("nan", "")

    # ── ACCOUNT CODE NORMALISATION ────────────
    if "account_code" in df.columns:
        df["account_code"] = df["account_code"].apply(
            lambda x: str(int(float(x))) if x not in ("", "None", "nan") and str(x).replace(".", "").isdigit() else str(x).strip()
        )

    # ── CATEGORY ENRICHMENT from INDEX ────────
    if "account_code" in df.columns:
        df["category_name"] = df["account_code"].map(
            lambda c: index_kpis.get(c, {}).get("category_name", "")
        )
    else:
        df["category_name"] = ""

    # ── STATE MACHINE ─────────────────────────
    today = datetime.now()
    state_rows = df.apply(lambda r: _compute_state(r.to_dict(), today), axis=1)
    state_df = pd.DataFrame(state_rows.tolist())
    df = pd.concat([df, state_df], axis=1)

    # ── COLUMN ORDERING ───────────────────────
    priority_cols = ["status_label", "flag", "ta_ref", "case_code", "description",
                     "equipment", "category_name", "date_requested", "supplier",
                     "order_date", "cost", "est_readiness", "port", "rcvd",
                     "account_code", "message", "confirmation", "awb", "invoice",
                     "document_url", "status", "sla_breach", "sla_days_over",
                     "days_in_stage", "sub_orders"]
    ordered = [c for c in priority_cols if c in df.columns]
    rest = [c for c in df.columns if c not in ordered]
    df = df[ordered + rest]

    return df, index_kpis, warnings
