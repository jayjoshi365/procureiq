"""Tests for evaluation.py"""
import pytest
from evaluation import get_subcategory_weights, recommend_auction_type, compute_edgar_financial_health


class TestEvaluation:
    """Test supplier evaluation and auction recommendation logic."""

    def test_get_subcategory_weights_basic(self):
        """Test get_subcategory_weights returns valid weights."""
        weights = get_subcategory_weights("ERP System (SAP / Oracle / etc.)", "Strategic")

        assert isinstance(weights, dict)
        assert len(weights) == 10  # Should have all dimensions

        # Check all dimensions are present
        from config import DIMENSIONS
        for dim in DIMENSIONS:
            assert dim in weights
            assert isinstance(weights[dim], int)
            assert 1 <= weights[dim] <= 10

    def test_get_subcategory_weights_kraljic_variations(self):
        """Test weights vary by Kraljic posture."""
        strategic_weights = get_subcategory_weights("ERP System (SAP / Oracle / etc.)", "Strategic")
        leverage_weights = get_subcategory_weights("ERP System (SAP / Oracle / etc.)", "Leverage")

        # Strategic should weight execution risk and stakeholder confidence higher
        assert strategic_weights["Execution Risk"] > leverage_weights["Execution Risk"]
        assert strategic_weights["Stakeholder Confidence"] > leverage_weights["Stakeholder Confidence"]

        # Leverage should weight price higher
        assert leverage_weights["Price / TCO"] > strategic_weights["Price / TCO"]

    def test_get_subcategory_weights_overrides(self):
        """Test subcategory-specific overrides work."""
        # HRIS has specific overrides
        hris_weights = get_subcategory_weights("HRIS / HCM Platform", "Strategic")

        # Should have high execution risk weight due to override
        assert hris_weights["Execution Risk"] == 10
        assert hris_weights["SLA Strength"] == 9
        assert hris_weights["Price / TCO"] == 5

    def test_get_subcategory_weights_unknown_subcategory(self):
        """Test unknown subcategory falls back to base Kraljic weights."""
        weights = get_subcategory_weights("Unknown Category", "Strategic")

        assert isinstance(weights, dict)
        assert len(weights) == 10  # 8 original + ESG / Sustainability + Supplier Diversity

        # Should match base Strategic weights (including the two newer dimensions)
        expected_strategic = {
            "Price / TCO": 6, "SLA Strength": 9, "Execution Risk": 9,
            "Stakeholder Confidence": 8, "Strategic Alignment": 8,
            "Innovation Capacity": 7, "Relationship Depth": 6,
            "Commercial Flexibility": 6, "ESG / Sustainability": 7,
            "Supplier Diversity": 5,
        }
        assert weights == expected_strategic

    def test_recommend_auction_type_bottleneck(self):
        """Test auction recommendation for Bottleneck category."""
        auction_type, rationale = recommend_auction_type(
            kraljic="Bottleneck",
            num_suppliers=2,
            price_weight=0.2,
            switching_cost_answer="High — significant transition risk",
            subcategory_auction="Negotiated"
        )

        assert "Negotiated Award" in auction_type
        assert isinstance(rationale, str)
        assert len(rationale) > 50

    def test_recommend_auction_type_reverse_auction(self):
        """Test reverse auction recommendation for leverage with conditions."""
        auction_type, rationale = recommend_auction_type(
            kraljic="Leverage",
            num_suppliers=5,
            price_weight=0.4,
            switching_cost_answer="Low — easy to switch",
            subcategory_auction=""
        )

        assert "Reverse Auction" in auction_type
        assert isinstance(rationale, str)

    def test_recommend_auction_type_strategic(self):
        """Test multi-round recommendation for strategic category."""
        auction_type, rationale = recommend_auction_type(
            kraljic="Strategic",
            num_suppliers=3,
            price_weight=0.3,
            switching_cost_answer="Medium — some disruption expected",
            subcategory_auction=""
        )

        assert "Multi-Round Negotiation" in auction_type
        assert isinstance(rationale, str)

    def test_recommend_auction_type_single_supplier(self):
        """Test negotiated award for single supplier."""
        auction_type, rationale = recommend_auction_type(
            kraljic="Leverage",
            num_suppliers=1,
            price_weight=0.3,
            switching_cost_answer="Low — easy to switch",
            subcategory_auction=""
        )

        assert "Negotiated Award" in auction_type
        assert "single-source" in rationale.lower() or "supply concentration" in rationale.lower()

    def test_recommend_auction_type_default(self):
        """Test default rank auction for most cases."""
        auction_type, rationale = recommend_auction_type(
            kraljic="Leverage",
            num_suppliers=4,
            price_weight=0.25,
            switching_cost_answer="Medium — some disruption expected",
            subcategory_auction=""
        )

        assert "Rank Auction" in auction_type
        assert "Coupa / Ariba Standard" in auction_type

