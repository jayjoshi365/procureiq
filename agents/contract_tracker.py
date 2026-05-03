"""
Agent: Contract Obligation Tracker
Extracts and monitors contract obligations from pasted contract text:
  - Renewal / expiry dates
  - Termination notice periods
  - Price escalation triggers (CPI, fixed %, milestone)
  - Performance review milestones (SLA review, QBR dates)
  - Auto-renewal traps
  - Payment terms and penalties
  - Exclusivity / non-compete clauses

Two extraction modes:
  1. LLM extraction (preferred) — structured JSON via Claude/OpenAI
  2. Regex fallback — pattern-based for no-key scenario

Returns a structured obligation calendar ready for display in Streamlit.
"""
import re
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

try:
    from agents.llm_router import call_llm as _call_llm
    _ROUTER_AVAILABLE = True
except ImportError:
    _call_llm = None
    _ROUTER_AVAILABLE = False


# ── LLM extraction prompt ─────────────────────────────────────────────

_EXTRACTION_PROMPT = """\
You are a senior contracts attorney specializing in procurement and vendor agreements.
Analyze the contract text and extract ALL obligation milestones and risk triggers.

Return ONLY valid JSON in this exact structure (no markdown, no explanation):
{
  "contract_summary": {
    "supplier_name": "string or null",
    "contract_type": "MSA|SOW|PO|NDA|SLA|Framework|Other",
    "effective_date": "YYYY-MM-DD or null",
    "expiry_date": "YYYY-MM-DD or null",
    "total_value": "string or null",
    "governing_law": "string or null"
  },
  "obligations": [
    {
      "type": "Renewal|Notice|Escalation|Review|Payment|Penalty|Exclusivity|Compliance|Other",
      "label": "Short label (max 60 chars)",
      "due_date": "YYYY-MM-DD or null",
      "recurrence": "Annual|Quarterly|Monthly|One-time|null",
      "trigger": "What triggers this obligation (max 120 chars)",
      "consequence": "What happens if missed (max 120 chars)",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "raw_clause": "Verbatim clause excerpt (max 300 chars)"
    }
  ],
  "risk_flags": [
    {
      "flag": "Short risk label",
      "detail": "Explanation (max 200 chars)",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW"
    }
  ],
  "recommended_actions": [
    {"action": "string", "urgency": "Immediate|30 days|60 days|90 days"}
  ]
}

Extract EVERY obligation clause. Be conservative: if something could be a trap or risk, flag it.
Common traps to watch for: auto-renewal without written notice, CPI escalation uncapped,
most-favored-customer clauses, exclusivity without carve-outs, unlimited liability, IP assignment.
"""


# ── Regex fallback patterns ───────────────────────────────────────────

_DATE_PATTERNS = [
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
    r"\b(\d{4}-\d{2}-\d{2})\b",
]

