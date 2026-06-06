# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage smoke tests for port.rand.halong.property.* (part 2)

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
