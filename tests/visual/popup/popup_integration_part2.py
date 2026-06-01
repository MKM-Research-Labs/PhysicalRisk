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

"""Popup integration tests using synthetic data (part 2).

Tests full popup builds and popup-layer integration with folium.
All tests use synthetic in-memory data -- no file I/O required.
"""

import folium


class TestFullPopupBuilds:
    """Full popup objects must be created and contain expected content."""

    def test_property_popup_without_extras(self, sample_property, sample_address):
        from visual.popups import PropertyPopupBuilder
        builder = PropertyPopupBuilder()
        popup = builder.build_property_popup(
            prop=sample_property,
            property_id='PROP-INTG-001',
            address=sample_address,
            coordinates='51.5074\u00b0N, -0.1278\u00b0E',
            flood_risk='Medium',
            thames_proximity='Close',
            ground_elevation=10.0,
            elevation_estimated=False,
            property_value=500000,
            construction_year=1985,
            property_age_factor='Medium (1925-1975)',
            has_rloan=False,
        )
        assert popup is not None

    def test_property_popup_with_mortgage(self, sample_property, sample_address, sample_mortgage, sample_flood_info):
        from visual.popups import PropertyPopupBuilder
        builder = PropertyPopupBuilder()
        popup = builder.build_property_popup(
            prop=sample_property,
            property_id='PROP-INTG-001',
            address=sample_address,
            coordinates='51.5074\u00b0N, -0.1278\u00b0E',
            flood_risk='Medium',
            thames_proximity='Close',
            ground_elevation=10.0,
            elevation_estimated=False,
            property_value=500000,
            construction_year=1985,
            property_age_factor='Medium (1925-1975)',
            has_rloan=True,
            rloan_info=sample_mortgage,
            flood_info=sample_flood_info,
        )
        assert popup is not None

    def test_gauge_popup_without_flood_info(self, sample_gauge_info):
        from visual.popups import GaugePopupBuilder
        builder = GaugePopupBuilder()
        popup = builder.build_gauge_popup(
            gauge_id='GAUGE-INTG-001',
            lat=51.5074,
            lon=-0.1278,
            info=sample_gauge_info,
        )
        assert popup is not None

    def test_gauge_popup_with_flood_info(self, sample_gauge_info):
        from visual.popups import GaugePopupBuilder
        builder = GaugePopupBuilder()
        flood_info = {
            'gauge_name': 'Test Thames Gauge',
            'elevation': 5.0,
            'max_level': 4.8,
            'alert_level': 2.5,
            'warning_level': 3.5,
            'severe_level': 4.5,
        }
        popup = builder.build_gauge_popup(
            gauge_id='GAUGE-INTG-001',
            lat=51.5074,
            lon=-0.1278,
            info=sample_gauge_info,
            flood_info=flood_info,
        )
        assert popup is not None


class TestPopupLayerIntegration:
    """Popups must be addable to folium markers on a folium map."""

    def test_property_popup_on_marker(self, sample_property, sample_address):
        from visual.popups import PropertyPopupBuilder
        builder = PropertyPopupBuilder()
        popup = builder.build_property_popup(
            prop=sample_property,
            property_id='PROP-INTG-001',
            address=sample_address,
            coordinates='51.5074\u00b0N, -0.1278\u00b0E',
            flood_risk='Medium',
            thames_proximity='Close',
            ground_elevation=10.0,
            elevation_estimated=False,
            property_value=500000,
            construction_year=1985,
            property_age_factor='Medium (1925-1975)',
            has_rloan=False,
        )
        test_map = folium.Map(location=[51.5074, -0.1278])
        folium.Marker(location=[51.5074, -0.1278], popup=popup).add_to(test_map)
        html = test_map._repr_html_()
        assert len(html) > 0

    def test_gauge_popup_on_marker(self, sample_gauge_info):
        from visual.popups import GaugePopupBuilder
        builder = GaugePopupBuilder()
        popup = builder.build_gauge_popup(
            gauge_id='GAUGE-INTG-001',
            lat=51.5074,
            lon=-0.1278,
            info=sample_gauge_info,
        )
        test_map = folium.Map(location=[51.5074, -0.1278])
        folium.Marker(location=[51.5074, -0.1278], popup=popup).add_to(test_map)
        html = test_map._repr_html_()
        assert len(html) > 0
