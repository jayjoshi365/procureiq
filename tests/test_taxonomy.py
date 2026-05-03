"""Tests for taxonomy.py"""
import pytest
from taxonomy import SUBCATEGORY_TAXONOMY


class TestTaxonomy:
    """Test procurement subcategory taxonomy."""

    def test_subcategory_taxonomy_structure(self):
        """Test SUBCATEGORY_TAXONOMY has correct structure."""
        assert isinstance(SUBCATEGORY_TAXONOMY, dict)
        assert len(SUBCATEGORY_TAXONOMY) > 50  # Should have many subcategories

    def test_subcategory_fields(self):
        """Test each subcategory has required fields."""
        for subcategory_name, subcategory_data in SUBCATEGORY_TAXONOMY.items():
            assert isinstance(subcategory_name, str)
            assert isinstance(subcategory_data, dict)

            # Check required fields
            required_fields = ["category", "description", "kraljic_default", "contract_type"]
            for field in required_fields:
                assert field in subcategory_data, f"Missing {field} in {subcategory_name}"

            # Validate Kraljic posture
            assert subcategory_data["kraljic_default"] in ["Strategic", "Leverage", "Bottleneck", "Non-Critical"]

            # Validate contract type
            valid_contract_types = ["Service Agreement", "License Agreement", "Supply Agreement",
                                  "Professional Services", "Master Services Agreement", "SOW"]
            assert subcategory_data["contract_type"] in valid_contract_types

    def test_subcategory_examples(self):
        """Test some key subcategories have expected properties."""
        # Test IT category
        assert "ERP System (SAP / Oracle / etc.)" in SUBCATEGORY_TAXONOMY
        erp = SUBCATEGORY_TAXONOMY["ERP System (SAP / Oracle / etc.)"]
        assert erp["kraljic_default"] == "Strategic"
        assert "category" in erp

        # Test HR category
        assert "HRIS / HCM Platform" in SUBCATEGORY_TAXONOMY
        hris = SUBCATEGORY_TAXONOMY["HRIS / HCM Platform"]
        assert hris["kraljic_default"] == "Strategic"

        # Test Logistics category
        assert "Truckload (TL) / Full Truckload" in SUBCATEGORY_TAXONOMY
        truckload = SUBCATEGORY_TAXONOMY["Truckload (TL) / Full Truckload"]
        assert truckload["kraljic_default"] in ["Leverage", "Non-Critical"]

    def test_taxonomy_completeness(self):
        """Test taxonomy covers major procurement categories."""
        subcategories = list(SUBCATEGORY_TAXONOMY.keys())

        # Check for major IT subcategories
        it_subcats = [s for s in subcategories if "ERP" in s or "Cloud" in s or "Cybersecurity" in s]
        assert len(it_subcats) >= 3

        # Check for HR subcategories
        hr_subcats = [s for s in subcategories if "HR" in s or "Payroll" in s]
        assert len(hr_subcats) >= 2

        # Check for Logistics subcategories
        logistics_subcats = [s for s in subcategories if "Truck" in s or "Logistics" in s]
        assert len(logistics_subcats) >= 2

    def test_no_duplicate_subcategories(self):
        """Test no duplicate subcategory names."""
        subcategories = list(SUBCATEGORY_TAXONOMY.keys())
        assert len(subcategories) == len(set(subcategories))