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
Tests for MapControls and MapBuilder defaults from visual.core.map_builder.
"""

import folium


# ===========================================================================
# MapControls
# ===========================================================================

class TestMapControls:

    def test_defaults_measure_true(self):
        from visual.core.map_builder import MapControls
        mc = MapControls()
        assert mc.measure is True

    def test_defaults_fullscreen_true(self):
        from visual.core.map_builder import MapControls
        mc = MapControls()
        assert mc.fullscreen is True

    def test_defaults_layer_control_true(self):
        from visual.core.map_builder import MapControls
        mc = MapControls()
        assert mc.layer_control is True

    def test_defaults_scale_true(self):
        from visual.core.map_builder import MapControls
        mc = MapControls()
        assert mc.scale is True

    def test_all_disabled(self):
        from visual.core.map_builder import MapControls
        mc = MapControls(measure=False, fullscreen=False, layer_control=False, scale=False)
        assert mc.measure is False
        assert mc.fullscreen is False
        assert mc.layer_control is False
        assert mc.scale is False

    def test_apply_to_map_does_not_crash(self):
        from visual.core.map_builder import MapControls
        mc = MapControls()
        m = folium.Map(location=[51.5, -0.1])
        mc.apply_to_map(m)

    def test_apply_to_map_measure_only(self):
        from visual.core.map_builder import MapControls
        mc = MapControls(measure=True, fullscreen=False, layer_control=False, scale=False)
        m = folium.Map(location=[51.5, -0.1])
        mc.apply_to_map(m)

    def test_apply_to_map_fullscreen_only(self):
        from visual.core.map_builder import MapControls
        mc = MapControls(measure=False, fullscreen=True, layer_control=False, scale=False)
        m = folium.Map(location=[51.5, -0.1])
        mc.apply_to_map(m)

    def test_apply_to_map_all_disabled_no_crash(self):
        from visual.core.map_builder import MapControls
        mc = MapControls(measure=False, fullscreen=False, layer_control=False, scale=False)
        m = folium.Map(location=[51.5, -0.1])
        mc.apply_to_map(m)

    def test_apply_to_map_with_include_layer_control_true(self):
        from visual.core.map_builder import MapControls
        mc = MapControls()
        m = folium.Map(location=[51.5, -0.1])
        mc.apply_to_map(m, include_layer_control=True)

    def test_apply_to_map_with_include_layer_control_false_no_crash(self):
        from visual.core.map_builder import MapControls
        mc = MapControls()
        m = folium.Map(location=[51.5, -0.1])
        mc.apply_to_map(m, include_layer_control=False)

    def test_apply_to_map_layer_control_false_with_include_true(self):
        from visual.core.map_builder import MapControls
        # layer_control=False means even if include_layer_control=True, no control added
        mc = MapControls(layer_control=False)
        m = folium.Map(location=[51.5, -0.1])
        mc.apply_to_map(m, include_layer_control=True)

    def test_add_layer_control_when_enabled(self):
        from visual.core.map_builder import MapControls
        mc = MapControls()
        m = folium.Map(location=[51.5, -0.1])
        mc.add_layer_control(m)

    def test_add_layer_control_when_disabled_no_crash(self):
        from visual.core.map_builder import MapControls
        mc = MapControls(layer_control=False)
        m = folium.Map(location=[51.5, -0.1])
        mc.add_layer_control(m)

    def test_apply_to_map_exception_handler(self):
        """Lines 87-88: exception in MeasureControl → warning logged, no crash."""
        from unittest.mock import patch
        from visual.core.map_builder import MapControls
        mc = MapControls(measure=True)
        m = folium.Map(location=[51.5, -0.1])
        with patch('visual.core.map_builder.controls.plugins.MeasureControl',
                   side_effect=RuntimeError("broken")):
            mc.apply_to_map(m)
        # No crash — exception is caught

    def test_add_layer_control_exception_handler(self):
        """Lines 95-96: exception in LayerControl → warning logged, no crash."""
        from unittest.mock import patch
        from visual.core.map_builder import MapControls
        mc = MapControls(layer_control=True)
        m = folium.Map(location=[51.5, -0.1])
        with patch('visual.core.map_builder.controls.folium.LayerControl',
                   side_effect=RuntimeError("broken")):
            mc.add_layer_control(m)
        # No crash — exception is caught


# ===========================================================================
# MapBuilder defaults
# ===========================================================================

class TestMapBuilderDefaults:

    def test_default_zoom_is_8(self):
        from visual.core.map_builder import MapBuilder
        b = MapBuilder()
        assert b.default_zoom == 8

    def test_default_tiles_is_openstreetmap(self):
        from visual.core.map_builder import MapBuilder
        b = MapBuilder()
        assert b.tiles == 'OpenStreetMap'

    def test_default_center_is_london(self):
        from visual.core.map_builder import MapBuilder
        assert MapBuilder.DEFAULT_CENTER == (51.5074, -0.1278)

    def test_custom_tiles_stored(self):
        from visual.core.map_builder import MapBuilder
        b = MapBuilder(tiles='CartoDB positron')
        assert b.tiles == 'CartoDB positron'

    def test_custom_zoom_stored(self):
        from visual.core.map_builder import MapBuilder
        b = MapBuilder(default_zoom=12)
        assert b.default_zoom == 12

    def test_controls_initialised(self):
        from visual.core.map_builder import MapBuilder, MapControls
        b = MapBuilder()
        assert isinstance(b.controls, MapControls)
