# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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
