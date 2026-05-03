"""
Agent #20: ERP Live File Connector
Reads any ERP/P2P export file (SAP, Oracle, Coupa, Ariba CSV/Excel),
auto-detects schema using field alias matching, normalizes columns to
ProcureIQ standard schema, and returns a clean DataFrame.
"""
import os
import re
import json
from typing import Dict, Any, List, Optional, Tuple

try:
    import pandas as pd
    _PD = True
except ImportError:
    _PD = False

try:
    import anthropic as _ant
    _AVAILABLE = True
except ImportError:
    _ant = None
    _AVAILABLE = False


# ── ERP field alias registry ──────────────────────────────────────────

ERP_ALIASES: Dict[str, Dict[str, List[str]]] = {
    "SAP S/4HANA": {
        "supplier":     ["NAME1", "LIFNR", "Vendor Name", "Vendor"],
        "amount":       ["DMBTR", "WRBTR", "Amount in Local Currency", "Net Value", "NETWR"],
        "description":  ["TXZ01", "MAKTX", "Short Text", "Material Description"],
        "gl_account":   ["SAKNR", "HKONT", "G/L Account", "GL Account"],
        "plant":        ["WERKS", "Plant", "Werk"],
        "cost_center":  ["KOSTL", "Cost Center"],
        "po_number":    ["EBELN", "Purchasing Document", "PO Number"],
        "invoice_date": ["BLDAT", "BUDAT", "Document Date", "Posting Date"],
        "currency":     ["WAERS", "Currency", "Local Currency"],
        "invoice_no":   ["BELNR", "Document Number", "Invoice Number"],
    },
    "Oracle Fusion": {
        "supplier":     ["VENDOR_NAME", "SUPPLIER_NAME", "Party Name", "Supplier"],
        "amount":       ["AMOUNT", "ENTERED_AMOUNT", "ACCOUNTED_AMOUNT", "Invoice Amount"],
        "description":  ["DESCRIPTION", "ITEM_DESCRIPTION", "LINE_DESCRIPTION"],
        "gl_account":   ["CODE_COMBINATION_ID", "ACCOUNT", "GL_CODE", "Natural Account"],
        "cost_center":  ["COST_CENTER", "DEPARTMENT", "Segment2"],
        "po_number":    ["PO_NUMBER", "ORDER_NUMBER", "Purchase Order"],
        "invoice_date": ["INVOICE_DATE", "ACCOUNTING_DATE", "GL Date"],
        "currency":     ["CURRENCY_CODE", "Invoice Currency"],
        "invoice_no":   ["INVOICE_NUMBER", "INVOICE_NUM"],
    },
    "Coupa": {
        "supplier":     ["Supplier Name", "supplier_name", "Vendor", "Requestor"],
        "amount":       ["Amount", "Total Price", "amount_in_usd", "Subtotal"],
        "description":  ["Description", "Line Description", "Commodity", "Item"],
        "gl_account":   ["Account", "Charge Account", "account_code", "GL Code"],
        "cost_center":  ["Cost Center", "Department", "Business Unit"],
        "po_number":    ["PO Number", "Purchase Order", "Requisition Number"],
        "invoice_date": ["Invoice Date", "Created At", "Submitted Date"],
        "currency":     ["Currency", "Invoice Currency"],
        "invoice_no":   ["Invoice Number", "Document Number"],
    },
    "SAP Ariba": {
        "supplier":     ["SupplierName", "VendorName", "supplier_name", "Supplier"],
        "amount":       ["InvoiceAmount", "TotalAmount", "NetAmount", "Amount"],
        "description":  ["LineDescription", "Description", "CommodityName"],
        "gl_account":   ["GLAccount", "AccountCode", "GL Account"],
        "cost_center":  ["CostCenter", "BusinessUnit", "DepartmentCode"],
        "po_number":    ["PurchaseOrderNumber", "OrderId", "PO"],
        "invoice_date": ["InvoiceDate", "PostingDate", "DocumentDate"],
        "currency":     ["Currency", "CurrencyCode"],
        "invoice_no":   ["InvoiceNumber", "DocumentNumber"],
    },
    "Generic": {
        "supplier":     ["supplier", "vendor", "payee", "merchant", "company"],
        "amount":       ["amount", "total", "spend", "cost", "price", "value", "net"],
        "description":  ["description", "item", "product", "service", "narration", "details"],
        "gl_account":   ["gl", "account", "gl_account", "account_code"],
        "cost_center":  ["cost_center", "department", "division", "bu"],
        "po_number":    ["po", "po_number", "order", "purchase_order"],
        "invoice_date": ["date", "invoice_date", "transaction_date", "posting_date"],
        "currency":     ["currency", "ccy"],
        "invoice_no":   ["invoice", "invoice_number", "document_number", "ref"],
    },
}

# Standard output schema
STANDARD_SCHEMA = ["supplier", "amount", "description", "gl_account",
                   "cost_center", "po_number", "invoice_date", "currency", "invoice_no"]

# CapEx GL account patterns (common ranges across ERP systems)
CAPEX_PATTERNS = re.compile(
    r"^(01|10|11|12|13|14|15|16|17|18|19|1[0-9]{3}|0[1-9]{3})", re.IGNORECASE
)
OPEX_PATTERNS = re.compile(
    r"^(4[0-9]|5[0-9]|6[0-9]|7[0-9]|40|41|42|43|44|45|5[0-9]{3}|6[0-9]{3})", re.IGNORECASE
)


