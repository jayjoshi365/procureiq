"""
Agent: Supplier Risk Monitor
Continuously scores supplier health by combining:
  - SEC 8-K material event filings (last 90 days)
  - XBRL financial ratio drift (current vs prior 10-K)
  - News sentiment signals (via yfinance)
  - Rule-based composite risk score (0–100, higher = more risk)
  - Optional LLM narrative synthesis

No API key required for the data layer. LLM key optional for narrative.
"""
import os
import json
import re
import time
import requests
from typing import Dict, List, Any, Optional

try:
    from agents.llm_router import call_llm as _call_llm
    _ROUTER_AVAILABLE = True
except ImportError:
    _call_llm = None
    _ROUTER_AVAILABLE = False

try:
    import yfinance as yf
    _YF = True
except ImportError:
    _YF = False

_EDGAR_HEADERS = {"User-Agent": "ProcureIQ contact@procureiq.app"}
_SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# 8-K item codes that signal material risk
_HIGH_RISK_8K_ITEMS = {
    "1.01": "Material Definitive Agreement",
    "1.02": "Termination of Material Agreement",
    "1.03": "Bankruptcy or Receivership",
    "2.04": "Triggering Events Affecting Repayment",
    "2.06": "Material Impairments",
    "3.01": "Notice of Delisting",
    "4.01": "Changes in Auditor",
    "4.02": "Non-Reliance on Prior Financial Statements",
    "8.01": "Other Events (Material)",
}
_MEDIUM_RISK_8K_ITEMS = {
    "2.01": "Asset Acquisition or Disposition",
    "2.02": "Results of Operations",
    "2.03": "Creation of Direct Financial Obligation",
    "5.02": "Changes in Directors / Officers",
    "8.01": "Other Events",
}


# ── SEC EDGAR helpers ──────────────────────────────────────────────────

def _resolve_cik(ticker_or_name: str) -> Optional[str]:
    """Return zero-padded CIK string for a ticker or company name."""
    try:
        r = requests.get(_SEC_TICKERS_URL, headers=_EDGAR_HEADERS, timeout=10)
        if r.status_code != 200:
            return None
        tickers = r.json()
        term = ticker_or_name.lower().strip()
        # Try ticker match first (exact), then name substring
        for entry in tickers.values():
            if entry.get("ticker", "").lower() == term:
                return str(entry["cik_str"]).zfill(10)
        for entry in tickers.values():
            if term in entry.get("title", "").lower():
                return str(entry["cik_str"]).zfill(10)
    except Exception:
        pass
    return None


def _get_recent_8ks(cik: str, days: int = 90) -> List[Dict]:
    """Return list of 8-K filings in the last `days` days with item codes parsed."""
    try:
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        r = requests.get(url, headers=_EDGAR_HEADERS, timeout=15)
        if r.status_code != 200:
            return []
        data = r.json()
        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])
        accessions = filings.get("accessionNumber", [])
        items_list = filings.get("items", [])

        cutoff = time.time() - (days * 86400)
        results = []
        for form, date_str, acc, items in zip(forms, dates, accessions, items_list):
            if form not in ("8-K", "8-K/A"):
                continue
            try:
                ts = time.mktime(time.strptime(date_str, "%Y-%m-%d"))
            except Exception:
                continue
            if ts < cutoff:
                continue
            results.append({
                "form": form,
                "date": date_str,
                "accession": acc,
                "items": str(items),
            })
        return results
    except Exception:
        return []


def _get_xbrl_ratios(cik: str) -> Dict:
    """Pull key financial ratios for current and prior 10-K period."""
    try:
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        r = requests.get(url, headers=_EDGAR_HEADERS, timeout=20)
        if r.status_code != 200:
            return {}
        us_gaap = r.json().get("facts", {}).get("us-gaap", {})

        def _annuals(concept: str) -> List[Dict]:
            data = us_gaap.get(concept, {}).get("units", {}).get("USD", [])
            return sorted(
                [d for d in data if d.get("form") in ("10-K", "10-K/A") and d.get("val")],
                key=lambda x: x.get("end", ""),
            )

        def _last_two(concept: str):
            recs = _annuals(concept)
            if len(recs) >= 2:
                return recs[-1]["val"], recs[-2]["val"], recs[-1].get("end", "")
            if len(recs) == 1:
                return recs[-1]["val"], None, recs[-1].get("end", "")
            return None, None, ""

        rev_cur, rev_pri, rev_end = _last_two(
            "Revenues") or _last_two("RevenueFromContractWithCustomerExcludingAssessedTax")
        asset_cur, asset_pri, _ = _last_two("Assets")
        liab_cur, liab_pri, _ = _last_two("Liabilities")
        ni_cur, ni_pri, _ = _last_two("NetIncomeLoss")
        cash_cur, _, _ = _last_two("CashAndCashEquivalentsAtCarryingValue")

        def _safe_ratio(n, d):
            if n is not None and d and d != 0:
                return round(n / d, 3)
            return None

        def _pct_change(cur, pri):
            if cur is not None and pri and pri != 0:
                return round((cur - pri) / abs(pri) * 100, 1)
            return None

        return {
            "period_end": rev_end,
            "revenue_current": rev_cur,
            "revenue_prior": rev_pri,
            "revenue_growth_pct": _pct_change(rev_cur, rev_pri),
            "debt_to_assets_current": _safe_ratio(liab_cur, asset_cur),
            "debt_to_assets_prior": _safe_ratio(liab_pri, asset_pri),
            "profit_margin_current": _safe_ratio(ni_cur, rev_cur),
            "profit_margin_prior": _safe_ratio(ni_pri, rev_pri),
            "cash": cash_cur,
            "net_income_current": ni_cur,
        }
    except Exception:
        return {}


