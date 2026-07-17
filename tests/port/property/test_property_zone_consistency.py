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

"""Tests for EA flood zone elevation boundary configuration and consistency."""

import math
import random
from unittest.mock import MagicMock

import pytest

from config.port import EA_FLOOD_ZONE_ELEVATION_BOUNDS


class TestZoneElevationBoundsConfig:
    """Verify EA_FLOOD_ZONE_ELEVATION_BOUNDS structure and contiguity."""

    EXPECTED_ZONES = ['Zone 3b', 'Zone 3a', 'Zone 2', 'Zone 1']

    def test_has_four_zones(self):
        assert set(EA_FLOOD_ZONE_ELEVATION_BOUNDS.keys()) == set(self.EXPECTED_ZONES)

    def test_zone_3b_unbounded_below(self):
        # Zone 3b (functional floodplain) extends to/below river level: its
        # lower bound is None (unbounded), so a property at or below the river
        # classifies as 3b rather than falling through to Zone 1.
        lo, _ = EA_FLOOD_ZONE_ELEVATION_BOUNDS['Zone 3b']
        assert lo is None

    def test_zone_1_has_no_upper_bound(self):
        _, hi = EA_FLOOD_ZONE_ELEVATION_BOUNDS['Zone 1']
        assert hi is None

    def test_bounds_are_contiguous(self):
        """Upper bound of each zone == lower bound of the next."""
        ordered = self.EXPECTED_ZONES  # 3b, 3a, 2, 1 (risk descending)
        for i in range(len(ordered) - 1):
            _, hi = EA_FLOOD_ZONE_ELEVATION_BOUNDS[ordered[i]]
            lo, _ = EA_FLOOD_ZONE_ELEVATION_BOUNDS[ordered[i + 1]]
            assert hi == lo, (
                f"{ordered[i]} upper={hi} != {ordered[i+1]} lower={lo}"
            )

    def test_lower_bounds_strictly_increasing(self):
        ordered = self.EXPECTED_ZONES
        # Zone 3b's lower bound is None (unbounded below); treat it as -inf so
        # the remaining finite lower bounds must still strictly increase.
        lowers = [
            EA_FLOOD_ZONE_ELEVATION_BOUNDS[z][0] if EA_FLOOD_ZONE_ELEVATION_BOUNDS[z][0] is not None
            else float('-inf')
            for z in ordered
        ]
        for i in range(len(lowers) - 1):
            assert lowers[i] < lowers[i + 1], (
                f"Lower bounds not increasing: {ordered[i]}={lowers[i]} >= "
                f"{ordered[i+1]}={lowers[i+1]}"
            )

    @pytest.mark.parametrize("zone", EXPECTED_ZONES)
    def test_lower_bound_non_negative_or_unbounded(self, zone):
        # A finite lower bound must be non-negative; Zone 3b's is None
        # (unbounded below), which is allowed.
        lo, _ = EA_FLOOD_ZONE_ELEVATION_BOUNDS[zone]
        assert lo is None or lo >= 0.0

    @pytest.mark.parametrize("zone", ['Zone 3b', 'Zone 3a', 'Zone 2'])
    def test_bounded_zones_have_finite_upper(self, zone):
        _, hi = EA_FLOOD_ZONE_ELEVATION_BOUNDS[zone]
        assert hi is not None
        assert hi > 0


class TestLocationVerticalOffset:
    """Verify that vertical_offset is present in generated locations."""

    def test_vertical_offset_in_location_dict(self):
        """Generated locations must include vertical_offset."""
        from port.src.property.main.locations import LocationsMixin

        class FakeGen(LocationsMixin):
            def __init__(self):
                self.params = MagicMock()
                self.params.CENTER_LAT = 51.5
                self.params.CENTER_LON = -0.1
                self.params.MIN_OFFSET_M = 100
                self.params.MAX_OFFSET_M = 2000

            def log(self, msg, level="INFO"):
                pass

        gen = FakeGen()
        # Use the fallback which is simpler to test
        locs = gen._generate_locations_fallback(
            10, ['TestArea'], {'TestArea': 1.0}, {})
        for loc in locs:
            assert 'vertical_offset' in loc, "vertical_offset missing from location"
            assert loc['vertical_offset'] >= 0.0


class TestEAZoneFromElevation:
    """Verify zone assignment is derived correctly from vertical offset."""

    def test_zone_3b_at_zero_offset(self):
        from port.rand.thames.property.property_random import _ea_zone_from_elevation
        assert _ea_zone_from_elevation({'vertical_offset': 0.0}) == 'Zone 3b'

    def test_zone_3b_at_049(self):
        from port.rand.thames.property.property_random import _ea_zone_from_elevation
        assert _ea_zone_from_elevation({'vertical_offset': 0.49}) == 'Zone 3b'

    def test_zone_3a_at_05(self):
        from port.rand.thames.property.property_random import _ea_zone_from_elevation
        assert _ea_zone_from_elevation({'vertical_offset': 0.5}) == 'Zone 3a'

    def test_zone_3a_at_14(self):
        from port.rand.thames.property.property_random import _ea_zone_from_elevation
        assert _ea_zone_from_elevation({'vertical_offset': 1.4}) == 'Zone 3a'

    def test_zone_2_at_15(self):
        from port.rand.thames.property.property_random import _ea_zone_from_elevation
        assert _ea_zone_from_elevation({'vertical_offset': 1.5}) == 'Zone 2'

    def test_zone_2_at_29(self):
        from port.rand.thames.property.property_random import _ea_zone_from_elevation
        assert _ea_zone_from_elevation({'vertical_offset': 2.9}) == 'Zone 2'

    def test_zone_1_at_30(self):
        from port.rand.thames.property.property_random import _ea_zone_from_elevation
        assert _ea_zone_from_elevation({'vertical_offset': 3.0}) == 'Zone 1'

    def test_zone_1_at_large_offset(self):
        from port.rand.thames.property.property_random import _ea_zone_from_elevation
        assert _ea_zone_from_elevation({'vertical_offset': 50.0}) == 'Zone 1'

    def test_missing_offset_defaults_to_zone_1(self):
        from port.rand.thames.property.property_random import _ea_zone_from_elevation
        assert _ea_zone_from_elevation({}) == 'Zone 1'

    def test_field_generator_uses_elevation_function(self):
        """The EAFloodZone field generator should use _ea_zone_from_elevation."""
        from port.rand.thames.property.property_random import get_field_generators
        generators = get_field_generators()
        # Zone 3b property
        result = generators['EAFloodZone']({'vertical_offset': 0.2})
        assert result == 'Zone 3b'
        # Zone 1 property
        result = generators['EAFloodZone']({'vertical_offset': 5.0})
        assert result == 'Zone 1'

    @pytest.mark.parametrize("offset,expected_zone", [
        (0.0, 'Zone 3b'), (0.25, 'Zone 3b'),
        (0.5, 'Zone 3a'), (1.0, 'Zone 3a'),
        (1.5, 'Zone 2'), (2.5, 'Zone 2'),
        (3.0, 'Zone 1'), (10.0, 'Zone 1'),
    ])
    def test_boundary_parametrized(self, offset, expected_zone):
        from port.rand.thames.property.property_random import _ea_zone_from_elevation
        assert _ea_zone_from_elevation({'vertical_offset': offset}) == expected_zone