def _detect_erp(columns: List[str]) -> Tuple[str, float]:
    """Detect which ERP system the file came from based on column names."""
    col_lower = {c.lower().strip() for c in columns}
    scores: Dict[str, int] = {}
    for erp_name, fields in ERP_ALIASES.items():
        if erp_name == "Generic":
            continue
        score = 0
        for aliases in fields.values():
            for alias in aliases:
                if alias.lower() in col_lower:
                    score += 1
        scores[erp_name] = score
    if not scores or max(scores.values()) == 0:
        return "Generic", 0.0
    best = max(scores, key=scores.get)
    confidence = scores[best] / max(sum(1 for aliases in ERP_ALIASES[best].values() for _ in aliases), 1)
    return best, min(round(confidence, 2), 1.0)


def _map_columns(df_columns: List[str], erp_name: str) -> Dict[str, str]:
    """Return mapping from DataFrame column → ProcureIQ standard field."""
    aliases = ERP_ALIASES.get(erp_name, ERP_ALIASES["Generic"])
    col_lower_map = {c.lower().strip(): c for c in df_columns}
    mapping: Dict[str, str] = {}

    for std_field, alias_list in aliases.items():
        for alias in alias_list:
            if alias.lower() in col_lower_map:
                mapping[col_lower_map[alias.lower()]] = std_field
                break

    # Fallback: fuzzy match on Generic aliases
    if len(mapping) < 3:
        generic = ERP_ALIASES["Generic"]
        for col in df_columns:
            if col in mapping:
                continue
            col_l = col.lower()
            for std_field, alias_list in generic.items():
                if std_field not in mapping.values():
                    if any(a in col_l for a in alias_list):
                        mapping[col] = std_field
                        break

    return mapping


def _classify_gl(gl_value: str) -> str:
    """Classify a GL account as CAPEX, OPEX, or UNKNOWN."""
    if not gl_value:
        return "UNKNOWN"
    gl_str = str(gl_value).strip()
    if CAPEX_PATTERNS.match(gl_str):
        return "CAPEX"
    if OPEX_PATTERNS.match(gl_str):
        return "OPEX"
    gl_keywords_capex = ["asset", "capital", "equipment", "construction", "capex"]
    gl_keywords_opex = ["expense", "operating", "opex", "service", "maintenance"]
    gl_l = gl_str.lower()
    if any(k in gl_l for k in gl_keywords_capex):
        return "CAPEX"
    if any(k in gl_l for k in gl_keywords_opex):
        return "OPEX"
    return "UNKNOWN"


def run_erp_connector(
    file_bytes: bytes,
    file_name: str,
    org_id: str = "default",
    api_key: str = "",
) -> Dict[str, Any]:
    """
    Parse an ERP export file, auto-detect schema, normalize to ProcureIQ standard.

    Returns:
        {
            "erp_detected": "SAP S/4HANA",
            "confidence": 0.72,
            "column_mapping": {...},
            "normalized_df": DataFrame (as JSON records),
            "row_count": 1450,
            "total_spend": 12500000.0,
            "capex_spend": 3200000.0,
            "opex_spend": 9300000.0,
            "unmapped_columns": [...],
            "quality_issues": [...]
        }
    """
    if not _PD:
        return {"error": "pandas not installed. Run: pip install pandas openpyxl"}

    try:
        import io
        buf = io.BytesIO(file_bytes)
        if file_name.lower().endswith(".csv"):
            df = pd.read_csv(buf, dtype=str, low_memory=False)
        else:
            df = pd.read_excel(buf, dtype=str)
    except Exception as e:
        return {"error": f"Could not parse file: {e}"}

    df = df.dropna(how="all").reset_index(drop=True)
    if df.empty:
        return {"error": "File is empty after removing blank rows."}

    erp_name, confidence = _detect_erp(list(df.columns))
    col_mapping = _map_columns(list(df.columns), erp_name)
    unmapped = [c for c in df.columns if c not in col_mapping]

    # Rename to standard schema
    df_norm = df.rename(columns=col_mapping)

    # Ensure all standard fields exist
    for field in STANDARD_SCHEMA:
        if field not in df_norm.columns:
            df_norm[field] = ""

    # Coerce amount to numeric
    if "amount" in df_norm.columns:
        df_norm["amount_num"] = (
            df_norm["amount"]
            .str.replace(r"[^\d\.\-]", "", regex=True)
            .replace("", "0")
            .astype(float, errors="ignore")
        )
    else:
        df_norm["amount_num"] = 0.0

    # GL classification
    if "gl_account" in df_norm.columns:
        df_norm["spend_type"] = df_norm["gl_account"].apply(_classify_gl)
    else:
        df_norm["spend_type"] = "UNKNOWN"

    # Summary stats
    total = float(df_norm["amount_num"].sum())
    capex = float(df_norm[df_norm["spend_type"] == "CAPEX"]["amount_num"].sum())
    opex  = float(df_norm[df_norm["spend_type"] == "OPEX"]["amount_num"].sum())

    quality_issues = []
    null_supplier = int(df_norm["supplier"].isnull().sum() + (df_norm["supplier"] == "").sum())
    null_amount   = int(df_norm["amount_num"].isna().sum())
    if null_supplier > 0:
        quality_issues.append(f"{null_supplier} rows missing supplier name")
    if null_amount > 0:
        quality_issues.append(f"{null_amount} rows with invalid/missing amount")
    if total == 0:
        quality_issues.append("Total spend is zero — check amount column mapping")

    return {
        "erp_detected": erp_name,
        "confidence": confidence,
        "column_mapping": col_mapping,
        "normalized_records": df_norm[STANDARD_SCHEMA + ["amount_num", "spend_type"]].to_dict("records"),
        "row_count": len(df_norm),
        "total_spend": total,
        "capex_spend": capex,
        "opex_spend": opex,
        "unmapped_columns": unmapped,
        "quality_issues": quality_issues,
        "all_columns": list(df.columns),
    }
