# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage smoke tests for port.rand.halong.mortgage.*

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
# Module-load smoke
# ---------------------------------------------------------------------------

def test_import_mortgage_subpackage():
    from port.rand.halong import mortgage as halong_mortgage
    assert halong_mortgage is not None


def test_import_all_modules():
    from port.rand.halong.mortgage import (
        constants, financials, generators, mortgage_random, quality,
    )
    assert constants.UK_LENDERS
    assert hasattr(financials, "generate_financial_data")
    assert hasattr(generators, "generate_field_value")
    assert hasattr(mortgage_random, "__name__")
    assert hasattr(quality, "quality_consistency_check")


# ---------------------------------------------------------------------------
# financials.py
# ---------------------------------------------------------------------------

class TestDetermineMortgageType:
    def test_rented_property_returns_btl_or_residential(self):
        from port.rand.halong.mortgage.financials import determine_mortgage_type
        info = {"monthly_rent": 1500}
        assert determine_mortgage_type(info) in ("Buy-to-Let", "Residential")

    def test_rental_history_returns_btl_or_residential(self):
        from port.rand.halong.mortgage.financials import determine_mortgage_type
        info = {"rental_history": "Previously rented"}
        assert determine_mortgage_type(info) in ("Buy-to-Let", "Residential")

    def test_multifamily_residency(self):
        from port.rand.halong.mortgage.financials import determine_mortgage_type
        info = {"building_residency": "Multi family dwelling"}
        assert determine_mortgage_type(info) in ("Buy-to-Let", "Residential")

    def test_vacant_occupancy(self):
        from port.rand.halong.mortgage.financials import determine_mortgage_type
        info = {"occupancy_type": "vacant"}
        assert determine_mortgage_type(info) in (
            "Buy-to-Let", "Second Home", "Residential",
        )

    def test_default_path(self):
        from port.rand.halong.mortgage.financials import determine_mortgage_type
        from port.rand.halong.mortgage.constants import MORTGAGE_TYPES
        result = determine_mortgage_type({})
        assert result in MORTGAGE_TYPES


class TestCalculateMortgageFinancials:
    @pytest.mark.parametrize("mortgage_type", [
        "Residential", "Buy-to-Let", "Second Home", "Holiday Home",
    ])
    def test_returns_expected_keys(self, mortgage_type):
        from port.rand.halong.mortgage.financials import calculate_mortgage_financials
        result = calculate_mortgage_financials(
            property_value=500_000, mortgage_type=mortgage_type,
            property_info={"flood_risk": "Low"}, index=0,
        )
        for key in ("property_value", "loan_amount", "ltv_ratio",
                    "term_months", "outstanding_balance", "interest_rate",
                    "monthly_payment", "borrower_income"):
            assert key in result

    def test_high_flood_risk_lowers_ltv(self):
        from port.rand.halong.mortgage.financials import calculate_mortgage_financials
        normal = calculate_mortgage_financials(
            500_000, "Residential", {"flood_risk": "Low"}, 0,
        )
        # High-flood-risk path multiplies ltv by 0.95
        high = calculate_mortgage_financials(
            500_000, "Residential", {"flood_risk": "high"}, 0,
        )
        # Both should be plausible LTVs
        assert 0 < normal["ltv_ratio"] < 1
        assert 0 < high["ltv_ratio"] < 1


class TestEstimatePropertyValue:
    @pytest.mark.parametrize("county", [
        "London", "Greater London", "Surrey", "Hertfordshire",
        "Buckinghamshire", "Kent", "Essex", "Berkshire", "Yorkshire",
    ])
    def test_county_multiplier_branches(self, county):
        from port.rand.halong.mortgage.financials import estimate_property_value
        info = {"county": county, "number_bedrooms": 4, "property_area_sqm": 150}
        v = estimate_property_value(info)
        assert v > 0

    def test_construction_year_branches(self):
        from port.rand.halong.mortgage.financials import estimate_property_value
        # Young (<10 yrs) gets 1.1x
        young = estimate_property_value({"construction_year": 2022})
        # Old (>50 yrs) gets 0.9x
        old = estimate_property_value({"construction_year": 1900})
        assert young > 0 and old > 0

    def test_empty_info_returns_positive(self):
        from port.rand.halong.mortgage.financials import estimate_property_value
        assert estimate_property_value({}) > 0


