"""
Agent #13: Spend Anomaly Detection
Statistical + AI-powered analysis of spend data to detect:
  - Duplicate invoices (same supplier + amount + date proximity)
  - Spend spikes (z-score > 2.5 vs category baseline)
  - Maverick spend (purchases from non-approved vendors)
  - Split transactions (multiple small invoices near approval threshold)
  - Supplier concentration risk (>40% spend with single vendor in a category)
"""
import os
import json
import re
import time
from typing import Dict, Any, List, Optional

try:
    import pandas as pd
    import numpy as np
    _PD = True
except ImportError:
    _PD = False

try:
    from agents.llm_router import call_llm as _call_llm
    _ROUTER_AVAILABLE = True
except ImportError:
    _call_llm = None
    _ROUTER_AVAILABLE = False


# ── Statistical detectors ─────────────────────────────────────────────

def _detect_duplicates(df: "pd.DataFrame", amount_col: str, supplier_col: str,
                        date_col: str, tolerance_pct: float = 0.01) -> List[Dict]:
    """Find duplicate invoices: same supplier, same amount (±1%), within 30 days."""
    flags = []
    if supplier_col not in df.columns or amount_col not in df.columns:
        return flags
    for supplier, group in df.groupby(supplier_col):
        amounts = group[amount_col].values
        for i in range(len(amounts)):
            for j in range(i + 1, len(amounts)):
                if amounts[i] == 0:
                    continue
                diff_pct = abs(amounts[i] - amounts[j]) / abs(amounts[i])
                if diff_pct <= tolerance_pct:
                    flags.append({
                        "type": "DUPLICATE_INVOICE",
                        "severity": "HIGH",
                        "supplier": str(supplier),
                        "amount_1": float(amounts[i]),
                        "amount_2": float(amounts[j]),
                        "rows": [int(group.index[i]), int(group.index[j])],
                        "reason": f"Near-identical amounts (${amounts[i]:,.0f} ≈ ${amounts[j]:,.0f}) from same supplier",
                    })
    return flags[:20]  # Cap to avoid flooding


def _detect_spend_spikes(df: "pd.DataFrame", amount_col: str,
                          category_col: str, z_threshold: float = 2.5) -> List[Dict]:
    """Flag transactions with z-score > threshold vs. category mean."""
    flags = []
    if category_col not in df.columns or amount_col not in df.columns:
        return flags

    for cat, group in df.groupby(category_col):
        amounts = group[amount_col].dropna()
        if len(amounts) < 3:
            continue
        mean = amounts.mean()
        std = amounts.std()
        if std == 0:
            continue
        z_scores = (amounts - mean) / std
        spikes = z_scores[z_scores > z_threshold]
        for idx in spikes.index:
            flags.append({
                "type": "SPEND_SPIKE",
                "severity": "MEDIUM" if z_scores[idx] < 4 else "HIGH",
                "category": str(cat),
                "amount": float(df.loc[idx, amount_col]),
                "category_mean": float(mean),
                "z_score": round(float(z_scores[idx]), 2),
                "row": int(idx),
                "reason": (
                    f"Transaction ${df.loc[idx, amount_col]:,.0f} is "
                    f"{z_scores[idx]:.1f}σ above category mean ${mean:,.0f}"
                ),
            })
    return flags


def _detect_split_transactions(df: "pd.DataFrame", amount_col: str,
                                 supplier_col: str, threshold: float = 10000.0,
                                 window: int = 5) -> List[Dict]:
    """Detect split transactions: multiple invoices from same supplier near approval threshold."""
    flags = []
    if supplier_col not in df.columns or amount_col not in df.columns:
        return flags

    for supplier, group in df.groupby(supplier_col):
        near_threshold = group[
            (group[amount_col] > threshold * 0.7) &
            (group[amount_col] < threshold * 1.05)
        ]
        if len(near_threshold) >= 3:
            flags.append({
                "type": "SPLIT_TRANSACTION",
                "severity": "HIGH",
                "supplier": str(supplier),
                "count": int(len(near_threshold)),
                "total_amount": float(near_threshold[amount_col].sum()),
                "approval_threshold": threshold,
                "reason": (
                    f"{len(near_threshold)} invoices from {supplier} "
                    f"clustered just below ${threshold:,.0f} approval threshold — "
                    "possible intentional splitting to avoid approval"
                ),
            })
    return flags


def _detect_concentration_risk(df: "pd.DataFrame", amount_col: str,
                                 supplier_col: str,
                                 category_col: Optional[str] = None,
                                 threshold_pct: float = 0.40) -> List[Dict]:
    """Flag single-supplier concentration > threshold within a category."""
    flags = []
    if supplier_col not in df.columns or amount_col not in df.columns:
        return flags

    if category_col and category_col in df.columns:
        category_groups = list(df.groupby(category_col))
    else:
        category_groups = [("All Categories", df)]

    for cat, cat_df in category_groups:
        total = cat_df[amount_col].sum()
        if total == 0:
            continue
        for supplier, grp in cat_df.groupby(supplier_col):
            share = grp[amount_col].sum() / total
            if share >= threshold_pct:
                flags.append({
                    "type": "CONCENTRATION_RISK",
                    "severity": "MEDIUM",
                    "supplier": str(supplier),
                    "category": str(cat),
                    "share_pct": round(float(share * 100), 1),
                    "amount": float(grp[amount_col].sum()),
                    "reason": (
                        f"{supplier} holds {share*100:.0f}% of {cat} spend "
                        f"(${grp[amount_col].sum():,.0f}) — single-source dependency risk"
                    ),
                })
    return flags


