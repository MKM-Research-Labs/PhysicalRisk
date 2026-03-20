# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for port.rand.thames.mortgage_random — menu, boolean, decimal value generators."""

import pytest
from port.rand.thames.mortgage.mortgage_random import (
    generate_menu_value,
    generate_boolean_value,
    generate_decimal_value,
)


# =============================================================================
# generate_menu_value
# =============================================================================

class TestGenerateMenuValue:

    def _fd(self, **kwargs):
        fd = {"mortgage_type": "Residential", "occupancy_type": "PrimaryResidence"}
        fd.update(kwargs)
        return fd

    def test_mortgage_type(self):
        result = generate_menu_value("MortgageType", {}, 0, self._fd(mortgage_type="Buy-to-Let"))
        assert result == "Buy-to-Let"

    def test_original_rate_type(self):
        result = generate_menu_value("OriginalRateType", {}, 0, self._fd())
        assert isinstance(result, str) and len(result) > 0

    def test_payment_frequency(self):
        assert generate_menu_value("PaymentFrequency", {}, 0, self._fd()) == "Monthly"

    def test_occupancy_type(self):
        result = generate_menu_value("OccupancyType", {}, 0, self._fd(occupancy_type="Investment"))
        assert result == "Investment"

    def test_loan_purpose_btl(self):
        result = generate_menu_value("LoanPurpose", {}, 0, self._fd(mortgage_type="Buy-to-Let"))
        assert result in ["Purchase", "Refinancing"]

    def test_loan_purpose_residential(self):
        result = generate_menu_value("LoanPurpose", {}, 0, self._fd())
        assert result in ["Purchase", "Refinancing", "Home Improvement"]

    def test_repayment_type_btl(self):
        result = generate_menu_value("RepaymentType", {}, 0, self._fd(mortgage_type="Buy-to-Let"))
        assert result in ["Interest only", "Repayment", "Part and part"]

    def test_repayment_type_residential(self):
        result = generate_menu_value("RepaymentType", {}, 0, self._fd())
        assert result in ["Repayment", "Interest only", "Part and part"]

    def test_application_channel(self):
        result = generate_menu_value("ApplicationChannel", {}, 0, self._fd())
        assert result in ["Retail", "Broker", "Correspondent"]

    def test_unknown_field_with_options(self):
        result = generate_menu_value("Unknown", {"options": ["X", "Y"]}, 0, self._fd())
        assert result in ["X", "Y"]

    def test_unknown_field_no_options(self):
        result = generate_menu_value("Unknown", {}, 0, self._fd())
        assert result == ""


# =============================================================================
# generate_boolean_value
# =============================================================================

class TestGenerateBooleanValue:

    def _fd(self, **kwargs):
        fd = {"mortgage_type": "Residential", "is_defaulted": False, "is_in_arrears": False,
              "property_value": 400000}
        fd.update(kwargs)
        return fd

    def test_default_flag_from_data(self):
        assert generate_boolean_value("DefaultFlag", self._fd(is_defaulted=True)) is True
        assert generate_boolean_value("DefaultFlag", self._fd(is_defaulted=False)) is False

    def test_in_arrears_flag(self):
        assert generate_boolean_value("InArrearsFlag", self._fd(is_in_arrears=True)) is True

    def test_btl_commercial_purpose(self):
        assert generate_boolean_value("BusinessOrCommercialPurpose", self._fd(mortgage_type="Buy-to-Let")) is True
        assert generate_boolean_value("BusinessOrCommercialPurpose", self._fd()) is False

    def test_first_time_buyer_btl_always_false(self):
        assert generate_boolean_value("FirstTimeBuyerFlag", self._fd(mortgage_type="Buy-to-Let")) is False

    def test_first_time_buyer_expensive_property(self):
        result = generate_boolean_value("FirstTimeBuyerFlag", self._fd(property_value=700000))
        assert isinstance(result, bool)

    def test_first_time_buyer_normal_property(self):
        result = generate_boolean_value("FirstTimeBuyerFlag", self._fd(property_value=300000))
        assert isinstance(result, bool)

    def test_advised_flag(self):
        assert isinstance(generate_boolean_value("AdvisedFlag", self._fd()), bool)

    def test_execution_only_flag(self):
        assert isinstance(generate_boolean_value("ExecutionOnlyFlag", self._fd()), bool)

    def test_mmr_compliant(self):
        assert generate_boolean_value("MMRCompliantFlag", self._fd()) is True

    def test_stress_test_compliant(self):
        assert generate_boolean_value("StressTestCompliantFlag", self._fd()) is True

    def test_unknown_field_returns_bool(self):
        assert isinstance(generate_boolean_value("Unknown", self._fd()), bool)


