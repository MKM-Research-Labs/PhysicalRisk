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

"""Tests for NotificationSystem, ContextMenuHandler, BackendHandler,
and InteractivityManager."""

import json

import pytest
import folium


class TestNotificationSystem:
    """Test the notification system functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from visual.interactivity.notifications import NotificationSystem, NotificationPosition
        self.NotificationSystem = NotificationSystem
        self.NotificationPosition = NotificationPosition
        self.ns = NotificationSystem()

    def test_initialization(self):
        assert isinstance(self.ns, self.NotificationSystem)
        assert self.ns.position == self.NotificationPosition.TOP_RIGHT
        assert self.ns.timeout == 5000
        assert self.ns.max_visible == 5

    def test_javascript_generation(self):
        html = self.ns.get_js()
        assert "showNotification" in html

    def test_build_templates_js(self):
        """Lines 74-78: _build_templates_js() returns JSON with notification type keys."""
        templates_json = self.ns._build_templates_js()
        assert isinstance(templates_json, str)
        assert len(templates_json) > 0
        templates = json.loads(templates_json)
        assert isinstance(templates, dict)
        assert len(templates) > 0

    def test_build_position_css(self):
        """Line 82: _build_position_css() returns CSS function string."""
        css = self.ns._build_position_css()
        assert isinstance(css, str)
        assert "getPositionStyles" in css
        assert "top-right" in css

    def test_no_template_literals_in_js(self):
        from pathlib import Path
        js_path = Path(__file__).parents[4] / 'src' / 'static' / 'js' / 'notifications.js'
        if js_path.exists():
            js = js_path.read_text()
            assert "${" not in js, "JS should not contain template literals"

    def test_configuration(self):
        self.ns.configure(
            position=self.NotificationPosition.BOTTOM_LEFT,
            timeout=3000,
            max_visible=10
        )
        assert self.ns.position == self.NotificationPosition.BOTTOM_LEFT
        assert self.ns.timeout == 3000
        assert self.ns.max_visible == 10

    def test_configure_timeout_only(self):
        self.ns.configure(timeout=1000)
        assert self.ns.timeout == 1000

    def test_statistics(self):
        stats = self.ns.get_statistics()
        assert 'default_position' in stats
        assert 'auto_dismiss_timeout' in stats
        assert 'max_notifications' in stats
        assert 'available_types' in stats
        assert 'available_positions' in stats

    def test_folium_integration(self):
        test_map = folium.Map(location=[51.5074, -0.1278])
        self.ns.add_to_map(test_map)
        html = test_map._repr_html_()
        assert "showNotification" in html


class TestContextMenuHandler:
    """Test the context menu handler functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from visual.interactivity.context_menus import ContextMenuHandler
        self.ContextMenuHandler = ContextMenuHandler
        self.handler = ContextMenuHandler()

    def test_initialization(self):
        assert isinstance(self.handler, self.ContextMenuHandler)
        assert len(self.handler.property_menu) > 0
        assert len(self.handler.gauge_menu) > 0

    def test_javascript_generation(self):
        html = self.handler.get_js()
        assert "createContextMenuHandler" in html or "__MENU_CONFIG" in html

    def test_configuration(self):
        custom_property = [{"id": "custom_action", "label": "Custom", "action": "customAction"}]
        custom_gauge = [{"id": "custom_gauge", "label": "Custom Gauge", "action": "customGaugeAction"}]
        self.handler.configure(property_menu=custom_property, gauge_menu=custom_gauge)
        assert self.handler.property_menu == custom_property
        assert self.handler.gauge_menu == custom_gauge

    def test_statistics(self):
        stats = self.handler.get_statistics()
        assert 'property_menu_items' in stats
        assert 'gauge_menu_items' in stats
        assert 'total_menu_items' in stats

    def test_folium_integration(self):
        test_map = folium.Map(location=[51.5074, -0.1278])
        self.handler.add_to_map(test_map)
        html = test_map._repr_html_()
        assert "createContextMenuHandler" in html or "__MENU_CONFIG" in html


class TestBackendHandler:
    """Test the backend handler functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from visual.interactivity.backend_handler import BackendHandler
        self.BackendHandler = BackendHandler
        self.handler = BackendHandler()

    def test_initialization(self):
        assert isinstance(self.handler, self.BackendHandler)
        assert self.handler.server_url is not None
        assert 'property_report' in self.handler.endpoints or len(self.handler.endpoints) > 0

    def test_custom_server_url(self):
        handler = self.BackendHandler("https://api.example.com")
        assert handler.server_url == "https://api.example.com"

    def test_none_server_url_defaults_to_config(self):
        handler = self.BackendHandler(None)
        assert handler.server_url is not None

    def test_javascript_generation(self):
        html = self.handler.get_js()
        assert len(html) > 0
        assert "<script>" in html

    def test_configuration_server_url(self):
        self.handler.configure(server_url="https://new-server.com")
        assert self.handler.server_url == "https://new-server.com"

    def test_configuration_endpoints(self):
        self.handler.configure(endpoints={"custom_endpoint": "/api/custom"})
        assert "custom_endpoint" in self.handler.endpoints

    def test_statistics(self):
        stats = self.handler.get_statistics()
        assert 'server_url' in stats
        assert 'total_endpoints' in stats
        assert 'endpoints' in stats

    def test_folium_integration(self):
        test_map = folium.Map(location=[51.5074, -0.1278])
        self.handler.add_to_map(test_map)
        html = test_map.get_root().render()
        assert "__BACKEND_CONFIG" in html


class TestInteractivityManager:
    """Test the InteractivityManager."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from visual.interactivity import (
            InteractivityManager,
            ContextMenuHandler,
            BackendHandler,
            NotificationSystem,
            NotificationPosition,
        )
        self.InteractivityManager = InteractivityManager
        self.ContextMenuHandler = ContextMenuHandler
        self.BackendHandler = BackendHandler
        self.NotificationSystem = NotificationSystem
        self.NotificationPosition = NotificationPosition
        self.manager = InteractivityManager()

    def test_initialization_components(self):
        assert isinstance(self.manager, self.InteractivityManager)
        assert isinstance(self.manager.context_menus, self.ContextMenuHandler)
        assert isinstance(self.manager.backend, self.BackendHandler)
        assert isinstance(self.manager.notifications, self.NotificationSystem)

    def test_custom_initialization(self):
        manager = self.InteractivityManager(
            server_url="https://custom.com",
            notification_position="bottom-left",
            notification_timeout=10000
        )
        assert manager.backend.server_url == "https://custom.com"
        assert manager.notifications.position == self.NotificationPosition.BOTTOM_LEFT
        assert manager.notifications.timeout == 10000

    def test_map_setup(self):
        test_map = folium.Map(location=[51.5074, -0.1278])
        result = self.manager.setup_map_interactivity(test_map)
        assert result is self.manager
        html = test_map._repr_html_()
        assert "showNotification" in html
        assert "createContextMenuHandler" in html or "__MENU_CONFIG" in html

    def test_configuration(self):
        self.manager.configure(
            server_url="https://test.com",
            notification_timeout=1000
        )
        assert self.manager.backend.server_url == "https://test.com"
        assert self.manager.notifications.timeout == 1000

    def test_statistics(self):
        stats = self.manager.get_statistics()
        assert 'context_menus' in stats
        assert 'backend_handler' in stats
        assert 'notifications' in stats
