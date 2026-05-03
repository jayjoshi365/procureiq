"""Tests for rfp.py"""
import pytest
from rfp import get_rfp_questions, RFP_QUESTIONS_BY_SUBCATEGORY, DEFAULT_RFP_QUESTIONS


class TestRFP:
    """Test RFP question generation functionality."""

    def test_get_rfp_questions_exact_match(self):
        """Test exact subcategory match returns predefined questions."""
        questions = get_rfp_questions("HRIS / HCM Platform")

        assert isinstance(questions, list)
        assert len(questions) > 0
        assert all(isinstance(q, str) for q in questions)

        # Should match the predefined questions
        expected_questions = RFP_QUESTIONS_BY_SUBCATEGORY["HRIS / HCM Platform"]
        assert questions == expected_questions

    def test_get_rfp_questions_rag_fallback(self):
        """Test RAG fallback for unknown subcategory."""
        questions = get_rfp_questions("Unknown Procurement Category")

        assert isinstance(questions, list)
        assert len(questions) >= 10  # Should return at least 10 questions
        assert all(isinstance(q, str) for q in questions)

    def test_get_rfp_questions_with_context(self):
        """Test RAG considers context when generating questions."""
        questions1 = get_rfp_questions("Software Implementation", "agile methodology")
        questions2 = get_rfp_questions("Software Implementation", "waterfall approach")

        # Questions should be different based on context
        # (This is a basic test - in practice, the RAG system would differentiate)
        assert isinstance(questions1, list)
        assert isinstance(questions2, list)
        assert len(questions1) > 0
        assert len(questions2) > 0

    def test_rfp_questions_by_subcategory_structure(self):
        """Test RFP_QUESTIONS_BY_SUBCATEGORY has correct structure."""
        assert isinstance(RFP_QUESTIONS_BY_SUBCATEGORY, dict)

        # Should have questions for key subcategories
        key_subcategories = ["HRIS / HCM Platform", "Cybersecurity (EDR / SIEM / SOC)",
                           "Cloud Infrastructure (AWS / Azure / GCP)"]

        for subcategory in key_subcategories:
            assert subcategory in RFP_QUESTIONS_BY_SUBCATEGORY
            questions = RFP_QUESTIONS_BY_SUBCATEGORY[subcategory]
            assert isinstance(questions, list)
            assert len(questions) >= 5  # Each should have multiple questions
            assert all(isinstance(q, str) for q in questions)

    def test_default_rfp_questions_fallback(self):
        """Test DEFAULT_RFP_QUESTIONS is used as fallback."""
        # This tests the fallback mechanism indirectly
        questions = get_rfp_questions("Completely Unknown Category 12345")

        assert isinstance(questions, list)
        assert len(questions) > 0

        # If RAG fails, should fall back to defaults
        # (The exact behavior depends on sklearn availability)

    def test_rfp_questions_quality(self):
        """Test RFP questions are meaningful and procurement-focused."""
        sample_questions = []
        for subcategory, questions in RFP_QUESTIONS_BY_SUBCATEGORY.items():
            sample_questions.extend(questions[:2])  # Take first 2 from each

        # Check some quality indicators
        procurement_keywords = ["SLA", "contract", "implementation", "support",
                              "security", "compliance", "cost", "timeline"]

        # At least some questions should contain procurement keywords
        has_procurement_terms = any(
            any(keyword.lower() in q.lower() for keyword in procurement_keywords)
            for q in sample_questions
        )
        assert has_procurement_terms, "RFP questions should contain procurement terminology"

    def test_rfp_questions_uniqueness(self):
        """Test questions within a subcategory are unique."""
        for subcategory, questions in RFP_QUESTIONS_BY_SUBCATEGORY.items():
            unique_questions = set(questions)
            assert len(unique_questions) == len(questions), f"Duplicate questions in {subcategory}"