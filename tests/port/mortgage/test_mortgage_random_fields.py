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

"""Tests for port.rand.thames.mortgage_random — integer, date, text, field, QCC."""

import pytest
from port.rand.thames.mortgage.mortgage_random import (
    generate_integer_value,
    generate_date_value,
    generate_text_value,
    generate_field_value,
    quality_consistency_check,
)


# =============================================================================
# generate_integer_value
# =============================================================================

class TestGenerateIntegerValue:

    def _fd(self, **kwargs):
        fd = {"mortgage_type": "Residential", "term_months": 300, "months_elapsed": 60,
              "is_defaulted": False, "is_in_arrears": False, "property_value": 400000,
              "interest_rate": 0.04}
        fd.update(kwargs)
        return fd

    def test_original_term(self):
        assert generate_integer_value("OriginalTerm", self._fd()) == 300

    def test_loan_term(self):
        assert generate_integer_value("LoanTerm", self._fd()) == 300

    def test_remaining_term(self):
        result = generate_integer_value("RemainingTerm", self._fd())
        assert result == 240

    def test_total_payments(self):
        result = generate_integer_value("TotalPayments", self._fd())
        assert result == 60

    def test_borrower_age_btl(self):
        result = generate_integer_value("BorrowerAge", self._fd(mortgage_type="Buy-to-Let"))
        assert 35 <= result <= 65

    def test_borrower_age_expensive(self):
        result = generate_integer_value("BorrowerAge", self._fd(property_value=900000))
        assert 35 <= result <= 65

    def test_borrower_age_normal(self):
        result = generate_integer_value("BorrowerAge", self._fd())
        assert 25 <= result <= 60

    def test_credit_score_low_rate(self):
        result = generate_integer_value("BorrowerCreditScore", self._fd(interest_rate=0.03))
        assert 750 <= result <= 850

    def test_credit_score_expensive_property(self):
        result = generate_integer_value("BorrowerCreditScore", self._fd(property_value=700000))
        assert 700 <= result <= 800

    def test_credit_score_normal(self):
        result = generate_integer_value("BorrowerCreditScore", self._fd())
        assert 650 <= result <= 750

    def test_family_members(self):
        result = generate_integer_value("FamilyMembers", self._fd())
        assert result in [1, 2, 3, 4]

    def test_number_of_borrowers(self):
        result = generate_integer_value("NumberOfBorrowers", self._fd())
        assert result in [1, 2]

    def test_days_in_arrears_defaulted(self):
        result = generate_integer_value("DaysInArrears", self._fd(is_defaulted=True))
        assert 90 <= result <= 365

    def test_days_in_arrears_in_arrears(self):
        result = generate_integer_value("DaysInArrears", self._fd(is_in_arrears=True))
        assert 1 <= result <= 89

    def test_days_in_arrears_current(self):
        assert generate_integer_value("DaysInArrears", self._fd()) == 0

    def test_arrears_months_in_arrears(self):
        result = generate_integer_value("ArrearsMonths", self._fd(is_in_arrears=True))
        assert 1 <= result <= 6

    def test_arrears_months_current(self):
        assert generate_integer_value("ArrearsMonths", self._fd()) == 0

    def test_behavioral_score(self):
        result = generate_integer_value("BehavioralScore", self._fd())
        assert 30 <= result <= 100

    def test_prepayment_risk_high_rate(self):
        result = generate_integer_value("PrepaymentRisk", self._fd(interest_rate=0.06))
        assert 7 <= result <= 10

    def test_prepayment_risk_low_rate(self):
        result = generate_integer_value("PrepaymentRisk", self._fd(interest_rate=0.04))
        assert 1 <= result <= 5

    def test_unknown_field(self):
        result = generate_integer_value("Unknown", self._fd())
        assert 1 <= result <= 10


# =============================================================================
# generate_date_value
# =============================================================================

