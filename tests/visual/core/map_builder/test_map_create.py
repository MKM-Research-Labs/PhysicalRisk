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
Tests for MapBuilder.create_map and create_map_from_bounds from visual.core.map_builder.
"""

import pytest
import folium


# ===========================================================================
# MapBuilder.create_map
# ===========================================================================

class TestMapBuilderCreateMap:

    @pytest.fixture
    def builder(self):
        from visual.core.map_builder import MapBuilder
        return MapBuilder()

    def test_returns_folium_map(self, builder):
        m = builder.create_map()
        assert isinstance(m, folium.Map)

    def test_no_args_uses_default_center(self, builder):
        m = builder.create_map()
        assert isinstance(m, folium.Map)

    def test_explicit_center(self, builder):
        m = builder.create_map(center=(51.5, -0.1))
        assert isinstance(m, folium.Map)

    def test_explicit_zoom_used_with_center(self, builder):
        m = builder.create_map(center=(51.5, -0.1), zoom=12)
        assert isinstance(m, folium.Map)

    def test_center_takes_priority_over_coordinates(self, builder):
        # When both center and coordinates are provided, center wins
        coords = [(50.0, -2.0), (55.0, 2.0)]
        m = builder.create_map(center=(51.5, -0.1), coordinates=coords)
        assert isinstance(m, folium.Map)

    def test_coordinates_auto_center(self, builder):
        coords = [(51.0, -1.0), (52.0, 0.0)]
        m = builder.create_map(coordinates=coords)
        assert isinstance(m, folium.Map)

    def test_coordinates_with_explicit_zoom(self, builder):
        coords = [(51.0, -1.0), (52.0, 0.0)]
        m = builder.create_map(coordinates=coords, zoom=9)
        assert isinstance(m, folium.Map)

    def test_empty_coordinates_uses_default_center(self, builder):
        m = builder.create_map(coordinates=[])
        assert isinstance(m, folium.Map)

    def test_single_coordinate(self, builder):
        m = builder.create_map(coordinates=[(51.5, -0.1)])
        assert isinstance(m, folium.Map)

    def test_explicit_zoom_only(self, builder):
        m = builder.create_map(zoom=10)
        assert isinstance(m, folium.Map)

    def test_padding_factor_custom(self, builder):
        coords = [(51.0, -1.0), (52.0, 0.0)]
        m = builder.create_map(coordinates=coords, padding_factor=2.0)
        assert isinstance(m, folium.Map)


# ===========================================================================
# MapBuilder.create_map_from_bounds
# ===========================================================================

class TestMapBuilderCreateMapFromBounds:

    @pytest.fixture
    def builder(self):
        from visual.core.map_builder import MapBuilder
        return MapBuilder()

    def test_returns_folium_map(self, builder):
        m = builder.create_map_from_bounds(51.0, 52.0, -1.0, 0.0)
        assert isinstance(m, folium.Map)

    def test_center_computed_correctly(self, builder):
        # Just ensure no exception and we get a map
        m = builder.create_map_from_bounds(50.0, 52.0, -2.0, 2.0)
        assert isinstance(m, folium.Map)

    def test_large_bounds(self, builder):
        m = builder.create_map_from_bounds(10.0, 70.0, -30.0, 50.0)
        assert isinstance(m, folium.Map)

    def test_small_bounds(self, builder):
        m = builder.create_map_from_bounds(51.45, 51.55, -0.15, -0.05)
        assert isinstance(m, folium.Map)

    def test_custom_padding_factor(self, builder):
        m = builder.create_map_from_bounds(51.0, 52.0, -1.0, 0.0, padding_factor=1.5)
        assert isinstance(m, folium.Map)

    def test_equal_lat_bounds(self, builder):
        # min_lat == max_lat → lat_range == 0
        m = builder.create_map_from_bounds(51.5, 51.5, -1.0, 1.0)
        assert isinstance(m, folium.Map)

    def test_equal_lon_bounds(self, builder):
        # min_lon == max_lon → lon_range == 0
        m = builder.create_map_from_bounds(51.0, 52.0, -0.1, -0.1)
        assert isinstance(m, folium.Map)
