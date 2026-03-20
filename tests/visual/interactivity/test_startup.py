"""Tests for visual/interactivity/startup.py — missing coverage lines 52-53, 60."""

from unittest.mock import MagicMock

import pytest


class TestStartupPreloaderAddToMap:
    """Lines 52-53: add_to_map wraps JS in script tags and adds to folium map."""

    def test_add_to_map_calls_add_child(self):
        from visual.interactivity.startup import StartupPreloader
        preloader = StartupPreloader()
        mock_map = MagicMock()
        mock_root = MagicMock()
        mock_html = MagicMock()
        mock_map.get_root.return_value = mock_root
        mock_root.html = mock_html
        preloader.add_to_map(mock_map)
        mock_html.add_child.assert_called_once()

    def test_add_to_map_output_contains_script(self):
        from visual.interactivity.startup import StartupPreloader
        import folium
        preloader = StartupPreloader()
        mock_map = MagicMock()
        mock_root = MagicMock()
        mock_html = MagicMock()
        mock_map.get_root.return_value = mock_root
        mock_root.html = mock_html
        preloader.add_to_map(mock_map)
        call_args = mock_html.add_child.call_args
        element = call_args[0][0]
        # folium.Element renders via _template
        rendered = element._template.render()
        assert '<script>' in rendered
        assert 'window._tdPreloadDone' in rendered


class TestGetPreloaderJs:
    """Line 60: _get_preloader_js delegates to get_js."""

    def test_get_preloader_js_returns_string(self):
        from visual.interactivity.startup import _get_preloader_js
        result = _get_preloader_js()
        assert isinstance(result, str)
        assert 'DOMContentLoaded' in result

    def test_get_preloader_js_matches_get_js(self):
        from visual.interactivity.startup import _get_preloader_js, get_js
        assert _get_preloader_js() == get_js()
