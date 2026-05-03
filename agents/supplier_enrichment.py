"""
Agent #3: Supplier Enrichment
Auto-enriches a supplier record using SEC EDGAR financials, Open Corporates
registration, and news sentiment. Caches results in market_data_cache table.
"""
import json
import os
import re
import time
import requests
from typing import Dict, Any, Optional

try:
    from agents.llm_router import call_llm as _call_llm
    _ROUTER_AVAILABLE = True
except ImportError:
    _call_llm = None
    _ROUTER_AVAILABLE = False


# ── Data fetchers ─────────────────────────────────────────────────────

def _get_sec_facts(company_name: str) -> Dict:
    """Resolve CIK and pull key XBRL financial facts."""
    try:
        r = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers={"User-Agent": "ProcureIQ contact@procureiq.app"},
            timeout=10,
        )
        if r.status_code != 200:
            return {}
        tickers = r.json()
        name_lower = company_name.lower()
        cik = None
        ticker = None
        for entry in tickers.values():
            if name_lower in entry.get("title", "").lower():
                cik = str(entry["cik_str"]).zfill(10)
                ticker = entry.get("ticker", "")
                break
        if not cik:
            return {}

        facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        rf = requests.get(
            facts_url,
            headers={"User-Agent": "ProcureIQ contact@procureiq.app"},
            timeout=15,
        )
        if rf.status_code != 200:
            return {"cik": cik, "ticker": ticker}

        facts = rf.json()
        us_gaap = facts.get("facts", {}).get("us-gaap", {})

        def _last_val(concept: str) -> Optional[float]:
            data = us_gaap.get(concept, {}).get("units", {}).get("USD", [])
            annuals = [d for d in data if d.get("form") in ("10-K", "10-K/A") and d.get("val")]
            return annuals[-1]["val"] if annuals else None

        revenues = _last_val("Revenues") or _last_val("RevenueFromContractWithCustomerExcludingAssessedTax")
        assets = _last_val("Assets")
        liabilities = _last_val("Liabilities")
        cash = _last_val("CashAndCashEquivalentsAtCarryingValue")
        net_income = _last_val("NetIncomeLoss")

        return {
            "cik": cik,
            "ticker": ticker,
            "revenue_usd": revenues,
            "total_assets_usd": assets,
            "total_liabilities_usd": liabilities,
            "cash_usd": cash,
            "net_income_usd": net_income,
            "debt_to_assets": round(liabilities / assets, 3) if (liabilities and assets and assets > 0) else None,
            "profit_margin": round(net_income / revenues, 3) if (net_income and revenues and revenues > 0) else None,
            "source": "SEC EDGAR XBRL",
        }
    except Exception as e:
        return {"error": str(e)}


def _get_opencorporates_profile(company_name: str) -> Dict:
    """Get company registration profile from Open Corporates."""
    try:
        r = requests.get(
            "https://api.opencorporates.com/v0.4/companies/search",
            params={"q": company_name, "format": "json", "per_page": 3},
            timeout=10,
        )
        if r.status_code == 200:
            companies = r.json().get("results", {}).get("companies", [])
            if companies:
                co = companies[0]["company"]
                return {
                    "legal_name": co.get("name", ""),
                    "jurisdiction": co.get("jurisdiction_code", ""),
                    "company_number": co.get("company_number", ""),
                    "company_type": co.get("company_type", ""),
                    "status": co.get("current_status", ""),
                    "incorporated": co.get("incorporation_date", ""),
                    "registered_address": co.get("registered_address_in_full", ""),
                    "source": "Open Corporates",
                }
    except Exception as e:
        return {"error": str(e)}
    return {}


def _get_usaspending_history(company_name: str) -> Dict:
    """Check federal contracting history for supplier."""
    payload = {
        "filters": {
            "award_type_codes": ["A", "B", "C", "D"],
            "recipient_search_text": [company_name],
            "time_period": [{"start_date": "2018-01-01", "end_date": "2025-12-31"}],
        },
        "fields": ["Award Amount", "Awarding Agency Name", "Action Date"],
        "page": 1, "limit": 5, "sort": "Award Amount", "order": "desc",
    }
    try:
        r = requests.post(
            "https://api.usaspending.gov/api/v2/search/spending_by_award/",
            json=payload, timeout=15,
            headers={"Content-Type": "application/json"},
        )
        if r.status_code == 200:
            results = r.json().get("results", [])
            total = sum(float(row.get("Award Amount") or 0) for row in results)
            return {
                "federal_contract_count": len(results),
                "total_federal_awards_usd": total,
                "agencies": list({row.get("Awarding Agency Name", "") for row in results if row.get("Awarding Agency Name")}),
                "source": "USASpending.gov",
            }
    except Exception:
        pass
    return {"federal_contract_count": 0, "total_federal_awards_usd": 0}