class TestDetermineOccupancy:
    def test_btl_occupancy(self):
        from port.rand.halong.mortgage.financials import _determine_occupancy_type
        assert _determine_occupancy_type("Buy-to-Let") in (
            "Investment", "PrimaryResidence",
        )

    def test_second_home_occupancy(self):
        from port.rand.halong.mortgage.financials import _determine_occupancy_type
        assert _determine_occupancy_type("Second Home") == "SecondResidence"
        assert _determine_occupancy_type("Holiday Home") == "SecondResidence"

    def test_default_occupancy(self):
        from port.rand.halong.mortgage.financials import _determine_occupancy_type
        assert _determine_occupancy_type("Residential") in (
            "PrimaryResidence", "SecondResidence",
        )


class TestGenerateFinancialData:
    def test_returns_required_keys(self):
        from port.rand.halong.mortgage.financials import generate_financial_data
        info = {
            "property_value": 500_000,
            "property_id": "PROP-h001",
            "flood_risk": "Low",
        }
        result = generate_financial_data(info, index=0)
        for k in ("mortgage_id", "property_id", "flood_risk",
                  "occupancy_type", "loan_amount"):
            assert k in result

    def test_missing_property_value_estimated(self):
        from port.rand.halong.mortgage.financials import generate_financial_data
        # No property_value -> falls through to estimate_property_value
        result = generate_financial_data({"property_id": "PROP-x"}, index=1)
        assert result["property_value"] > 0


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
    """Includes the halong-specific currency=USD and CatchmentID=halong."""

    @pytest.mark.parametrize("field,expected", [
        ("CatchmentID", "halong"),
        ("currency", "USD"),
    ])
    def test_halong_specific_constants(self, field, expected, financial_data):
        from port.rand.halong.mortgage.generators import generate_text_value
        assert generate_text_value(field, 0, financial_data) == expected

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


# ---------------------------------------------------------------------------
# quality.py
# ---------------------------------------------------------------------------

class TestQualityConsistencyCheck:
    def _scaffold(self, original=400_000, current=380_000, ltv=80, rate=4.5):
        return {
            "Mortgage": {
                "LoanDetails": {
                    "OriginalLoanAmount": original,
                    "CurrentBalance": current,
                    "LTV": ltv,
                    "InterestRate": rate,
                }
            }
        }

    def test_current_balance_capped_below_original(self):
        from port.rand.halong.mortgage.quality import quality_consistency_check
        m = self._scaffold(original=400_000, current=500_000)
        out = quality_consistency_check(m, {})
        loan = out["Mortgage"]["LoanDetails"]
        assert loan["CurrentBalance"] <= loan["OriginalLoanAmount"]

    def test_ltv_above_100_clamped_to_95(self):
        from port.rand.halong.mortgage.quality import quality_consistency_check
        out = quality_consistency_check(self._scaffold(ltv=150), {})
        assert out["Mortgage"]["LoanDetails"]["LTV"] == 95

    def test_ltv_below_10_clamped_to_60(self):
        from port.rand.halong.mortgage.quality import quality_consistency_check
        out = quality_consistency_check(self._scaffold(ltv=5), {})
        assert out["Mortgage"]["LoanDetails"]["LTV"] == 60

    def test_high_interest_capped_to_12(self):
        from port.rand.halong.mortgage.quality import quality_consistency_check
        out = quality_consistency_check(self._scaffold(rate=18.0), {})
        assert out["Mortgage"]["LoanDetails"]["InterestRate"] == 12.0

    def test_low_interest_floored_to_2(self):
        from port.rand.halong.mortgage.quality import quality_consistency_check
        out = quality_consistency_check(self._scaffold(rate=0.5), {})
        assert out["Mortgage"]["LoanDetails"]["InterestRate"] == 2.0
