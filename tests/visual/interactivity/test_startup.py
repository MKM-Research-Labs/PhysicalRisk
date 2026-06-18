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
