"""
Agent #25: Conversational Intake Agent
Replaces the static intake form with a Claude-powered chat that asks smart
procurement questions and maps the answers to ProcureIQ session state keys.

Usage in Streamlit:
    from agents.intake_agent import run_intake_agent, get_intake_session_values

    result = run_intake_agent(conversation_history, user_message, api_key)
    # result["reply"]         — assistant message to display
    # result["session_updates"] — dict of session_state keys to set
    # result["complete"]      — True when intake is finished
"""
import os
import json
import re
from typing import Dict, Any, List, Optional

from agents.llm_router import call_llm


# ── Intake field mapping ──────────────────────────────────────────────
# Maps conversation concepts → ProcureIQ session state keys

INTAKE_FIELD_MAP = {
    "category":       "ctrl_category",
    "subcategory":    "selected_sub_name",
    "parent_cat":     "selected_parent_cat",
    "event_name":     "ctrl_event",
    "annual_value":   "ctrl_annual_value",
    "num_suppliers":  "ctrl_suppliers",
    "kraljic":        "ctrl_kraljic",
    "geography":      "ctrl_geography",
    "timeline_weeks": "ctrl_timeline_weeks",
}

# Valid values for constrained fields
VALID_KRALJIC = ["Strategic", "Leverage", "Bottleneck", "Non-Critical"]
CATEGORY_KEYWORDS = {
    "it": "Information Technology",
    "software": "Information Technology",
    "saas": "Information Technology",
    "cloud": "Information Technology",
    "tech": "Information Technology",
    "hr": "Human Resources",
    "hris": "Human Resources",
    "payroll": "Human Resources",
    "staffing": "Human Resources",
    "marketing": "Marketing & Communications",
    "advertising": "Marketing & Communications",
    "logistics": "Logistics & Transportation",
    "freight": "Logistics & Transportation",
    "shipping": "Logistics & Transportation",
    "warehouse": "Logistics & Transportation",
    "facilities": "Facilities & Real Estate",
    "janitorial": "Facilities & Real Estate",
    "maintenance": "Operations & MRO",
    "mro": "Operations & MRO",
    "manufacturing": "Operations & MRO",
    "finance": "Finance & Professional Services",
    "legal": "Finance & Professional Services",
    "consulting": "Finance & Professional Services",
    "professional services": "Finance & Professional Services",
    "marketing": "Marketing & Communications",
    "media": "Marketing & Communications",
}


_SYSTEM_PROMPT = """\
You are a world-class procurement intake specialist at ProcureIQ. Your job is to gather
the information needed to set up a sourcing event through a natural, professional conversation.

You need to collect:
1. What they are buying (category/subcategory) — REQUIRED
2. Approximate annual spend value — REQUIRED
3. How many suppliers they're evaluating — REQUIRED (default 3 if unsure)
4. Their strategic posture (Kraljic: Strategic, Leverage, Bottleneck, or Non-Critical) — REQUIRED
5. Geographic preference — optional (default: United States)
6. Target timeline in weeks — optional (default: 12)
7. Event/project name — optional (default: based on category)

Rules:
- Ask 1-2 questions at a time maximum. Never dump a long list.
- Be conversational and professional. Match the user's tone.
- Make intelligent inferences: if they say "we're sourcing MRO supplies for our Texas plant",
  infer category=Operations & MRO, geography=Texas, and ask to confirm.
- Explain Kraljic briefly if asked, but don't force the user to know the term.
  Ask instead: "Is this a critical/strategic purchase or a routine operational buy?"
- When you have enough information (at minimum: category, spend, num_suppliers, kraljic),
  set complete=true and summarize what was captured.

When you have extracted values, return them in a JSON block at the END of your reply:
<session_update>
{
  "category": "Information Technology",
  "subcategory": "IT Managed Services",
  "parent_cat": "information_technology",
  "event_name": "IT MSP Sourcing 2025",
  "annual_value": 850000,
  "num_suppliers": 4,
  "kraljic": "Strategic",
  "geography": "United States",
  "timeline_weeks": 12,
  "complete": false
}
</session_update>

Only include fields you are confident about. Use null for unknown fields.
Set "complete": true only when you have: category, annual_value, num_suppliers, and kraljic.

CATEGORY OPTIONS (use exact spelling for parent_cat key):
- information_technology → Information Technology
- human_resources → Human Resources
- logistics_transportation → Logistics & Transportation
- facilities_real_estate → Facilities & Real Estate
- operations_mro → Operations & MRO
- finance_professional_services → Finance & Professional Services
- marketing_communications → Marketing & Communications
- corporate_services → Corporate Services

KRALJIC VALUES: Strategic | Leverage | Bottleneck | Non-Critical
"""


