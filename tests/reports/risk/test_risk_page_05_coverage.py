# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