def _get_news_signals(ticker: str) -> List[Dict]:
    """Pull yfinance news signals — same pattern as app.py."""
    if not _YF or not ticker:
        return []
    _RISK_TERMS = [
        "lawsuit", "litigation", "bankrupt", "restructur", "layoff", "recall",
        "breach", "hack", "cyber", "fraud", "investigation", "subpoena", "fine",
        "penalty", "downgrade", "loss", "deficit", "shutdown", "delay", "miss",
        "default", "impairment", "restate", "SEC", "DOJ", "FTC", "warning",
    ]
    try:
        tk = yf.Ticker(ticker)
        news = tk.news or []
        signals = []
        for item in news[:10]:
            title = (item.get("title") or "").lower()
            hits = [t for t in _RISK_TERMS if t in title]
            if hits:
                signals.append({
                    "title": item.get("title", ""),
                    "risk_terms": hits,
                    "publish_time": item.get("providerPublishTime", 0),
                })
        return signals
    except Exception:
        return []


# ── Risk scoring ──────────────────────────────────────────────────────

def _score_supplier(
    company_name: str,
    ticker: str,
    cik: Optional[str],
    filings_8k: List[Dict],
    ratios: Dict,
    news: List[Dict],
) -> Dict:
    """Compute a 0–100 composite risk score and breakdown."""
    score = 0
    flags = []

    # 8-K filing signals (max 40 pts)
    for f in filings_8k:
        items_str = f.get("items", "")
        for code, label in _HIGH_RISK_8K_ITEMS.items():
            if code in items_str:
                score += 15
                flags.append({"severity": "HIGH", "source": "SEC 8-K",
                               "detail": f"{f['date']}: {label} (Item {code})"})
                break
        else:
            for code, label in _MEDIUM_RISK_8K_ITEMS.items():
                if code in items_str:
                    score += 7
                    flags.append({"severity": "MEDIUM", "source": "SEC 8-K",
                                  "detail": f"{f['date']}: {label} (Item {code})"})
                    break
    score = min(score, 40)

    # Financial ratio drift (max 40 pts)
    if ratios:
        rev_growth = ratios.get("revenue_growth_pct")
        debt_cur = ratios.get("debt_to_assets_current")
        debt_pri = ratios.get("debt_to_assets_prior")
        margin_cur = ratios.get("profit_margin_current")
        margin_pri = ratios.get("profit_margin_prior")
        ni = ratios.get("net_income_current")

        if rev_growth is not None and rev_growth < -15:
            pts = 20 if rev_growth < -30 else 12
            score += pts
            flags.append({"severity": "HIGH" if pts == 20 else "MEDIUM",
                           "source": "XBRL", "detail": f"Revenue declined {rev_growth:.1f}% YoY"})

        if debt_cur is not None and debt_cur > 0.75:
            score += 15
            flags.append({"severity": "HIGH", "source": "XBRL",
                           "detail": f"Debt-to-assets ratio {debt_cur:.2f} — highly leveraged"})
        elif debt_cur and debt_pri and (debt_cur - debt_pri) > 0.15:
            score += 8
            flags.append({"severity": "MEDIUM", "source": "XBRL",
                           "detail": f"Debt ratio increased {(debt_cur-debt_pri):.2f} pts YoY"})

        if margin_cur is not None and margin_cur < 0:
            score += 12
            flags.append({"severity": "HIGH", "source": "XBRL",
                           "detail": f"Net loss — profit margin {margin_cur:.1%}"})
        elif margin_cur and margin_pri and (margin_cur - margin_pri) < -0.10:
            score += 6
            flags.append({"severity": "MEDIUM", "source": "XBRL",
                           "detail": f"Profit margin compressed {(margin_cur-margin_pri):.1%} YoY"})

    # News sentiment (max 20 pts)
    news_pts = min(len(news) * 5, 20)
    score += news_pts
    for sig in news[:3]:
        flags.append({"severity": "MEDIUM", "source": "News",
                       "detail": sig["title"][:120]})

    score = min(score, 100)

    if score >= 60:
        tier, color = "HIGH", "#F87171"
    elif score >= 30:
        tier, color = "MEDIUM", "#FCD34D"
    else:
        tier, color = "LOW", "#4ADE80"

    return {
        "company": company_name,
        "ticker": ticker,
        "risk_score": score,
        "risk_tier": tier,
        "risk_color": color,
        "flags": flags,
        "recent_8k_count": len(filings_8k),
        "ratios": ratios,
        "news_signals": news,
        "scanned_at": time.time(),
    }


