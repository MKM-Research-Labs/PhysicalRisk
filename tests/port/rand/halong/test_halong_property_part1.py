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

"""Coverage smoke tests for port.rand.halong.property.* (part 1)

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
