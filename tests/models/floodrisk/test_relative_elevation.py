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

"""Unit tests for models.floodrisk.relative_elevation.

The relative_elevation function is the single source of truth for
computing the effective elevation of a property above its reference
gauge.  It is used by:
  - flood propagation (propagation.py)
  - compound hydrograph construction (compound.py)
  - REIT portfolio blotter (_load_property_details)
"""

import pytest

from models.floodrisk import relative_elevation


class TestBasicCalculation:
    """Core formula: max(0, prop - gauge) + floor."""

    def test_property_above_gauge(self):
        assert relative_elevation(10.0, 5.0) == 5.0

    def test_property_below_gauge_clamps_to_zero(self):
        assert relative_elevation(5.0, 10.0) == 0.0

    def test_property_at_gauge_level(self):
        assert relative_elevation(8.0, 8.0) == 0.0

    def test_floor_level_additive(self):
        assert relative_elevation(10.0, 5.0, 0.5) == 5.5

    def test_floor_on_lower_property(self):
        """Even if prop < gauge, the floor still lifts the threshold."""
        assert relative_elevation(5.0, 10.0, 0.3) == 0.3

    def test_zero_floor_is_default(self):
        assert relative_elevation(10.0, 5.0) == relative_elevation(10.0, 5.0, 0.0)


class TestEdgeCases:

    def test_all_zeros(self):
        assert relative_elevation(0.0, 0.0, 0.0) == 0.0

    def test_very_small_difference(self):
        result = relative_elevation(10.001, 10.0, 0.0)
        assert result == pytest.approx(0.001, abs=1e-10)

    def test_large_elevation_difference(self):
        assert relative_elevation(500.0, 10.0, 0.0) == 490.0

    def test_large_floor(self):
        assert relative_elevation(10.0, 10.0, 3.5) == 3.5


class TestConsistencyWithPRSPricer:
    """Verify the formula matches the inline calculations previously used
    in propagation.py and compound.py."""

    @pytest.mark.parametrize("prop_elev, gauge_elev, floor, expected", [
        # Property well above gauge
        (14.23, 12.2, 0.03, 2.06),
        # Property barely above gauge
        (8.05, 7.6, 0.07, 0.52),
        # Moderate difference with real floor
        (5.62, 4.3, 0.44, 1.76),
        # Property below gauge
        (3.0, 5.0, 0.2, 0.2),
    ])
    def test_matches_inline_formula(self, prop_elev, gauge_elev, floor, expected):
        """These values come from real Thames portfolio properties."""
        inline = max(0.0, prop_elev - gauge_elev) + floor
        result = relative_elevation(prop_elev, gauge_elev, floor)
        assert result == pytest.approx(inline, abs=1e-10)
        assert result == pytest.approx(expected, abs=0.01)


class TestReturnType:

    def test_returns_float(self):
        result = relative_elevation(10.0, 5.0, 0.5)
        assert isinstance(result, float)

    def test_integer_inputs_return_float(self):
        result = relative_elevation(10, 5, 0)
        assert isinstance(result, (int, float))
        assert result == 5.0