class TestGenerateDateValue:

    def _fd(self, **kwargs):
        fd = {"months_elapsed": 24, "term_months": 300, "is_defaulted": False}
        fd.update(kwargs)
        return fd

    def test_application_date_is_string(self):
        result = generate_date_value("ApplicationDate", self._fd())
        assert isinstance(result, str)
        assert len(result) == 10  # YYYY-MM-DD

    def test_disbursal_date(self):
        result = generate_date_value("DisbursalDate", self._fd())
        assert isinstance(result, str)

    def test_maturity_date(self):
        result = generate_date_value("MaturityDate", self._fd())
        assert isinstance(result, str)

    def test_default_date_when_defaulted(self):
        result = generate_date_value("DefaultDate", self._fd(is_defaulted=True))
        assert isinstance(result, str)

    def test_default_date_not_defaulted(self):
        result = generate_date_value("DefaultDate", self._fd())
        assert result is None

    def test_unknown_field(self):
        result = generate_date_value("Unknown", self._fd())
        assert isinstance(result, str)


# =============================================================================
# generate_text_value
# =============================================================================

class TestGenerateTextValue:

    def _fd(self, **kwargs):
        fd = {"mortgage_id": "MORT-abc123", "property_id": "PROP-001",
              "mortgage_type": "Residential", "is_defaulted": False, "flood_risk": "Low"}
        fd.update(kwargs)
        return fd

    def test_mortgage_id(self):
        assert generate_text_value("MortgageID", 0, self._fd()) == "MORT-abc123"

    def test_mortgage_provider(self):
        result = generate_text_value("MortgageProvider", 0, self._fd())
        assert isinstance(result, str)

    def test_member_id(self):
        result = generate_text_value("MemberID", 0, self._fd())
        assert result.startswith("MEMBER-")

    def test_uprn_no_existing(self):
        result = generate_text_value("UPRN", 0, self._fd())
        assert result.startswith("UPRN-") or isinstance(result, str)

    def test_uprn_with_existing(self):
        result = generate_text_value("UPRN", 0, self._fd(uprn="UPRN-12345"))
        assert result == "UPRN-12345"

    def test_property_id(self):
        assert generate_text_value("PropertyID", 0, self._fd()) == "PROP-001"

    def test_catchment_id(self):
        assert generate_text_value("CatchmentID", 0, self._fd()) == "thames"

    def test_currency(self):
        assert generate_text_value("currency", 0, self._fd()) == "GBP"

    def test_account_status_defaulted(self):
        result = generate_text_value("AccountStatus", 0, self._fd(is_defaulted=True))
        assert result == "Default"

    def test_account_status_normal(self):
        result = generate_text_value("AccountStatus", 0, self._fd())
        assert result in ["Current", "Arrears", "Closed"]

    def test_latest_status_defaulted(self):
        result = generate_text_value("LatestStatus", 0, self._fd(is_defaulted=True))
        assert result == "Defaulted"

    def test_latest_status_normal(self):
        result = generate_text_value("LatestStatus", 0, self._fd())
        assert result in ["Current", "Completed", "Redeemed"]

    def test_borrower_employment_btl(self):
        result = generate_text_value("BorrowerEmployment", 0, self._fd(mortgage_type="Buy-to-Let"))
        assert isinstance(result, str)

    def test_employment_type_residential(self):
        result = generate_text_value("EmploymentType", 0, self._fd())
        assert isinstance(result, str)

    def test_marital_status_young(self):
        result = generate_text_value("MaritalStatus", 0, self._fd(borrower_age=25))
        assert result in ["Single", "Married", "Civil Partnership"]

    def test_marital_status_older(self):
        result = generate_text_value("MaritalStatus", 0, self._fd(borrower_age=45))
        assert isinstance(result, str)

    def test_flood_risk_category(self):
        result = generate_text_value("FloodRiskCategory", 0, self._fd(flood_risk="Medium"))
        assert result == "Medium"

    def test_unknown_field(self):
        result = generate_text_value("Unknown", 5, self._fd())
        assert "Text-5-" in result


