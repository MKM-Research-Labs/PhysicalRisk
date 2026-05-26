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

"""Quick integration tests for the visual system.

Verifies that all modules import, instantiate, and expose their basic API.
No file I/O required — tests run entirely in-memory.
"""

import pytest
import folium
from unittest.mock import Mock


class TestModuleImports:
    """All visual modules must be importable."""

    def test_core_imports(self):
        from visual.core import DataLoader, MapBuilder, TCEventVisualization
        assert DataLoader is not None
        assert MapBuilder is not None
        assert TCEventVisualization is not None

    def test_layer_imports(self):
        from visual.layer import GaugeLayer, PropertyLayer
        assert GaugeLayer is not None
        assert PropertyLayer is not None

    def test_popup_imports(self):
        from visual.popups import GaugePopupBuilder, PropertyPopupBuilder
        assert GaugePopupBuilder is not None
        assert PropertyPopupBuilder is not None

    def test_interactivity_imports(self):
        from visual.interactivity.backend_handler import BackendHandler
        from visual.interactivity.context_menus import ContextMenuHandler
        assert BackendHandler is not None
        assert ContextMenuHandler is not None

    def test_utils_imports(self):
        from visual.utils import DataFormatter, RiskAssessor, ColorSchemes
        assert DataFormatter is not None
        assert RiskAssessor is not None
        assert ColorSchemes is not None


class TestModuleInstantiation:
    """All visual modules must be instantiable."""

    def test_core_instantiation(self, tmp_path):
        from visual.core import DataLoader, MapBuilder, TCEventVisualization
        assert DataLoader(tmp_path) is not None
        assert MapBuilder() is not None
        assert TCEventVisualization() is not None

    def test_layer_instantiation(self):
        from visual.layer import GaugeLayer, PropertyLayer
        assert GaugeLayer() is not None
        assert PropertyLayer() is not None

    def test_popup_instantiation(self):
        from visual.popups import GaugePopupBuilder, PropertyPopupBuilder
        assert GaugePopupBuilder() is not None
        assert PropertyPopupBuilder() is not None

    def test_interactivity_instantiation(self):
        from visual.interactivity.backend_handler import BackendHandler
        from visual.interactivity.context_menus import ContextMenuHandler
        assert BackendHandler() is not None
        assert ContextMenuHandler() is not None


class TestBasicFunctionality:
    """Core APIs must return expected output types."""

    def test_backend_handler_js(self):
        from visual.interactivity.backend_handler import BackendHandler
        backend = BackendHandler()
        js = backend.get_js()
        assert isinstance(js, str) and len(js) > 0
        assert '<script>' in js

    def test_context_menu_js(self):
        from visual.interactivity.context_menus import ContextMenuHandler
        context = ContextMenuHandler()
        js = context.get_js()
        assert isinstance(js, str) and len(js) > 0

    def test_data_formatter_currency(self):
        from visual.utils import DataFormatter
        result = DataFormatter.format_currency(500000)
        assert isinstance(result, str)
        assert '500' in result

    def test_risk_assessor_returns_string(self):
        from visual.utils import RiskAssessor
        level = RiskAssessor.assess_flood_risk_level(1.5)
        assert isinstance(level, str) and len(level) > 0

    def test_color_schemes_flood_risk(self):
        from visual.utils import ColorSchemes
        color = ColorSchemes.get_flood_risk_color('High')
        assert isinstance(color, str) and len(color) > 0

    def test_backend_statistics(self):
        from visual.interactivity.backend_handler import BackendHandler
        stats = BackendHandler().get_statistics()
        assert isinstance(stats, dict)
        assert 'server_url' in stats

    def test_context_menu_statistics(self):
        from visual.interactivity.context_menus import ContextMenuHandler
        stats = ContextMenuHandler().get_statistics()
        assert isinstance(stats, dict)
        assert 'property_menu_items' in stats


class TestModuleCommunication:
    """Modules must integrate with folium maps without errors."""

    def test_backend_add_to_map(self):
        from visual.interactivity.backend_handler import BackendHandler
        test_map = folium.Map(location=[51.5074, -0.1278])
        BackendHandler().add_to_map(test_map)
        html = test_map.get_root().render()
        assert '__BACKEND_CONFIG' in html

    def test_context_menu_add_to_map(self):
        from visual.interactivity.context_menus import ContextMenuHandler
        test_map = folium.Map(location=[51.5074, -0.1278])
        ContextMenuHandler().add_to_map(test_map)
        html = test_map._repr_html_()
        assert len(html) > 0

    def test_notification_add_to_map(self):
        from visual.interactivity.notifications import NotificationSystem
        test_map = folium.Map(location=[51.5074, -0.1278])
        NotificationSystem().add_to_map(test_map)
        html = test_map._repr_html_()
        assert 'showNotification' in html


class TestModuleConfiguration:
    """Configuration APIs must persist changes."""

    def test_backend_server_url_config(self):
        from visual.interactivity.backend_handler import BackendHandler
        backend = BackendHandler()
        backend.configure(server_url='http://test.example.com:8080')
        assert backend.server_url == 'http://test.example.com:8080'
        assert backend.get_statistics()['server_url'] == 'http://test.example.com:8080'

    def test_context_menu_config(self):
        from visual.interactivity.context_menus import ContextMenuHandler
        context = ContextMenuHandler()
        custom_items = [{'id': 'test', 'label': 'Test', 'action': 'testAction'}]
        context.configure(property_menu=custom_items)
        assert context.property_menu == custom_items

    def test_backend_endpoints_config(self):
        from visual.interactivity.backend_handler import BackendHandler
        backend = BackendHandler()
        backend.configure(endpoints={'custom': '/api/custom'})
        assert 'custom' in backend.endpoints
