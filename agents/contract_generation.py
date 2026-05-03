"""
Agent #2: Contract Generation
Generates a full procurement contract (MSA, SOW, or Supply Agreement) using Claude.
Contract terms are calibrated to Kraljic posture, RAQSCI flags, and jurisdiction.
Output: HTML string (renderable by WeasyPrint to PDF).
"""
import os
import json
import re
import time
from typing import Dict, Any, Optional

from agents.llm_router import call_llm


_CONTRACT_SYSTEM = """\
You are a senior procurement attorney with 20 years of experience drafting commercial contracts.
Generate a complete, professional contract in clean HTML suitable for PDF rendering.

Rules calibrated by Kraljic posture:
- STRATEGIC: 3-5 year terms, step-in rights, liquidated damages, IP ownership by buyer,
  mandatory performance reviews, audit rights, DR/BCP requirements, technology escrow
- LEVERAGE: 1-3 year terms, standard limitation of liability, competitive benchmarking rights,
  most-favored-nation pricing clause, volume discount triggers
- BOTTLENECK: Dual-sourcing provisions, stockpiling rights, price cap mechanisms,
  long lead-time accommodation, force majeure protections for supply
- NON-CRITICAL: 1-year renewable terms, light SLA, standard limitation of liability,
  simple termination for convenience

RAQSCI integration:
- R (Regulatory): Include compliance representations, regulatory change notification obligations
- A (Assurance): Include supply assurance, business continuity, audit rights
- Q (Quality): Include quality standards, inspection rights, defect remedies
- S (Service): Include SLA schedule, measurement methodology, remedies/credits
- C (Cost): Include pricing model, escalation limits, benchmarking rights
- I (Innovation): Include continuous improvement obligations, technology roadmap sharing

Output ONLY valid HTML with embedded CSS. No markdown. No explanation text outside HTML.
Structure:
1. Cover page with party details, effective date, and contract reference
2. Definitions
3. Scope of Supply / Services
4. Commercial Terms (pricing, payment, escalation)
5. Term and Termination
6. Performance Standards / SLA (as applicable)
7. Intellectual Property
8. Confidentiality
9. Liability and Indemnification
10. Governing Law and Dispute Resolution
11. General Provisions
12. Signature Block
"""


def run_contract_generation_agent(
    contract_type: str = "Master Service Agreement",
    buyer_name: str = "Buyer Organization",
    supplier_name: str = "Supplier",
    category: str = "",
    subcategory: str = "",
    annual_value: float = 0,
    contract_term_years: int = 3,
    jurisdiction: str = "State of Delaware, USA",
    kraljic: str = "Strategic",
    raqsci_flags: Optional[Dict[str, bool]] = None,
    sla_targets: str = "",
    payment_terms: str = "Net 30",
    notice_period_days: int = 90,
    api_key: str = "",
    provider: str = "claude",
) -> Dict[str, Any]:
    """
    Generate a complete procurement contract as HTML.

    Returns:
        {
            "html": "<full contract HTML>",
            "contract_type": "...",
            "word_count": 2400,
            "sections": [...],
            "generated_at": timestamp
        }
    """
    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        return {"error": "No API key configured. Enter your key in the sidebar.", "html": ""}

    raqsci = raqsci_flags or {}
    raqsci_active = [k for k, v in raqsci.items() if v]

    user_prompt = f"""Generate a complete {contract_type} with these parameters:

PARTIES:
- Buyer: {buyer_name}
- Supplier: {supplier_name}

COMMERCIAL:
- Category: {category} — {subcategory}
- Annual Value: ${annual_value:,.0f}
- Contract Term: {contract_term_years} year(s)
- Payment Terms: {payment_terms}
- Notice Period for Termination: {notice_period_days} days

STRATEGIC POSTURE:
- Kraljic Classification: {kraljic}
- Active RAQSCI Requirements: {', '.join(raqsci_active) if raqsci_active else 'Standard'}

PERFORMANCE:
- SLA Targets: {sla_targets or 'Standard commercial SLA per category'}

LEGAL:
- Governing Law: {jurisdiction}

Apply all Kraljic-specific terms from your instructions.
Generate the full contract HTML now. Make it professionally formatted and complete (minimum 12 sections).
"""

    raw = call_llm(
        messages=[{"role": "user", "content": user_prompt}],
        provider=provider,
        api_key=key,
        system=_CONTRACT_SYSTEM,
        max_tokens=8192,
    )

    # Wrap in minimal HTML if model returned partial HTML
    if "<html" not in raw.lower():
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: 'Georgia', serif; max-width: 800px; margin: 0 auto; padding: 40px;
          color: #1a1a2e; line-height: 1.7; font-size: 11pt; }}
  h1   {{ font-size: 18pt; text-align: center; color: #0a1628; border-bottom: 2px solid #1d4ed8; padding-bottom: 8px; }}
  h2   {{ font-size: 13pt; color: #1d4ed8; margin-top: 24px; }}
  h3   {{ font-size: 11pt; color: #0a1628; font-weight: bold; }}
  .cover {{ text-align: center; padding: 60px 0; border-bottom: 1px solid #ccc; margin-bottom: 40px; }}
  .party  {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; margin: 8px 0; }}
  .clause {{ margin-bottom: 16px; }}
  .sig-block {{ display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 60px; }}
  .sig-line  {{ border-top: 1px solid #555; padding-top: 8px; margin-top: 40px; font-size: 10pt; }}
</style>
</head>
<body>
{raw}
</body>
</html>"""
    else:
        html = raw

    word_count = len(raw.split())

    return {
        "html": html,
        "contract_type": contract_type,
        "supplier_name": supplier_name,
        "buyer_name": buyer_name,
        "category": category,
        "jurisdiction": jurisdiction,
        "kraljic": kraljic,
        "word_count": word_count,
        "generated_at": time.time(),
    }
