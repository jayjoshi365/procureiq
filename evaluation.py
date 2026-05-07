# evaluation.py
# Evaluation and scoring logic for ProcureIQ

import math
from typing import Dict, List, Optional, Tuple
from config import DIMENSIONS, CURRENT_DIMS, FUTURE_DIMS, FINANCIAL_FIELDS

def get_subcategory_weights(subcategory_name: str, kraljic: str) -> Dict[str, int]:
    """
    Returns recommended dimension weights for a given subcategory + Kraljic position.
    These are evidence-based defaults derived from procurement best practice:
    - Strategic: resilience, execution, stakeholder alignment over price
    - Leverage: price and commercial flexibility elevated
    - Bottleneck: execution risk and assurance of supply dominate
    - Non-Critical: price and simplicity, minimal strategic weight
    Each subcategory further adjusts based on its primary risk profile.
    """
    # Base weights by Kraljic posture — includes ESG and Supplier Diversity
    # ESG weight reflects CSRD and public company reporting requirements (all postures ≥5)
    # Diversity weight reflects supplier diversity program mandates at public companies
    base = {
        "Strategic":    {"Price / TCO": 6, "SLA Strength": 9, "Execution Risk": 9, "Stakeholder Confidence": 8, "Strategic Alignment": 8, "Innovation Capacity": 7, "Relationship Depth": 6, "Commercial Flexibility": 6, "ESG / Sustainability": 7, "Supplier Diversity": 5},
        "Leverage":     {"Price / TCO": 9, "SLA Strength": 7, "Execution Risk": 7, "Stakeholder Confidence": 7, "Strategic Alignment": 6, "Innovation Capacity": 6, "Relationship Depth": 5, "Commercial Flexibility": 9, "ESG / Sustainability": 6, "Supplier Diversity": 5},
        "Bottleneck":   {"Price / TCO": 5, "SLA Strength": 8, "Execution Risk":10, "Stakeholder Confidence": 7, "Strategic Alignment": 6, "Innovation Capacity": 5, "Relationship Depth": 7, "Commercial Flexibility": 5, "ESG / Sustainability": 5, "Supplier Diversity": 4},
        "Non-Critical": {"Price / TCO": 9, "SLA Strength": 6, "Execution Risk": 6, "Stakeholder Confidence": 5, "Strategic Alignment": 4, "Innovation Capacity": 4, "Relationship Depth": 4, "Commercial Flexibility": 8, "ESG / Sustainability": 5, "Supplier Diversity": 4},
    }

    # Subcategory-specific overrides — each one has a distinct risk reason, keyed by posture where needed
    overrides = {
        "HRIS / HCM Platform": {
            "Strategic": {"Execution Risk": 10, "SLA Strength": 9, "Price / TCO": 5},
        },
        "Payroll Processing": {
            "Strategic": {"Execution Risk": 10, "SLA Strength": 10, "Price / TCO": 4},
        },
        "401(k) / Retirement Platform": {
            "Strategic": {"Execution Risk": 10, "Stakeholder Confidence": 9, "Price / TCO": 5},
        },
        "ERP System (SAP / Oracle / etc.)": {
            "Strategic": {"Execution Risk": 10, "Strategic Alignment": 9, "Price / TCO": 4},
        },
        "Cloud Infrastructure (AWS / Azure / GCP)": {
            "Strategic": {"Execution Risk": 10, "SLA Strength": 10, "Price / TCO": 5},
        },
        "Cybersecurity (EDR / SIEM / SOC)": {
            "Strategic": {"Execution Risk": 10, "SLA Strength": 10, "Stakeholder Confidence": 9},
        },
        "Audit Services (External)": {
            "Strategic": {"Stakeholder Confidence": 10, "Execution Risk": 9, "Commercial Flexibility": 5},
        },
        "Corporate Banking / Treasury Services": {
            "Strategic": {"Execution Risk": 10, "Relationship Depth": 9, "Price / TCO": 4},
        },
        "Contract Manufacturing / OEM": {
            "Strategic": {"Execution Risk": 10, "SLA Strength": 9, "Relationship Depth": 8},
        },
        "Electronic Components / Semiconductors": {
            "Strategic": {"Execution Risk": 10, "SLA Strength": 9, "Stakeholder Confidence": 8},
        },
        "Pharmaceutical / API": {
            "Strategic": {"Execution Risk": 10, "SLA Strength": 10, "Price / TCO": 4},
        },
        "Creative Agency (AOR)": {
            "Strategic": {"Stakeholder Confidence": 9, "Innovation Capacity": 9, "Relationship Depth": 8},
        },
        "Media Buying / Planning Agency": {
            "Strategic": {"Commercial Flexibility": 9, "Price / TCO": 8, "Stakeholder Confidence": 8},
        },
        "Truckload (TL) / Full Truckload": {
            "Leverage": {"Price / TCO": 10, "SLA Strength": 8, "Commercial Flexibility": 9},
        },
        "Parcel / Small Package": {
            "Bottleneck": {"SLA Strength": 9, "Price / TCO": 8, "Execution Risk": 9},
        },
        "Third-Party Logistics (3PL) / Warehousing": {
            "Strategic": {"Execution Risk": 10, "SLA Strength": 9, "Relationship Depth": 8},
        },
        "MRO Distribution": {
            "Leverage": {"Price / TCO": 10, "Commercial Flexibility": 9, "SLA Strength": 6},
        },
        "Energy (Electricity / Natural Gas)": {
            "Strategic": {"Execution Risk": 9, "Price / TCO": 9, "Commercial Flexibility": 8},
        },
        "Outside Counsel (Law Firm)": {
            "Strategic": {"Stakeholder Confidence": 10, "Execution Risk": 9, "Price / TCO": 5},
        },
        "Commercial Real Estate (Office / Industrial)": {
            "Strategic": {"Execution Risk": 10, "Stakeholder Confidence": 9, "Price / TCO": 7},
        },
    }

    weights = dict(base.get(kraljic, base["Strategic"]))
    if subcategory_name in overrides:
        weights.update(overrides[subcategory_name].get(kraljic, {}))

    return weights


