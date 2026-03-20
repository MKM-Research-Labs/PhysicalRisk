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
Tests for calculate_zoom_for_range and calculate_bounds from visual.core.map_builder.
"""

import pytest


# ===========================================================================
# calculate_zoom_for_range
# ===========================================================================

class TestCalculateZoomForRange:

    def _fn(self, rng, pad=1.0):
        from visual.core.map_builder import calculate_zoom_for_range
        return calculate_zoom_for_range(rng, pad)

    def test_very_large_range_returns_2(self):
        assert self._fn(25) == 2

    def test_large_range_returns_3(self):
        assert self._fn(15) == 3

    def test_range_5_to_10_returns_4(self):
        assert self._fn(7.0) == 4

    def test_range_2_to_5_returns_5(self):
        assert self._fn(3.0) == 5

    def test_range_1_to_2_returns_6(self):
        assert self._fn(1.5) == 6

    def test_range_0p5_to_1_returns_7(self):
        assert self._fn(0.7) == 7

    def test_range_0p2_to_0p5_returns_8(self):
        assert self._fn(0.3) == 8

    def test_range_0p1_to_0p2_returns_9(self):
        assert self._fn(0.15) == 9

    def test_small_range_returns_higher_zoom(self):
        assert self._fn(0.05) == 10

    def test_zero_range_returns_zoom_10(self):
        assert self._fn(0.0) == 10

    def test_padding_factor_shifts_zoom(self):
        # With padding 2x, a 0.3 range becomes 0.6, mapping to zoom 7
        assert self._fn(0.3, pad=2.0) == 7

    def test_padding_factor_less_than_1_shrinks_range(self):
        # 1.5 * 0.5 = 0.75, which is > 0.5 → zoom 7
        assert self._fn(1.5, pad=0.5) == 7

    def test_returns_int(self):
        assert isinstance(self._fn(1.0), int)

    # Exact boundary tests — the boundary values themselves
    def test_exactly_20_range(self):
        # 20 is not > 20, so falls through to > 10 check
        assert self._fn(20.0) == 3

    def test_just_above_20_range(self):
        assert self._fn(20.01) == 2

    def test_exactly_10_range(self):
        # 10 is not > 10, so falls through to > 5 check
        assert self._fn(10.0) == 4

    def test_just_above_10_range(self):
        assert self._fn(10.01) == 3

    def test_exactly_5_range(self):
        # 5 is not > 5, falls through to > 2 check
        assert self._fn(5.0) == 5

    def test_just_above_5_range(self):
        assert self._fn(5.01) == 4

    def test_exactly_2_range(self):
        # 2 is not > 2, falls through to > 1 check
        assert self._fn(2.0) == 6

    def test_just_above_2_range(self):
        assert self._fn(2.01) == 5

    def test_exactly_1_range(self):
        # 1 is not > 1, falls through to > 0.5 check
        assert self._fn(1.0) == 7

    def test_just_above_1_range(self):
        assert self._fn(1.01) == 6

    def test_exactly_0p5_range(self):
        # 0.5 is not > 0.5, falls through to > 0.2 check
        assert self._fn(0.5) == 8

    def test_just_above_0p5_range(self):
        assert self._fn(0.51) == 7

    def test_exactly_0p2_range(self):
        # 0.2 is not > 0.2, falls through to > 0.1 check
        assert self._fn(0.2) == 9

    def test_just_above_0p2_range(self):
        assert self._fn(0.21) == 8

    def test_exactly_0p1_range(self):
        # 0.1 is not > 0.1, falls through to default 10
        assert self._fn(0.1) == 10

    def test_just_above_0p1_range(self):
        assert self._fn(0.11) == 9

    def test_negative_range_returns_zoom_10(self):
        # Negative padded range — falls through all conditions
        assert self._fn(-1.0) == 10


# ===========================================================================
# calculate_bounds
# ===========================================================================

class TestCalculateBounds:

    def _fn(self, coords):
        from visual.core.map_builder import calculate_bounds
        return calculate_bounds(coords)

    def test_empty_returns_empty_dict(self):
        assert self._fn([]) == {}

    def test_single_point_min_max_equal(self):
        result = self._fn([(51.5, -0.1)])
        assert result['min_lat'] == 51.5
        assert result['max_lat'] == 51.5
        assert result['min_lon'] == -0.1
        assert result['max_lon'] == -0.1

    def test_single_point_ranges_zero(self):
        result = self._fn([(51.5, -0.1)])
        assert result['lat_range'] == 0.0
        assert result['lon_range'] == 0.0

    def test_single_point_center_equals_point(self):
        result = self._fn([(51.5, -0.1)])
        assert result['center_lat'] == pytest.approx(51.5)
        assert result['center_lon'] == pytest.approx(-0.1)

    def test_two_points_center(self):
        result = self._fn([(51.0, -1.0), (52.0, 0.0)])
        assert result['center_lat'] == pytest.approx(51.5)
        assert result['center_lon'] == pytest.approx(-0.5)

    def test_min_max_keys_present(self):
        result = self._fn([(50.0, -2.0), (52.0, 1.0)])
        assert result['min_lat'] == 50.0
        assert result['max_lat'] == 52.0
        assert result['min_lon'] == -2.0
        assert result['max_lon'] == 1.0

    def test_lat_range_and_lon_range(self):
        result = self._fn([(50.0, -2.0), (52.0, 1.0)])
        assert result['lat_range'] == pytest.approx(2.0)
        assert result['lon_range'] == pytest.approx(3.0)

    def test_multiple_points(self):
        coords = [(51.0, -0.5), (51.5, -0.1), (52.0, 0.3)]
        result = self._fn(coords)
        assert result['min_lat'] == 51.0
        assert result['max_lat'] == 52.0

    def test_negative_latitudes(self):
        result = self._fn([(-33.9, 151.2), (-33.5, 151.5)])
        assert result['min_lat'] == pytest.approx(-33.9)
        assert result['center_lat'] == pytest.approx(-33.7)

    def test_negative_longitudes(self):
        result = self._fn([(51.0, -5.0), (51.0, -3.0)])
        assert result['min_lon'] == pytest.approx(-5.0)
        assert result['max_lon'] == pytest.approx(-3.0)

    def test_all_required_keys_present(self):
        result = self._fn([(51.0, -1.0), (52.0, 0.0)])
        for key in ('min_lat', 'max_lat', 'min_lon', 'max_lon',
                    'center_lat', 'center_lon', 'lat_range', 'lon_range'):
            assert key in result, f"Missing key: {key}"

    def test_center_is_float(self):
        result = self._fn([(51.0, -1.0), (52.0, 0.0)])
        assert isinstance(result['center_lat'], float)
        assert isinstance(result['center_lon'], float)

    def test_identical_coordinates_in_list(self):
        coords = [(51.5, -0.1), (51.5, -0.1), (51.5, -0.1)]
        result = self._fn(coords)
        assert result['lat_range'] == 0.0
        assert result['lon_range'] == 0.0
        assert result['center_lat'] == pytest.approx(51.5)
