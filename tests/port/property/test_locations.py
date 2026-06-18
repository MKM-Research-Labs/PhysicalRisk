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

"""
Tests for PropertyPortfolioGenerator location generation:
  _generate_locations, _generate_locations_fallback.
"""

from unittest.mock import MagicMock

import pytest

from port.src.property.main import PropertyPortfolioGenerator

from .conftest import GAUGE_POINTS, make_portfolio_gen, make_portfolio_params


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
        gen = PropertyPortfolioGenerator(output_dir=tmp_path, verbose=False,
                                          catchment_params=params)
        locs = gen._generate_locations(3)
        assert len(locs) == 3

    def test_fallback_used_when_no_gauge_points(self, tmp_path):
        params = make_portfolio_params(gauge_points=None)
        params.GAUGE_POINTS = None
        gen = PropertyPortfolioGenerator(output_dir=tmp_path, verbose=False,
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
        gen = PropertyPortfolioGenerator(output_dir=tmp_path, verbose=False,
                                          catchment_params=params)
        locs = gen._generate_locations_fallback(5, ["A", "B"], {}, {})
        assert len(locs) == 5
        for loc in locs:
            assert 0 <= loc["elevation"] <= 40  # generous bounds
