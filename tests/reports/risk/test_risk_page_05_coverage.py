"""Tests for risk_page_05_rloan_analysis.py coverage:
- Lines 115-119: exception handler in generate_elements
"""

from reports.risk.risk_page_05_rloan_analysis import RiskRLoanAnalysisPage


class TestRiskRLoanAnalysisErrorHandler:
    def test_no_summary_returns_unavailable_message(self):
        """flood_data without 'summary' → graceful empty path (not exception)."""
        page = RiskRLoanAnalysisPage()
        elements = page.generate_elements({})
        assert len(elements) >= 1

    def test_error_in_generate_elements_appends_message(self):
        """Lines 115-119: a malformed flood_data triggers the bare-except
        and a paragraph reporting the error is appended.
        """
        page = RiskRLoanAnalysisPage()
        # mortgage_summary contains a non-numeric total_mortgages so the
        # f"{total_mortgages:,}" format spec raises TypeError
        bad = {
            "summary": {
                "mortgage_summary": {
                    "total_mortgages": object(),  # not formattable with `:,`
                    "total_mortgage_value": 1_000_000,
                    "mortgage_value_at_risk": 100_000,
                    "percentage_mortgage_value_at_risk": 10,
                },
            },
        }
        elements = page.generate_elements(bad)
        assert len(elements) >= 1
        error_el = elements[-1]
        assert "Error generating mortgage analysis" in error_el.text
