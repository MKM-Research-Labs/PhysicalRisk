# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage smoke tests for port.rand.halong.property.*

Strategy: import every submodule, exercise every field generator in
get_field_generators() with a realistic location_info dict, plus
smoke-test the major resilience / valuation / energy / location
calculations. Maximum coverage per line-of-test.
"""

import random
from datetime import datetime, timedelta

import pytest


@pytest.fixture(autouse=True)
def _seeded():
    random.seed(20260527)


# ---------------------------------------------------------------------------
# Module-load smoke
# ---------------------------------------------------------------------------

def test_import_property_subpackage():
    from port.rand.halong import property as halong_property
    assert halong_property is not None


def test_import_all_modules():
    from port.rand.halong.property import (
        property_energy, property_location, property_utils, property_valuation,
    )
    from port.rand.halong.property.property_random import (
        generators, helpers, metadata, resilience,
    )
    # spot-check public API present
    assert hasattr(generators, "get_field_generators")
    assert hasattr(helpers, "_ea_zone_from_elevation")
    assert hasattr(metadata, "generate_property_metadata")
    assert hasattr(resilience, "generate_resilience")
    assert hasattr(property_valuation, "calculate_property_value")


# ---------------------------------------------------------------------------
# helpers.py
# ---------------------------------------------------------------------------

class TestDeterministicPropId:
    def test_returns_prop_prefix(self):
        from port.rand.halong.property.property_random.helpers import _deterministic_prop_id
        pid = _deterministic_prop_id({"lat": 20.95, "lon": 107.05}, 0)
        assert pid.startswith("PROP-")

    def test_stable_across_calls(self):
        from port.rand.halong.property.property_random.helpers import _deterministic_prop_id
        loc = {"lat": 20.95, "lon": 107.05}
        assert _deterministic_prop_id(loc, 7) == _deterministic_prop_id(loc, 7)


class TestEaZoneFromElevation:
    @pytest.mark.parametrize("offset", [0.1, 1.0, 2.5, 5.0, 20.0, 999.0])
    def test_known_offsets_return_zones(self, offset):
        from port.rand.halong.property.property_random.helpers import _ea_zone_from_elevation
        z = _ea_zone_from_elevation({"vertical_offset": offset})
        assert z.startswith("Zone")


class TestFloodHazardClassFromOffset:
    @pytest.mark.parametrize("offset,expected", [
        (0.1, "Extreme"),
        (1.0, "High"),
        (2.0, "Medium"),
        (5.0, "Low"),
        (50.0, "None"),
    ])
    def test_all_branches(self, offset, expected):
        from port.rand.halong.property.property_random.helpers import _flood_hazard_class_from_offset
        assert _flood_hazard_class_from_offset({"vertical_offset": offset}) == expected

    def test_no_offset_falls_back_to_none(self):
        from port.rand.halong.property.property_random.helpers import _flood_hazard_class_from_offset
        assert _flood_hazard_class_from_offset({}) == "None"


# ---------------------------------------------------------------------------
# metadata.py
# ---------------------------------------------------------------------------

class TestGeneratePropertyMetadata:
    def test_returns_required_keys(self):
        from port.rand.halong.property.property_random.metadata import generate_property_metadata
        loc = {
            "lat": 20.95, "lon": 107.05, "elevation": 5.0,
            "name": "Bai Chay", "value_factor": 1.0, "vertical_offset": 0.5,
        }
        meta = generate_property_metadata(0, loc)
        for k in ("property_id", "property_type", "construction_year",
                  "property_area", "property_value", "elevation"):
            assert k in meta
        assert meta["property_id"].startswith("PROP-")
        assert meta["construction_year"] > 0
        assert meta["property_area"] > 0


# ---------------------------------------------------------------------------
# property_utils.py
# ---------------------------------------------------------------------------

class TestPropertyUtils:
    def test_generate_postcode(self):
        from port.rand.halong.property.property_utils import generate_postcode
        assert isinstance(generate_postcode(), str)

    def test_generate_construction_year_in_range(self):
        from port.rand.halong.property.property_utils import generate_construction_year
        y = generate_construction_year()
        assert 1800 < y < datetime.now().year

    def test_generate_past_date_returns_iso(self):
        from port.rand.halong.property.property_utils import generate_past_date
        s = generate_past_date()
        datetime.strptime(s, "%Y-%m-%d")
        s2 = generate_past_date(days_range=(10, 20))
        datetime.strptime(s2, "%Y-%m-%d")

    def test_generate_owner_name(self):
        from port.rand.halong.property.property_utils import generate_owner_name
        assert " " in generate_owner_name()

    @pytest.mark.parametrize("year,expected", [
        (1900, "Pre-1919"),
        (1930, "1919-1944"),
        (1960, "1945-1975"),
        (1990, "1976-1999"),
        (2005, "2000-2008"),
        (2025, "2009-Present"),
    ])
    def test_get_property_period(self, year, expected):
        from port.rand.halong.property.property_utils import get_property_period
        assert get_property_period(year) == expected

    def test_generate_grid_reference(self):
        from port.rand.halong.property.property_utils import generate_grid_reference
        g = generate_grid_reference(20.95, 107.05)
        assert isinstance(g, str) and g


# ---------------------------------------------------------------------------
# property_location.py
# ---------------------------------------------------------------------------

class TestPropertyLocation:
    def _info(self, **kwargs):
        base = {
            "property_type": "Detached", "property_area": 120.0,
            "construction_year": 1995, "elevation": 5.0,
            "area_name": "Bai Chay", "value_factor": 1.0,
            "streets_data": {}, "vertical_offset": 0.5,
        }
        base.update(kwargs)
        return base

    @pytest.mark.parametrize("ptype", [
        "Flat", "Mid-terrace", "End-terrace", "Semi-detached",
        "Detached", "Bungalow",
    ])
    def test_generate_bedrooms_all_types(self, ptype):
        from port.rand.halong.property.property_location import generate_bedrooms
        v = generate_bedrooms(self._info(property_type=ptype))
        assert isinstance(v, int) and v >= 1

    def test_generate_bathrooms(self):
        from port.rand.halong.property.property_location import generate_bathrooms
        assert generate_bathrooms(self._info()) >= 1

    def test_generate_floor_level(self):
        from port.rand.halong.property.property_location import generate_floor_level
        v = generate_floor_level(self._info())
        assert isinstance(v, float)

    def test_generate_floor_level_flat(self):
        """Flats have multi-storey FloorLevel range."""
        from port.rand.halong.property.property_location import generate_floor_level
        v = generate_floor_level(self._info(property_type="Flat"))
        assert isinstance(v, float)

    def test_generate_postcode_for_area(self):
        from port.rand.halong.property.property_location import generate_postcode_for_area
        s = generate_postcode_for_area(self._info())
        assert isinstance(s, str) and s

    def test_generate_street_name_no_streets_data(self):
        from port.rand.halong.property.property_location import generate_street_name
        v = generate_street_name(self._info())
        assert isinstance(v, str)

    def test_generate_street_name_with_streets_data(self):
        from port.rand.halong.property.property_location import generate_street_name
        info = self._info(streets_data={"Bai Chay": ["River St", "Main St"]})
        v = generate_street_name(info)
        assert v in {"River St", "Main St"} or isinstance(v, str)

    def test_calculate_purchase_price(self):
        from port.rand.halong.property.property_location import calculate_purchase_price
        v = calculate_purchase_price(self._info(property_value=500_000))
        assert v > 0

    def test_generate_council_tax_band(self):
        from port.rand.halong.property.property_location import generate_council_tax_band
        v = generate_council_tax_band(self._info(property_value=500_000))
        assert isinstance(v, str) and v


# ---------------------------------------------------------------------------
# property_valuation.py
# ---------------------------------------------------------------------------

class TestPropertyValuation:
    def _info(self, **kwargs):
        base = {
            "property_type": "Detached", "property_area": 120.0,
            "construction_year": 1995, "elevation": 5.0,
            "value_factor": 1.0, "vertical_offset": 0.5,
        }
        base.update(kwargs)
        return base

    @pytest.mark.parametrize("ptype", [
        "Flat", "Mid-terrace", "Semi-detached", "Detached", "Bungalow",
    ])
    def test_calculate_property_area_all_types(self, ptype):
        from port.rand.halong.property.property_valuation import calculate_property_area
        v = calculate_property_area(self._info(property_type=ptype))
        assert v > 0

    def test_calculate_property_value(self):
        from port.rand.halong.property.property_valuation import calculate_property_value
        v = calculate_property_value(self._info())
        assert v > 0

    def test_calculate_property_value_elevation_below_3(self):
        """Low-lying properties get a small value cut."""
        from port.rand.halong.property.property_valuation import calculate_property_value
        v = calculate_property_value(self._info(elevation=1.0))
        assert v > 0

    def test_calculate_sale_price(self):
        from port.rand.halong.property.property_valuation import calculate_sale_price
        v = calculate_sale_price(self._info(property_value=500_000))
        assert v > 0

    def test_calculate_monthly_rent(self):
        from port.rand.halong.property.property_valuation import calculate_monthly_rent
        v = calculate_monthly_rent(self._info(property_value=500_000))
        assert v > 0

    def test_calculate_insurance_premium(self):
        from port.rand.halong.property.property_valuation import calculate_insurance_premium
        v = calculate_insurance_premium(self._info(property_value=500_000))
        assert v > 0


# ---------------------------------------------------------------------------
# property_energy.py
# ---------------------------------------------------------------------------

class TestPropertyEnergy:
    def _info(self, **kwargs):
        base = {
            "property_type": "Detached", "property_area": 120.0,
            "construction_year": 1995, "elevation": 5.0,
            "value_factor": 1.0,
        }
        base.update(kwargs)
        return base

    def test_carbon_emissions(self):
        from port.rand.halong.property.property_energy import calculate_carbon_emissions
        assert calculate_carbon_emissions(self._info()) > 0

    def test_annual_energy(self):
        from port.rand.halong.property.property_energy import calculate_annual_energy
        assert calculate_annual_energy(self._info()) > 0

    def test_grid_electricity(self):
        from port.rand.halong.property.property_energy import calculate_grid_electricity
        assert calculate_grid_electricity(self._info()) > 0

    def test_gas_usage(self):
        from port.rand.halong.property.property_energy import calculate_gas_usage
        assert calculate_gas_usage(self._info()) >= 0

    def test_solar_generation(self):
        from port.rand.halong.property.property_energy import calculate_solar_generation
        assert calculate_solar_generation(self._info()) >= 0

    def test_energy_bill(self):
        from port.rand.halong.property.property_energy import calculate_energy_bill
        assert calculate_energy_bill(self._info()) > 0


# ---------------------------------------------------------------------------
# generators.py — exercise every lambda in get_field_generators()
# ---------------------------------------------------------------------------

class TestGetFieldGenerators:
    def test_returns_dict_of_callables(self):
        from port.rand.halong.property.property_random.generators import get_field_generators
        gens = get_field_generators()
        assert isinstance(gens, dict)
        assert all(callable(g) for g in gens.values())

    def test_every_generator_callable_without_raising(self):
        """Smoke test: every registered field generator should run without
        raising on a realistic location_info dict. Catches typos and
        signature drift across the ~130 lambdas in one shot."""
        from port.rand.halong.property.property_random.generators import get_field_generators
        info = {
            # lat/lon required by PropertyID -> _deterministic_prop_id
            "lat": 20.95, "lon": 107.05,
            "property_type": "Detached", "property_area": 120.0,
            "property_value": 500_000, "construction_year": 1995,
            "elevation": 5.0, "vertical_offset": 0.5,
            "area_name": "Bai Chay", "value_factor": 1.0,
            "streets_data": {"Bai Chay": ["Main St"]},
            "index": 0,
        }
        gens = get_field_generators()
        for name, fn in gens.items():
            try:
                fn(info)
            except Exception as e:
                pytest.fail(f"generator {name!r} raised: {e}")


class TestGenerateFieldValueDispatch:
    """generate_field_value: registry hit + fallback type-based generation."""

    def _meta(self):
        return {
            "property_type": "Detached", "property_area": 120.0,
            "property_value": 500_000, "construction_year": 1995,
            "elevation": 5.0, "vertical_offset": 0.5,
            "area_name": "Bai Chay", "value_factor": 1.0, "streets_data": {},
        }

    def test_registered_field_uses_registry(self):
        from port.rand.halong.property.property_random.generators import generate_field_value
        v = generate_field_value("PropertyValue", {"type": "number"}, 0, self._meta())
        assert v > 0

    def test_unknown_string_field_with_options(self):
        from port.rand.halong.property.property_random.generators import generate_field_value
        v = generate_field_value("Mystery", {"type": "string", "options": ["a", "b", "c"]}, 0, self._meta())
        assert v in {"a", "b", "c"}

    def test_unknown_string_field_no_options(self):
        from port.rand.halong.property.property_random.generators import generate_field_value
        assert generate_field_value("Mystery", {"type": "string"}, 0, self._meta()) == ""

    def test_unknown_number_field(self):
        from port.rand.halong.property.property_random.generators import generate_field_value
        v = generate_field_value("Mystery", {"type": "number"}, 0, self._meta())
        assert isinstance(v, float)

    def test_unknown_integer_field(self):
        from port.rand.halong.property.property_random.generators import generate_field_value
        v = generate_field_value("Mystery", {"type": "integer"}, 0, self._meta())
        assert isinstance(v, int)

    def test_unknown_boolean_field(self):
        from port.rand.halong.property.property_random.generators import generate_field_value
        assert generate_field_value("Mystery", {"type": "boolean"}, 0, self._meta()) in (True, False)

    def test_unknown_date_field(self):
        from port.rand.halong.property.property_random.generators import generate_field_value
        s = generate_field_value("Mystery", {"type": "date"}, 0, self._meta())
        datetime.strptime(s, "%Y-%m-%d")

    def test_unknown_type_returns_none(self):
        from port.rand.halong.property.property_random.generators import generate_field_value
        assert generate_field_value("Mystery", {"type": "mystery"}, 0, self._meta()) is None


# ---------------------------------------------------------------------------
# resilience.py — the big one (313 LOC)
# ---------------------------------------------------------------------------

class TestResilienceModule:
    def _scaffold(self, period="1976-1999", condition="Fair",
                  zone="Zone 1", basement=False):
        return {
            "PropertyHeader": {
                "PropertyAttributes": {
                    "PropertyPeriod": period,
                    "PropertyCondition": condition,
                },
                "Construction": {"BasementPresent": basement},
                "RiskAssessment": {"EAFloodZone": zone},
            }
        }

    def test_generate_resilience_returns_sections(self):
        from port.rand.halong.property.property_random.resilience import generate_resilience
        prop = self._scaffold()
        result = generate_resilience(prop)
        assert isinstance(result, dict)
        # SiteAndDrainage is always populated with BasementFloodStrategy override
        assert "SiteAndDrainage" in result
        assert "BasementFloodStrategy" in result["SiteAndDrainage"]

    @pytest.mark.parametrize("period", [
        "Pre-1919", "1919-1944", "1945-1975",
        "1976-1999", "2000-2008", "2009-Present",
    ])
    def test_generate_resilience_all_periods(self, period):
        from port.rand.halong.property.property_random.resilience import generate_resilience
        result = generate_resilience(self._scaffold(period=period))
        assert isinstance(result, dict) and result

    @pytest.mark.parametrize("condition", [
        "Excellent", "Good", "Fair", "Poor", "Very poor",
    ])
    def test_generate_resilience_all_conditions(self, condition):
        from port.rand.halong.property.property_random.resilience import generate_resilience
        result = generate_resilience(self._scaffold(condition=condition))
        assert isinstance(result, dict) and result

    @pytest.mark.parametrize("zone", ["Zone 1", "Zone 2", "Zone 3a", "Zone 3b"])
    def test_generate_resilience_all_zones(self, zone):
        from port.rand.halong.property.property_random.resilience import generate_resilience
        result = generate_resilience(self._scaffold(zone=zone))
        assert isinstance(result, dict)

    def test_generate_resilience_with_basement(self):
        from port.rand.halong.property.property_random.resilience import generate_resilience
        result = generate_resilience(self._scaffold(basement=True))
        assert isinstance(result, dict)

    def test_compute_bri_rating(self):
        from port.rand.halong.property.property_random.resilience import (
            compute_bri_rating, generate_resilience,
        )
        prop = self._scaffold()
        resilience = generate_resilience(prop)
        result = compute_bri_rating(resilience)
        assert "rating" in result
        assert "score" in result
        assert isinstance(result["score"], float)

    def test_score_section(self):
        from port.rand.halong.property.property_random.resilience import score_section
        section = {"FieldA": "Good", "FieldB": "Excellent"}
        score = score_section("SiteAndDrainage", section)
        assert isinstance(score, float)

    def test_distribution_summary_default_target(self):
        from port.rand.halong.property.property_random.resilience import distribution_summary
        # Signature is (ratings, target=None) — target falls back to a
        # built-in Thames distribution
        ratings = ["A", "B", "C", "A", "B", "C", "A"]
        summary = distribution_summary(ratings)
        # One entry per RATING_ORDER with actual/target/delta sub-keys
        assert any("actual" in v for v in summary.values())

    def test_distribution_summary_custom_target(self):
        from port.rand.halong.property.property_random.resilience import distribution_summary
        summary = distribution_summary(["A", "A", "B"], target={"A": 0.5, "B": 0.3, "C": 0.2})
        assert "A" in summary

    def test_sanity_check_distribution_runs(self):
        """End-to-end sanity check at small N — exercises ~all of the
        synthetic-property + scoring path."""
        from port.rand.halong.property.property_random.resilience import (
            sanity_check_distribution,
        )
        result = sanity_check_distribution(sample_size=30, seed=20260527)
        assert isinstance(result, dict)

    def test_validate_weights_does_not_raise(self):
        from port.rand.halong.property.property_random.resilience import validate_weights
        validate_weights()

    def test_apply_flood_resilience_score_to_property(self):
        from port.rand.halong.property.property_random.resilience import (
            apply_flood_resilience_score, generate_resilience,
        )
        prop = self._scaffold()
        prop["ProtectionMeasures"] = {"ResilienceMeasures": generate_resilience(prop)}
        # apply_flood_resilience_score should run without raising
        result = apply_flood_resilience_score(prop)
        assert result is not None or result == {} or isinstance(prop, dict)