def recommend_auction_type(kraljic, num_suppliers, price_weight, switching_cost_answer, subcategory_auction):
    """
    Returns the correct procurement event type used in Coupa/Ariba.
    Note: RFP and RFQ are sourcing PROCESSES, not auction event types.
    Auction event types are the competitive bidding mechanisms within those processes.
    """
    low_switch = switching_cost_answer in ["Low — easy to switch", "Medium — some disruption expected"]
    high_switch = switching_cost_answer in ["High — significant transition risk", "Very High — near-irreversible"]

    # Single-source or high switching cost → Negotiated Award
    if kraljic == "Bottleneck" or high_switch or num_suppliers <= 1:
        return "Negotiated Award (Single Source)", (
            "Supply concentration or high switching cost makes competitive bidding impractical. "
            "Direct negotiation protects continuity and relationship while still pursuing commercial improvement."
        )

    # Strategic complex categories → Multi-Round with BAFO
    if kraljic == "Strategic" and num_suppliers >= 2:
        return "Multi-Round Negotiation (Best and Final)", (
            f"Strategic category with {num_suppliers} suppliers warrants a structured multi-round process "
            "ending in Best and Final Offer — commercial terms, SLAs, and contract structure matter as much as price."
        )

    # High price weight + multiple suppliers + low switching = Reverse Auction
    if price_weight >= 0.32 and num_suppliers >= 3 and low_switch and kraljic in ["Leverage", "Non-Critical"]:
        return "Reverse Auction (eRA)", (
            "Strong leverage position, multiple qualified suppliers, and price sensitivity support a real-time "
            "electronic reverse auction. Specs must be locked before launch."
        )

    # Non-critical, simple → Sealed Bid
    if kraljic == "Non-Critical" and num_suppliers >= 3:
        return "Sealed Bid Auction", (
            "Non-critical category with clear specs and multiple suppliers. "
            "Sealed bids minimize admin overhead and drive honest first-offer pricing."
        )

    # Subcategory default is Negotiated
    if subcategory_auction in ["Negotiated"]:
        return "Negotiated Award (Single Source)", (
            "This subcategory's market structure typically requires direct negotiation. "
            "Few viable suppliers and/or high proprietary dependency reduces competitive leverage."
        )

    # Default: Rank Auction for most indirect categories
    return "Rank Auction (Coupa / Ariba Standard)", (
        f"Leverage category with {num_suppliers} suppliers supports a rank-based auction event "
        "where suppliers see their relative position but not competitors' prices — "
        "balancing competition with strategic relationship protection."
    )