# =============================================================================
# generate_decimal_value
# =============================================================================

class TestGenerateDecimalValue:

    def _fd(self, **kwargs):
        fd = {"property_value": 400000, "loan_amount": 320000, "outstanding_balance": 290000,
              "ltv_ratio": 0.8, "current_ltv": 0.75, "interest_rate": 0.04,
              "monthly_payment": 1500, "borrower_income": 70000, "annual_payment": 18000}
        fd.update(kwargs)
        return fd

    def test_purchase_value(self):
        assert generate_decimal_value("PurchaseValue", self._fd()) == 400000

    def test_application_property_valuation(self):
        assert generate_decimal_value("ApplicationPropertyValuation", self._fd()) == 400000

    def test_original_loan(self):
        assert generate_decimal_value("OriginalLoan", self._fd()) == 320000

    def test_original_loan_amount(self):
        assert generate_decimal_value("OriginalLoanAmount", self._fd()) == 320000

    def test_outstanding_balance(self):
        assert generate_decimal_value("OutstandingBalance", self._fd()) == 290000

    def test_current_balance(self):
        assert generate_decimal_value("CurrentBalance", self._fd()) == 290000

    def test_original_ltv(self):
        result = generate_decimal_value("OriginalLTV", self._fd())
        assert abs(result - 80.0) < 0.01

    def test_current_ltv(self):
        result = generate_decimal_value("CurrentLTV", self._fd())
        assert abs(result - 75.0) < 0.01

    def test_ltv_field(self):
        result = generate_decimal_value("LTV", self._fd())
        assert abs(result - 75.0) < 0.01

    def test_loan_to_value_ratio(self):
        result = generate_decimal_value("LoanToValueRatio", self._fd())
        assert abs(result - 80.0) < 0.01

    def test_original_lending_rate(self):
        result = generate_decimal_value("OriginalLendingRate", self._fd())
        assert abs(result - 4.0) < 0.01

    def test_current_lending_rate(self):
        result = generate_decimal_value("CurrentLendingRate", self._fd())
        assert abs(result - 4.0) < 0.01

    def test_interest_rate(self):
        result = generate_decimal_value("InterestRate", self._fd())
        assert isinstance(result, float)

    def test_current_payment(self):
        assert generate_decimal_value("CurrentPayment", self._fd()) == 1500

    def test_borrower_income(self):
        assert generate_decimal_value("BorrowerIncome", self._fd()) == 70000

    def test_debt_to_income_ratio(self):
        result = generate_decimal_value("DebtToIncomeRatio", self._fd())
        assert isinstance(result, float)

    def test_debt_to_income_zero_income(self):
        result = generate_decimal_value("DebtToIncomeRatio", self._fd(borrower_income=0))
        assert result == 0.3

    def test_aprc_initial_rate(self):
        result = generate_decimal_value("APRCInitialRate", self._fd())
        assert isinstance(result, float)

    def test_aprc_secondary_rate(self):
        result = generate_decimal_value("APRCSecondaryRate", self._fd())
        assert isinstance(result, float)

    def test_default_field(self):
        result = generate_decimal_value("Unknown", self._fd())
        assert isinstance(result, float)
