# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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


class TestGetStatistics:
    """Line 106: get_statistics() returns correct counts."""

    def test_default_statistics(self):
        from visual.interactivity.context_menus import (
            ContextMenuHandler, DEFAULT_PROPERTY_MENU, DEFAULT_GAUGE_MENU)

        handler = ContextMenuHandler()
        stats = handler.get_statistics()
        assert stats['property_menu_items'] == len(DEFAULT_PROPERTY_MENU)
        assert stats['gauge_menu_items'] == len(DEFAULT_GAUGE_MENU)
        assert stats['total_menu_items'] == len(DEFAULT_PROPERTY_MENU) + len(DEFAULT_GAUGE_MENU)

    def test_custom_statistics(self):
        from visual.interactivity.context_menus import ContextMenuHandler

        handler = ContextMenuHandler(
            property_menu=[{"id": "a"}, {"id": "b"}],
            gauge_menu=[{"id": "c"}])
        stats = handler.get_statistics()
        assert stats['property_menu_items'] == 2
        assert stats['gauge_menu_items'] == 1
        assert stats['total_menu_items'] == 3
