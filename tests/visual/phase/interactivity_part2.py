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

"""Tests for convenience functions, integration scenarios, flood anim modules,
and create_visualization."""

import pytest
import folium


class TestConvenienceFunctions:
    """Test notification convenience functions."""

    def test_create_notification_system(self):
        from visual.interactivity.notifications import (
            NotificationSystem,
            NotificationPosition,
            create_notification_system,
        )
        ns = create_notification_system(position="bottom-right", timeout=3000, max_notifications=10)
        assert isinstance(ns, NotificationSystem)
        assert ns.position == NotificationPosition.BOTTOM_RIGHT
        assert ns.timeout == 3000
        assert ns.max_visible == 10

    def test_add_notifications_to_map(self):
        from visual.interactivity.notifications import NotificationSystem, add_notifications_to_map
        test_map = folium.Map(location=[51.5074, -0.1278])
        result = add_notifications_to_map(test_map, position="top-left", timeout=2000)
        assert isinstance(result, NotificationSystem)
        html = test_map._repr_html_()
        assert "showNotification" in html


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_minimal_setup(self):
        from visual.interactivity import InteractivityManager
        test_map = folium.Map(location=[51.5074, -0.1278])
        manager = InteractivityManager()
        manager.setup_map_interactivity(test_map)
        html = test_map._repr_html_()
        assert "showNotification" in html

    def test_custom_configuration(self):
        from visual.interactivity import InteractivityManager
        test_map = folium.Map(location=[51.5074, -0.1278])
        manager = InteractivityManager(
            server_url="https://api.example.com",
            notification_position="bottom-left"
        )
        manager.context_menus.configure(
            property_menu=[{"id": "analyze", "label": "Analyze", "action": "analyzeProperty"}]
        )
        manager.setup_map_interactivity(test_map)
        html = test_map._repr_html_()
        # get_js() uses empty URL for relative paths; custom URL stored on object
        assert 'BACKEND_CONFIG' in html
        assert '&quot;url&quot;: &quot;&quot;' in html
        assert manager.backend.server_url == "https://api.example.com"
        assert "bottom-left" in html

    def test_individual_components(self):
        from visual.interactivity.backend_handler import BackendHandler
        from visual.interactivity.notifications import NotificationSystem
        test_map = folium.Map(location=[51.5074, -0.1278])
        notifications = NotificationSystem()
        notifications.add_to_map(test_map)
        backend = BackendHandler("https://test.com")
        backend.add_to_map(test_map)
        html = test_map._repr_html_()
        assert "showNotification" in html
        # get_js() uses empty URL for relative paths; custom URL stored on object
        assert '&quot;url&quot;: &quot;&quot;' in html
        assert backend.server_url == "https://test.com"

    def test_invalid_notification_position_fallback(self):
        from visual.interactivity import InteractivityManager
        from visual.interactivity.notifications import NotificationPosition
        manager = InteractivityManager(notification_position="invalid-position")
        assert manager.notifications.position == NotificationPosition.TOP_RIGHT

    def test_none_server_url_handled(self):
        from visual.interactivity import InteractivityManager
        manager = InteractivityManager(server_url=None)
        assert manager.backend.server_url is not None


class TestWithRealData:
    """Test complete workflow with sample data structures."""

    def test_complete_workflow(self):
        from visual.interactivity import InteractivityManager
        test_map = folium.Map(location=[51.5074, -0.1278])
        folium.Marker(
            location=[51.5074, -0.1278],
            popup="Property: PROP-test123",
            tooltip="Property: PROP-test123 | Risk: Medium"
        ).add_to(test_map)
        folium.Marker(
            location=[51.508, -0.13],
            popup="Gauge: GAUGE-test123",
            tooltip="Gauge: Test Gauge | Status: Fully operational"
        ).add_to(test_map)
        manager = InteractivityManager()
        manager.setup_map_interactivity(test_map)
        html = test_map._repr_html_()
        assert "showNotification" in html
        assert "createContextMenuHandler" in html or "__MENU_CONFIG" in html
        assert "PROP-test123" in html
        assert "GAUGE-test123" in html


class TestFloodAnimModules:
    """Tests for storm/fa_panel.py and storm/fa_render.py -- get_js() coverage."""

    def test_fa_panel_get_js_returns_string(self):
        """Lines 6-8 in fa_panel.py: get_js() returns non-empty string."""
        from visual.interactivity.storm.fa_panel import get_js
        js = get_js()
        assert isinstance(js, str)
        assert len(js) > 100
        assert "createPanel" in js

    def test_fa_render_get_js_returns_string(self):
        """Lines 6-8 in fa_render.py: get_js() returns non-empty string."""
        from visual.interactivity.storm.fa_render import get_js
        js = get_js()
        assert isinstance(js, str)
        assert len(js) > 100


class TestCreateVisualization:
    """Test visual/__init__.py line 32 -- create_visualization()."""

    def test_create_visualization_returns_instance(self, tmp_path):
        """Line 32: create_visualization() returns TCEventVisualization."""
        from visual import create_visualization, TCEventVisualization
        vis = create_visualization(input_dir=tmp_path, output_dir=tmp_path)
        assert isinstance(vis, TCEventVisualization)
