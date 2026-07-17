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

"""Tests for visual/interactivity/backend_handler.py — all method bodies."""

from unittest.mock import MagicMock, patch

import pytest


class TestBackendHandlerInit:
    """Constructor uses config defaults or custom values."""

    def test_default_init_uses_config(self):
        """Lines 60-61: default server_url and endpoints from config."""
        from config import config
        from visual.interactivity.backend_handler import BackendHandler

        handler = BackendHandler()
        assert handler.server_url == config.SERVER_URL
        assert handler.endpoints == config.ENDPOINTS

    def test_custom_init(self):
        """Lines 60-61: custom server_url and endpoints override config."""
        from visual.interactivity.backend_handler import BackendHandler

        handler = BackendHandler(server_url='http://test:9999',
                                 endpoints={'a': '/api/a'})
        assert handler.server_url == 'http://test:9999'
        assert handler.endpoints == {'a': '/api/a'}

    def test_endpoints_are_copied(self):
        """Endpoints dict is a copy, not a reference."""
        from visual.interactivity.backend_handler import BackendHandler

        eps = {'x': '/y'}
        handler = BackendHandler(endpoints=eps)
        eps['z'] = '/w'
        assert 'z' not in handler.endpoints


class TestGetJs:
    """Lines 65-73: get_js() returns script tag with config and JS code."""

    def test_returns_script_tag(self):
        from visual.interactivity.backend_handler import BackendHandler

        handler = BackendHandler(server_url='http://localhost:5013',
                                 endpoints={'health': '/api/v1/health'})
        js = handler.get_js()
        assert '<script>' in js
        assert '</script>' in js
        assert 'window.__BACKEND_CONFIG' in js
        # URL is intentionally empty — API calls use relative paths so the
        # baked HTML works on any port (see backend_handler.py lines 68-72).
        assert '"url": ""' in js

    def test_contains_timeout(self):
        from visual.interactivity.backend_handler import BackendHandler

        handler = BackendHandler(server_url='http://localhost:5013',
                                 endpoints={})
        js = handler.get_js()
        assert '30000' in js


class TestAddToMap:
    """Line 77: add_to_map adds Element to folium map."""

    def test_add_to_map_calls_add_child(self):
        from visual.interactivity.backend_handler import BackendHandler

        handler = BackendHandler(server_url='http://test:1234',
                                 endpoints={'a': '/b'})

        mock_map = MagicMock()
        mock_root = MagicMock()
        mock_html = MagicMock()
        mock_map.get_root.return_value = mock_root
        mock_root.html = mock_html

        handler.add_to_map(mock_map)
        mock_html.add_child.assert_called_once()


class TestConfigure:
    """Lines 81-84: configure() updates server_url and endpoints."""

    def test_configure_updates_server_url(self):
        from visual.interactivity.backend_handler import BackendHandler

        handler = BackendHandler(server_url='http://old:1111',
                                 endpoints={'a': '/b'})
        handler.configure(server_url='http://new:2222')
        assert handler.server_url == 'http://new:2222'
        assert handler.endpoints == {'a': '/b'}

    def test_configure_updates_endpoints(self):
        from visual.interactivity.backend_handler import BackendHandler

        handler = BackendHandler(server_url='http://test:1234',
                                 endpoints={'a': '/b'})
        handler.configure(endpoints={'c': '/d'})
        assert handler.endpoints == {'a': '/b', 'c': '/d'}

    def test_configure_no_args_no_change(self):
        from visual.interactivity.backend_handler import BackendHandler

        handler = BackendHandler(server_url='http://test:1234',
                                 endpoints={'a': '/b'})
        handler.configure()
        assert handler.server_url == 'http://test:1234'


class TestGetStatistics:
    """Line 88: get_statistics() returns dict with expected keys."""

    def test_get_statistics_keys(self):
        from visual.interactivity.backend_handler import BackendHandler

        handler = BackendHandler(server_url='http://test:1234',
                                 endpoints={'x': '/x', 'y': '/y'})
        stats = handler.get_statistics()
        assert stats['server_url'] == 'http://test:1234'
        assert stats['total_endpoints'] == 2
        assert set(stats['endpoints']) == {'x', 'y'}

    def test_get_statistics_single_endpoint(self):
        from visual.interactivity.backend_handler import BackendHandler

        handler = BackendHandler(server_url='http://test:1234',
                                 endpoints={'only': '/api/only'})
        stats = handler.get_statistics()
        assert stats['total_endpoints'] == 1
        assert stats['endpoints'] == ['only']
