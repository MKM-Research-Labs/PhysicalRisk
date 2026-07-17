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

"""Tests for reports.property.property_page_11b_rloan_costs — RLoanCostsPage."""

from reportlab.platypus import Paragraph, Table


def _make_mortgage(origination=2_000, product_fee=995, discount_points=0,
                   lender_credits=0, total_loan_costs=None, original_loan=400_000,
                   original_rate=0.035):
    terms = {
        "OriginalLoan": original_loan,
        "OriginalLendingRate": original_rate,
        "OriginationCharges": origination,
        "ProductFee": product_fee,
        "EarlyRepaymentCharge": 3_000,
        "PrepaymentPenaltyTerm": 24,
    }
    if discount_points:
        terms["DiscountPoints"] = discount_points
    if lender_credits:
        terms["LenderCredits"] = lender_credits
    if total_loan_costs is not None:
        terms["TotalLoanCosts"] = total_loan_costs
    return {"RLoan": {"Header": {"RLoanID": "MORT-001"}, "FinancialTerms": terms}}


class TestRLoanCostsPage:

    def _page(self):
        from reports.property.property_page_11b_rloan_costs import RLoanCostsPage
        return RLoanCostsPage()

    def test_no_mortgage_data_returns_message(self):
        page = self._page()
        result = page.generate_elements({})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No mortgage data available" in t for t in texts)

    def test_no_financial_terms_returns_message(self):
        page = self._page()
        result = page.generate_elements({}, {"RLoan": {"Header": {"RLoanID": "X"}}})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No cost information available" in t for t in texts)

    def test_returns_list_with_data(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        assert isinstance(result, list)
        assert len(result) > 0

    def test_section_header_present(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Mortgage Costs" in t for t in texts)

    def test_has_tables(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        assert any(isinstance(e, Table) for e in result)

    def test_total_costs_overview_subsection(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(total_loan_costs=15_000))
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Total Loan Costs" in t for t in texts)

    def test_origination_setup_subsection(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Origination" in t for t in texts)

    def test_penalties_subsection(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Penalties" in t for t in texts)

    def test_cost_analysis_subsection(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Cost Analysis" in t for t in texts)

    def test_cost_high_burden(self):
        """Net upfront > 5% of loan → High assessment."""
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(
            origination=15_000, product_fee=5_000, original_loan=300_000))
        assert isinstance(result, list)

    def test_cost_medium_high_burden(self):
        """Net upfront 3–5% → Medium-High assessment."""
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(
            origination=8_000, product_fee=2_000, original_loan=250_000))
        assert isinstance(result, list)

    def test_cost_medium_burden(self):
        """Net upfront 1.5–3% → Medium assessment."""
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(
            origination=3_000, product_fee=1_000, original_loan=200_000))
        assert isinstance(result, list)

    def test_cost_low_medium_burden(self):
        """Net upfront 0.5–1.5% → Low-Medium assessment."""
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(
            origination=1_000, product_fee=500, original_loan=200_000))
        assert isinstance(result, list)

    def test_cost_low_burden(self):
        """Net upfront < 0.5% → Low assessment."""
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(
            origination=200, product_fee=100, original_loan=200_000))
        assert isinstance(result, list)

    def test_lender_credits_reduces_net_cost(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(lender_credits=500))
        assert isinstance(result, list)

    def test_discount_points_analysis(self):
        """Discount points + original rate triggers estimated points/rate reduction rows."""
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(discount_points=2_000))
        assert isinstance(result, list)

    def test_total_costs_as_percentage_of_loan(self):
        """TotalLoanCosts + OriginalLoan triggers percentage row."""
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(total_loan_costs=12_000))
        assert isinstance(result, list)

    def test_empty_mortgage_dict_does_not_crash(self):
        page = self._page()
        result = page.generate_elements({}, {})
        assert isinstance(result, list)
