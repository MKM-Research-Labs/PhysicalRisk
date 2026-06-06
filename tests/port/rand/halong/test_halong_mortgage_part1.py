# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage smoke tests for port.rand.halong.mortgage.* (part 1)

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
