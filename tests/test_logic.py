"""Unit tests for deterministic business logic functions.

Covers: build_cfo_challenge, build_executive_summary, generate_rfp_risk_flags
(from app.py) and compute_financial_health / financial_risk_label (from evaluation.py).
All tests are purely deterministic — no LLM calls, no streamlit state.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DIMENSIONS
from evaluation import compute_financial_health, financial_risk_label

# ── Shared fixtures ────────────────────────────────────────────────────────────

def _make_leader(scores_override=None, fin_risk="LOW", fin_health=80, ws=85, price=100_000):
    scores = {d: 75 for d in DIMENSIONS}
    if scores_override:
        scores.update(scores_override)
    return {
        "Supplier": "AlphaSupply",
        "Weighted Score": ws,
        "Current Fit": 78,
        "Future Fit": 82,
        "Raw Price": price,
        "Financial Health": fin_health,
        "Financial Risk Label": fin_risk,
        "Scores": scores,
    }


def _make_runner_up(ws=80, price=95_000):
    return {
        "Supplier": "BetaCorp",
        "Weighted Score": ws,
        "Raw Price": price,
        "Current Fit": 72,
        "Future Fit": 74,
        "Scores": {d: 70 for d in DIMENSIONS},
    }


_CATEGORY_RULE = {"weight_focus": "balanced"}


# ── compute_financial_health ───────────────────────────────────────────────────

class TestComputeFinancialHealth:
    def test_strong_answers_yield_high_score(self):
        fin_dict = {
            "Years in Business": "25+ years",
            "Ownership Structure": "Publicly traded",
            "Revenue Trajectory": "Growing 15%+",
            "Recent M&A Activity": "None in 2 years",
            "Payment Terms Offered": "Net 90+",
            "Workforce Changes (12mo)": "Significant hiring",
        }
        score = compute_financial_health(fin_dict)
        assert score >= 80, f"Expected strong answers → score ≥ 80, got {score}"

    def test_weak_answers_yield_low_score(self):
        fin_dict = {
            "Years in Business": "<3 years",
            "Revenue Trajectory": "Declining",
            "Recent M&A Activity": "Being acquired",
            "Workforce Changes (12mo)": "Major layoffs >10%",
            "Payment Terms Offered": "Net 15 or less",
        }
        score = compute_financial_health(fin_dict)
        assert score <= 40, f"Expected weak answers → score ≤ 40, got {score}"

    def test_empty_dict_returns_midpoint(self):
        assert compute_financial_health({}) == 50

    def test_unknown_answers_default_to_midpoint(self):
        score = compute_financial_health({"Years in Business": "unknown_value_xyz"})
        assert score == 50

    def test_returns_integer(self):
        result = compute_financial_health({"Years in Business": "25+ years"})
        assert isinstance(result, int)

    def test_score_bounded_0_to_100(self):
        score = compute_financial_health({"Years in Business": "25+ years"})
        assert 0 <= score <= 100


# ── financial_risk_label ───────────────────────────────────────────────────────

class TestFinancialRiskLabel:
    def test_high_score_is_low_risk(self):
        label, color, bg = financial_risk_label(80)
        assert label == "LOW"
        assert "#" in color

    def test_medium_score_is_medium_risk(self):
        label, _, _ = financial_risk_label(60)
        assert label == "MEDIUM"

    def test_low_score_is_high_risk(self):
        label, _, _ = financial_risk_label(30)
        assert label == "HIGH"

    def test_boundary_75_is_low(self):
        label, _, _ = financial_risk_label(75)
        assert label == "LOW"

    def test_boundary_50_is_medium(self):
        label, _, _ = financial_risk_label(50)
        assert label == "MEDIUM"

    def test_returns_three_tuple(self):
        result = financial_risk_label(60)
        assert len(result) == 3


# ── generate_rfp_risk_flags ────────────────────────────────────────────────────

class TestGenerateRfpRiskFlags:
    def setup_method(self):
        from app import generate_rfp_risk_flags
        self.fn = generate_rfp_risk_flags

    def test_always_returns_at_least_one_flag(self):
        flags = self.fn(_make_leader(), None, None, "Leverage", _CATEGORY_RULE)
        assert len(flags) >= 1

    def test_critical_dim_score_triggers_high_flag(self):
        leader = _make_leader({"Price / TCO": 25})
        flags = self.fn(leader, None, None, "Leverage", _CATEGORY_RULE)
        high_flags = [f for f in flags if f["tier"] == "HIGH"]
        assert any("Critical gap" in f["title"] for f in high_flags)

    def test_high_financial_risk_triggers_high_flag(self):
        leader = _make_leader(fin_risk="HIGH", fin_health=20)
        flags = self.fn(leader, None, None, "Leverage", _CATEGORY_RULE)
        high_flags = [f for f in flags if f["tier"] == "HIGH"]
        assert any("financial" in f["title"].lower() for f in high_flags)

    def test_blocker_row_triggers_high_flag(self):
        blocker = {"Name": "Jane CFO", "Role": "CFO", "Position": "Blocker", "Priority": "Cost"}
        flags = self.fn(_make_leader(), None, blocker, "Leverage", _CATEGORY_RULE)
        high_flags = [f for f in flags if f["tier"] == "HIGH"]
        assert any("blocker" in f["title"].lower() for f in high_flags)

    def test_thin_lead_triggers_medium_flag(self):
        leader = _make_leader(ws=83)
        runner_up = _make_runner_up(ws=80)
        flags = self.fn(leader, runner_up, None, "Leverage", _CATEGORY_RULE)
        medium_flags = [f for f in flags if f["tier"] == "MEDIUM"]
        assert any("thin lead" in f["title"].lower() for f in medium_flags)

    def test_no_risks_produces_no_critical_flags_placeholder(self):
        # All scores healthy, no financial risk, no blocker, comfortable lead
        leader = _make_leader(ws=90, fin_risk="LOW", fin_health=85)
        runner_up = _make_runner_up(ws=75)
        flags = self.fn(leader, runner_up, None, "Leverage", _CATEGORY_RULE)
        titles = [f["title"] for f in flags]
        assert any("No critical flags" in t for t in titles)

    def test_each_flag_has_required_keys(self):
        flags = self.fn(_make_leader(), None, None, "Strategic", _CATEGORY_RULE)
        for flag in flags:
            assert "tier" in flag
            assert "title" in flag
            assert "body" in flag


# ── build_executive_summary ────────────────────────────────────────────────────

class TestBuildExecutiveSummary:
    def setup_method(self):
        from app import build_executive_summary
        self.fn = build_executive_summary

    def test_returns_string(self):
        result = self.fn(_make_leader(), _make_runner_up(), None, "Q3 Cloud RFP", "Strategic", _CATEGORY_RULE, "SLA Strength")
        assert isinstance(result, str)

    def test_contains_leader_name(self):
        result = self.fn(_make_leader(), _make_runner_up(), None, "Q3 Cloud RFP", "Strategic", _CATEGORY_RULE, "SLA Strength")
        assert "AlphaSupply" in result

    def test_contains_event_name(self):
        result = self.fn(_make_leader(), None, None, "MyEvent2025", "Leverage", _CATEGORY_RULE, "Price / TCO")
        assert "MyEvent2025" in result

    def test_contains_weakest_dim(self):
        result = self.fn(_make_leader(), None, None, "Cloud RFP", "Leverage", _CATEGORY_RULE, "Innovation Capacity")
        assert "Innovation Capacity" in result

    def test_contains_kraljic_type(self):
        result = self.fn(_make_leader(), None, None, "Cloud RFP", "Bottleneck", _CATEGORY_RULE, "SLA Strength")
        assert "Bottleneck" in result

    def test_no_runner_up_still_works(self):
        result = self.fn(_make_leader(), None, None, "Cloud RFP", "Leverage", _CATEGORY_RULE, "SLA Strength")
        assert "AlphaSupply" in result


# ── build_cfo_challenge ────────────────────────────────────────────────────────

class TestBuildCfoChallenge:
    def setup_method(self):
        from app import build_cfo_challenge
        self.fn = build_cfo_challenge

    def test_returns_list_of_dicts(self):
        result = self.fn(_make_leader(), _make_runner_up(), "Q3 Cloud RFP", "Leverage", _CATEGORY_RULE, "SLA Strength", {})
        assert isinstance(result, list)
        assert len(result) >= 1
        for item in result:
            assert "question" in item
            assert "answer" in item
            assert "severity" in item

    def test_premium_leader_triggers_price_justification(self):
        leader = _make_leader(ws=88, price=120_000)
        runner_up = _make_runner_up(ws=80, price=100_000)
        challenges = self.fn(leader, runner_up, "Cloud RFP", "Leverage", _CATEGORY_RULE, "Price / TCO", {})
        questions = [c["question"] for c in challenges]
        assert any("cheaper" in q.lower() or "pay more" in q.lower() for q in questions)

    def test_cheaper_leader_triggers_dominance_message(self):
        leader = _make_leader(ws=88, price=80_000)
        runner_up = _make_runner_up(ws=80, price=100_000)
        challenges = self.fn(leader, runner_up, "Cloud RFP", "Leverage", _CATEGORY_RULE, "SLA Strength", {})
        answers = [c["answer"] for c in challenges]
        assert any("dominant" in a.lower() or "cheaper" in a.lower() for a in answers)

    def test_high_fin_risk_produces_high_severity_challenge(self):
        leader = _make_leader(fin_risk="HIGH", fin_health=25)
        challenges = self.fn(leader, _make_runner_up(), "Cloud RFP", "Leverage", _CATEGORY_RULE, "SLA Strength", {})
        severities = [c["severity"] for c in challenges]
        assert "HIGH" in severities

    def test_always_includes_evaluation_rigor_question(self):
        challenges = self.fn(_make_leader(), _make_runner_up(), "Cloud RFP", "Strategic", _CATEGORY_RULE, "SLA Strength", {})
        questions = " ".join(c["question"] for c in challenges).lower()
        assert "rigorous" in questions or "gut" in questions or "rigour" in questions

    def test_no_runner_up_skips_price_comparison(self):
        challenges = self.fn(_make_leader(), None, "Cloud RFP", "Leverage", _CATEGORY_RULE, "SLA Strength", {})
        assert isinstance(challenges, list)
