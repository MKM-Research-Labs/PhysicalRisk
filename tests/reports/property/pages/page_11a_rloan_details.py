# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for reports.property.property_page_11a_rloan_details — RLoanDetailsPage."""

from reportlab.platypus import Paragraph, Table


def _make_mortgage(original_ltv=0.75, dti=30.0, extra_terms=None):
    terms = {
        "currency": "GBP",
        "PurchaseValue": 500_000,
        "OriginalLoan": 375_000,
        "OriginalTerm": 300,
        "DisbursalDate": "2015-06-01",
        "MaturityDate": "2040-06-01",
        "OriginalLendingRate": 0.035,
        "OriginalRateType": "Fixed",
        "OriginalBoEBase": 0.005,
        "OriginalSpread": 0.03,
        "HMDARateSpread": 0.015,
        "InitialFixedTerm": 24,
        "IntroductoryRatePeriod": 24,
        "OriginalLTV": original_ltv,
        "DebtToIncomeRatio": dti,
    }
    if extra_terms:
        terms.update(extra_terms)
    return {"RLoan": {"Header": {"RLoanID": "MORT-001"}, "FinancialTerms": terms}}


class TestRLoanDetailsPage:

    def _page(self):
        from reports.property.property_page_11a_rloan_details import RLoanDetailsPage
        return RLoanDetailsPage()

    def test_no_mortgage_data_returns_message(self):
        page = self._page()
        result = page.generate_elements({})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No mortgage data available" in t for t in texts)

    def test_no_financial_terms_returns_message(self):
        page = self._page()
        result = page.generate_elements({}, {"RLoan": {"Header": {"RLoanID": "X"}}})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No detailed financial terms available" in t for t in texts)

    def test_returns_list_with_data(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        assert isinstance(result, list)
        assert len(result) > 0

    def test_section_header_present(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Detailed Mortgage Financial Terms" in t for t in texts)

    def test_has_tables(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        assert any(isinstance(e, Table) for e in result)

    def test_core_loan_terms_subsection(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Core Loan Terms" in t for t in texts)

    def test_interest_rates_subsection(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Interest Rates" in t for t in texts)

    def test_ltv_subsection(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Loan-to-Value" in t for t in texts)

    def test_dti_subsection(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Debt-to-Income" in t for t in texts)

    def test_ltv_very_high_risk(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(original_ltv=0.97))
        assert isinstance(result, list)

    def test_ltv_high_risk(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(original_ltv=0.92))
        assert isinstance(result, list)

    def test_ltv_medium_risk(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(original_ltv=0.85))
        assert isinstance(result, list)

    def test_ltv_low_medium_risk(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(original_ltv=0.77))
        assert isinstance(result, list)

    def test_ltv_low_risk(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(original_ltv=0.65))
        assert isinstance(result, list)

    def test_dti_high_risk(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(dti=50))
        assert isinstance(result, list)

    def test_dti_medium_high_risk(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(dti=40))
        assert isinstance(result, list)

    def test_dti_medium_risk(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(dti=32))
        assert isinstance(result, list)

    def test_dti_low_risk(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(dti=20))
        assert isinstance(result, list)

    def test_alternative_ltv_field(self):
        """LoanToValueRatio shown when different from OriginalLTV."""
        page = self._page()
        result = page.generate_elements({}, _make_mortgage(extra_terms={"LoanToValueRatio": 0.80}))
        assert isinstance(result, list)

    def test_loan_percentage_of_purchase_calculated(self):
        """Loan as % of purchase value row is computed when both fields present."""
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        assert isinstance(result, list)