_OBLIGATION_PATTERNS = {
    "Renewal": [
        r"(?:auto(?:matically)?[-\s]renew|renew(?:al|s)?(?:\s+automatically)?)[^\n.]{0,200}",
        r"(?:term|agreement)\s+shall\s+(?:renew|continue)[^\n.]{0,200}",
    ],
    "Notice": [
        r"(?:written?\s+)?notice\s+of\s+(?:at\s+least\s+)?(\d+)\s+(?:days?|months?|calendar\s+days?)[^\n.]{0,150}",
        r"(\d+)[\s-]day\s+(?:written\s+)?(?:termination\s+)?notice[^\n.]{0,150}",
    ],
    "Escalation": [
        r"(?:price|fee|rate)s?\s+(?:shall\s+)?(?:increase|escalat|adjust)[^\n.]{0,200}",
        r"CPI\s*(?:[-+]?\s*\d+(?:\.\d+)?\s*%)?[^\n.]{0,150}",
        r"(?:annual|yearly)\s+(?:price|rate|fee)\s+(?:increase|adjustment)[^\n.]{0,150}",
    ],
    "Payment": [
        r"(?:net\s*\d+|payment\s+(?:due|terms?|within))[^\n.]{0,150}",
        r"invoice\s+(?:due|payable|within)[^\n.]{0,150}",
        r"late\s+(?:payment\s+)?(?:fee|penalty|interest)[^\n.]{0,150}",
    ],
    "Review": [
        r"(?:quarterly|annual|monthly|semi-annual)\s+(?:business\s+review|QBR|performance\s+review|SLA\s+review)[^\n.]{0,150}",
        r"(?:review|audit)\s+(?:shall|will|must)\s+(?:occur|take\s+place|be\s+conducted)[^\n.]{0,150}",
    ],
    "Penalty": [
        r"(?:liquidated\s+damages?|penalty|penalties|service\s+credit)[^\n.]{0,200}",
        r"(?:SLA|service\s+level)\s+(?:breach|violation|failure)[^\n.]{0,150}",
    ],
    "Exclusivity": [
        r"(?:exclusive|exclusivity|sole\s+provider|preferred\s+(?:vendor|supplier))[^\n.]{0,200}",
        r"(?:non-compete|noncompete|not\s+(?:to\s+)?(?:solicit|engage|compete))[^\n.]{0,200}",
    ],
}

_SEVERITY_KEYWORDS = {
    "CRITICAL": ["bankrupt", "insolvency", "termination for cause", "material breach", "immediately"],
    "HIGH": ["auto-renew", "automatic renewal", "liquidated damages", "exclusivity", "unlimited liability", "indemnif"],
    "MEDIUM": ["escalat", "CPI", "notice", "review", "audit", "penalty", "credit"],
    "LOW": ["prefer", "best effort", "reasonable", "may"],
}


def _regex_extract(text: str) -> Dict:
    """Fallback extraction using regex — no LLM required."""
    text_lower = text.lower()
    obligations = []
    risk_flags = []

    for ob_type, patterns in _OBLIGATION_PATTERNS.items():
        for pat in patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                excerpt = m.group(0).strip()[:300]
                sev = "MEDIUM"
                for level, kws in _SEVERITY_KEYWORDS.items():
                    if any(kw.lower() in excerpt.lower() for kw in kws):
                        sev = level
                        break
                obligations.append({
                    "type": ob_type,
                    "label": f"{ob_type}: {excerpt[:55]}{'…' if len(excerpt) > 55 else ''}",
                    "due_date": None,
                    "recurrence": None,
                    "trigger": "See raw clause",
                    "consequence": "Review manually",
                    "severity": sev,
                    "raw_clause": excerpt,
                })

    # Risk flag heuristics
    high_risk_phrases = [
        ("auto-renew", "AUTO-RENEWAL TRAP", "Contract auto-renews without written notice — set calendar reminder"),
        ("unlimited liability", "UNLIMITED LIABILITY", "Supplier may be exposed to uncapped damages"),
        ("most favored", "MFN CLAUSE", "Most-favored-nation pricing may restrict renegotiation leverage"),
        ("exclusiv", "EXCLUSIVITY", "Exclusivity clause limits ability to dual-source or switch"),
        ("cpi", "UNCAPPED CPI ESCALATION", "CPI-linked escalation with no cap increases unpredictably"),
        ("ip assign", "IP ASSIGNMENT", "IP may transfer to supplier — review ownership terms"),
        ("indemnif", "INDEMNIFICATION", "Broad indemnification clause — verify scope and caps"),
    ]
    for kw, flag, detail in high_risk_phrases:
        if kw in text_lower:
            risk_flags.append({"flag": flag, "detail": detail, "severity": "HIGH"})

    # Extract dates for summary
    all_dates = []
    for pat in _DATE_PATTERNS:
        all_dates.extend(re.findall(pat, text, re.IGNORECASE))

    return {
        "contract_summary": {
            "supplier_name": None,
            "contract_type": "Other",
            "effective_date": None,
            "expiry_date": None,
            "total_value": None,
            "governing_law": None,
        },
        "obligations": obligations[:30],
        "risk_flags": risk_flags,
        "recommended_actions": [
            {"action": "Review auto-renewal provisions and set calendar reminders 90 days before expiry", "urgency": "30 days"},
            {"action": "Validate all price escalation clauses and model total cost of ownership", "urgency": "60 days"},
            {"action": "Confirm SLA review schedule and performance baseline metrics", "urgency": "90 days"},
        ],
        "_extraction_mode": "regex_fallback",
    }


