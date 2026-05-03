"""Tests for app.py functions"""
import pytest
from unittest.mock import patch, MagicMock


class TestAppFunctions:
    """Test key functions from app.py."""

    def test_build_supplier_template_df(self):
        """Test supplier template DataFrame creation."""
        from app import build_supplier_template_df
        df = build_supplier_template_df()

        assert df is not None
        expected_columns = ["Supplier Name", "Ticker", "Quoted Price ($)",
                          "SLA Strength (Strong/Moderate/Weak)",
                          "Execution Risk (Low/Medium/High)",
                          "Stakeholder Confidence (1-5)", "Strategic Alignment (1-5)",
                          "Innovation Capacity (1-5)", "Relationship Depth (1-5)",
                          "Commercial Flexibility (1-5)", "Years in Business",
                          "Ownership Structure", "Revenue Trajectory",
                          "Recent M&A Activity", "Payment Terms Offered",
                          "Workforce Changes (12mo)", "Notes"]

        for col in expected_columns:
            assert col in df.columns

    @patch('app._YFINANCE_AVAILABLE', False)
    def test_enrich_market_leaders_no_yfinance(self):
        """Test market leaders enrichment without yfinance."""
        from app import enrich_market_leaders_with_live_data

        leaders = enrich_market_leaders_with_live_data("Cloud Infrastructure (AWS / Azure / GCP)")

        assert isinstance(leaders, list)
        if leaders:
            for leader in leaders:
                assert isinstance(leader, dict)
                assert "name" in leader
                # Should not have live data
                assert leader.get("live") is None

    def test_fmt_market_cap(self):
        """Test market cap formatting."""
        from app import _fmt_market_cap

        assert _fmt_market_cap(1000000000) == "$1.00B"
        assert _fmt_market_cap(500000000) == "$500.00M"
        assert _fmt_market_cap(None) == "N/A"
        assert _fmt_market_cap(0) == "$0.00"

    def test_fmt_pct(self):
        """Test percentage formatting."""
        from app import _fmt_pct

        assert _fmt_pct(0.15) == "+15.0%"
        assert _fmt_pct(-0.05) == "-5.0%"
        assert _fmt_pct(None) == "N/A"
        assert _fmt_pct(0) == "0.0%"

    def test_normalize_weights(self):
        """Test weight normalization."""
        from app import normalize_weights

        weights = {"A": 6, "B": 8, "C": 10}
        normalized = normalize_weights(weights)

        assert isinstance(normalized, dict)
        assert len(normalized) == 3

        # Should sum to approximately 1.0
        total = sum(normalized.values())
        assert abs(total - 1.0) < 0.001

        # Higher weights should have higher normalized values
        assert normalized["C"] > normalized["B"] > normalized["A"]

    def test_build_briefing_helpers(self):
        """Test briefing memo and action plan generation."""
        import pandas as pd
        from app import (
            build_briefing_action_plan,
            build_briefing_memo,
            build_express_brief,
            build_express_board_bullets,
            build_express_cfo_narrative,
            build_express_action_matrix,
            build_quickscan_board_bullets,
            build_quickscan_action_matrix,
            build_quickscan_cfo_summary,
        )

        leader = {
            "Supplier": "Supplier A",
            "Weighted Score": 88,
            "Current Fit": 80,
            "Future Fit": 85,
            "Scores": {"Price / TCO": 90, "SLA Strength": 80, "Execution Risk": 75, "Stakeholder Confidence": 85, "Strategic Alignment": 80, "Innovation Capacity": 70, "Relationship Depth": 75, "Commercial Flexibility": 65},
        }
        runner_up = {"Supplier": "Supplier B", "Weighted Score": 82}
        blocker_row = {"Name": "Jane Doe", "Role": "CFO", "Position": "Blocker", "Priority": "Cost / Savings"}
        category_rule = {"type": "Indirect", "tag": "Technology / SaaS", "requirements": "req", "assurance": "assure", "cost": "cost", "innovation": "innov"}
        stake_df = pd.DataFrame([{"Name": "Jane Doe", "Role": "CFO", "Power": 8, "Interest": 7, "Position": "Blocker", "Priority": "Cost / Savings"}])

        action_plan = build_briefing_action_plan("Strategic", category_rule, "Price / TCO", blocker_row, {})
        assert isinstance(action_plan, list)
        assert any("90 days" in item or "90-day" in item for item in action_plan)

        memo = build_briefing_memo(leader, runner_up, blocker_row, "Test Event", "Technology", "Strategic", category_rule, "Price / TCO", stake_df)
        assert isinstance(memo, str)
        assert "Recommendation: Supplier A" in memo
        assert "Most likely blocker: Jane Doe" in memo

        express_brief = build_express_brief(
            event_name="Express Procurement Decision",
            category="Technology",
            kraljic="Strategic",
            annual_spend=500000,
            months_since_bid=18,
            score=70,
            event_type="Full RFP",
            savings_low=40000,
            savings_high=100000,
            reasons=["Test reason 1", "Test reason 2"],
            timeline="Launch in 30 days",
            next_steps=["[ ] Step 1", "[ ] Step 2"],
        )
        assert "Recommendation: Launch a Full RFP for Technology." in express_brief
        assert "Executive note:" in express_brief

        board_bullets = build_express_board_bullets(
            category="Technology",
            event_type="Full RFP",
            annual_spend=500000,
            savings_low=40000,
            savings_high=100000,
            kraljic="Strategic",
            timeline="Launch in 30 days · Award in 60–90 days",
        )
        assert isinstance(board_bullets, list)
        assert any("Approve a Full RFP" in bullet for bullet in board_bullets)

        cfo_text = build_express_cfo_narrative(
            category="Technology",
            annual_spend=500000,
            savings_low=40000,
            savings_high=100000,
            event_type="Full RFP",
            kraljic="Strategic",
            timeline="Launch in 30 days",
        )
        assert "CFO-ready" not in cfo_text
        assert "$40,000" in cfo_text  # savings_low value appears in narrative

        matrix = build_express_action_matrix(
            event_type="Full RFP",
            category="Technology",
            kraljic="Strategic",
            score=70,
        )
        assert isinstance(matrix, list)
        assert any(row["Owner"] == "Procurement Lead" for row in matrix)

        scan_bullets = build_quickscan_board_bullets([
            {"name": "Cloud", "spend": 800000, "months": 30, "score": 75, "priority": "🔴 P1 — Act Now", "time_flag": "🔴 Overdue", "time_action": "Launch RFP", "savings_est": 60000, "spend_tier": "Tier 2 — Mid-Market"},
        ])
        assert any("Approve near-term" in bullet for bullet in scan_bullets)

        scan_matrix = build_quickscan_action_matrix([
            {"name": "Cloud", "spend": 800000, "months": 30, "score": 75, "priority": "🔴 P1 — Act Now", "time_flag": "🔴 Overdue", "time_action": "Launch RFP", "savings_est": 60000, "spend_tier": "Tier 2 — Mid-Market"},
        ])
        assert isinstance(scan_matrix, list)
        assert scan_matrix[0]["Owner"] == "Category Manager"

        scan_cfo = build_quickscan_cfo_summary([
            {"name": "Cloud", "spend": 800000, "months": 30, "score": 75, "priority": "🔴 P1 — Act Now", "time_flag": "🔴 Overdue", "time_action": "Launch RFP", "savings_est": 60000, "spend_tier": "Tier 2 — Mid-Market"},
        ])
        assert "90-Day scan covers" in scan_cfo

        from app import build_express_brief, build_quickscan_brief
        express_brief = build_express_brief(
            event_name="Express Procurement Decision",
            category="Technology",
            kraljic="Strategic",
            annual_spend=500000,
            months_since_bid=18,
            score=70,
            event_type="Full RFP",
            savings_low=40000,
            savings_high=100000,
            reasons=["Test reason 1", "Test reason 2"],
            timeline="Launch in 30 days",
            next_steps=["[ ] Step 1", "[ ] Step 2"],
        )
        assert "Recommendation: Launch a Full RFP for Technology." in express_brief
        assert "Immediate next actions:" in express_brief

        scan_brief = build_quickscan_brief([
            {"name": "Cloud", "spend": 800000, "months": 30, "score": 75, "priority": "🔴 P1 — Act Now", "time_flag": "🔴 Overdue", "time_action": "Launch RFP", "savings_est": 60000, "spend_tier": "Tier 2 — Mid-Market"},
        ])
        assert "90-Day Portfolio Scan Summary" in scan_brief
        assert "🔴 P1 — Act Now" in scan_brief


