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
Tests for PropertyPortfolioGenerator geometry helpers:
  _haversine, _nearest_on_segment, _min_river_distance,
  _perpendicular_offset, _ensure_off_river.
"""

import pytest

from port.src.property.main import PropertyPortfolioGenerator

from .conftest import GAUGE_POINTS, make_portfolio_gen


# ===========================================================================
# _haversine
# ===========================================================================

class TestHaversine:
    """Known-distance checks for the static haversine helper."""

    def test_same_point_returns_zero(self):
        d = PropertyPortfolioGenerator._haversine(51.5, -0.1, 51.5, -0.1)
        assert d == pytest.approx(0.0, abs=1e-6)

    def test_approximate_one_degree_lat(self):
        # 1 degree latitude ~ 111 km
        d = PropertyPortfolioGenerator._haversine(51.0, 0.0, 52.0, 0.0)
        assert 110_000 < d < 112_000

    def test_approximate_one_degree_lon_at_equator(self):
        # At equator 1 degree longitude ~ 111 km
        d = PropertyPortfolioGenerator._haversine(0.0, 0.0, 0.0, 1.0)
        assert 110_000 < d < 112_000

    def test_symmetry(self):
        d1 = PropertyPortfolioGenerator._haversine(51.0, -0.1, 51.5, -0.3)
        d2 = PropertyPortfolioGenerator._haversine(51.5, -0.3, 51.0, -0.1)
        assert d1 == pytest.approx(d2, rel=1e-9)


# ===========================================================================
# _nearest_on_segment
# ===========================================================================

class TestNearestOnSegment:
    """Project a point onto a segment and verify the result."""

    def test_midpoint_projects_to_midpoint(self):
        nx, ny, d = PropertyPortfolioGenerator._nearest_on_segment(
            51.5, 0.5, 51.0, 0.0, 52.0, 0.0
        )
        assert abs(nx - 51.5) < 0.01
        assert abs(ny - 0.0) < 0.01
        assert d > 0

    def test_point_before_start_clamps_to_start(self):
        nx, ny, d = PropertyPortfolioGenerator._nearest_on_segment(
            50.0, 0.0, 51.0, 0.0, 52.0, 0.0
        )
        assert abs(nx - 51.0) < 0.01
        assert abs(ny - 0.0) < 0.01

    def test_point_past_end_clamps_to_end(self):
        nx, ny, d = PropertyPortfolioGenerator._nearest_on_segment(
            53.0, 0.0, 51.0, 0.0, 52.0, 0.0
        )
        assert abs(nx - 52.0) < 0.01
        assert abs(ny - 0.0) < 0.01

    def test_degenerate_segment_returns_start(self):
        """When segment is a point (seg2 < 1e-18), returns start point distance."""
        nx, ny, d = PropertyPortfolioGenerator._nearest_on_segment(
            51.5, -0.1, 51.5, -0.1, 51.5, -0.1
        )
        assert abs(nx - 51.5) < 1e-9
        assert abs(ny + 0.1) < 1e-9
        assert d == pytest.approx(0.0, abs=1e-6)

    def test_distance_is_non_negative(self):
        _, _, d = PropertyPortfolioGenerator._nearest_on_segment(
            51.4, -0.2, 51.0, 0.0, 52.0, 0.0
        )
        assert d >= 0


# ===========================================================================
# _min_river_distance
# ===========================================================================

class TestMinRiverDistance:

    def test_returns_float(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        d = gen._min_river_distance(51.46, -0.30, GAUGE_POINTS)
        assert isinstance(d, float)
        assert d >= 0

    def test_point_on_gauge_returns_small_distance(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        lat, lon = GAUGE_POINTS[2][0], GAUGE_POINTS[2][1]
        d = gen._min_river_distance(lat + 0.00001, lon + 0.00001, GAUGE_POINTS)
        assert d < 10_000  # well within 10 km

    def test_distant_point_returns_larger_distance(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        d_near = gen._min_river_distance(51.46, -0.30, GAUGE_POINTS)
        d_far = gen._min_river_distance(52.50, -0.30, GAUGE_POINTS)
        assert d_far > d_near


# ===========================================================================
# _perpendicular_offset
# ===========================================================================

class TestPerpendicularOffset:

    def test_returns_two_floats(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        lat, lon = gen._perpendicular_offset(
            51.46, -0.30,
            GAUGE_POINTS[1], GAUGE_POINTS[2]
        )
        assert isinstance(lat, float)
        assert isinstance(lon, float)

    def test_offset_moves_point(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        base_lat, base_lon = 51.46, -0.30
        lat, lon = gen._perpendicular_offset(
            base_lat, base_lon,
            GAUGE_POINTS[0], GAUGE_POINTS[1]
        )
        dist = PropertyPortfolioGenerator._haversine(base_lat, base_lon, lat, lon)
        # Should be at least MIN_OFFSET_M away (400 m)
        assert dist >= PropertyPortfolioGenerator.MIN_OFFSET_M * 0.5

    def test_degenerate_segment_falls_back_to_pure_lat_offset(self, tmp_path):
        """When seg_start == seg_end, norm ~ 0 -> degenerate fallback path."""
        gen = make_portfolio_gen(tmp_path)
        degenerate_pt = (51.46, -0.30, 4.0)
        lat, lon = gen._perpendicular_offset(
            51.46, -0.30, degenerate_pt, degenerate_pt
        )
        # Longitude should be unchanged (fallback only shifts lat)
        assert abs(lon - (-0.30)) < 1e-9


# ===========================================================================
# _ensure_off_river
# ===========================================================================

class TestEnsureOffRiver:

    def test_far_point_unchanged(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        lat, lon = 53.0, -0.30  # > 100 km north
        new_lat, new_lon = gen._ensure_off_river(lat, lon, GAUGE_POINTS)
        assert new_lat == pytest.approx(lat)
        assert new_lon == pytest.approx(lon)

    def test_close_point_pushed_away(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        g_lat, g_lon = GAUGE_POINTS[2][0], GAUGE_POINTS[2][1]
        new_lat, new_lon = gen._ensure_off_river(g_lat, g_lon, GAUGE_POINTS)
        dist = PropertyPortfolioGenerator._haversine(g_lat, g_lon, new_lat, new_lon)
        assert dist >= PropertyPortfolioGenerator.MIN_RIVER_DISTANCE_M * 0.8

    def test_returns_tuple_of_two_floats(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        result = gen._ensure_off_river(51.46, -0.30, GAUGE_POINTS)
        assert len(result) == 2
        assert all(isinstance(v, float) for v in result)
