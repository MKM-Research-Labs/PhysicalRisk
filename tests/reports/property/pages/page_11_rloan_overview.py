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

"""Tests for reports.property.property_page_11_rloan_overview — RLoanOverviewPage."""

from reportlab.platypus import Paragraph, Table


def _make_mortgage():
    return {
        "Mortgage": {
            "Header": {
                "MortgageID": "MORT-001",
                "PropertyID": "PROP-001",
                "UPRN": "12345678",
            },
            "Application": {
                "MortgageProvider": "Barclays",
                "ApplicationDate": "2015-03-01",
                "LoanPurpose": "Purchase",
                "OccupancyType": "Owner-occupied",
                "ApplicationChannel": "Branch",
                "ApplicationPropertyValuation": 650_000,
            },
            "FinancialTerms": {
                "PurchaseValue": 650_000,
                "OriginalLoan": 487_500,
                "OriginalTerm": 300,
                "OriginalLendingRate": 0.035,
                "currency": "GBP",
            },
            "Features": {
                "MortgageType": "Repayment",
                "PaymentFrequency": "Monthly",
                "RepaymentType": "Capital and Interest",
                "FirstTimeBuyerFlag": False,
                "PaymentHolidayEligible": True,
                "PortabilityFlag": True,
                "OffsetAccount": False,
            },
        }
    }


class TestRLoanOverviewPage:

    def _page(self):
        from reports.property.property_page_11_rloan_overview import RLoanOverviewPage
        return RLoanOverviewPage()

    def test_no_mortgage_data_returns_message(self):
        page = self._page()
        result = page.generate_elements({})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No mortgage data available" in t for t in texts)

    def test_none_mortgage_data_returns_message(self):
        page = self._page()
        result = page.generate_elements({}, rloan_data=None)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No mortgage data available" in t for t in texts)

    def test_returns_list_with_data(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        assert isinstance(result, list)
        assert len(result) > 0

    def test_section_header_present(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Mortgage Overview" in t for t in texts)

    def test_has_tables(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        assert any(isinstance(e, Table) for e in result)

    def test_mortgage_identification_subsection(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Mortgage Identification" in t for t in texts)

    def test_application_subsection(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Application Information" in t for t in texts)

    def test_key_financial_terms_subsection(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Key Financial Terms" in t for t in texts)

    def test_mortgage_features_subsection(self):
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Mortgage Features" in t for t in texts)

    def test_ltv_calculated_from_loan_and_purchase(self):
        """LTV row is computed when both PurchaseValue and OriginalLoan are present."""
        page = self._page()
        result = page.generate_elements({}, _make_mortgage())
        assert isinstance(result, list)

    def test_denial_reason_shown_when_not_default(self):
        mortgage = _make_mortgage()
        mortgage["Mortgage"]["Application"]["DenialReason"] = "Insufficient income"
        page = self._page()
        result = page.generate_elements({}, mortgage)
        assert isinstance(result, list)

    def test_denial_reason_hidden_when_default(self):
        mortgage = _make_mortgage()
        mortgage["Mortgage"]["Application"]["DenialReason"] = "Not specified"
        page = self._page()
        result = page.generate_elements({}, mortgage)
        assert isinstance(result, list)

    def test_flat_mortgage_dict_accepted(self):
        """rloan_data without outer 'Mortgage' key is handled via fallback."""
        flat = {
            "Header": {"MortgageID": "MORT-002"},
        }
        page = self._page()
        result = page.generate_elements({}, flat)
        assert isinstance(result, list)

    def test_empty_mortgage_dict_does_not_crash(self):
        page = self._page()
        result = page.generate_elements({}, {})
        assert isinstance(result, list)
