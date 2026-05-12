"""Tests for Phase 3/4B Decision Brief additions.

Covers: Executive Defensibility Score (EDS), Why Not Selected section,
Conditions of Award section, and HTML export output.
All functions under test are deterministic — no LLM calls, no I/O.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock


# ── Shared fixtures ───────────────────────────────────────────────────

def _make_leader(score=78, price=480000, fin=75, fin_source="SEC EDGAR/XBRL",
                 edgar_period="2025-01-31", dims=None):
    base_dims = {
        "Price / TCO": 72, "SLA Strength": 80, "Execution Risk": 75,
        "Stakeholder Confidence": 70, "Strategic Alignment": 82,
        "Innovation Capacity": 65, "Relationship Depth": 60,
        "Commercial Flexibility": 68, "ESG / Sustainability": 55,
        "Supplier Diversity": 50,
    }
    if dims:
        base_dims.update(dims)
    return {
        "Supplier": "Workday", "Weighted Score": score, "Raw Price": price,
        "Financial Health": fin, "Financial Risk Label": "LOW",
        "Financial Risk Color": "#4ADE80", "Financial Health Source": fin_source,
        "EDGAR Period End": edgar_period, "Scores": base_dims,
        "Future Fit": 72,
    }


def _make_runner_up(score=65, price=390000, dims=None):
    base_dims = {
        "Price / TCO": 85, "SLA Strength": 60, "Execution Risk": 58,
        "Stakeholder Confidence": 55, "Strategic Alignment": 65,
        "Innovation Capacity": 50, "Relationship Depth": 45,
        "Commercial Flexibility": 60, "ESG / Sustainability": 48,
        "Supplier Diversity": 52,
    }
    if dims:
        base_dims.update(dims)
    return {
        "Supplier": "Rippling", "Weighted Score": score, "Raw Price": price,
        "Financial Health": 60, "Financial Risk Label": "MEDIUM",
        "Financial Risk Color": "#FCD34D", "Financial Health Source": "User Assessment",
        "EDGAR Period End": "", "Scores": base_dims, "Future Fit": 60,
    }


def _make_risk_flags(tiers=("HIGH",)):
    flags = []
    for t in tiers:
        flags.append({"tier": t, "title": f"{t} risk title", "body": f"{t} risk body."})
    return flags


def _make_stake_df(positions=("Champion",)):
    rows = [{"Name": f"Person {i}", "Role": "VP", "Position": p,
             "Power": 4, "Interest": 4, "Priority": "Cost",
             "Action": "", "Talk Track": "", "Last Contact": "",
             "Relationship Health": "", "Next Action": ""}
            for i, p in enumerate(positions)]
    return pd.DataFrame(rows)


def _make_category_rule():
    return {"requirements": "Must support 5000+ employees.",
            "quality": "ISO 27001 required.", "service": "24/7 support.",
            "cost": "Net 60 payment terms."}


def _make_action_plan():
    return [{"phase": "Phase 1", "label": "Foundation",
             "actions": ["Negotiate SLA", "Confirm legal review"]}]


def _call_html(**kwargs):
    from app import build_executive_onepager_html, DIMENSIONS
    leader  = kwargs.pop("leader",  _make_leader())
    runner_up = kwargs.pop("runner_up", _make_runner_up())
    ranked  = kwargs.pop("ranked",  [leader, runner_up])
    rf      = kwargs.pop("risk_flags", _make_risk_flags())
    ap      = kwargs.pop("action_plan", _make_action_plan())
    cr      = kwargs.pop("category_rule", _make_category_rule())
    wd      = kwargs.pop("leader_weakest_dim", "Supplier Diversity")
    blocker = kwargs.pop("blocker", None)
    sdf     = kwargs.pop("stake_df", _make_stake_df())
    return build_executive_onepager_html(
        "HR Tech RFP 2025", "Human Resources", "HRIS / HCM Platform",
        "Strategic", leader, runner_up, ranked, rf, ap, cr, wd,
        blocker=blocker, stake_df=sdf, **kwargs
    )


# ── EDS — component scoring ───────────────────────────────────────────

class TestEDSCompleteness:
    def test_all_dims_scored_gives_20(self):
        html = _call_html()
        # Completeness: all 10 dims ≠ 50 → 20 pts
        assert "20/20" in html

    def test_few_dims_scored_gives_lower_completeness(self):
        leader = _make_leader(dims={d: 50 for d in [
            "Innovation Capacity", "Relationship Depth", "Commercial Flexibility",
            "ESG / Sustainability", "Supplier Diversity", "Strategic Alignment",
            "Stakeholder Confidence",
        ]})
        html = _call_html(leader=leader)
        # Only 3 dims ≠ 50 → 30% completeness → 5 pts
        assert "5/20" in html


class TestEDSGap:
    def test_gap_ge_10_gives_20(self):
        leader = _make_leader(score=85)
        runner = _make_runner_up(score=74)
        html = _call_html(leader=leader, runner_up=runner,
                          ranked=[leader, runner])
        assert "20/20" in html

    def test_gap_ge_5_gives_15(self):
        leader = _make_leader(score=78)
        runner = _make_runner_up(score=71)
        html = _call_html(leader=leader, runner_up=runner,
                          ranked=[leader, runner])
        assert "15/20" in html

    def test_gap_lt_2_gives_5(self):
        leader = _make_leader(score=78)
        runner = _make_runner_up(score=77)
        html = _call_html(leader=leader, runner_up=runner,
                          ranked=[leader, runner])
        assert "5/20" in html

    def test_no_runner_up_gives_12(self):
        leader = _make_leader(score=78)
        html = _call_html(leader=leader, runner_up=None,
                          ranked=[leader])
        assert "12/20" in html


class TestEDSRiskProfile:
    def test_no_high_flags_gives_20(self):
        html = _call_html(risk_flags=_make_risk_flags(("MEDIUM",)))
        assert "20/20" in html

    def test_one_high_flag_gives_12(self):
        html = _call_html(risk_flags=_make_risk_flags(("HIGH",)))
        assert "12/20" in html

    def test_two_high_flags_gives_5(self):
        html = _call_html(risk_flags=_make_risk_flags(("HIGH", "HIGH")))
        assert "5/20" in html


class TestEDSFinancialQuality:
    def test_edgar_fresh_gives_15(self):
        leader = _make_leader(fin_source="SEC EDGAR/XBRL",
                              edgar_period="2025-01-31")
        html = _call_html(leader=leader)
        assert "15/15" in html

    def test_qualitative_gives_8(self):
        leader = _make_leader(fin_source="User Assessment", edgar_period="")
        html = _call_html(leader=leader)
        assert "8/15" in html


class TestEDSStakeholderAlignment:
    def test_champion_no_blocker_gives_15(self):
        sdf = _make_stake_df(("Champion",))
        html = _call_html(stake_df=sdf, blocker=None)
        assert "15/15" in html

    def test_blocker_present_gives_5(self):
        sdf = _make_stake_df(("Champion",))
        blocker = {"Name": "CFO", "Role": "CFO", "Position": "Skeptic",
                   "Priority": "Cost", "Power": 5, "Interest": 4}
        html = _call_html(stake_df=sdf, blocker=blocker)
        assert "5/15" in html

    def test_no_champion_no_blocker_gives_10(self):
        sdf = _make_stake_df(("Neutral",))
        html = _call_html(stake_df=sdf, blocker=None)
        assert "10/15" in html


class TestEDSWeakestDim:
    def test_weakest_ge_70_gives_10(self):
        leader = _make_leader(dims={"Supplier Diversity": 72})
        html = _call_html(leader=leader, leader_weakest_dim="Supplier Diversity")
        assert "10/10" in html

    def test_weakest_lt_40_gives_1(self):
        leader = _make_leader(dims={"Supplier Diversity": 35})
        html = _call_html(leader=leader, leader_weakest_dim="Supplier Diversity")
        assert "1/10" in html


class TestEDSLabel:
    def _eds_from_html(self, html):
        import re
        m = re.search(r'Exec\. Defensibility.*?(\d+)/100', html, re.DOTALL)
        return int(m.group(1)) if m else None

    def test_defensible_label_when_ge_85(self):
        # Maximise all components
        leader = _make_leader(score=90, fin_source="SEC EDGAR/XBRL",
                              edgar_period="2025-01-31")
        runner = _make_runner_up(score=78)
        sdf = _make_stake_df(("Champion",))
        html = _call_html(leader=leader, runner_up=runner,
                          ranked=[leader, runner],
                          risk_flags=_make_risk_flags(("MEDIUM",)),
                          stake_df=sdf, blocker=None,
                          leader_weakest_dim="Supplier Diversity")
        assert "DEFENSIBLE" in html.upper()

    def test_vulnerable_label_when_lt_55(self):
        leader = _make_leader(
            score=51, fin_source="User Assessment", edgar_period="",
            dims={d: 50 for d in [
                "Price / TCO", "SLA Strength", "Execution Risk",
                "Stakeholder Confidence", "Strategic Alignment",
                "Innovation Capacity", "Relationship Depth",
                "Commercial Flexibility", "ESG / Sustainability",
                "Supplier Diversity",
            ]}
        )
        runner = _make_runner_up(score=50)
        blocker = {"Name": "CFO", "Role": "CFO", "Position": "Blocker",
                   "Priority": "Cost", "Power": 5, "Interest": 4}
        html = _call_html(
            leader=leader, runner_up=runner, ranked=[leader, runner],
            risk_flags=_make_risk_flags(("HIGH", "HIGH", "HIGH")),
            stake_df=_make_stake_df(("Neutral",)),
            blocker=blocker,
            leader_weakest_dim="Supplier Diversity",
        )
        assert "VULNERABLE" in html.upper()


# ── Why Not Selected ──────────────────────────────────────────────────

class TestWhyNotSelected:
    def test_section_absent_when_single_supplier(self):
        leader = _make_leader()
        html = _call_html(leader=leader, runner_up=None, ranked=[leader])
        assert "NOT SELECTED" not in html

    def test_section_present_for_runner_up(self):
        html = _call_html()
        assert "NOT SELECTED" in html
        assert "Rippling" in html

    def test_cheaper_runner_up_story(self):
        leader = _make_leader(price=480000)
        runner = _make_runner_up(price=390000)
        html = _call_html(leader=leader, runner_up=runner,
                          ranked=[leader, runner])
        assert "cheaper" in html.lower()

    def test_pricier_runner_up_story(self):
        leader = _make_leader(price=390000)
        runner = _make_runner_up(price=480000)
        html = _call_html(leader=leader, runner_up=runner,
                          ranked=[leader, runner])
        assert "expensive" in html.lower()

    def test_score_deficit_shown(self):
        leader = _make_leader(score=78)
        runner = _make_runner_up(score=65)
        html = _call_html(leader=leader, runner_up=runner,
                          ranked=[leader, runner])
        assert "13" in html  # gap = 78 - 65


# ── Conditions of Award ───────────────────────────────────────────────

class TestConditionsOfAward:
    def test_legal_review_always_required(self):
        html = _call_html(risk_flags=[])
        assert "legal review" in html.lower()

    def test_high_flag_becomes_required_condition(self):
        rf = [{"tier": "HIGH", "title": "Key Person Risk",
               "body": "Single point of failure."}]
        html = _call_html(risk_flags=rf)
        assert "Key Person Risk" in html

    def test_blocker_generates_endorsement_requirement(self):
        blocker = {"Name": "Marcus Webb", "Role": "CFO",
                   "Position": "Skeptic", "Priority": "Cost",
                   "Power": 5, "Interest": 4}
        html = _call_html(blocker=blocker)
        assert "Marcus Webb" in html

    def test_narrow_gap_generates_rationale_requirement(self):
        leader = _make_leader(score=72)
        runner = _make_runner_up(score=70)
        html = _call_html(leader=leader, runner_up=runner,
                          ranked=[leader, runner])
        assert "narrow" in html.lower()

    def test_reference_check_always_standard(self):
        html = _call_html()
        assert "reference check" in html.lower()

    def test_security_assessment_always_standard(self):
        html = _call_html()
        assert "security assessment" in html.lower()

    def test_medium_flag_does_not_become_required(self):
        rf = [{"tier": "MEDIUM", "title": "Medium Risk", "body": "Body."}]
        html = _call_html(risk_flags=rf)
        # MEDIUM flags appear in the Risk Flags section but must NOT appear
        # in the Conditions of Award section as a REQUIRED item
        coa_idx = html.find("Conditions of Award")
        assert coa_idx != -1, "Conditions of Award section not found"
        assert "Medium Risk" not in html[coa_idx:]


# ── HTML export structure ─────────────────────────────────────────────

class TestHTMLExportStructure:
    def test_eds_kpi_card_present(self):
        html = _call_html()
        assert "Exec. Defensibility" in html

    def test_eds_score_in_footer(self):
        html = _call_html()
        assert "Exec. Defensibility Score" in html
        assert "/100" in html

    def test_why_not_selected_heading_present(self):
        html = _call_html()
        assert "Why Not Selected" in html

    def test_conditions_of_award_heading_present(self):
        html = _call_html()
        assert "Conditions of Award" in html

    def test_risk_flags_render_title_not_dict_repr(self):
        rf = [{"tier": "HIGH", "title": "Single Vendor Risk",
               "body": "No fallback supplier identified."}]
        html = _call_html(risk_flags=rf)
        assert "Single Vendor Risk" in html
        assert "{'tier'" not in html

    def test_valid_html_structure(self):
        html = _call_html()
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html
        assert "<body>" in html
