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

"""Tests for visual layer modules: GaugeLayer, PropertyLayer."""


class TestLayerImports:
    """Test that all existing layer modules can be imported and instantiated."""

    def test_gauge_layer_import(self):
        from visual.layer import GaugeLayer
        layer = GaugeLayer()
        assert layer is not None

    def test_property_layer_import(self):
        from visual.layer import PropertyLayer
        layer = PropertyLayer()
        assert layer is not None

    def test_layer_names_are_strings(self):
        from visual.layer import GaugeLayer, PropertyLayer
        assert isinstance(GaugeLayer().layer_name, str)
        assert isinstance(PropertyLayer().layer_name, str)

    def test_layer_names_are_distinct(self):
        from visual.layer import GaugeLayer, PropertyLayer
        names = {GaugeLayer().layer_name, PropertyLayer().layer_name}
        assert len(names) == 2


class TestLayerConfiguration:
    """Test layer configuration options on the three existing layers."""

    def test_gauge_layer_configure(self):
        from visual.layer import GaugeLayer
        layer = GaugeLayer()
        # configure() should not raise
        layer.configure(show_status_colors=True, show_flood_thresholds=False)

    def test_property_layer_configure(self):
        from visual.layer import PropertyLayer
        layer = PropertyLayer()
        layer.configure(show_risk_colors=False, show_rloan_status=True, risk_based_sizing=True)

    def test_configure_returns_none_or_self(self):
        from visual.layer import GaugeLayer
        layer = GaugeLayer()
        result = layer.configure(show_status_colors=True)
        # configure may return None or self — either is acceptable
        assert result is None or result is layer