# ── AI synthesis ──────────────────────────────────────────────────────

_SYNTHESIS_PROMPT = """\
You are a senior internal audit specialist reviewing a procurement spend anomaly report.
Given the following statistical findings, write a concise executive summary and prioritized action list.

Return ONLY valid JSON:
{
  "executive_summary": "2-3 sentence overview of findings and financial exposure",
  "total_flagged_amount": 0,
  "priority_actions": [
    {
      "priority": 1,
      "action": "Specific action to take",
      "responsible_party": "Finance / Procurement / Legal",
      "deadline": "Immediate / 30 days / 90 days"
    }
  ],
  "risk_rating": "LOW | MEDIUM | HIGH | CRITICAL",
  "investigation_recommended": true
}
"""


def run_spend_anomaly_agent(
    records: List[Dict],
    amount_col: str = "amount_num",
    supplier_col: str = "supplier",
    category_col: str = "Auto Category",
    approval_threshold: float = 10000.0,
    approved_vendors: Optional[List[str]] = None,
    api_key: str = "",
    provider: str = "claude",
) -> Dict[str, Any]:
    """
    Run the full spend anomaly detection suite.

    Args:
        records: List of dicts (from ERP connector normalized output)
        amount_col: Column name for transaction amounts
        supplier_col: Column name for supplier/vendor name
        category_col: Column name for spend category
        approval_threshold: PO approval threshold for split-transaction detection
        approved_vendors: Optional list of approved vendor names (for maverick detection)
        api_key: Anthropic API key (optional, for AI synthesis)

    Returns:
        {
            "anomalies": [...],
            "summary_stats": {...},
            "synthesis": {...},
            "total_anomalies": N,
            "high_severity_count": N
        }
    """
    if not _PD:
        return {"error": "pandas and numpy required. Run: pip install pandas numpy"}

    import pandas as pd
    import numpy as np

    df = pd.DataFrame(records)
    if df.empty:
        return {"anomalies": [], "summary_stats": {}, "total_anomalies": 0}

    # Ensure amount column is numeric
    if amount_col in df.columns:
        df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce").fillna(0)
    else:
        df[amount_col] = 0.0

    # Ensure supplier is string
    if supplier_col in df.columns:
        df[supplier_col] = df[supplier_col].fillna("Unknown").astype(str)

    anomalies: List[Dict] = []

    # Run detectors
    anomalies.extend(_detect_duplicates(df, amount_col, supplier_col, "invoice_date"))
    anomalies.extend(_detect_spend_spikes(df, amount_col, category_col))
    anomalies.extend(_detect_split_transactions(df, amount_col, supplier_col, approval_threshold))
    anomalies.extend(_detect_concentration_risk(df, amount_col, supplier_col, category_col))

    # Maverick spend detection
    if approved_vendors:
        approved_lower = {v.lower().strip() for v in approved_vendors}
        if supplier_col in df.columns:
            maverick = df[~df[supplier_col].str.lower().str.strip().isin(approved_lower)]
            if not maverick.empty:
                total_maverick = float(maverick[amount_col].sum())
                for supplier, grp in maverick.groupby(supplier_col):
                    amt = float(grp[amount_col].sum())
                    if amt > 0:
                        anomalies.append({
                            "type": "MAVERICK_SPEND",
                            "severity": "MEDIUM",
                            "supplier": str(supplier),
                            "amount": amt,
                            "transaction_count": int(len(grp)),
                            "reason": f"{supplier} is not on the approved vendor list. Total off-contract spend: ${amt:,.0f}",
                        })

    high_count = sum(1 for a in anomalies if a.get("severity") == "HIGH")
    total_flagged = sum(a.get("amount", a.get("amount_1", 0)) for a in anomalies)

    summary_stats = {
        "total_rows": len(df),
        "total_spend": float(df[amount_col].sum()),
        "total_anomalies": len(anomalies),
        "high_severity": high_count,
        "medium_severity": sum(1 for a in anomalies if a.get("severity") == "MEDIUM"),
        "unique_suppliers": int(df[supplier_col].nunique()) if supplier_col in df.columns else 0,
        "anomaly_types": list({a["type"] for a in anomalies}),
        "total_flagged_amount": total_flagged,
    }

    # AI synthesis (optional — works with any provider)
    synthesis = {}
    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if _ROUTER_AVAILABLE and _call_llm and key and anomalies:
        try:
            text = _call_llm(
                messages=[{
                    "role": "user",
                    "content": (
                        f"Anomalies found:\n{json.dumps(anomalies[:15], indent=2)}\n\n"
                        f"Stats: {json.dumps(summary_stats, indent=2)}"
                    ),
                }],
                provider=provider,
                api_key=key,
                system=_SYNTHESIS_PROMPT,
                max_tokens=1024,
            )
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                synthesis = json.loads(m.group())
        except Exception as e:
            synthesis = {"error": str(e)}

    return {
        "anomalies": anomalies,
        "summary_stats": summary_stats,
        "synthesis": synthesis,
        "total_anomalies": len(anomalies),
        "high_severity_count": high_count,
    }
