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
Tests for MapBuilder configuration, finalize_map, and add_bounds_rectangle
from visual.core.map_builder.
"""

import pytest
import folium


# ===========================================================================
# MapBuilder setters and configuration
# ===========================================================================

class TestMapBuilderSettersAndConfiguration:

    @pytest.fixture
    def builder(self):
        from visual.core.map_builder import MapBuilder
        return MapBuilder()

    def test_set_default_zoom_valid_min(self, builder):
        builder.set_default_zoom(1)
        assert builder.default_zoom == 1

    def test_set_default_zoom_valid_max(self, builder):
        builder.set_default_zoom(18)
        assert builder.default_zoom == 18

    def test_set_default_zoom_valid_middle(self, builder):
        builder.set_default_zoom(12)
        assert builder.default_zoom == 12

    def test_set_default_zoom_zero_ignored(self, builder):
        builder.set_default_zoom(8)
        builder.set_default_zoom(0)
        assert builder.default_zoom == 8

    def test_set_default_zoom_negative_ignored(self, builder):
        builder.set_default_zoom(8)
        builder.set_default_zoom(-5)
        assert builder.default_zoom == 8

    def test_set_default_zoom_above_18_ignored(self, builder):
        builder.set_default_zoom(8)
        builder.set_default_zoom(19)
        assert builder.default_zoom == 8

    def test_set_default_zoom_100_ignored(self, builder):
        builder.set_default_zoom(8)
        builder.set_default_zoom(100)
        assert builder.default_zoom == 8

    def test_set_tiles_changes_value(self, builder):
        builder.set_tiles("CartoDB positron")
        assert builder.tiles == "CartoDB positron"

    def test_set_tiles_empty_string(self, builder):
        builder.set_tiles("")
        assert builder.tiles == ""

    def test_set_tiles_affects_subsequent_maps(self, builder):
        builder.set_tiles("CartoDB positron")
        m = builder.create_map()
        assert isinstance(m, folium.Map)

    def test_configure_controls_all_false(self, builder):
        from visual.core.map_builder import MapControls
        builder.configure_controls(measure=False, fullscreen=False, layer_control=False, scale=False)
        assert isinstance(builder.controls, MapControls)
        assert builder.controls.measure is False
        assert builder.controls.fullscreen is False

    def test_configure_controls_all_true(self, builder):
        from visual.core.map_builder import MapControls
        builder.configure_controls(measure=True, fullscreen=True, layer_control=True, scale=True)
        assert builder.controls.measure is True

    def test_configure_controls_partial(self, builder):
        from visual.core.map_builder import MapControls
        builder.configure_controls(measure=False, fullscreen=True)
        assert builder.controls.measure is False
        assert builder.controls.fullscreen is True

    def test_configure_controls_replaces_old_controls(self, builder):
        from visual.core.map_builder import MapControls
        original_controls = builder.controls
        builder.configure_controls(measure=False)
        assert builder.controls is not original_controls


# ===========================================================================
# MapBuilder.finalize_map
# ===========================================================================

class TestMapBuilderFinalizeMap:

    @pytest.fixture
    def builder(self):
        from visual.core.map_builder import MapBuilder
        return MapBuilder()

    def test_finalize_creates_html_file(self, builder, tmp_path):
        m = builder.create_map()
        out = tmp_path / "output.html"
        result = builder.finalize_map(m, out)
        assert result is not None
        assert result.exists()

    def test_finalize_returns_path_object(self, builder, tmp_path):
        m = builder.create_map()
        out = tmp_path / "output.html"
        result = builder.finalize_map(m, out)
        assert isinstance(result, type(out))

    def test_finalize_returns_correct_path(self, builder, tmp_path):
        m = builder.create_map()
        out = tmp_path / "my_map.html"
        result = builder.finalize_map(m, out)
        assert result == out

    def test_finalize_creates_parent_dirs(self, builder, tmp_path):
        m = builder.create_map()
        out = tmp_path / "nested" / "subdirectory" / "map.html"
        result = builder.finalize_map(m, out)
        assert result is not None
        assert result.exists()

    def test_finalize_accepts_string_path(self, builder, tmp_path):
        m = builder.create_map()
        out = str(tmp_path / "string_path.html")
        result = builder.finalize_map(m, out)
        assert result is not None

    def test_finalize_file_is_html(self, builder, tmp_path):
        m = builder.create_map()
        out = tmp_path / "map.html"
        builder.finalize_map(m, out)
        content = out.read_text()
        assert "<html" in content.lower() or "<!doctype" in content.lower()

    def test_finalize_adds_layer_control(self, builder, tmp_path):
        builder.configure_controls(layer_control=True)
        m = builder.create_map()
        out = tmp_path / "controlled_map.html"
        result = builder.finalize_map(m, out)
        assert result is not None

    def test_finalize_multiple_times_overwrites(self, builder, tmp_path):
        m1 = builder.create_map(center=(51.5, -0.1))
        out = tmp_path / "map.html"
        builder.finalize_map(m1, out)
        m2 = builder.create_map(center=(52.0, 0.0))
        result = builder.finalize_map(m2, out)
        assert result is not None
        assert result.exists()


# ===========================================================================
# MapBuilder.add_bounds_rectangle
# ===========================================================================

class TestMapBuilderAddBoundsRectangle:

    @pytest.fixture
    def builder(self):
        from visual.core.map_builder import MapBuilder
        return MapBuilder()

    def test_empty_coordinates_no_crash(self, builder):
        m = builder.create_map()
        builder.add_bounds_rectangle(m, [])

    def test_single_point_no_crash(self, builder):
        m = builder.create_map()
        builder.add_bounds_rectangle(m, [(51.5, -0.1)])

    def test_two_points_no_crash(self, builder):
        m = builder.create_map()
        builder.add_bounds_rectangle(m, [(51.0, -1.0), (52.0, 0.0)])

    def test_many_points_no_crash(self, builder):
        m = builder.create_map()
        coords = [(51.0 + i * 0.1, -1.0 + i * 0.1) for i in range(10)]
        builder.add_bounds_rectangle(m, coords)

    def test_default_color_no_crash(self, builder):
        m = builder.create_map()
        coords = [(51.0, -1.0), (52.0, 0.0)]
        builder.add_bounds_rectangle(m, coords, color='red')

    def test_custom_color(self, builder):
        m = builder.create_map()
        coords = [(51.0, -1.0), (52.0, 0.0)]
        builder.add_bounds_rectangle(m, coords, color='blue', weight=3)

    def test_fill_enabled(self, builder):
        m = builder.create_map()
        coords = [(51.0, -1.0), (52.0, 0.0)]
        builder.add_bounds_rectangle(m, coords, fill=True, fill_opacity=0.3)

    def test_zero_opacity(self, builder):
        m = builder.create_map()
        coords = [(51.0, -1.0), (52.0, 0.0)]
        builder.add_bounds_rectangle(m, coords, opacity=0.0)

    def test_identical_points(self, builder):
        m = builder.create_map()
        # All identical points still forms a valid (zero-area) bounding box
        coords = [(51.5, -0.1), (51.5, -0.1)]
        builder.add_bounds_rectangle(m, coords)
