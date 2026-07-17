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