# =============================================================================
# generate_field_value
# =============================================================================

class TestGenerateFieldValue:

    def _fd(self):
        return {"mortgage_type": "Residential", "is_defaulted": False,
                "loan_amount": 320000, "mortgage_id": "MORT-xyz"}

    def test_non_dict_field_def_returns_string(self):
        result = generate_field_value("f", "literal", 0, self._fd())
        assert result == "literal"

    def test_non_dict_non_string_returns_empty(self):
        result = generate_field_value("f", 42, 0, self._fd())
        assert result == ""

    def test_menu_type(self):
        result = generate_field_value("PaymentFrequency", {"type": "menu"}, 0, self._fd())
        assert result == "Monthly"

    def test_enum_type(self):
        result = generate_field_value("PaymentFrequency", {"type": "enum"}, 0, self._fd())
        assert result == "Monthly"

    def test_boolean_type(self):
        result = generate_field_value("DefaultFlag", {"type": "boolean"}, 0, self._fd())
        assert isinstance(result, bool)

    def test_decimal_type(self):
        result = generate_field_value("OriginalLoan", {"type": "decimal"}, 0, self._fd())
        assert isinstance(result, (int, float))

    def test_integer_type(self):
        result = generate_field_value("OriginalTerm", {"type": "integer"}, 0,
                                      {"term_months": 300, "months_elapsed": 0})
        assert result == 300

    def test_date_type(self):
        result = generate_field_value("ApplicationDate", {"type": "date"}, 0,
                                      {"months_elapsed": 12})
        assert isinstance(result, str)

    def test_text_type(self):
        result = generate_field_value("CatchmentID", {"type": "text"}, 0, self._fd())
        assert result == "thames"

    def test_unknown_type_returns_empty(self):
        result = generate_field_value("f", {"type": "unknown"}, 0, self._fd())
        assert result == ""


# =============================================================================
# quality_consistency_check
# =============================================================================

class TestQualityConsistencyCheck:

    def _mortgage_data(self, original=400000, current=390000, ltv=80, interest=4.5):
        return {
            "Mortgage": {
                "LoanDetails": {
                    "OriginalLoanAmount": original,
                    "CurrentBalance": current,
                    "LTV": ltv,
                    "InterestRate": interest,
                }
            }
        }

    def test_current_exceeds_original_is_capped(self):
        data = self._mortgage_data(original=400000, current=420000)
        result = quality_consistency_check(data, {})
        assert result["Mortgage"]["LoanDetails"]["CurrentBalance"] <= 400000

    def test_ltv_over_100_capped_at_95(self):
        data = self._mortgage_data(ltv=110)
        result = quality_consistency_check(data, {})
        assert result["Mortgage"]["LoanDetails"]["LTV"] == 95

    def test_ltv_under_10_set_to_60(self):
        data = self._mortgage_data(ltv=5)
        result = quality_consistency_check(data, {})
        assert result["Mortgage"]["LoanDetails"]["LTV"] == 60

    def test_interest_over_15_capped(self):
        data = self._mortgage_data(interest=20.0)
        result = quality_consistency_check(data, {})
        assert result["Mortgage"]["LoanDetails"]["InterestRate"] == 12.0

    def test_interest_under_1_raised(self):
        data = self._mortgage_data(interest=0.5)
        result = quality_consistency_check(data, {})
        assert result["Mortgage"]["LoanDetails"]["InterestRate"] == 2.0

    def test_valid_data_unchanged(self):
        data = self._mortgage_data(original=400000, current=350000, ltv=80, interest=4.5)
        result = quality_consistency_check(data, {})
        assert result["Mortgage"]["LoanDetails"]["CurrentBalance"] == 350000
        assert result["Mortgage"]["LoanDetails"]["LTV"] == 80
        assert result["Mortgage"]["LoanDetails"]["InterestRate"] == 4.5
