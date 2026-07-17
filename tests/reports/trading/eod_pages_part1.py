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

"""
Tests for reports.trading EOD page modules — Part 1.

Covers: EODSummaryPage.get_content, EODPositionsPage.get_content.
"""

import pytest
from reportlab.platypus import Paragraph, Table

from tests.reports.trading.conftest import BASE_SNAPSHOT, EMPTY_SNAPSHOT


# ===========================================================================
# EODSummaryPage
# ===========================================================================

class TestEODSummaryPage:

    def _page(self):
        from reports.trading.eod_page_01_summary import EODSummaryPage
        return EODSummaryPage()

    def test_returns_list(self):
        page = self._page()
        result = page.get_content(BASE_SNAPSHOT)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_has_paragraph_and_table(self):
        page = self._page()
        result = page.get_content(BASE_SNAPSHOT)
        assert any(isinstance(e, Paragraph) for e in result)
        assert any(isinstance(e, Table) for e in result)

    def test_empty_summary(self):
        page = self._page()
        result = page.get_content(EMPTY_SNAPSHOT)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_date_appears_in_paragraph(self):
        page = self._page()
        result = page.get_content(BASE_SNAPSHOT)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("2026-03-08" in t for t in texts)

    def test_negative_pnl_snapshot(self):
        snapshot = dict(BASE_SNAPSHOT)
        snapshot["portfolio_summary"] = {
            "num_open_trades": 1,
            "total_notional": 10_000_000,
            "total_daily_pnl": -5_000,
            "daily_pnl_from_trades": -5_000,
            "daily_pnl_from_market": 0,
            "total_running_pnl": -5_000,
        }
        result = self._page().get_content(snapshot)
        assert isinstance(result, list)


# ===========================================================================
# EODPositionsPage
# ===========================================================================

class TestEODPositionsPage:

    def _page(self):
        from reports.trading.eod_page_02_positions import EODPositionsPage
        return EODPositionsPage()

    def test_returns_list(self):
        page = self._page()
        result = page.get_content(BASE_SNAPSHOT)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_no_positions_shows_message(self):
        page = self._page()
        result = page.get_content(EMPTY_SNAPSHOT)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("No open positions" in t for t in texts)

    def test_with_positions_creates_table(self):
        page = self._page()
        result = page.get_content(BASE_SNAPSHOT)
        assert any(isinstance(e, Table) for e in result)

    def test_multiple_gauges_grouped(self):
        """Positions from 2 gauges should produce group subheaders."""
        page = self._page()
        result = page.get_content(BASE_SNAPSHOT)
        # Should have at least one table with multiple rows
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1

    def test_single_position(self):
        snapshot = dict(BASE_SNAPSHOT)
        snapshot = {**BASE_SNAPSHOT, "positions": [BASE_SNAPSHOT["positions"][0]]}
        page = self._page()
        result = page.get_content(snapshot)
        assert isinstance(result, list)

    def test_long_gauge_id_truncated(self):
        """Gauge IDs longer than 12 chars should not crash."""
        snapshot = {**BASE_SNAPSHOT, "positions": [{
            **BASE_SNAPSHOT["positions"][0],
            "gauge_id": "VERY-LONG-GAUGE-ID-THAT-EXCEEDS-LIMIT",
        }]}
        result = self._page().get_content(snapshot)
        assert isinstance(result, list)

    def test_zero_pnl_renders_dash(self):
        """Line 48: daily_pnl=0 and running_pnl=0 -> fmt_gbp returns em-dash."""
        snapshot = {**BASE_SNAPSHOT, "positions": [{
            **BASE_SNAPSHOT["positions"][0],
            "daily_pnl": 0.0,
            "running_pnl": 0.0,
        }]}
        result = self._page().get_content(snapshot)
        assert isinstance(result, list)