class TestCSVImport:
    """Tests for parse_supplier_csv and validate_supplier_csv_row."""

    def _make_file(self, content: str):
        import io
        f = io.BytesIO(content.encode("utf-8"))
        f.name = "test.csv"
        return f

    def test_valid_three_row_csv(self):
        from app import parse_supplier_csv
        csv_content = (
            "supplier_name,ticker,quoted_price,years_in_business,revenue_trajectory\n"
            "Acme Corp,ACME,1200000,10–25 years,Growing 5–15%\n"
            "BetaTech,,950000,3–10 years,Flat\n"
            "GammaCo,GMC,1100000,25+ years,Growing 15%+\n"
        )
        rows, warnings = parse_supplier_csv(self._make_file(csv_content))
        assert rows is not None
        assert len(rows) == 3
        assert rows[0]["supplier_name"] == "Acme Corp"
        assert rows[0]["ticker"] == "ACME"
        assert rows[0]["raw_price"] == 1_200_000.0
        assert rows[1]["ticker"] == ""
        assert rows[2]["fin_inputs"]["Years in Business"] == "25+ years"
        assert warnings == []

    def test_missing_supplier_name_column_returns_none(self):
        from app import parse_supplier_csv
        csv_content = "company,ticker\nAcme,ACME\n"
        rows, warnings = parse_supplier_csv(self._make_file(csv_content))
        assert rows is None
        assert any("supplier_name" in w for w in warnings)

    def test_empty_supplier_name_row_skipped(self):
        from app import parse_supplier_csv
        csv_content = (
            "supplier_name,ticker\n"
            ",ACME\n"
            "ValidCo,\n"
        )
        rows, warnings = parse_supplier_csv(self._make_file(csv_content))
        assert rows is not None
        assert len(rows) == 1
        assert rows[0]["supplier_name"] == "ValidCo"
        assert any("skipped" in w for w in warnings)

    def test_invalid_dropdown_value_cleared_with_warning(self):
        from app import parse_supplier_csv
        csv_content = (
            "supplier_name,years_in_business\n"
            "Acme Corp,definitely not valid\n"
        )
        rows, warnings = parse_supplier_csv(self._make_file(csv_content))
        assert rows is not None
        assert rows[0]["fin_inputs"]["Years in Business"] == ""
        assert any("not a valid option" in w for w in warnings)

    def test_invalid_ticker_cleared_with_warning(self):
        from app import parse_supplier_csv
        csv_content = "supplier_name,ticker\nAcme Corp,TOO-LONG-123\n"
        rows, warnings = parse_supplier_csv(self._make_file(csv_content))
        assert rows is not None
        assert rows[0]["ticker"] == ""
        assert any("invalid ticker" in w for w in warnings)

    def test_max_20_rows_enforced(self):
        from app import parse_supplier_csv
        header = "supplier_name\n"
        body = "".join(f"Supplier {n}\n" for n in range(1, 26))
        rows, warnings = parse_supplier_csv(self._make_file(header + body))
        assert rows is not None
        assert len(rows) == 20
        assert any("20" in w for w in warnings)

    def test_invalid_price_defaults_to_one_million(self):
        from app import parse_supplier_csv
        csv_content = "supplier_name,quoted_price\nAcme Corp,not_a_number\n"
        rows, warnings = parse_supplier_csv(self._make_file(csv_content))
        assert rows is not None
        assert rows[0]["raw_price"] == 1_000_000.0
        assert any("quoted_price" in w for w in warnings)

    def test_empty_file_returns_empty_list(self):
        from app import parse_supplier_csv
        csv_content = "supplier_name,ticker\n"
        rows, warnings = parse_supplier_csv(self._make_file(csv_content))
        assert rows == []
        assert warnings == []

    def test_validate_supplier_csv_row_valid(self):
        from validation import validate_supplier_csv_row
        row = {
            "supplier_name": "Acme",
            "ticker": "ACME",
            "quoted_price": "1200000",
            "years_in_business": "25+ years",
            "revenue_trajectory": "Growing 15%+",
        }
        cleaned, warnings = validate_supplier_csv_row(row, 2)
        assert cleaned is not None
        assert cleaned["supplier_name"] == "Acme"
        assert cleaned["ticker"] == "ACME"
        assert cleaned["raw_price"] == 1_200_000.0
        assert cleaned["fin_inputs"]["Years in Business"] == "25+ years"
        assert warnings == []

    def test_dimension_scores_imported(self):
        from validation import validate_supplier_csv_row
        row = {
            "supplier_name": "ScoreCo",
            "sla_strength": "Strong",
            "execution_risk": "Low",
            "stakeholder_confidence": "4",
            "strategic_alignment": "5",
            "innovation_capacity": "3",
            "relationship_depth": "2",
            "commercial_flexibility": "4",
            "esg_sustainability": "Moderate",
            "supplier_diversity": "Weak",
        }
        cleaned, warnings = validate_supplier_csv_row(row, 2)
        assert cleaned is not None
        assert warnings == []
        sc = cleaned["scores"]
        assert sc["sla"] == "Strong"
        assert sc["risk"] == "Low"
        assert sc["stake"] == 4
        assert sc["strategic"] == 5
        assert sc["innovation"] == 3
        assert sc["relationship"] == 2
        assert sc["flexibility"] == 4
        assert sc["esg"] == "Moderate"
        assert sc["diversity"] == "Weak"

    def test_dimension_scores_case_insensitive(self):
        from validation import validate_supplier_csv_row
        row = {"supplier_name": "X", "sla_strength": "strong", "execution_risk": "HIGH",
               "esg_sustainability": "MODERATE", "supplier_diversity": "weak"}
        cleaned, warnings = validate_supplier_csv_row(row, 2)
        assert cleaned is not None
        assert cleaned["scores"]["sla"] == "Strong"
        assert cleaned["scores"]["risk"] == "High"
        assert cleaned["scores"]["esg"] == "Moderate"
        assert cleaned["scores"]["diversity"] == "Weak"
        assert warnings == []

    def test_dimension_score_out_of_range_clamped(self):
        from validation import validate_supplier_csv_row
        row = {"supplier_name": "X", "stakeholder_confidence": "7", "strategic_alignment": "-1"}
        cleaned, warnings = validate_supplier_csv_row(row, 2)
        assert cleaned is not None
        assert cleaned["scores"]["stake"] == 5   # clamped from 7
        assert cleaned["scores"]["strategic"] == 1  # clamped from -1
        assert len(warnings) == 2

    def test_invalid_dimension_dropdown_cleared_with_warning(self):
        from validation import validate_supplier_csv_row
        row = {"supplier_name": "X", "sla_strength": "Excellent", "esg_sustainability": "Unknown"}
        cleaned, warnings = validate_supplier_csv_row(row, 2)
        assert cleaned is not None
        assert cleaned["scores"]["sla"] is None
        assert cleaned["scores"]["esg"] is None
        assert len(warnings) == 2

    def test_missing_scores_return_none_not_error(self):
        from validation import validate_supplier_csv_row
        row = {"supplier_name": "Minimal"}
        cleaned, warnings = validate_supplier_csv_row(row, 2)
        assert cleaned is not None
        assert warnings == []
        assert all(v is None for v in cleaned["scores"].values())