# ── Days-until helper ─────────────────────────────────────────────────

def _days_until(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    try:
        target = datetime.strptime(date_str, "%Y-%m-%d")
        return (target - datetime.now()).days
    except Exception:
        return None


def _enrich_obligations(obligations: List[Dict]) -> List[Dict]:
    """Add days_until and urgency_color to each obligation."""
    enriched = []
    for ob in obligations:
        days = _days_until(ob.get("due_date"))
        if days is not None:
            if days < 0:
                urgency_color = "#6B7280"   # grey — past due
            elif days <= 30:
                urgency_color = "#F87171"   # red
            elif days <= 90:
                urgency_color = "#FCD34D"   # amber
            else:
                urgency_color = "#4ADE80"   # green
        else:
            urgency_color = "#60A5FA"       # blue — no date parsed
        enriched.append({**ob, "days_until": days, "urgency_color": urgency_color})
    return enriched


# ── Main entry point ──────────────────────────────────────────────────

def run_contract_tracker(
    contract_text: str,
    contract_label: str = "Contract",
    api_key: str = "",
    provider: str = "claude",
) -> Dict[str, Any]:
    """
    Extract and track obligations from contract text.

    Args:
        contract_text: Raw contract text (paste from PDF/Word)
        contract_label: Human-readable name for this contract
        api_key: Optional LLM key for intelligent extraction
        provider: LLM provider name

    Returns:
        {
            "label": str,
            "contract_summary": {...},
            "obligations": [enriched obligation dicts],
            "risk_flags": [...],
            "recommended_actions": [...],
            "extraction_mode": "llm" | "regex_fallback",
            "scanned_at": timestamp,
            "obligation_counts": {"CRITICAL": N, "HIGH": N, "MEDIUM": N, "LOW": N}
        }
    """
    if not contract_text or not contract_text.strip():
        return {
            "label": contract_label,
            "error": "No contract text provided",
            "obligations": [],
            "risk_flags": [],
            "recommended_actions": [],
            "extraction_mode": "none",
            "scanned_at": time.time(),
        }

    import os
    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    extraction_mode = "regex_fallback"
    result = {}

    # Attempt LLM extraction
    if _ROUTER_AVAILABLE and _call_llm and key:
        try:
            # Truncate to ~12k chars to stay within token budget
            truncated = contract_text[:12000]
            raw = _call_llm(
                messages=[{"role": "user", "content": f"CONTRACT TEXT:\n\n{truncated}"}],
                provider=provider,
                api_key=key,
                system=_EXTRACTION_PROMPT,
                max_tokens=2000,
            )
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                result = json.loads(m.group())
                extraction_mode = "llm"
        except Exception:
            pass

    if not result:
        result = _regex_extract(contract_text)

    obligations = _enrich_obligations(result.get("obligations", []))
    # Sort by severity then by days_until
    sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    obligations.sort(key=lambda x: (
        sev_order.get(x.get("severity", "LOW"), 3),
        x.get("days_until") if x.get("days_until") is not None else 9999,
    ))

    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for ob in obligations:
        sev = ob.get("severity", "LOW")
        if sev in counts:
            counts[sev] += 1

    return {
        "label": contract_label,
        "contract_summary": result.get("contract_summary", {}),
        "obligations": obligations,
        "risk_flags": result.get("risk_flags", []),
        "recommended_actions": result.get("recommended_actions", []),
        "extraction_mode": extraction_mode,
        "scanned_at": time.time(),
        "obligation_counts": counts,
    }
