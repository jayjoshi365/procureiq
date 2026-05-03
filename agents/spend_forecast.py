"""
Agent: Spend Forecasting Agent
Projects category spend 12 months forward using:
  - Linear regression on historical monthly spend data
  - Category-specific inflation / market rate factors
  - Seasonal adjustment (optional)
  - Confidence intervals (±1 std dev of residuals)
  - Optional LLM CFO-style narrative with savings levers

No API key required for the quantitative layer.
LLM key optional for CFO narrative and savings recommendations.
"""
import json
import math
import time
import os
from typing import Dict, List, Any, Optional, Tuple

try:
    from agents.llm_router import call_llm as _call_llm
    _ROUTER_AVAILABLE = True
except ImportError:
    _call_llm = None
    _ROUTER_AVAILABLE = False


# ── Category inflation benchmarks (annualized %) ──────────────────────
# Sourced from BLS PPI, ISM, Gartner benchmarks — updated to 2025 estimates
_CATEGORY_INFLATION = {
    "IT": 3.5,
    "HR": 5.2,
    "Finance": 4.1,
    "Marketing": 3.8,
    "Logistics": 6.4,
    "Legal": 5.8,
    "Facilities": 4.7,
    "Professional Services": 5.0,
    "Direct Materials": 7.2,
    "Operations / MRO": 5.5,
}
_DEFAULT_INFLATION = 4.5  # fallback

# Subcategory-level overrides (subset of highest-volatility)
_SUBCATEGORY_INFLATION = {
    "Freight & Parcel": 8.5,
    "Air Freight": 9.2,
    "Cold Chain Logistics": 7.8,
    "Battery Cells & ESS": 12.0,
    "Critical Minerals": 14.0,
    "Carbon Credits": 11.0,
    "Cloud Infrastructure": 2.1,   # cloud prices trend down
    "SaaS Licenses": 4.8,
    "IT Managed Services": 5.5,
    "Temporary Staffing": 6.2,
    "Executive Search": 7.5,
    "Legal AI & Contract Tech": 2.5,
    "Cybersecurity Advisory": 6.8,
}

# Seasonality index per month (1.0 = flat, >1 = above average)
# Generic procurement pattern — peaks Q4 budget flush, dip Q1
_SEASONAL_INDEX = [0.88, 0.86, 0.95, 0.98, 1.00, 1.02, 1.01, 0.99, 1.04, 1.06, 1.10, 1.11]


# ── Pure-Python linear regression (no scipy/numpy required) ──────────

def _linreg(x: List[float], y: List[float]) -> Tuple[float, float, float]:
    """
    Returns (slope, intercept, r_squared).
    Operates on parallel lists of equal length.
    """
    n = len(x)
    if n < 2:
        return 0.0, y[0] if y else 0.0, 0.0
    sx = sum(x)
    sy = sum(y)
    sxy = sum(xi * yi for xi, yi in zip(x, y))
    sx2 = sum(xi ** 2 for xi in x)
    denom = n * sx2 - sx ** 2
    if denom == 0:
        return 0.0, sy / n, 0.0
    slope = (n * sxy - sx * sy) / denom
    intercept = (sy - slope * sx) / n
    # R²
    y_mean = sy / n
    ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    y_pred = [slope * xi + intercept for xi in x]
    ss_res = sum((yi - yp) ** 2 for yi, yp in zip(y, y_pred))
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    return slope, intercept, max(0.0, r2)


def _residual_std(x: List[float], y: List[float], slope: float, intercept: float) -> float:
    """Standard deviation of regression residuals."""
    if len(y) < 2:
        return 0.0
    residuals = [yi - (slope * xi + intercept) for xi, yi in zip(x, y)]
    mean_r = sum(residuals) / len(residuals)
    variance = sum((r - mean_r) ** 2 for r in residuals) / (len(residuals) - 1)
    return math.sqrt(variance)


# ── Core forecast engine ──────────────────────────────────────────────

def _build_forecast(
    monthly_spend: List[float],
    category: str,
    subcategory: str,
    apply_seasonality: bool,
    months_ahead: int,
) -> Dict:
    """
    Given historical monthly spend list, return 12-month forecast.

    monthly_spend: ordered list of monthly actuals (oldest first), at least 3 values
    """
    n = len(monthly_spend)
    if n == 0:
        return {"error": "No spend data provided"}

    x = list(range(n))
    slope, intercept, r2 = _linreg(x, monthly_spend)
    std = _residual_std(x, monthly_spend, slope, intercept)

    # Inflation rate
    inf_rate = _SUBCATEGORY_INFLATION.get(subcategory,
                _CATEGORY_INFLATION.get(category, _DEFAULT_INFLATION)) / 100.0
    monthly_inf = (1 + inf_rate) ** (1 / 12)

    # Build forecast
    forecast_months = []
    last_actual_idx = n - 1
    base_month_offset = 0  # will be set below

    for i in range(months_ahead):
        future_x = n + i
        trend_val = slope * future_x + intercept

        # Apply cumulative inflation from last data point
        inflation_factor = monthly_inf ** (i + 1)
        projected = trend_val * inflation_factor

        # Seasonal adjustment
        season_month_idx = (last_actual_idx + i + 1) % 12
        if apply_seasonality:
            projected *= _SEASONAL_INDEX[season_month_idx]

        projected = max(0.0, projected)
        ci_low = max(0.0, projected - std * 1.645)   # 90% CI lower
        ci_high = projected + std * 1.645             # 90% CI upper

        forecast_months.append({
            "month_offset": i + 1,
            "projected": round(projected, 2),
            "ci_low": round(ci_low, 2),
            "ci_high": round(ci_high, 2),
            "inflation_factor": round(inflation_factor, 4),
        })

    total_forecast = sum(m["projected"] for m in forecast_months)
    total_historical = sum(monthly_spend)
    avg_historical = total_historical / n if n else 0
    run_rate_annual = avg_historical * 12
    forecast_vs_run_rate_pct = ((total_forecast - run_rate_annual) / run_rate_annual * 100) if run_rate_annual else 0

    return {
        "monthly_actuals": monthly_spend,
        "forecast_months": forecast_months,
        "regression": {
            "slope": round(slope, 2),
            "intercept": round(intercept, 2),
            "r_squared": round(r2, 4),
        },
        "inflation_rate_annual_pct": round(inf_rate * 100, 2),
        "summary": {
            "total_historical": round(total_historical, 2),
            "avg_monthly_actual": round(avg_historical, 2),
            "run_rate_annual": round(run_rate_annual, 2),
            "total_12mo_forecast": round(total_forecast, 2),
            "forecast_vs_run_rate_pct": round(forecast_vs_run_rate_pct, 1),
        },
    }