def run_intake_agent(
    conversation: List[Dict[str, str]],
    user_message: str,
    api_key: str = "",
    existing_session: Optional[Dict] = None,
    provider: str = "claude",
) -> Dict[str, Any]:
    """
    Process one turn of conversational intake.

    Args:
        conversation: List of {"role": "user"|"assistant", "content": "..."} dicts
        user_message: The latest user message
        api_key: Anthropic API key
        existing_session: Current session state values (to avoid re-asking known fields)

    Returns:
        {
            "reply": "assistant message",
            "session_updates": {"ctrl_category": "IT", ...},
            "complete": False,
            "conversation": [updated history]
        }
    """
    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        return {
            "reply": "No API key configured. Enter your key in the sidebar to enable chat intake.",
            "session_updates": {},
            "complete": False,
            "conversation": conversation,
            "error": "no api key",
        }

    # Build context note about already-known fields
    context_note = ""
    if existing_session:
        known = {k: v for k, v in existing_session.items() if v}
        if known:
            context_note = (
                f"\n\nAlready known from prior session: {json.dumps(known)}. "
                "Do not re-ask for these fields."
            )

    system = _SYSTEM_PROMPT + context_note
    updated_conv = conversation + [{"role": "user", "content": user_message}]

    reply_text = call_llm(
        messages=updated_conv,
        provider=provider,
        api_key=key,
        system=system,
        max_tokens=1024,
    )

    # Parse session_update block
    session_updates: Dict[str, Any] = {}
    complete = False
    m = re.search(r"<session_update>(.*?)</session_update>", reply_text, re.DOTALL)
    if m:
        try:
            raw = json.loads(m.group(1).strip())
            complete = bool(raw.pop("complete", False))
            session_updates = _map_to_session_keys(raw)
        except Exception:
            pass

    # Strip the JSON block from the displayed reply
    display_reply = re.sub(r"<session_update>.*?</session_update>", "", reply_text, flags=re.DOTALL).strip()

    updated_conv.append({"role": "assistant", "content": reply_text})

    return {
        "reply": display_reply,
        "session_updates": session_updates,
        "complete": complete,
        "conversation": updated_conv,
    }


def _map_to_session_keys(raw: Dict) -> Dict[str, Any]:
    """Map agent output field names → ProcureIQ session state keys."""
    result: Dict[str, Any] = {}
    mapping = {
        "category":       "ctrl_category",
        "subcategory":    "selected_sub_name",
        "parent_cat":     "selected_parent_cat",
        "event_name":     "ctrl_event",
        "annual_value":   "ctrl_annual_value",
        "num_suppliers":  "ctrl_suppliers",
        "kraljic":        "ctrl_kraljic",
        "geography":      "ctrl_geography",
        "timeline_weeks": "ctrl_timeline_weeks",
    }
    for agent_key, session_key in mapping.items():
        val = raw.get(agent_key)
        if val is not None:
            result[session_key] = val
    return result


def get_intake_session_values(session_state: Dict) -> Dict[str, Any]:
    """Extract current intake-relevant values from session state for context injection."""
    return {
        "category":      session_state.get("ctrl_category"),
        "subcategory":   session_state.get("selected_sub_name"),
        "event_name":    session_state.get("ctrl_event"),
        "annual_value":  session_state.get("ctrl_annual_value"),
        "num_suppliers": session_state.get("ctrl_suppliers"),
        "kraljic":       session_state.get("ctrl_kraljic"),
    }
