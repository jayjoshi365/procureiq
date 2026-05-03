"""Tests for config.py"""
import pytest
from config import (
    DIMENSIONS, CURRENT_DIMS, FUTURE_DIMS, POSITION_COLORS,
    KRALJIC_INFO, AUCTION_TYPES, INTAKE_QUESTIONS, AI_TOOLS,
    AI_PROMPT_MODES, USE_CASE_TEMPLATES, CATEGORY_RULES,
    DEFAULT_RFP_STAKEHOLDERS, FINANCIAL_FIELDS, RFP_TIMELINE,
    PHASE_COLORS, DEFAULT_RFP_QUESTIONS
)


class TestConfigConstants:
    """Test configuration constants are properly defined."""

    def test_dimensions_structure(self):
        """Test DIMENSIONS contains expected procurement dimensions."""
        assert isinstance(DIMENSIONS, list)
        assert len(DIMENSIONS) == 10  # 8 original + ESG / Sustainability + Supplier Diversity
        assert "Price / TCO" in DIMENSIONS
        assert "Execution Risk" in DIMENSIONS

    def test_current_dims_subset(self):
        """Test CURRENT_DIMS is subset of DIMENSIONS."""
        assert isinstance(CURRENT_DIMS, list)
        assert all(dim in DIMENSIONS for dim in CURRENT_DIMS)

    def test_future_dims_subset(self):
        """Test FUTURE_DIMS is subset of DIMENSIONS."""
        assert isinstance(FUTURE_DIMS, list)
        assert all(dim in DIMENSIONS for dim in FUTURE_DIMS)

    def test_position_colors(self):
        """Test POSITION_COLORS contains valid hex colors."""
        assert isinstance(POSITION_COLORS, dict)
        for position, color in POSITION_COLORS.items():
            assert color.startswith("#")
            assert len(color) == 7  # #RRGGBB format

    def test_kraljic_info_structure(self):
        """Test KRALJIC_INFO has correct structure for all postures."""
        expected_postures = ["Strategic", "Leverage", "Bottleneck", "Non-Critical"]
        assert isinstance(KRALJIC_INFO, dict)
        for posture in expected_postures:
            assert posture in KRALJIC_INFO
            info = KRALJIC_INFO[posture]
            assert "axis" in info
            assert "desc" in info
            assert "color" in info
            assert "bg" in info
            assert "accent" in info

    def test_auction_types_structure(self):
        """Test AUCTION_TYPES contains expected auction types."""
        assert isinstance(AUCTION_TYPES, dict)
        assert len(AUCTION_TYPES) >= 6  # At least the main types
        for auction_type, details in AUCTION_TYPES.items():
            assert "desc" in details
            assert "when" in details
            assert "coupa_ariba" in details
            assert "color" in details

    def test_intake_questions_structure(self):
        """Test INTAKE_QUESTIONS has proper structure."""
        assert isinstance(INTAKE_QUESTIONS, list)
        for question in INTAKE_QUESTIONS:
            assert "id" in question
            assert "question" in question
            assert "options" in question
            assert "impact" in question
            assert isinstance(question["options"], list)

    def test_ai_tools_structure(self):
        """Test AI_TOOLS contains valid tool definitions."""
        assert isinstance(AI_TOOLS, list)
        for tool in AI_TOOLS:
            assert "name" in tool
            assert "url" in tool
            assert "icon" in tool
            assert "color" in tool

    def test_use_case_templates(self):
        """Test USE_CASE_TEMPLATES structure."""
        assert isinstance(USE_CASE_TEMPLATES, dict)
        for template_name, template in USE_CASE_TEMPLATES.items():
            assert "category" in template
            assert "kraljic" in template
            assert "weights" in template
            assert template["kraljic"] in KRALJIC_INFO

    def test_category_rules(self):
        """Test CATEGORY_RULES contains procurement categories."""
        assert isinstance(CATEGORY_RULES, dict)
        expected_categories = ["technology", "hr", "finance", "marketing", "services"]
        for category in expected_categories:
            assert category in CATEGORY_RULES
            rule = CATEGORY_RULES[category]
            assert "type" in rule
            assert "tag" in rule
            assert "requirements" in rule
            assert "rfp_stakeholders" in rule

    def test_financial_fields(self):
        """Test FINANCIAL_FIELDS structure."""
        assert isinstance(FINANCIAL_FIELDS, dict)
        for field_name, field_config in FINANCIAL_FIELDS.items():
            assert "options" in field_config
            assert "scores" in field_config
            assert isinstance(field_config["options"], list)
            assert isinstance(field_config["scores"], dict)

    def test_rfp_timeline(self):
        """Test RFP_TIMELINE structure."""
        assert isinstance(RFP_TIMELINE, dict)
        for kraljic, timeline in RFP_TIMELINE.items():
            assert kraljic in KRALJIC_INFO
            assert isinstance(timeline, list)
            for phase in timeline:
                assert "week" in phase
                assert "phase" in phase
                assert "tasks" in phase

    def test_default_rfp_questions(self):
        """Test DEFAULT_RFP_QUESTIONS is a list of strings."""
        assert isinstance(DEFAULT_RFP_QUESTIONS, list)
        assert len(DEFAULT_RFP_QUESTIONS) > 0
        assert all(isinstance(q, str) for q in DEFAULT_RFP_QUESTIONS)