def calculate_financial_health(supplier_data):
    """Calculate financial health score from supplier inputs."""
    score = 0
    total_weight = 0

    for field, data in FINANCIAL_FIELDS.items():
        if field in supplier_data.get("Financial Inputs", {}):
            value = supplier_data["Financial Inputs"][field].strip()
            if value in data["scores"]:
                score += data["scores"][value]
                total_weight += 1

    if total_weight == 0:
        return 50  # Neutral if no data

    return min(100, max(0, score / total_weight))


def calculate_current_fit(scores):
    """Calculate current execution fit from current dimensions."""
    current_scores = [scores.get(dim, 50) for dim in CURRENT_DIMS]
    return sum(current_scores) / len(current_scores) if current_scores else 50


def calculate_future_fit(scores):
    """Calculate future strategic fit from future dimensions."""
    future_scores = [scores.get(dim, 50) for dim in FUTURE_DIMS]
    return sum(future_scores) / len(future_scores) if future_scores else 50


def calculate_weighted_score(scores, weights):
    """Calculate weighted overall score."""
    total_weight = sum(weights.values())
    if total_weight == 0:
        return 50

    weighted_sum = sum(scores.get(dim, 50) * weights.get(dim, 1) for dim in DIMENSIONS)
    return min(100, max(0, weighted_sum / total_weight))


def get_financial_risk_label(financial_health):
    """Get risk label based on financial health score."""
    if financial_health >= 80:
        return "Low Risk"
    elif financial_health >= 60:
        return "Medium Risk"
    else:
        return "High Risk"


def compute_financial_health(fin_dict: Dict[str, str]) -> int:
    """Compute a 0-100 financial health score from the FINANCIAL_FIELDS qualitative inputs.

    Each field contributes its mapped score; missing or unrecognised answers default to 50.
    Returns the average across all fields, rounded to the nearest integer.

    This is the canonical implementation — the scoring UI and Decision Brief both rely on this.
    Do not compute financial health scores anywhere else; import from this module.
    """
    values = [
        meta["scores"].get(fin_dict.get(field_name, ""), 50)
        for field_name, meta in FINANCIAL_FIELDS.items()
    ]
    return round(sum(values) / len(values)) if values else 50


