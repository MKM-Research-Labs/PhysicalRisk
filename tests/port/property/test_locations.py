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

"""
Tests for PropertyPortfolioGenerator location generation:
  _generate_locations, _generate_locations_fallback.
"""

from unittest.mock import MagicMock

import pytest

from port.src.property.main import PropertyPortfolioGenerator
from db_helpers import tmp_catchment

from .conftest import GAUGE_POINTS, make_portfolio_gen, make_portfolio_params


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend (catchment "thames") for every test in this module.

    ``_generate_locations`` reads synthetic gauges via ``database.get_gauge_portfolio``;
    rooting the backend at ``tmp_path`` keeps those reads off real data and lets a test
    pre-write ``tmp_path / 'gauge.json'`` when it needs synthetic gauges."""
    with tmp_catchment(tmp_path):
        yield


# ===========================================================================
# _generate_locations -- triangle construction
# ===========================================================================

class TestGenerateLocations:

    def test_returns_correct_count(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        locs = gen._generate_locations(10)
        assert len(locs) == 10

    def test_each_location_has_required_keys(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        locs = gen._generate_locations(5)
        for loc in locs:
            assert "lat" in loc
            assert "lon" in loc
            assert "name" in loc
            assert "elevation" in loc
            assert "value_factor" in loc
            assert "reference_gauge_indices" in loc

    def test_elevation_is_non_negative(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        locs = gen._generate_locations(10)
        for loc in locs:
            assert loc["elevation"] >= 0

    def test_reference_gauge_indices_sorted(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        locs = gen._generate_locations(10)
        for loc in locs:
            idxs = loc["reference_gauge_indices"]
            assert idxs == sorted(idxs)

    def test_reference_gauge_indices_three_elements(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        locs = gen._generate_locations(10)
        for loc in locs:
            assert len(loc["reference_gauge_indices"]) == 3

    def test_primary_idx_zero_uses_gauges_012(self, tmp_path):
        """When primary_idx == 0, triangle is gauges 0, 1, 2 -> sorted [0,1,2]."""
        gen = make_portfolio_gen(tmp_path, gauge_points=GAUGE_POINTS)
        locs = gen._generate_locations(1)
        ref = locs[0]["reference_gauge_indices"]
        assert set(ref) == {0, 1, 2}

    def test_fallback_used_when_fewer_than_3_gauge_points(self, tmp_path):
        """With < 3 gauge points, fallback generator is called."""
        params = make_portfolio_params(gauge_points=[(51.5, -0.1, 5.0)])
        gen = PropertyPortfolioGenerator(verbose=False,
                                          catchment_params=params)
        locs = gen._generate_locations(3)
        assert len(locs) == 3

    def test_fallback_used_when_no_gauge_points(self, tmp_path):
        params = make_portfolio_params(gauge_points=None)
        params.GAUGE_POINTS = None
        gen = PropertyPortfolioGenerator(verbose=False,
                                          catchment_params=params)
        locs = gen._generate_locations(3)
        assert len(locs) == 3


# ===========================================================================
# _generate_locations_fallback -- missing get_elevation attribute
# ===========================================================================

class TestGenerateLocationsFallbackNoElevation:

    def test_fallback_without_get_elevation_uses_random(self, tmp_path):
        """When params has no get_elevation, elevation is sampled from
        uniform(2, 30)."""
        params = MagicMock()
        params.AREAS = ["A", "B"]
        params.AREA_VALUE_FACTORS = {}
        params.STREETS = {}
        params.CENTER_LAT = 51.5
        params.CENTER_LON = -0.1
        params.GAUGE_POINTS = None
        params.GAUGEPOINTS = None
        # Remove get_elevation to trigger the else-branch
        del params.get_elevation
        gen = PropertyPortfolioGenerator(verbose=False,
                                          catchment_params=params)
        locs = gen._generate_locations_fallback(5, ["A", "B"], {}, {})
        assert len(locs) == 5
        for loc in locs:
            assert 0 <= loc["elevation"] <= 40  # generous bounds
