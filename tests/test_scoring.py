"""
Unit tests for ProcureIQ scoring engine.

Tests cover:
- Deterministic scoring (same inputs produce same outputs)
- Kraljic weight adjustments (weights change appropriately by posture)
- Edge cases (all zeros, all maxes, single supplier)
- Financial health calculation
- Weighted composite score calculation
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation import (
    calculate_weighted_score,
    calculate_financial_health,
    get_subcategory_weights,
    get_financial_risk_label,
)
from config import DIMENSIONS, CURRENT_DIMS, FINANCIAL_FIELDS


class TestDeterministicScoring:
    """Test that scoring is deterministic - same inputs always produce same outputs."""

    def test_same_scores_produce_same_weighted_result(self):
        """Verify that identical score and weight inputs produce identical results."""
        scores = {
            "Price / TCO": 75,
            "SLA Strength": 82,
            "Execution Risk": 88,
            "Stakeholder Confidence": 79,
            "Strategic Alignment": 85,
            "Innovation Capacity": 70,
            "Relationship Depth": 80,
            "Commercial Flexibility": 76,
            "ESG / Sustainability": 72,
            "Supplier Diversity": 68,
        }
        weights = {dim: 5 for dim in DIMENSIONS}

        result1 = calculate_weighted_score(scores, weights)
        result2 = calculate_weighted_score(scores, weights)
        result3 = calculate_weighted_score(scores, weights)

        assert result1 == result2 == result3, "Scoring should be deterministic"
        assert 0 <= result1 <= 100, "Score should be within valid range"

    def test_scoring_consistent_across_multiple_calls(self):
        """Verify scoring consistency across 10 sequential calls."""
        scores = {"Price / TCO": 65, "SLA Strength": 88, "Execution Risk": 92}
        # Pad with neutral scores
        for dim in DIMENSIONS:
            if dim not in scores:
                scores[dim] = 50
        weights = {"Price / TCO": 3, "SLA Strength": 2, "Execution Risk": 1}
        # Pad weights
        for dim in DIMENSIONS:
            if dim not in weights:
                weights[dim] = 1

        results = [calculate_weighted_score(scores, weights) for _ in range(10)]
        assert len(set(results)) == 1, "All 10 scoring runs should produce identical results"


class TestKraljicWeightAdjustment:
    """Test that Kraljic posture correctly adjusts dimension weights."""

    def test_strategic_prioritizes_execution_and_sla(self):
        """Strategic posture should weight SLA and Execution Risk heavily."""
        strategic_weights = get_subcategory_weights("HRIS / HCM Platform", "Strategic")
        
        sla_weight = strategic_weights.get("SLA Strength", 0)
        execution_weight = strategic_weights.get("Execution Risk", 0)
        price_weight = strategic_weights.get("Price / TCO", 0)
        
        assert sla_weight >= 8, "SLA should be weighted 8+ in Strategic posture"
        assert execution_weight >= 9, "Execution Risk should be weighted 9+ in Strategic"
        assert price_weight < sla_weight, "Price should not be weighted higher than SLA in Strategic"

    def test_leverage_prioritizes_price(self):
        """Leverage posture should weight Price / TCO heavily."""
        leverage_weights = get_subcategory_weights("HRIS / HCM Platform", "Leverage")
        
        price_weight = leverage_weights.get("Price / TCO", 0)
        execution_weight = leverage_weights.get("Execution Risk", 0)
        
        assert price_weight >= 8, "Price should be weighted 8+ in Leverage posture"
        assert price_weight > execution_weight, "Price should be weighted higher than Execution in Leverage"

    def test_bottleneck_prioritizes_execution_risk(self):
        """Bottleneck posture should heavily weight Execution Risk."""
        bottleneck_weights = get_subcategory_weights("Cloud Infrastructure (AWS / Azure / GCP)", "Bottleneck")
        
        execution_weight = bottleneck_weights.get("Execution Risk", 0)
        price_weight = bottleneck_weights.get("Price / TCO", 0)
        
        assert execution_weight >= 9, "Execution Risk should be weighted 9+ in Bottleneck"
        assert execution_weight > price_weight, "Execution Risk should exceed Price in Bottleneck"

    def test_non_critical_balances_price_and_simplicity(self):
        """Non-Critical posture should weight price and simplicity."""
        non_critical_weights = get_subcategory_weights("HRIS / HCM Platform", "Non-Critical")
        
        price_weight = non_critical_weights.get("Price / TCO", 0)
        strategic_weight = non_critical_weights.get("Strategic Alignment", 0)
        
        assert price_weight >= 8, "Price should be weighted appropriately in Non-Critical"
        assert price_weight > strategic_weight, "Price should exceed Strategic alignment in Non-Critical"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_all_zero_scores(self):
        """Test scoring with all dimensions at zero."""
        scores = {dim: 0 for dim in DIMENSIONS}
        weights = {dim: 1 for dim in DIMENSIONS}
        
        result = calculate_weighted_score(scores, weights)
        
        assert result == 0, "All-zero scores should produce score of 0"
        assert 0 <= result <= 100, "Result should be within valid range"

    def test_all_max_scores(self):
        """Test scoring with all dimensions at maximum (100)."""
        scores = {dim: 100 for dim in DIMENSIONS}
        weights = {dim: 1 for dim in DIMENSIONS}
        
        result = calculate_weighted_score(scores, weights)
        
        assert result == 100, "All-max scores should produce score of 100"
        assert 0 <= result <= 100, "Result should be within valid range"

    def test_mixed_high_and_low_scores(self):
        """Test scoring with mixed high (100) and low (0) scores."""
        scores = {dim: 100 if i % 2 == 0 else 0 for i, dim in enumerate(DIMENSIONS)}
        weights = {dim: 1 for dim in DIMENSIONS}
        
        result = calculate_weighted_score(scores, weights)
        
        # Should be approximately 50 (average of 100s and 0s)
        assert 45 <= result <= 55, f"Mixed scores should produce result near 50, got {result}"

    def test_single_dimension_scored(self):
        """Test scoring with only one dimension having a score."""
        scores = {dim: 50 for dim in DIMENSIONS}
        weights = {DIMENSIONS[0]: 10}  # Only one dimension has weight
        for dim in DIMENSIONS[1:]:
            weights[dim] = 0
        
        result = calculate_weighted_score(scores, weights)
        
        assert result == 50, "Single-dimension scoring should return that dimension's score"

    def test_heavily_weighted_dimension(self):
        """Test that heavily weighted dimension dominates score."""
        scores = {dim: 0 for dim in DIMENSIONS}
        scores["Price / TCO"] = 100
        
        weights = {dim: 1 for dim in DIMENSIONS}
        weights["Price / TCO"] = 100  # Overwhelming weight
        
        result = calculate_weighted_score(scores, weights)
        
        assert result > 80, "Heavily weighted high-score dimension should dominate overall score"


class TestFinancialHealth:
    """Test financial health calculations."""

    def test_financial_health_returns_valid_range(self):
        """Financial health score should always be within 0-100."""
        test_data = {"Financial Inputs": {}}
        result = calculate_financial_health(test_data)
        
        assert 0 <= result <= 100, "Financial health should be within 0-100 range"

    def test_financial_health_neutral_when_no_data(self):
        """Financial health should return neutral (50) when no data provided."""
        test_data = {"Financial Inputs": {}}
        result = calculate_financial_health(test_data)
        
        assert result == 50, "Empty financial data should return neutral score of 50"

    def test_financial_risk_label_high_score(self):
        """High financial health (80+) should map to Low Risk."""
        label = get_financial_risk_label(85)
        assert label == "Low Risk", "Financial health 85+ should be Low Risk"

    def test_financial_risk_label_medium_score(self):
        """Medium financial health (60-79) should map to Medium Risk."""
        label = get_financial_risk_label(70)
        assert label == "Medium Risk", "Financial health 60-79 should be Medium Risk"

    def test_financial_risk_label_low_score(self):
        """Low financial health (<60) should map to High Risk."""
        label = get_financial_risk_label(45)
        assert label == "High Risk", "Financial health <60 should be High Risk"


class TestWeightBoundaryConditions:
    """Test weight calculations at boundary conditions."""

    def test_zero_total_weight(self):
        """Scoring with zero total weight should return neutral 50."""
        scores = {dim: 100 for dim in DIMENSIONS}
        weights = {dim: 0 for dim in DIMENSIONS}
        
        result = calculate_weighted_score(scores, weights)
        
        assert result == 50, "Zero total weight should return neutral score of 50"

    def test_unequal_weights(self):
        """Test unequal weight distribution affects scoring."""
        scores = {dim: 100 for dim in DIMENSIONS}
        
        # Scenario 1: Equal weights
        equal_weights = {dim: 1 for dim in DIMENSIONS}
        result_equal = calculate_weighted_score(scores, equal_weights)
        
        # Scenario 2: Heavily favor one dimension to max, others to zero
        unequal_weights = {DIMENSIONS[0]: 100}
        for dim in DIMENSIONS[1:]:
            unequal_weights[dim] = 0
        result_unequal = calculate_weighted_score(scores, unequal_weights)
        
        # Equal weights should equal unequal when all scores are the same and equal
        assert abs(result_equal - result_unequal) < 1, "When all scores equal, weight distribution shouldn't matter significantly"


class TestScoreScaling:
    """Test that scores scale correctly."""

    def test_score_respects_0_to_100_bounds(self):
        """Scores should never exceed 0-100 range."""
        for test_score in [1, 50, 99, 100]:
            scores = {dim: test_score for dim in DIMENSIONS}
            weights = {dim: 1 for dim in DIMENSIONS}
            result = calculate_weighted_score(scores, weights)
            
            assert 0 <= result <= 100, f"Score {result} out of range for input {test_score}"

    def test_normalized_scores_stay_normalized(self):
        """Output should be normalized even with extreme weight differences."""
        scores = {dim: 50 for dim in DIMENSIONS}
        weights = {"Price / TCO": 1000, "SLA Strength": 1}
        for dim in DIMENSIONS[2:]:
            weights[dim] = 1
        
        result = calculate_weighted_score(scores, weights)
        
        assert 0 <= result <= 100, "Normalized scoring should stay in range despite extreme weights"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
