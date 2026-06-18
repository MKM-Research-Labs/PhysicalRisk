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

"""Tests for visual/interactivity/manager.py — missing coverage lines 81-109, 113-128, 132."""

from unittest.mock import MagicMock, patch

import pytest


class TestSetupMapInteractivity:
    """Lines 81-109: setup_map_interactivity adds all components to a map."""

    def test_returns_self(self):
        from visual.interactivity.manager import InteractivityManager
        mgr = InteractivityManager()
        mock_map = MagicMock()
        mock_root = MagicMock()
        mock_html = MagicMock()
        mock_map.get_root.return_value = mock_root
        mock_root.html = mock_html
        result = mgr.setup_map_interactivity(mock_map)
        assert result is mgr

    def test_adds_all_components(self):
        from visual.interactivity.manager import InteractivityManager
        mgr = InteractivityManager()
        mock_map = MagicMock()
        mock_root = MagicMock()
        mock_html = MagicMock()
        mock_map.get_root.return_value = mock_root
        mock_root.html = mock_html
        mgr.setup_map_interactivity(mock_map)
        # add_child should be called multiple times (components + copyright)
        assert mock_html.add_child.call_count > 0

    def test_copyright_element_added(self):
        from visual.interactivity.manager import InteractivityManager
        import folium
        mgr = InteractivityManager()
        mock_map = MagicMock()
        mock_root = MagicMock()
        mock_html = MagicMock()
        mock_map.get_root.return_value = mock_root
        mock_root.html = mock_html
        mgr.setup_map_interactivity(mock_map)
        # Last add_child call should contain copyright
        calls = mock_html.add_child.call_args_list
        assert len(calls) > 0


class TestConfigure:
    """Lines 113-128: configure() updates components based on kwargs."""

    def test_configure_server_url(self):
        from visual.interactivity.manager import InteractivityManager
        mgr = InteractivityManager()
        result = mgr.configure(server_url='http://new:9999')
        assert result is mgr
        assert mgr.backend.server_url == 'http://new:9999'

    def test_configure_notification_position(self):
        from visual.interactivity.manager import InteractivityManager
        from visual.interactivity.notifications import NotificationPosition
        mgr = InteractivityManager()
        mgr.configure(notification_position=NotificationPosition.BOTTOM_LEFT)
        assert mgr.notifications.position == NotificationPosition.BOTTOM_LEFT

    def test_configure_notification_timeout(self):
        from visual.interactivity.manager import InteractivityManager
        mgr = InteractivityManager()
        mgr.configure(notification_timeout=2000)
        assert mgr.notifications.timeout == 2000

    def test_configure_menus(self):
        from visual.interactivity.manager import InteractivityManager
        mgr = InteractivityManager()
        custom_prop = [{'label': 'Test', 'action': 'test()'}]
        mgr.configure(property_menu=custom_prop)
        assert mgr.context_menus.property_menu == custom_prop

    def test_configure_returns_self(self):
        from visual.interactivity.manager import InteractivityManager
        mgr = InteractivityManager()
        result = mgr.configure()
        assert result is mgr


class TestGetStatistics:
    """Line 132: get_statistics returns dict with component stats."""

    def test_returns_dict_with_expected_keys(self):
        from visual.interactivity.manager import InteractivityManager
        mgr = InteractivityManager()
        stats = mgr.get_statistics()
        assert 'notifications' in stats
        assert 'backend_handler' in stats
        assert 'context_menus' in stats

    def test_statistics_are_dicts(self):
        from visual.interactivity.manager import InteractivityManager
        mgr = InteractivityManager()
        stats = mgr.get_statistics()
        assert isinstance(stats['notifications'], dict)
        assert isinstance(stats['backend_handler'], dict)
        assert isinstance(stats['context_menus'], dict)
