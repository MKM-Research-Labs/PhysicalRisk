# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for visual/interactivity/notifications.py — missing coverage lines.

Covers:
  93-97  _build_templates_js
  101    _build_position_css
  134    add_to_map
  139-144 configure
  148    get_statistics
  164-165 create_notification_system with invalid position
  172-174 add_notifications_to_map
"""

import json
from unittest.mock import MagicMock

import pytest
from config.theme import colour


class TestBuildTemplatesJs:
    """Lines 93-97: _build_templates_js returns JSON of all NotificationType entries."""

    def test_returns_valid_json(self):
        from visual.interactivity.notifications import NotificationSystem
        ns = NotificationSystem()
        result = ns._build_templates_js()
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_contains_all_types(self):
        from visual.interactivity.notifications import NotificationSystem, NotificationType
        ns = NotificationSystem()
        parsed = json.loads(ns._build_templates_js())
        for t in NotificationType:
            assert t.key in parsed
            assert 'icon' in parsed[t.key]
            assert 'color' in parsed[t.key]
            assert 'background' in parsed[t.key]

    def test_info_template_values(self):
        from visual.interactivity.notifications import NotificationSystem
        ns = NotificationSystem()
        parsed = json.loads(ns._build_templates_js())
        assert parsed['info']['color'] == colour('accent-bright')


class TestBuildPositionCss:
    """Line 101: _build_position_css returns JS function string."""

    def test_returns_position_function(self):
        from visual.interactivity.notifications import NotificationSystem
        ns = NotificationSystem()
        css = ns._build_position_css()
        assert 'getPositionStyles' in css
        assert 'top-right' in css
        assert 'bottom-left' in css


class TestAddToMap:
    """Line 134: add_to_map adds Element to folium map."""

    def test_add_to_map_calls_add_child(self):
        from visual.interactivity.notifications import NotificationSystem
        ns = NotificationSystem()
        mock_map = MagicMock()
        mock_root = MagicMock()
        mock_html = MagicMock()
        mock_map.get_root.return_value = mock_root
        mock_root.html = mock_html
        ns.add_to_map(mock_map)
        mock_html.add_child.assert_called_once()


class TestConfigure:
    """Lines 139-144: configure updates position, timeout, max_visible."""

    def test_configure_position(self):
        from visual.interactivity.notifications import (
            NotificationSystem, NotificationPosition
        )
        ns = NotificationSystem()
        ns.configure(position=NotificationPosition.BOTTOM_LEFT)
        assert ns.position == NotificationPosition.BOTTOM_LEFT

    def test_configure_timeout(self):
        from visual.interactivity.notifications import NotificationSystem
        ns = NotificationSystem(timeout=5000)
        ns.configure(timeout=3000)
        assert ns.timeout == 3000

    def test_configure_max_visible(self):
        from visual.interactivity.notifications import NotificationSystem
        ns = NotificationSystem(max_visible=5)
        ns.configure(max_visible=10)
        assert ns.max_visible == 10

    def test_configure_no_args_no_change(self):
        from visual.interactivity.notifications import (
            NotificationSystem, NotificationPosition
        )
        ns = NotificationSystem(
            position=NotificationPosition.TOP_LEFT,
            timeout=7000,
            max_visible=3
        )
        ns.configure()
        assert ns.position == NotificationPosition.TOP_LEFT
        assert ns.timeout == 7000
        assert ns.max_visible == 3


class TestGetStatistics:
    """Line 148: get_statistics returns config dict."""

    def test_returns_expected_keys(self):
        from visual.interactivity.notifications import NotificationSystem
        ns = NotificationSystem()
        stats = ns.get_statistics()
        assert 'default_position' in stats
        assert 'auto_dismiss_timeout' in stats
        assert 'max_notifications' in stats
        assert 'available_types' in stats
        assert 'available_positions' in stats

    def test_statistics_reflect_config(self):
        from visual.interactivity.notifications import (
            NotificationSystem, NotificationPosition
        )
        ns = NotificationSystem(
            position=NotificationPosition.BOTTOM_CENTER,
            timeout=9000,
            max_visible=2
        )
        stats = ns.get_statistics()
        assert stats['default_position'] == 'bottom-center'
        assert stats['auto_dismiss_timeout'] == 9000
        assert stats['max_notifications'] == 2


class TestCreateNotificationSystem:
    """Lines 164-165: create_notification_system with invalid position falls back."""

    def test_valid_position(self):
        from visual.interactivity.notifications import create_notification_system
        ns = create_notification_system(position="bottom-left")
        assert ns.position.value == "bottom-left"

    def test_invalid_position_defaults_to_top_right(self):
        from visual.interactivity.notifications import create_notification_system
        ns = create_notification_system(position="invalid-position")
        assert ns.position.value == "top-right"

    def test_custom_timeout(self):
        from visual.interactivity.notifications import create_notification_system
        ns = create_notification_system(timeout=1000)
        assert ns.timeout == 1000

    def test_custom_max_notifications(self):
        from visual.interactivity.notifications import create_notification_system
        ns = create_notification_system(max_notifications=8)
        assert ns.max_visible == 8


class TestAddNotificationsToMap:
    """Lines 172-174: add_notifications_to_map convenience function."""

    def test_returns_notification_system(self):
        from visual.interactivity.notifications import add_notifications_to_map
        mock_map = MagicMock()
        mock_root = MagicMock()
        mock_html = MagicMock()
        mock_map.get_root.return_value = mock_root
        mock_root.html = mock_html
        result = add_notifications_to_map(mock_map)
        from visual.interactivity.notifications import NotificationSystem
        assert isinstance(result, NotificationSystem)

    def test_adds_to_map(self):
        from visual.interactivity.notifications import add_notifications_to_map
        mock_map = MagicMock()
        mock_root = MagicMock()
        mock_html = MagicMock()
        mock_map.get_root.return_value = mock_root
        mock_root.html = mock_html
        add_notifications_to_map(mock_map, position="bottom-right", timeout=2000)
        mock_html.add_child.assert_called_once()