# ── Synthesis prompt ──────────────────────────────────────────────────

_SYNTHESIS_PROMPT = """\
You are a senior procurement analyst writing a supplier due diligence brief.
Given the following raw data about a supplier, write a structured risk assessment.

Return ONLY valid JSON in this structure:
{
  "financial_health": "STRONG | STABLE | WATCH | DISTRESSED | UNKNOWN",
  "financial_summary": "2-3 sentence summary of financial position",
  "risk_flags": ["list of specific risk flags — only real ones, not generic"],
  "federal_credibility": "HIGH | MEDIUM | LOW | NONE",
  "registration_status": "ACTIVE | INACTIVE | UNKNOWN",
  "procurement_recommendation": "SHORTLIST | QUALIFY_FIRST | MONITOR | AVOID",
  "recommendation_reason": "1-2 sentences explaining the recommendation",
  "key_strengths": ["up to 3 specific strengths"],
  "key_concerns": ["up to 3 specific concerns"]
}
"""


def run_supplier_enrichment_agent(
    company_name: str,
    api_key: str = "",
    use_cache: bool = True,
    provider: str = "claude",
) -> Dict[str, Any]:
    """
    Enrich a supplier record with financial, registration, and credibility data.
    Caches results for 24 hours via the database market_data_cache table.
    """
    cache_key = f"enrichment_{company_name.lower().replace(' ', '_')}"

    # Check cache first
    if use_cache:
        try:
            from database import get_database
            db = get_database()
            cached = db.get_cached_market_data(cache_key)
            if cached:
                return cached
        except Exception:
            pass

    sec_data = _get_sec_facts(company_name)
    oc_data = _get_opencorporates_profile(company_name)
    fed_data = _get_usaspending_history(company_name)

    raw_data = {
        "company_name": company_name,
        "sec_financial_data": sec_data,
        "registration_data": oc_data,
        "federal_contract_history": fed_data,
    }

    # Use LLM to synthesize if available (any provider)
    synthesis = {}
    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if _ROUTER_AVAILABLE and _call_llm and key:
        try:
            text = _call_llm(
                messages=[{
                    "role": "user",
                    "content": (
                        f"Company: {company_name}\n\n"
                        f"Raw data:\n{json.dumps(raw_data, indent=2)}"
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
    else:
        # Rule-based fallback without Claude
        revenue = sec_data.get("revenue_usd")
        debt_ratio = sec_data.get("debt_to_assets")
        margin = sec_data.get("profit_margin")
        fed_awards = fed_data.get("total_federal_awards_usd", 0)

        if revenue and revenue > 1_000_000_000:
            health = "STRONG"
        elif revenue and revenue > 100_000_000:
            health = "STABLE"
        elif revenue:
            health = "WATCH"
        else:
            health = "UNKNOWN"

        synthesis = {
            "financial_health": health,
            "financial_summary": f"Revenue: ${revenue:,.0f}" if revenue else "No public financial data found.",
            "risk_flags": (["High debt-to-assets ratio"] if (debt_ratio and debt_ratio > 0.7) else []),
            "federal_credibility": "HIGH" if fed_awards > 1_000_000 else ("MEDIUM" if fed_awards > 0 else "NONE"),
            "registration_status": oc_data.get("status", "UNKNOWN").upper() or "UNKNOWN",
            "procurement_recommendation": "SHORTLIST" if (revenue and fed_awards > 0) else "QUALIFY_FIRST",
            "recommendation_reason": "Based on available public data.",
            "key_strengths": [],
            "key_concerns": [],
        }

    result = {**raw_data, "synthesis": synthesis, "enriched_at": time.time()}

    # Store in cache (24-hour TTL)
    try:
        from database import get_database
        db = get_database()
        db.cache_market_data(cache_key, result, ttl_seconds=86400)
    except Exception:
        pass

    return result
