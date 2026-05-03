"""Tests for market_data.py"""
import pytest
from market_data import MARKET_LEADERS, get_market_leaders_extended, DEFAULT_MARKET_LEADERS


class TestMarketData:
    """Test market leaders data and retrieval functions."""

    def test_market_leaders_structure(self):
        """Test MARKET_LEADERS has correct structure."""
        assert isinstance(MARKET_LEADERS, dict)

        # Should have data for key subcategories
        key_subcategories = ["Cloud Infrastructure (AWS / Azure / GCP)",
                           "Cybersecurity (EDR / SIEM / SOC)",
                           "ERP System (SAP / Oracle / etc.)"]

        for subcategory in key_subcategories:
            assert subcategory in MARKET_LEADERS
            leaders = MARKET_LEADERS[subcategory]
            assert isinstance(leaders, list)
            assert len(leaders) > 0

            # Check structure of each leader
            for leader in leaders:
                assert isinstance(leader, dict)
                assert "name" in leader
                assert "description" in leader
                # ticker is optional
                # assert "ticker" in leader

    def test_market_leader_fields(self):
        """Test market leader entries have required fields."""
        for subcategory, leaders in MARKET_LEADERS.items():
            for leader in leaders:
                required_fields = ["name", "description"]
                for field in required_fields:
                    assert field in leader, f"Missing {field} in {subcategory} leader"

                # Name and description should be non-empty strings
                assert isinstance(leader["name"], str)
                assert len(leader["name"]) > 0
                assert isinstance(leader["description"], str)
                assert len(leader["description"]) > 0

    def test_get_market_leaders_extended_known_category(self):
        """Test get_market_leaders_extended for known category."""
        leaders = get_market_leaders_extended("Cloud Infrastructure (AWS / Azure / GCP)")

        assert isinstance(leaders, list)
        if leaders:  # If extended data is available
            assert len(leaders) > 0
            for leader in leaders:
                assert isinstance(leader, dict)
                assert "name" in leader

    def test_get_market_leaders_extended_unknown_category(self):
        """Test get_market_leaders_extended for unknown category."""
        leaders = get_market_leaders_extended("Unknown Category XYZ")

        # Should return default leaders
        assert isinstance(leaders, list)
        assert leaders == DEFAULT_MARKET_LEADERS

    def test_default_market_leaders_fallback(self):
        """Test DEFAULT_MARKET_LEADERS is properly defined."""
        assert isinstance(DEFAULT_MARKET_LEADERS, list)
        assert len(DEFAULT_MARKET_LEADERS) > 0

        for leader in DEFAULT_MARKET_LEADERS:
            assert isinstance(leader, dict)
            assert "name" in leader
            assert "description" in leader

    def test_market_data_availability(self):
        """Test _MARKET_DATA_AVAILABLE flag."""
        from market_data import _MARKET_DATA_AVAILABLE
        assert isinstance(_MARKET_DATA_AVAILABLE, bool)
        # Should be True since we have the extended data
        assert _MARKET_DATA_AVAILABLE is True

    def test_market_leaders_completeness(self):
        """Test market leaders cover major procurement categories."""
        subcategories = list(MARKET_LEADERS.keys())
        assert len(subcategories) >= 8  # Should have data for multiple categories

        # Check for diversity of categories
        has_it = any("Cloud" in s or "Cybersecurity" in s or "ERP" in s for s in subcategories)
        has_hr = any("HR" in s or "Payroll" in s for s in subcategories)
        has_logistics = any("Truck" in s or "Logistics" in s for s in subcategories)

        assert has_it, "Should have IT-related market leaders"
        assert has_hr, "Should have HR-related market leaders"
        assert has_logistics, "Should have logistics-related market leaders"