class TestLiveScoringFunctions:
    """Tests for the live scoring functions defined in app.py (not evaluation.py)."""

    def test_score_price_single_supplier_returns_80(self):
        from app import score_price
        assert score_price(1_000_000, [1_000_000]) == 80

    def test_score_price_at_mean_returns_50(self):
        from app import score_price
        # At exactly the mean, sigmoid input is 0, so output is 50
        result = score_price(100, [50, 100, 150])
        assert result == 50

    def test_score_price_below_mean_scores_higher(self):
        from app import score_price
        below = score_price(500_000, [500_000, 1_000_000, 1_500_000])
        above = score_price(1_500_000, [500_000, 1_000_000, 1_500_000])
        assert below > above

    def test_score_price_outlier_does_not_collapse_normal_resolution(self):
        """With a 10x outlier, normal-price suppliers should still be differentiated.
        Linear scoring collapses everyone else to 100; sigmoid preserves differentiation."""
        from app import score_price
        prices = [900_000, 1_000_000, 1_200_000, 10_000_000]
        low   = score_price(900_000,    prices)
        mid   = score_price(1_000_000,  prices)
        high  = score_price(1_200_000,  prices)
        # Normal suppliers should still be spread out, not all bunched at 100
        assert low > mid > high
        # And the outlier is penalized hardest
        outlier = score_price(10_000_000, prices)
        assert high > outlier

    def test_score_price_empty_prices_returns_80(self):
        from app import score_price
        assert score_price(1_000_000, []) == 80

    def test_weighted_score_equal_weights(self):
        from app import weighted_score
        from config import DIMENSIONS
        scores = {d: 70 for d in DIMENSIONS}
        weights = {d: 1.0 / len(DIMENSIONS) for d in DIMENSIONS}
        result = weighted_score(scores, weights)
        assert abs(result - 70.0) < 0.1

    def test_weighted_score_emphasizes_high_weight_dimension(self):
        from app import weighted_score
        from config import DIMENSIONS
        scores = {d: 50 for d in DIMENSIONS}
        scores["Price / TCO"] = 100
        weights = {d: 0.0 for d in DIMENSIONS}
        weights["Price / TCO"] = 1.0
        assert weighted_score(scores, weights) == 100.0

    def test_compute_supplier_scores_returns_all_dimensions(self):
        from app import compute_supplier_scores
        from config import DIMENSIONS
        supplier = {
            "Raw Price": 1_000_000,
            "SLA Strength": "Strong",
            "Execution Risk": "Low",
            "Stakeholder Confidence": 4,
            "Strategic Alignment": 4,
            "Innovation Capacity": 3,
            "Relationship Depth": 3,
            "Commercial Flexibility": 4,
            "ESG / Sustainability": "Moderate",
            "Supplier Diversity": "Moderate",
        }
        scores = compute_supplier_scores(supplier, [800_000, 1_000_000, 1_200_000], 70)
        assert set(scores.keys()) == set(DIMENSIONS)
        for dim, val in scores.items():
            assert 0 <= val <= 100, f"{dim} score {val} out of 0-100 range"

    def test_compute_supplier_scores_high_fin_risk_lowers_execution(self):
        from app import compute_supplier_scores
        base = {"Raw Price": 1_000_000, "SLA Strength": "Moderate", "Execution Risk": "Medium",
                "Stakeholder Confidence": 3, "Strategic Alignment": 3, "Innovation Capacity": 3,
                "Relationship Depth": 3, "Commercial Flexibility": 3,
                "ESG / Sustainability": "Moderate", "Supplier Diversity": "Moderate"}
        high_fin = compute_supplier_scores(base, [1_000_000], fin_score=20)
        low_fin  = compute_supplier_scores(base, [1_000_000], fin_score=80)
        assert high_fin["Execution Risk"] < low_fin["Execution Risk"]


