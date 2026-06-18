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

"""Tests for visual/interactivity/trading/td_main_map.py — coverage for get_statistics."""

from unittest.mock import MagicMock

import pytest


class TestMainMapFS01GetStatistics:
    """Line 233: get_statistics returns component identifier."""

    def test_get_statistics_returns_dict(self):
        from visual.interactivity.trading.td_main_map import MainMapFS01
        obj = MainMapFS01()
        result = obj.get_statistics()
        assert isinstance(result, dict)
        assert result["component"] == "main_map_fs01"

    def test_get_js_returns_script(self):
        from visual.interactivity.trading.td_main_map import MainMapFS01
        obj = MainMapFS01()
        js = obj.get_js()
        assert "<script>" in js
        assert "refreshMainMapFS01" in js

    def test_add_to_map_calls_add_child(self):
        from visual.interactivity.trading.td_main_map import MainMapFS01
        obj = MainMapFS01()
        mock_map = MagicMock()
        mock_root = MagicMock()
        mock_html = MagicMock()
        mock_map.get_root.return_value = mock_root
        mock_root.html = mock_html
        obj.add_to_map(mock_map)
        mock_html.add_child.assert_called_once()
