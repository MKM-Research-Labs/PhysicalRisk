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

"""Tests for visual/interactivity/context_menus.py — missing method bodies."""

from unittest.mock import MagicMock

import pytest


class TestContextMenuInit:
    """Default and custom menu initialization."""

    def test_default_init(self):
        from visual.interactivity.context_menus import (
            ContextMenuHandler, DEFAULT_PROPERTY_MENU, DEFAULT_GAUGE_MENU)

        handler = ContextMenuHandler()
        assert handler.property_menu == DEFAULT_PROPERTY_MENU
        assert handler.gauge_menu == DEFAULT_GAUGE_MENU

    def test_custom_menus(self):
        from visual.interactivity.context_menus import ContextMenuHandler

        pm = [{"id": "a", "label": "A", "action": "doA"}]
        gm = [{"id": "b", "label": "B", "action": "doB"}]
        handler = ContextMenuHandler(property_menu=pm, gauge_menu=gm)
        assert handler.property_menu == pm
        assert handler.gauge_menu == gm


class TestAddToMap:
    """Line 94: add_to_map adds Element to folium map."""

    def test_add_to_map_calls_add_child(self):
        from visual.interactivity.context_menus import ContextMenuHandler

        handler = ContextMenuHandler()
        mock_map = MagicMock()
        mock_root = MagicMock()
        mock_html = MagicMock()
        mock_map.get_root.return_value = mock_root
        mock_root.html = mock_html

        handler.add_to_map(mock_map)
        mock_html.add_child.assert_called_once()


class TestConfigure:
    """Lines 99-102: configure() updates property_menu and gauge_menu."""

    def test_configure_property_menu(self):
        from visual.interactivity.context_menus import ContextMenuHandler

        handler = ContextMenuHandler()
        new_pm = [{"id": "new", "label": "New", "action": "doNew"}]
        handler.configure(property_menu=new_pm)
        assert handler.property_menu == new_pm

    def test_configure_gauge_menu(self):
        from visual.interactivity.context_menus import ContextMenuHandler

        handler = ContextMenuHandler()
        new_gm = [{"id": "g1", "label": "G1", "action": "doG1"}]
        handler.configure(gauge_menu=new_gm)
        assert handler.gauge_menu == new_gm

    def test_configure_both_menus(self):
        from visual.interactivity.context_menus import ContextMenuHandler

        handler = ContextMenuHandler()
        pm = [{"id": "p"}]
        gm = [{"id": "g"}]
        handler.configure(property_menu=pm, gauge_menu=gm)
        assert handler.property_menu == pm
        assert handler.gauge_menu == gm

    def test_configure_no_args_no_change(self):
        from visual.interactivity.context_menus import (
            ContextMenuHandler, DEFAULT_PROPERTY_MENU, DEFAULT_GAUGE_MENU)

        handler = ContextMenuHandler()
        handler.configure()
        assert handler.property_menu == DEFAULT_PROPERTY_MENU
        assert handler.gauge_menu == DEFAULT_GAUGE_MENU


class TestNavMenusJS:
    """_build_nav_menus_js() generates navigation select menus."""

    def test_nav_menus_js_contains_gauge_select(self):
        from visual.interactivity.context_menus import ContextMenuHandler

        handler = ContextMenuHandler()
        js = handler._build_nav_menus_js()
        assert 'nav-menu-container' in js
        assert 'nav-gauge-select' in js
        assert '_tdPreGauges' in js

    def test_nav_menus_js_contains_property_select(self):
        from visual.interactivity.context_menus import ContextMenuHandler

        handler = ContextMenuHandler()
        js = handler._build_nav_menus_js()
        assert 'nav-prop-select' in js
        assert '_prePropertyTS' in js

    def test_nav_menus_js_includes_menu_actions(self):
        from visual.interactivity.context_menus import (
            ContextMenuHandler, DEFAULT_GAUGE_MENU, DEFAULT_PROPERTY_MENU)

        handler = ContextMenuHandler()
        js = handler._build_nav_menus_js()
        for item in DEFAULT_GAUGE_MENU:
            assert item['action'] in js, f"Missing gauge action: {item['action']}"
        for item in DEFAULT_PROPERTY_MENU:
            assert item['action'] in js, f"Missing property action: {item['action']}"

    def test_nav_menus_js_filters_synthetic_gauges(self):
        from visual.interactivity.context_menus import ContextMenuHandler

        handler = ContextMenuHandler()
        js = handler._build_nav_menus_js()
        assert 'SYNTH' in js, "Should filter SYNTH gauges"

    def test_nav_menus_js_has_action_bar(self):
        from visual.interactivity.context_menus import ContextMenuHandler

        handler = ContextMenuHandler()
        js = handler._build_nav_menus_js()
        assert 'nav-action-bar' in js

    def test_nav_menus_not_rendered_in_get_js(self):
        # The top-left gauge/property dropdowns are no longer rendered
        # (browsing moved to the CDM Asset Review workstream). The builder is
        # retained but not wired into get_js.
        from visual.interactivity.context_menus import ContextMenuHandler

        handler = ContextMenuHandler()
        js = handler.get_js()
        assert 'nav-menu-container' not in js
        assert '__NAV_MENU_CONFIG' not in js
        # The right-click context menus are unaffected.
        assert '__MENU_CONFIG' in js


class TestGetStatistics:
    """Line 106: get_statistics() returns correct counts."""

    def test_default_statistics(self):
        from visual.interactivity.context_menus import (
            ContextMenuHandler, DEFAULT_PROPERTY_MENU, DEFAULT_GAUGE_MENU)

        from visual.interactivity.context_menus import DEFAULT_COMMERCIAL_MENU
        handler = ContextMenuHandler()
        stats = handler.get_statistics()
        assert stats['property_menu_items'] == len(DEFAULT_PROPERTY_MENU)
        assert stats['gauge_menu_items'] == len(DEFAULT_GAUGE_MENU)
        assert stats['commercial_menu_items'] == len(DEFAULT_COMMERCIAL_MENU)
        assert stats['total_menu_items'] == (
            len(DEFAULT_PROPERTY_MENU)
            + len(DEFAULT_GAUGE_MENU)
            + len(DEFAULT_COMMERCIAL_MENU)
        )

    def test_custom_statistics(self):
        from visual.interactivity.context_menus import ContextMenuHandler

        handler = ContextMenuHandler(
            property_menu=[{"id": "a"}, {"id": "b"}],
            gauge_menu=[{"id": "c"}],
            commercial_menu=[{"id": "d"}, {"id": "e"}, {"id": "f"}])
        stats = handler.get_statistics()
        assert stats['property_menu_items'] == 2
        assert stats['gauge_menu_items'] == 1
        assert stats['commercial_menu_items'] == 3
        assert stats['total_menu_items'] == 6
