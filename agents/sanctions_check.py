"""
Agent #28: Sanctions & Exclusions Check
Screens suppliers against:
  1. OFAC Specially Designated Nationals (SDN) list — US Treasury (free, no key)
  2. SAM.gov Exclusions — US federal debarment database (free API key required)
  3. Basic heuristic name screening for high-risk jurisdictions
"""
import re
import os
import requests
import json
from typing import Dict, Any, List


# ── OFAC Check ────────────────────────────────────────────────────────

_OFAC_ENDPOINTS = [
    # Primary Treasury SDN API
    "https://sanctionslistservice.ofac.treas.gov/api/PublicatnEx/SDN",
    # Backup: OFAC search API (different path)
    "https://sanctionslistservice.ofac.treas.gov/api/PublicatnEx/SDNSearch",
]


def _check_ofac(company_name: str) -> Dict:
    """
    Check OFAC Consolidated Sanctions List via Treasury API.
    No API key required. Tries two endpoint variants.
    """
    for endpoint in _OFAC_ENDPOINTS:
        try:
            r = requests.get(
                endpoint,
                params={"value": company_name, "type": "name"},
                timeout=10,
                headers={"Accept": "application/json", "User-Agent": "ProcureIQ/1.0"},
            )
            if r.status_code == 200:
                data = r.json()
                sdns = data if isinstance(data, list) else data.get("sdnList", {}).get("sdnEntry", [])
                if not isinstance(sdns, list):
                    sdns = [sdns] if sdns else []
                matches = []
                name_lower = company_name.lower()
                for entry in sdns:
                    entry_name = str(
                        entry.get("lastName", "") + " " + entry.get("firstName", "")
                    ).strip().lower()
                    aka_list = entry.get("akaList", {})
                    if isinstance(aka_list, dict):
                        aka_list = aka_list.get("aka", [])
                    if not isinstance(aka_list, list):
                        aka_list = [aka_list]
                    aka_names = [str(a.get("lastName", "")).lower() for a in aka_list if a]
                    all_names = [entry_name] + aka_names
                    if any(name_lower in n or n in name_lower for n in all_names if n.strip()):
                        matches.append({
                            "sdn_name": (
                                entry.get("lastName", "") + " " + entry.get("firstName", "")
                            ).strip(),
                            "type": entry.get("sdnType", ""),
                            "programs": entry.get("programList", {}).get("program", []),
                        })
                return {
                    "screened": True,
                    "source": "OFAC SDN List",
                    "matches": matches,
                    "hit": len(matches) > 0,
                }
            # Non-200 status — try next endpoint
        except Exception:
            continue  # Try next endpoint

    # All endpoints failed — do NOT silently pass; require manual review
    return {
        "screened": False,
        "source": "OFAC SDN List",
        "error": (
            "OFAC API unreachable. Complete manual OFAC screening at "
            "https://sanctionslistservice.ofac.treas.gov before award."
        ),
        "hit": False,
    }


# ── SAM.gov Exclusions ────────────────────────────────────────────────

def _check_sam_exclusions(company_name: str, api_key: str = "") -> Dict:
    """
    Check SAM.gov federal exclusions (debarred contractors).
    Requires free API key from api.sam.gov — degrades gracefully without one.
    """
    key = api_key or os.getenv("SAM_GOV_API_KEY", "")
    if not key:
        return {
            "screened": False,
            "source": "SAM.gov Exclusions",
            "note": "SAM_GOV_API_KEY not configured. Register free at api.sam.gov to enable federal debarment screening.",
            "hit": False,
        }
    try:
        r = requests.get(
            "https://api.sam.gov/entity-information/v3/exclusions",
            params={"api_key": key, "legalBusinessName": company_name, "q": company_name},
            timeout=12,
        )
        if r.status_code == 200:
            data = r.json()
            results = data.get("exclusionData", [])
            matches = [
                {
                    "legal_name": e.get("entityInformation", {}).get("legalBusinessName", ""),
                    "exclusion_type": e.get("exclusionDetails", {}).get("exclusionType", ""),
                    "agency": e.get("exclusionDetails", {}).get("agencyName", ""),
                    "active": e.get("exclusionDetails", {}).get("activeExclusion", False),
                }
                for e in results
            ]
            return {
                "screened": True,
                "source": "SAM.gov Exclusions",
                "matches": matches,
                "hit": len(matches) > 0,
            }
        elif r.status_code == 403:
            return {"screened": False, "source": "SAM.gov Exclusions",
                    "error": "Invalid API key.", "hit": False}
    except Exception as e:
        return {"screened": False, "source": "SAM.gov Exclusions", "error": str(e), "hit": False}
    return {"screened": True, "source": "SAM.gov Exclusions", "matches": [], "hit": False}


# ── High-risk jurisdiction heuristic ─────────────────────────────────

_HIGH_RISK_COUNTRIES = {
    "russia", "russian federation", "iran", "north korea", "dprk", "syria",
    "cuba", "venezuela", "myanmar", "burma", "belarus", "sudan",
    "zimbabwe", "somalia", "eritrea", "nicaragua",
}


def _check_jurisdiction_risk(company_name: str, location: str = "") -> Dict:
    """Flag if company name or location references high-risk jurisdictions."""
    combined = (company_name + " " + location).lower()
    flagged = [c for c in _HIGH_RISK_COUNTRIES if c in combined]
    return {
        "screened": True,
        "source": "Jurisdiction Heuristic",
        "high_risk_terms": flagged,
        "hit": len(flagged) > 0,
    }


# ── Main entry point ──────────────────────────────────────────────────

def run_sanctions_check(
    company_name: str,
    location: str = "",
    ein: str = "",
    sam_api_key: str = "",
) -> Dict[str, Any]:
    """
    Run all sanctions and exclusion checks for a supplier.

    Returns:
        {
            "overall_status": "PASS" | "FLAG" | "FAIL",
            "checks": [...],
            "summary": "human-readable summary",
            "action_required": bool
        }
    """
    if not company_name.strip():
        return {"overall_status": "SKIP", "checks": [], "summary": "No company name provided."}

    checks = []

    ofac = _check_ofac(company_name)
    checks.append(ofac)

    sam = _check_sam_exclusions(company_name, sam_api_key)
    checks.append(sam)

    juris = _check_jurisdiction_risk(company_name, location)
    checks.append(juris)

    # Aggregate verdict
    hard_fails = [c for c in checks if c.get("hit") and c.get("screened")]
    soft_flags = [c for c in checks if not c.get("screened") and not c.get("error")]

    unscreened_sources = [c["source"] for c in checks if not c.get("screened")]

    if hard_fails:
        status = "FAIL"
        summary = (
            f"FAILED: {company_name} matched against "
            f"{', '.join(c['source'] for c in hard_fails)}. "
            "Do not proceed without legal review."
        )
    elif any(c.get("error") for c in checks):
        status = "FLAG"
        summary = (
            f"INCOMPLETE: Screening could not reach {', '.join(unscreened_sources)} for {company_name}. "
            "Manual compliance review required before award."
        )
    else:
        cleared = [c["source"] for c in checks if c.get("screened")]
        status = "PASS"
        summary = (
            f"PASS: {company_name} cleared {' and '.join(cleared)}. "
            "No sanctions matches found."
        )

    return {
        "overall_status": status,
        "company_name": company_name,
        "checks": checks,
        "summary": summary,
        "action_required": status != "PASS",
        "checked_at": __import__("time").time(),
    }
