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

"""Tests for mortgage_random — integer and date value generators."""

import pytest
from port.rand.thames.mortgage.mortgage_random import (
    generate_integer_value,
    generate_date_value,
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