def compute_edgar_financial_health(xbrl: Dict) -> Optional[Dict]:
    """Compute a 0-100 financial health score from raw SEC EDGAR/XBRL ratios.

    This is a separate scoring path from compute_financial_health().  It operates
    on the numeric dict returned by get_xbrl_financial_ratios() (supplier_risk_monitor).
    compute_financial_health() is unchanged and still used for private/no-ticker suppliers.

    Returns a dict:
        {
            "score": int,           # 0-100 weighted average of available metrics
            "confidence": str,      # "high" | "partial" | "unavailable"
            "n_metrics": int,       # how many of the 3 main metrics contributed
            "inputs": dict,         # human-readable per-metric breakdown
            "flags": list[str],     # red-flag conditions detected
            "source": "SEC EDGAR/XBRL",
            "period_end": str,
        }

    Returns None when no EDGAR metrics are available (caller falls back to
    compute_financial_health() unchanged).

    Thresholds are conservative, based on S&P/D&B supplier risk benchmarks.
    Missing metrics are excluded from the weighted average — the score reflects
    only what is available and is labelled accordingly.
    """
    if not xbrl:
        return None

    # ── Metric 1: Revenue growth (weight 35%) ────────────────────────────
    rev_growth = xbrl.get("revenue_growth_pct")
    rev_score: Optional[int] = None
    rev_label = "Not reported"
    if rev_growth is not None:
        if rev_growth >= 20:
            rev_score, rev_label = 95, f"+{rev_growth:.1f}% YoY — strong growth"
        elif rev_growth >= 10:
            rev_score, rev_label = 80, f"+{rev_growth:.1f}% YoY — moderate growth"
        elif rev_growth >= 0:
            rev_score, rev_label = 60, f"+{rev_growth:.1f}% YoY — stable"
        elif rev_growth >= -10:
            rev_score, rev_label = 35, f"{rev_growth:.1f}% YoY — declining"
        else:
            rev_score, rev_label = 15, f"{rev_growth:.1f}% YoY — significant decline"

    # ── Metric 2: Profit margin (weight 35%) ─────────────────────────────
    margin = xbrl.get("profit_margin_current")
    margin_pct = round(margin * 100, 1) if margin is not None else None
    margin_score: Optional[int] = None
    margin_label = "Not reported"
    if margin_pct is not None:
        if margin_pct >= 15:
            margin_score, margin_label = 95, f"{margin_pct:.1f}% net margin — strong"
        elif margin_pct >= 5:
            margin_score, margin_label = 78, f"{margin_pct:.1f}% net margin — healthy"
        elif margin_pct >= 0:
            margin_score, margin_label = 55, f"{margin_pct:.1f}% net margin — thin"
        elif margin_pct >= -5:
            margin_score, margin_label = 35, f"{margin_pct:.1f}% net margin — operating loss"
        else:
            margin_score, margin_label = 15, f"{margin_pct:.1f}% net margin — material loss"

    # ── Metric 3: Debt-to-assets leverage (weight 30%) ───────────────────
    d2a = xbrl.get("debt_to_assets_current")
    d2a_score: Optional[int] = None
    d2a_label = "Not reported"
    if d2a is not None:
        if d2a <= 0.30:
            d2a_score, d2a_label = 90, f"{d2a:.2f} debt/assets — low leverage"
        elif d2a <= 0.50:
            d2a_score, d2a_label = 75, f"{d2a:.2f} debt/assets — moderate leverage"
        elif d2a <= 0.65:
            d2a_score, d2a_label = 55, f"{d2a:.2f} debt/assets — elevated leverage"
        elif d2a <= 0.85:
            d2a_score, d2a_label = 30, f"{d2a:.2f} debt/assets — high leverage"
        else:
            d2a_score, d2a_label = 10, f"{d2a:.2f} debt/assets — very high leverage"

    # ── Weighted average over available metrics only ──────────────────────
    weights = [(rev_score, 0.35), (margin_score, 0.35), (d2a_score, 0.30)]
    available = [(s, w) for s, w in weights if s is not None]
    n_metrics = len(available)

    if n_metrics == 0:
        return None  # No metrics → caller falls back to manual entry

    total_weight = sum(w for _, w in available)
    raw_score = sum(s * w for s, w in available) / total_weight
    final_score = round(raw_score)

    confidence = "high" if n_metrics == 3 else "partial"

    # ── Red flags ──────────────────────────────────────────────────────────
    flags: list = []
    ni = xbrl.get("net_income_current")
    if ni is not None and ni < 0:
        flags.append("Net loss reported in most recent fiscal year")
    if d2a is not None and d2a > 1.0:
        flags.append("Total liabilities exceed total assets — review solvency")
    if rev_growth is not None and rev_growth < -15:
        flags.append(f"Revenue declined {abs(rev_growth):.1f}% — material continuity risk")

    return {
        "score": final_score,
        "confidence": confidence,
        "n_metrics": n_metrics,
        "inputs": {
            "Revenue Growth": rev_label,
            "Profit Margin": margin_label,
            "Debt-to-Assets": d2a_label,
        },
        "flags": flags,
        "source": "SEC EDGAR/XBRL",
        "period_end": xbrl.get("period_end", ""),
    }


def financial_risk_label(score: int) -> Tuple[str, str, str]:
    """Return (label, hex_color, rgba_background) for a 0-100 financial health score.

    Used for colour-coded risk badges throughout the UI.
    """
    if score >= 75:
        return ("LOW", "#22C55E", "rgba(34,197,94,0.08)")
    if score >= 50:
        return ("MEDIUM", "#F59E0B", "rgba(245,158,11,0.08)")
    return ("HIGH", "#EF4444", "rgba(239,68,68,0.08)")


def evaluate_suppliers(suppliers, weights):
    """Evaluate and rank suppliers based on scores and weights."""
    ranked = []
    for supplier in suppliers:
        scores = supplier.get("Scores", {})
        current_fit = calculate_current_fit(scores)
        future_fit = calculate_future_fit(scores)
        weighted_score = calculate_weighted_score(scores, weights)
        financial_health = calculate_financial_health(supplier)
        financial_risk = get_financial_risk_label(financial_health)

        supplier.update({
            "Current Fit": current_fit,
            "Future Fit": future_fit,
            "Weighted Score": weighted_score,
            "Financial Health": financial_health,
            "Financial Risk Label": financial_risk,
        })
        ranked.append(supplier)

    # Sort by weighted score descending
    ranked.sort(key=lambda x: x["Weighted Score"], reverse=True)
    return ranked

