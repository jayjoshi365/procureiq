"""Agent orchestrator — thin wrapper around the agents package.

All agent calls that used to be scattered through app.py should route through
here so that the _AGENTS_AVAILABLE guard is enforced in one place and callers
never have to import from agents directly.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# ── Availability check ────────────────────────────────────────────────────────
try:
    from agents.supplier_discovery import run_supplier_discovery_agent
    from agents.sanctions_check import run_sanctions_check
    from agents.contract_generation import run_contract_generation_agent
    from agents.spend_analysis import run_spend_anomaly_agent
    from agents.intake import run_intake_agent, get_intake_session_values
    from agents.erp_connector import run_erp_connector
    from agents.llm_router import call_llm as _router_call_llm, stream_llm as _router_stream_llm
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False


class AgentUnavailableError(RuntimeError):
    """Raised when an agent call is attempted without the agents package installed."""


def _require_agents() -> None:
    if not AGENTS_AVAILABLE:
        raise AgentUnavailableError(
            "Agent services unavailable — install the agents package and restart."
        )


# ── Public API ────────────────────────────────────────────────────────────────

def discover_suppliers(
    subcategory: str,
    category: str,
    requirements: Optional[str] = None,
    count: int = 5,
) -> Dict[str, Any]:
    """Run the supplier discovery agent for a given subcategory."""
    _require_agents()
    return run_supplier_discovery_agent(
        subcategory=subcategory,
        category=category,
        requirements=requirements,
        count=count,
    )


def screen_sanctions(supplier_name: str, country: str = "") -> Dict[str, Any]:
    """Run an OFAC / SAM.gov name screen for a supplier."""
    _require_agents()
    return run_sanctions_check(supplier_name=supplier_name, country=country)


def generate_contract(
    supplier_name: str,
    event_id: str,
    category: str,
    subcategory: str,
    award_value: float,
    terms: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate a contract draft for an awarded supplier."""
    _require_agents()
    return run_contract_generation_agent(
        supplier_name=supplier_name,
        event_id=event_id,
        category=category,
        subcategory=subcategory,
        award_value=award_value,
        terms=terms or {},
    )


def analyze_spend(spend_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run the spend anomaly detection agent."""
    _require_agents()
    return run_spend_anomaly_agent(spend_data=spend_data)


def run_intake(
    user_message: str,
    session_id: str,
    conversation: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Send a user message to the intake agent and return the updated state."""
    _require_agents()
    return run_intake_agent(
        user_message=user_message,
        session_id=session_id,
        conversation=conversation or [],
    )


def call_llm(
    messages: List[Dict[str, str]],
    provider: str,
    api_key: str,
    model: str,
    **kwargs: Any,
) -> str:
    """Call the LLM router and return the full response string."""
    _require_agents()
    return _router_call_llm(
        messages=messages, provider=provider, api_key=api_key, model=model, **kwargs
    )


def stream_llm(
    messages: List[Dict[str, str]],
    provider: str,
    api_key: str,
    model: str,
    **kwargs: Any,
):
    """Stream tokens from the LLM router."""
    _require_agents()
    yield from _router_stream_llm(
        messages=messages, provider=provider, api_key=api_key, model=model, **kwargs
    )