# ── LLM narrative prompt ──────────────────────────────────────────────

_CFO_PROMPT = """\
You are a CFO-level procurement analyst. Given spend forecast data for a category, write a concise
executive briefing and identify actionable savings levers.

Return ONLY valid JSON:
{
  "headline": "One sentence describing the spend trajectory",
  "key_driver": "Primary driver of the forecast increase/decrease",
  "savings_levers": [
    {"lever": "lever name", "estimated_savings_pct": 5.0, "effort": "Low|Medium|High", "timeline": "90 days|6 months|12 months"}
  ],
  "risk_factors": ["factor 1", "factor 2"],
  "recommended_budget": <number — recommended annual budget allocation>,
  "narrative": "2-3 sentence CFO-ready summary"
}
"""


# ── Utility: parse CSV-style spend input ──────────────────────────────

def parse_spend_csv(raw: str) -> List[float]:
    """
    Parse user-pasted monthly spend data. Accepts:
    - Comma-separated: 10000, 12000, 11500
    - Newline-separated
    - With $ or , formatting: $10,000
    - Month labels: Jan: $10,000
    Returns list of floats (oldest first).
    """
    values = []
    # Strip dollar signs, commas within numbers, and month labels
    cleaned = re.sub(r"[A-Za-z]+\s*[\d]?\s*[:=]", " ", raw)   # strip "Jan:", "Q1:"
    cleaned = re.sub(r"\$", "", cleaned)
    cleaned = re.sub(r"(?<=\d),(?=\d{3})", "", cleaned)        # 10,000 → 10000
    tokens = re.split(r"[\s,;\n\r|]+", cleaned)
    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue
        try:
            values.append(float(tok))
        except ValueError:
            pass
    return values


import re  # noqa: E402 — imported again for parse_spend_csv above


# ── Main entry point ──────────────────────────────────────────────────

def run_spend_forecast(
    monthly_spend: List[float],
    category: str = "",
    subcategory: str = "",
    months_ahead: int = 12,
    apply_seasonality: bool = True,
    api_key: str = "",
    provider: str = "claude",
) -> Dict[str, Any]:
    """
    Run 12-month spend forecast for a category.

    Args:
        monthly_spend: List of historical monthly spend values (oldest first), min 3
        category: Procurement category (e.g., "IT") for inflation benchmark
        subcategory: Subcategory for more precise inflation rate
        months_ahead: How many months to forecast (default 12)
        apply_seasonality: Whether to apply seasonal index (default True)
        api_key: Optional LLM key for CFO narrative
        provider: LLM provider name

    Returns:
        {
            "forecast": {monthly_actuals, forecast_months, regression, summary},
            "category": str,
            "subcategory": str,
            "inflation_rate_pct": float,
            "narrative": {headline, savings_levers, risk_factors, ...} or {},
            "scanned_at": timestamp
        }
    """
    if len(monthly_spend) < 3:
        return {
            "error": "At least 3 months of historical spend required",
            "forecast": {},
            "narrative": {},
            "scanned_at": time.time(),
        }

    forecast = _build_forecast(
        monthly_spend=monthly_spend,
        category=category,
        subcategory=subcategory,
        apply_seasonality=apply_seasonality,
        months_ahead=months_ahead,
    )

    # LLM narrative
    narrative = {}
    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if _ROUTER_AVAILABLE and _call_llm and key and "error" not in forecast:
        try:
            payload = {
                "category": category,
                "subcategory": subcategory,
                "summary": forecast["summary"],
                "inflation_rate_annual_pct": forecast["inflation_rate_annual_pct"],
                "regression_r2": forecast["regression"]["r_squared"],
                "forecast_12mo": [m["projected"] for m in forecast["forecast_months"]],
            }
            raw = _call_llm(
                messages=[{"role": "user",
                            "content": f"Spend forecast data:\n{json.dumps(payload, indent=2)}"}],
                provider=provider,
                api_key=key,
                system=_CFO_PROMPT,
                max_tokens=800,
            )
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                narrative = json.loads(m.group())
        except Exception as e:
            narrative = {"error": str(e)}

    return {
        "forecast": forecast,
        "category": category,
        "subcategory": subcategory,
        "inflation_rate_pct": forecast.get("inflation_rate_annual_pct", _DEFAULT_INFLATION),
        "narrative": narrative,
        "scanned_at": time.time(),
    }
