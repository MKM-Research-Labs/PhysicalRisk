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

"""Coverage smoke tests for port.rand.halong.mortgage.* (part 2)

Halong mortgages use USD + 'halong' catchment ID — the only two lines
that distinguish them from the thames implementation. Tests exercise
every field-name branch in the per-type generators plus the high-level
generate_financial_data / quality_consistency_check entry points.
"""

import random

import pytest


@pytest.fixture(autouse=True)
def _seeded():
    random.seed(20260527)


# ---------------------------------------------------------------------------
# generators.py
# ---------------------------------------------------------------------------

@pytest.fixture
def financial_data():
    return {
        "property_value": 500_000, "loan_amount": 400_000,
        "outstanding_balance": 350_000, "ltv_ratio": 0.8, "current_ltv": 0.75,
        "interest_rate": 0.045, "monthly_payment": 1900,
        "borrower_income": 80_000, "annual_payment": 22_800,
        "term_months": 300, "months_elapsed": 24,
        "mortgage_type": "Residential", "is_defaulted": False,
        "is_in_arrears": False, "occupancy_type": "PrimaryResidence",
        "mortgage_id": "MORT-h00001", "property_id": "PROP-h001",
        "flood_risk": "Low",
    }


class TestMortgageMenuGenerator:
    @pytest.mark.parametrize("field", [
        "MortgageType", "OriginalRateType", "PaymentFrequency",
        "OccupancyType", "LoanPurpose", "RepaymentType",
        "ApplicationChannel",
    ])
    def test_known_fields_return_strings(self, field, financial_data):
        from port.rand.halong.mortgage.generators import generate_menu_value
        v = generate_menu_value(field, {}, 0, financial_data)
        assert isinstance(v, str) and v

    def test_btl_loan_purpose_path(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_menu_value
        financial_data["mortgage_type"] = "Buy-to-Let"
        v = generate_menu_value("LoanPurpose", {}, 0, financial_data)
        assert v in {"Purchase", "Refinancing"}

    def test_btl_repayment_path(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_menu_value
        financial_data["mortgage_type"] = "Buy-to-Let"
        v = generate_menu_value("RepaymentType", {}, 0, financial_data)
        assert v in {"Interest only", "Repayment", "Part and part"}

    def test_unknown_with_options(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_menu_value
        v = generate_menu_value("Unknown", {"options": ["a", "b"]}, 0, financial_data)
        assert v in {"a", "b"}

    def test_unknown_no_options_returns_empty(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_menu_value
        assert generate_menu_value("Unknown", {}, 0, financial_data) == ""


class TestMortgageBooleanGenerator:
    @pytest.mark.parametrize("field", [
        "DefaultFlag", "InArrearsFlag", "BusinessOrCommercialPurpose",
        "FirstTimeBuyerFlag", "AdvisedFlag", "ExecutionOnlyFlag",
        "MMRCompliantFlag", "StressTestCompliantFlag",
    ])
    def test_known_fields_return_bool(self, field, financial_data):
        from port.rand.halong.mortgage.generators import generate_boolean_value
        v = generate_boolean_value(field, financial_data)
        assert isinstance(v, bool)

    def test_btl_first_time_buyer_false(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_boolean_value
        financial_data["mortgage_type"] = "Buy-to-Let"
        assert generate_boolean_value("FirstTimeBuyerFlag", financial_data) is False

    def test_first_time_buyer_high_value_path(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_boolean_value
        financial_data["property_value"] = 1_000_000
        # Just exercise the >600k branch; outcome random.
        v = generate_boolean_value("FirstTimeBuyerFlag", financial_data)
        assert isinstance(v, bool)

    def test_unknown_field(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_boolean_value
        assert isinstance(generate_boolean_value("Mystery", financial_data), bool)


class TestMortgageDecimalGenerator:
    @pytest.mark.parametrize("field", [
        "PurchaseValue", "ApplicationPropertyValuation",
        "OriginalLoan", "OriginalLoanAmount",
        "OutstandingBalance", "CurrentBalance",
        "OriginalLTV", "CurrentLTV", "LTV", "LoanToValueRatio",
        "OriginalLendingRate", "CurrentLendingRate", "InterestRate",
        "CurrentPayment", "BorrowerIncome", "DebtToIncomeRatio",
        "APRCInitialRate", "APRCSecondaryRate",
    ])
    def test_known_fields_return_float(self, field, financial_data):
        from port.rand.halong.mortgage.generators import generate_decimal_value
        v = generate_decimal_value(field, financial_data)
        assert isinstance(v, (int, float))

    def test_dti_handles_zero_income(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_decimal_value
        financial_data["borrower_income"] = 0
        assert generate_decimal_value("DebtToIncomeRatio", financial_data) == 0.3

    def test_unknown_field_returns_float(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_decimal_value
        v = generate_decimal_value("Mystery", financial_data)
        assert isinstance(v, (int, float)) and v > 0


class TestMortgageIntegerGenerator:
    @pytest.mark.parametrize("field", [
        "OriginalTerm", "LoanTerm", "RemainingTerm", "TotalPayments",
        "BorrowerAge", "BorrowerCreditScore", "FamilyMembers",
        "NumberOfBorrowers", "DaysInArrears", "ArrearsMonths",
        "BehavioralScore", "PrepaymentRisk",
    ])
    def test_known_fields_return_int(self, field, financial_data):
        from port.rand.halong.mortgage.generators import generate_integer_value
        v = generate_integer_value(field, financial_data)
        assert isinstance(v, int)

    def test_defaulted_days_in_arrears(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_integer_value
        financial_data["is_defaulted"] = True
        assert generate_integer_value("DaysInArrears", financial_data) >= 90

    def test_in_arrears_days(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_integer_value
        financial_data["is_in_arrears"] = True
        assert 1 <= generate_integer_value("DaysInArrears", financial_data) <= 89

    def test_btl_age_range(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_integer_value
        financial_data["mortgage_type"] = "Buy-to-Let"
        assert 35 <= generate_integer_value("BorrowerAge", financial_data) <= 65

    def test_credit_score_branches(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_integer_value
        financial_data["interest_rate"] = 0.03  # low → 750-850
        assert 750 <= generate_integer_value("BorrowerCreditScore", financial_data) <= 850
        financial_data["interest_rate"] = 0.05
        financial_data["property_value"] = 700_000  # high → 700-800
        assert 700 <= generate_integer_value("BorrowerCreditScore", financial_data) <= 800
        financial_data["property_value"] = 300_000  # default → 650-750
        assert 650 <= generate_integer_value("BorrowerCreditScore", financial_data) <= 750


class TestMortgageDateGenerator:
    @pytest.mark.parametrize("field", [
        "ApplicationDate", "DisbursalDate", "MaturityDate",
    ])
    def test_known_date_fields_return_iso(self, field, financial_data):
        from datetime import datetime
        from port.rand.halong.mortgage.generators import generate_date_value
        s = generate_date_value(field, financial_data)
        datetime.strptime(s, "%Y-%m-%d")

    def test_default_date_returns_iso(self, financial_data):
        from datetime import datetime
        from port.rand.halong.mortgage.generators import generate_date_value
        s = generate_date_value("Mystery", financial_data)
        datetime.strptime(s, "%Y-%m-%d")

    def test_default_date_when_not_defaulted_is_none(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_date_value
        financial_data["is_defaulted"] = False
        assert generate_date_value("DefaultDate", financial_data) is None

    def test_default_date_when_defaulted(self, financial_data):
        from datetime import datetime
        from port.rand.halong.mortgage.generators import generate_date_value
        financial_data["is_defaulted"] = True
        s = generate_date_value("DefaultDate", financial_data)
        datetime.strptime(s, "%Y-%m-%d")


class TestMortgageTextGenerator:
    """CatchmentID and currency now come from config.CATCHMENT / config.CURRENCY
    (the active catchment) rather than a per-catchment hard-coded literal —
    the generator is shared across catchments."""

    def test_catchment_id_and_currency_delegate_to_config(self, financial_data):
        from config import config as cfg
        from port.rand.halong.mortgage.generators import generate_text_value
        assert generate_text_value("CatchmentID", 0, financial_data) == cfg.CATCHMENT
        assert generate_text_value("currency", 0, financial_data) == cfg.CURRENCY

    @pytest.mark.parametrize("field", [
        "MortgageID", "MortgageProvider", "MemberID", "UPRN", "PropertyID",
        "AccountStatus", "LatestStatus", "MaritalStatus", "FloodRiskCategory",
        "BorrowerEmployment", "EmploymentType",
    ])
    def test_known_text_fields_return_str(self, field, financial_data):
        from port.rand.halong.mortgage.generators import generate_text_value
        v = generate_text_value(field, 0, financial_data)
        assert isinstance(v, str) and v

    def test_defaulted_account_status(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_text_value
        financial_data["is_defaulted"] = True
        assert generate_text_value("AccountStatus", 0, financial_data) == "Default"
        assert generate_text_value("LatestStatus", 0, financial_data) == "Defaulted"

    def test_btl_employment_path(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_text_value
        financial_data["mortgage_type"] = "Buy-to-Let"
        assert generate_text_value("BorrowerEmployment", 0, financial_data) in {
            "Self-employed", "Employed", "Director", "Retired",
        }

    def test_young_marital_status(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_text_value
        financial_data["borrower_age"] = 25
        assert generate_text_value("MaritalStatus", 0, financial_data) in {
            "Single", "Married", "Civil Partnership",
        }

    def test_unknown_field_default(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_text_value
        v = generate_text_value("Mystery", 0, financial_data)
        assert v.startswith("Text-0-")


class TestMortgageFieldValueDispatch:
    @pytest.mark.parametrize("ftype,field", [
        ("text", "MortgageProvider"),
        ("decimal", "PurchaseValue"),
        ("integer", "FamilyMembers"),
        ("date", "ApplicationDate"),
        ("menu", "MortgageType"),
        ("boolean", "AdvisedFlag"),
    ])
    def test_dispatch_by_type(self, ftype, field, financial_data):
        from port.rand.halong.mortgage.generators import generate_field_value
        v = generate_field_value(field, {"type": ftype}, 0, financial_data)
        # Just verify dispatch produced something type-appropriate
        if ftype == "boolean":
            assert isinstance(v, bool)
        elif ftype == "integer":
            assert isinstance(v, int)
        elif ftype == "decimal":
            assert isinstance(v, (int, float))

    def test_non_dict_field_def_returns_literal(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_field_value
        assert generate_field_value("X", "lit", 0, financial_data) == "lit"
        assert generate_field_value("X", 42, 0, financial_data) == ""

    def test_unknown_type_returns_empty(self, financial_data):
        from port.rand.halong.mortgage.generators import generate_field_value
        assert generate_field_value("X", {"type": "mystery"}, 0, financial_data) == ""