class TestCFOChallengeStaleness:
    """Tests for EDGAR staleness clause in build_cfo_challenge()."""

    def _make_leader(self, period_end: str, fin_source: str = "SEC EDGAR/XBRL",
                     fin_score: int = 72, fin_risk: str = "LOW") -> dict:
        return {
            "Supplier": "Workday",
            "Weighted Score": 78.5,
            "Raw Price": 1_200_000,
            "Financial Health": fin_score,
            "Financial Health Source": fin_source,
            "Financial Risk Label": fin_risk,
            "EDGAR Period End": period_end,
            "Scores": {},
        }

    def _make_runner_up(self) -> dict:
        return {
            "Supplier": "SAP SuccessFactors",
            "Weighted Score": 71.0,
            "Raw Price": 950_000,
            "Financial Health": 68,
            "Financial Risk Label": "LOW",
        }

    def _run(self, leader, runner_up=None):
        from app import build_cfo_challenge
        results = build_cfo_challenge(
            leader=leader,
            runner_up=runner_up or self._make_runner_up(),
            event_name="HR Tech RFP",
            kraljic="Strategic",
            category_rule={},
            weakest_dim="Execution Risk",
            intake_answers={},
        )
        return " ".join(r["answer"] for r in results)

    def test_fresh_edgar_no_staleness_clause(self):
        """EDGAR data <12 months old: no staleness warning in CFO Challenge."""
        from datetime import date, timedelta
        recent = (date.today() - timedelta(days=180)).isoformat()  # ~6 months
        leader = self._make_leader(period_end=recent)
        combined = self._run(leader)
        assert "months ago" not in combined
        assert "verify recency" not in combined

    def test_amber_edgar_shows_verify_recency(self):
        """EDGAR data 13–18 months old: amber clause appears."""
        from datetime import date, timedelta
        amber_date = (date.today() - timedelta(days=450)).isoformat()  # ~15 months ago
        leader = self._make_leader(period_end=amber_date)
        combined = self._run(leader)
        assert "verify recency" in combined.lower()

    def test_stale_edgar_shows_age_in_months(self):
        """EDGAR data >18 months old: stale clause with age in months appears."""
        from datetime import date
        # 24 months ago
        d = date.today()
        stale_year = d.year - 2
        stale_date = f"{stale_year}-{d.month:02d}-01"
        leader = self._make_leader(period_end=stale_date)
        combined = self._run(leader)
        assert "months ago" in combined
        assert "financial health should be refreshed" in combined.lower()

    def test_user_assessment_source_no_edgar_clause(self):
        """User Assessment source: no EDGAR staleness clause regardless of date."""
        leader = self._make_leader(period_end="2020-01-01", fin_source="User Assessment")
        combined = self._run(leader)
        assert "months ago" not in combined
        assert "SEC data" not in combined

    def test_malformed_period_end_does_not_crash(self):
        """Malformed EDGAR period end: no crash, no staleness clause."""
        leader = self._make_leader(period_end="not-a-date")
        combined = self._run(leader)  # must not raise
        assert isinstance(combined, str)

    def test_missing_period_end_no_clause(self):
        """Empty EDGAR period end: no staleness clause, no crash."""
        leader = self._make_leader(period_end="")
        combined = self._run(leader)
        assert "months ago" not in combined
