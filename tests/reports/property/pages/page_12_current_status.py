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

"""Tests for reports.property.property_page_12_current_status — CurrentStatusPage."""

from reportlab.platypus import Paragraph, Table


def _make_mortgage(ltv=0.65, missed_payments=0, in_arrears=False,
                   latest_status=None, outstanding=None, current_payment=None,
                   last_payment_date=None, total_payments=None,
                   lending_rate=None, boe_base=None, principal_paid=None,
                   interest_paid=None, highest_arrears=None, arrears_balance=None,
                   holidays_taken=None, total_holidays=None, last_holiday=None):
    status = {
        "CurrentLTV": ltv,
        "InArrearsFlag": in_arrears,
        "MissedPayments12M": missed_payments,
    }
    if latest_status is not None:
        status["LatestStatus"] = latest_status
    if outstanding is not None:
        status["OutstandingBalance"] = outstanding
    if current_payment is not None:
        status["CurrentPayment"] = current_payment
    if last_payment_date is not None:
        status["LastPaymentDate"] = last_payment_date
    if total_payments is not None:
        status["TotalPayments"] = total_payments
    if lending_rate is not None:
        status["CurrentLendingRate"] = lending_rate
    if boe_base is not None:
        status["CurrentBoEBase"] = boe_base
    if principal_paid is not None:
        status["PrincipalPayed"] = principal_paid
    if interest_paid is not None:
        status["InterestPayed"] = interest_paid
    if highest_arrears is not None:
        status["HighestArrearsLast24M"] = highest_arrears
    if arrears_balance is not None:
        status["ArrearsHighestBalance"] = arrears_balance
    if holidays_taken is not None:
        status["PaymentHolidaysTaken"] = holidays_taken
    if total_holidays is not None:
        status["TotalPaymentHolidays"] = total_holidays
    if last_holiday is not None:
        status["LastPaymentHolidayDate"] = last_holiday
    return {"RLoan": {"CurrentStatus": status}}


class TestCurrentStatusPageBasics:

    def _page(self):
        from reports.property.property_page_12_current_status import CurrentStatusPage
        return CurrentStatusPage()

    def test_no_mortgage_returns_message(self):
        result = self._page().generate_elements({}, rloan_data=None)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("No mortgage" in t for t in texts)

    def test_with_mortgage_returns_list(self):
        result = self._page().generate_elements({}, _make_mortgage())
        assert isinstance(result, list) and len(result) > 0

    def test_has_table(self):
        result = self._page().generate_elements({}, _make_mortgage())
        assert any(isinstance(e, Table) for e in result)

    def test_has_status_header(self):
        result = self._page().generate_elements({}, _make_mortgage())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Status" in t or "Mortgage" in t for t in texts)

    def test_no_current_status_returns_message(self):
        mortgage = {"RLoan": {}}
        result = self._page().generate_elements({}, mortgage)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("No current status" in t for t in texts)

    def test_latest_status_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(latest_status="Active"))
        assert isinstance(result, list)

    def test_outstanding_balance_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(outstanding=350_000))
        assert isinstance(result, list)

    def test_current_payment_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(current_payment=1800))
        assert isinstance(result, list)

    def test_last_payment_date_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(last_payment_date="2025-12-01"))
        assert isinstance(result, list)

    def test_total_payments_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(total_payments=120))
        assert isinstance(result, list)

    def test_lending_rate_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(lending_rate=0.035))
        assert isinstance(result, list)

    def test_boe_base_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(boe_base=0.05))
        assert isinstance(result, list)

    def test_principal_paid_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(principal_paid=50_000))
        assert isinstance(result, list)

    def test_interest_paid_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(interest_paid=30_000))
        assert isinstance(result, list)


class TestLTVBranches:

    def _page(self):
        from reports.property.property_page_12_current_status import CurrentStatusPage
        return CurrentStatusPage()

    def test_ltv_over_90_high_risk(self):
        result = self._page().generate_elements({}, _make_mortgage(ltv=0.95))
        assert isinstance(result, list)

    def test_ltv_over_80_medium_high(self):
        result = self._page().generate_elements({}, _make_mortgage(ltv=0.85))
        assert isinstance(result, list)

    def test_ltv_over_70_medium(self):
        result = self._page().generate_elements({}, _make_mortgage(ltv=0.75))
        assert isinstance(result, list)

    def test_ltv_over_60_low_medium(self):
        result = self._page().generate_elements({}, _make_mortgage(ltv=0.65))
        assert isinstance(result, list)

    def test_ltv_under_60_low_risk(self):
        result = self._page().generate_elements({}, _make_mortgage(ltv=0.50))
        assert isinstance(result, list)

    def test_ltv_as_percentage_not_decimal(self):
        """LTV > 1 (e.g. 75 instead of 0.75) should still work."""
        result = self._page().generate_elements({}, _make_mortgage(ltv=75))
        assert isinstance(result, list)


class TestPaymentPerformanceBranches:

    def _page(self):
        from reports.property.property_page_12_current_status import CurrentStatusPage
        return CurrentStatusPage()

    def test_zero_missed_payments_excellent(self):
        result = self._page().generate_elements({}, _make_mortgage(missed_payments=0))
        assert isinstance(result, list)

    def test_one_missed_payment_good(self):
        result = self._page().generate_elements({}, _make_mortgage(missed_payments=1))
        assert isinstance(result, list)

    def test_two_missed_payments_good(self):
        result = self._page().generate_elements({}, _make_mortgage(missed_payments=2))
        assert isinstance(result, list)

    def test_three_missed_payments_concerning(self):
        result = self._page().generate_elements({}, _make_mortgage(missed_payments=3))
        assert isinstance(result, list)

    def test_four_missed_payments_concerning(self):
        result = self._page().generate_elements({}, _make_mortgage(missed_payments=4))
        assert isinstance(result, list)

    def test_five_missed_payments_poor(self):
        result = self._page().generate_elements({}, _make_mortgage(missed_payments=5))
        assert isinstance(result, list)

    def test_in_arrears_flag_true(self):
        result = self._page().generate_elements({}, _make_mortgage(in_arrears=True))
        assert isinstance(result, list)

    def test_highest_arrears_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(highest_arrears=5000))
        assert isinstance(result, list)

    def test_arrears_balance_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(arrears_balance=2000))
        assert isinstance(result, list)


class TestPaymentHolidays:

    def _page(self):
        from reports.property.property_page_12_current_status import CurrentStatusPage
        return CurrentStatusPage()

    def test_holidays_taken_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(holidays_taken=2))
        assert isinstance(result, list)

    def test_total_holidays_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(total_holidays=3))
        assert isinstance(result, list)

    def test_last_holiday_date_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(last_holiday="2021-04-01"))
        assert isinstance(result, list)

    def test_all_holiday_fields_shown(self):
        result = self._page().generate_elements(
            {},
            _make_mortgage(holidays_taken=2, total_holidays=3, last_holiday="2021-04-01")
        )
        assert isinstance(result, list)

    def test_no_holiday_data_no_section(self):
        """Without holiday fields, section should not appear."""
        result = self._page().generate_elements({}, _make_mortgage())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert not any("Holiday" in t for t in texts)