# ── Synthesis prompt ──────────────────────────────────────────────────

_SYNTHESIS_PROMPT = """\
You are a senior supply chain risk analyst. Given structured risk data for multiple suppliers,
write a concise executive risk briefing.

Return ONLY valid JSON:
{
  "headline": "One sentence overall portfolio risk assessment",
  "high_risk_suppliers": ["supplier names"],
  "immediate_actions": [
    {"supplier": "...", "action": "...", "urgency": "Immediate|30 days|90 days"}
  ],
  "portfolio_risk_rating": "LOW|MEDIUM|HIGH|CRITICAL",
  "summary": "2-3 sentence narrative"
}
"""


def get_xbrl_financial_ratios(cik: str) -> Dict:
    """Public wrapper around _get_xbrl_ratios for use outside this module.

    Returns the same dict as _get_xbrl_ratios:
        revenue_growth_pct, profit_margin_current, debt_to_assets_current,
        net_income_current, cash, period_end, ...
    Returns {} on any failure — callers must handle the empty case gracefully.
    """
    if not cik:
        return {}
    try:
        return _get_xbrl_ratios(cik)
    except Exception:
        return {}


def run_supplier_risk_monitor(
    suppliers: List[Dict],
    api_key: str = "",
    provider: str = "claude",
    days_lookback: int = 90,
) -> Dict[str, Any]:
    """
    Run risk monitoring scan for a list of suppliers.

    Args:
        suppliers: List of {"name": str, "ticker": str} dicts
        api_key: Optional LLM key for narrative synthesis
        provider: LLM provider name
        days_lookback: How far back to scan 8-K filings (default 90 days)

    Returns:
        {
            "supplier_scores": [risk report per supplier],
            "portfolio_summary": {headline, actions, rating},
            "scanned_at": timestamp,
            "total_suppliers": N,
            "high_risk_count": N
        }
    """
    scores = []
    for sup in suppliers:
        name = sup.get("name", "").strip()
        ticker = sup.get("ticker", "").strip().upper()
        if not name:
            continue

        # Resolve CIK via ticker or name
        lookup = ticker if ticker and ticker not in ("—", "PRIVATE", "") else name
        cik = _resolve_cik(lookup)

        filings = _get_recent_8ks(cik, days_lookback) if cik else []
        ratios = _get_xbrl_ratios(cik) if cik else {}
        news = _get_news_signals(ticker) if ticker else []

        report = _score_supplier(name, ticker, cik, filings, ratios, news)
        scores.append(report)

    high_count = sum(1 for s in scores if s["risk_tier"] == "HIGH")
    medium_count = sum(1 for s in scores if s["risk_tier"] == "MEDIUM")

    # LLM synthesis (optional)
    synthesis = {}
    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if _ROUTER_AVAILABLE and _call_llm and key and scores:
        try:
            payload = [
                {"supplier": s["company"], "risk_score": s["risk_score"],
                 "risk_tier": s["risk_tier"], "flags": s["flags"][:5]}
                for s in scores
            ]
            text = _call_llm(
                messages=[{"role": "user",
                            "content": f"Supplier risk data:\n{json.dumps(payload, indent=2)}"}],
                provider=provider, api_key=key,
                system=_SYNTHESIS_PROMPT, max_tokens=800,
            )
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                synthesis = json.loads(m.group())
        except Exception as e:
            synthesis = {"error": str(e)}

    return {
        "supplier_scores": sorted(scores, key=lambda x: x["risk_score"], reverse=True),
        "portfolio_summary": synthesis,
        "scanned_at": time.time(),
        "total_suppliers": len(scores),
        "high_risk_count": high_count,
        "medium_risk_count": medium_count,
    }