class TestComputeEdgarFinancialHealth:
    """Tests for compute_edgar_financial_health() — EDGAR/XBRL scoring path."""

    def test_none_on_empty_dict(self):
        assert compute_edgar_financial_health({}) is None

    def test_none_on_missing_all_three_metrics(self):
        # Only cash present — not enough to score
        assert compute_edgar_financial_health({"cash": 1_000_000}) is None

    def test_high_confidence_all_three_metrics(self):
        result = compute_edgar_financial_health({
            "revenue_growth_pct": 18.0,
            "profit_margin_current": 0.12,
            "debt_to_assets_current": 0.40,
        })
        assert result is not None
        assert result["confidence"] == "high"
        assert result["n_metrics"] == 3
        assert result["source"] == "SEC EDGAR/XBRL"
        assert 60 <= result["score"] <= 100

    def test_partial_confidence_two_metrics(self):
        result = compute_edgar_financial_health({
            "revenue_growth_pct": 8.0,
            "profit_margin_current": 0.06,
        })
        assert result is not None
        assert result["confidence"] == "partial"
        assert result["n_metrics"] == 2

    def test_partial_confidence_one_metric(self):
        result = compute_edgar_financial_health({
            "debt_to_assets_current": 0.55,
        })
        assert result is not None
        assert result["confidence"] == "partial"
        assert result["n_metrics"] == 1

    def test_strong_company_scores_high(self):
        result = compute_edgar_financial_health({
            "revenue_growth_pct": 25.0,
            "profit_margin_current": 0.20,
            "debt_to_assets_current": 0.25,
        })
        assert result is not None
        assert result["score"] >= 88

    def test_distressed_company_scores_low(self):
        result = compute_edgar_financial_health({
            "revenue_growth_pct": -18.0,
            "profit_margin_current": -0.08,
            "debt_to_assets_current": 0.92,
        })
        assert result is not None
        assert result["score"] <= 20

    def test_net_loss_flag_raised(self):
        result = compute_edgar_financial_health({
            "revenue_growth_pct": 5.0,
            "profit_margin_current": -0.03,
            "debt_to_assets_current": 0.45,
            "net_income_current": -50_000_000,
        })
        assert result is not None
        assert any("net loss" in f.lower() for f in result["flags"])

    def test_liabilities_exceed_assets_flag(self):
        result = compute_edgar_financial_health({
            "revenue_growth_pct": 2.0,
            "debt_to_assets_current": 1.10,
        })
        assert result is not None
        assert any("liabilities exceed" in f.lower() for f in result["flags"])

    def test_revenue_decline_flag_raised(self):
        result = compute_edgar_financial_health({
            "revenue_growth_pct": -20.0,
            "profit_margin_current": 0.05,
        })
        assert result is not None
        assert any("decline" in f.lower() or "continuity" in f.lower() for f in result["flags"])

    def test_inputs_dict_has_human_readable_labels(self):
        result = compute_edgar_financial_health({
            "revenue_growth_pct": 12.0,
            "profit_margin_current": 0.08,
            "debt_to_assets_current": 0.35,
        })
        assert result is not None
        assert "Revenue Growth" in result["inputs"]
        assert "Profit Margin" in result["inputs"]
        assert "Debt-to-Assets" in result["inputs"]
        # Labels should be strings, not raw numbers
        for v in result["inputs"].values():
            assert isinstance(v, str)

    def test_score_in_valid_range(self):
        for revenue_growth in [-25, -5, 0, 8, 15, 30]:
            for margin in [-0.10, 0, 0.05, 0.15]:
                for d2a in [0.20, 0.50, 0.75, 0.95]:
                    result = compute_edgar_financial_health({
                        "revenue_growth_pct": revenue_growth,
                        "profit_margin_current": margin,
                        "debt_to_assets_current": d2a,
                    })
                    assert result is not None
                    assert 0 <= result["score"] <= 100, (
                        f"Score {result['score']} out of range for inputs "
                        f"rev={revenue_growth} margin={margin} d2a={d2a}"
                    )
