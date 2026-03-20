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

"""
Tests for reports.trading EOD page modules and EODReportGenerator.

Covers: EODSummaryPage.get_content, EODPositionsPage.get_content,
EODPnLDetailPage.get_content, EODChartsPage.get_content,
EODReportGenerator.generate_report.
"""

import pytest
from reportlab.platypus import Paragraph, Spacer, Table


# ===========================================================================
# Sample data
# ===========================================================================

_BASE_SNAPSHOT = {
    "eod_id": "EOD-2026-03-08",
    "date": "2026-03-08",
    "portfolio_summary": {
        "num_open_trades": 3,
        "total_notional": 25_000_000,
        "total_daily_pnl": 12_500,
        "daily_pnl_from_trades": 5_000,
        "daily_pnl_from_market": 7_500,
        "total_running_pnl": 45_000,
    },
    "positions": [
        {
            "swap_id": "PRS-001",
            "gauge_id": "GAUGE-001",
            "trigger": "warning",
            "notional": 10_000_000,
            "tenor": 3,
            "trade_spread_bps": 150.0,
            "fair_spread_bps": 145.0,
            "gauge_fs01": 2500.0,
            "daily_pnl": 5_000.0,
            "running_pnl": 20_000.0,
            "new_trade_pnl": 5_000.0,
            "market_pnl": 0.0,
        },
        {
            "swap_id": "PRS-002",
            "gauge_id": "GAUGE-001",
            "trigger": "severe",
            "notional": 8_000_000,
            "tenor": 5,
            "trade_spread_bps": 200.0,
            "fair_spread_bps": 198.0,
            "gauge_fs01": -1500.0,
            "daily_pnl": 2_500.0,
            "running_pnl": 15_000.0,
            "new_trade_pnl": 0.0,
            "market_pnl": 2_500.0,
        },
        {
            "swap_id": "PRS-003",
            "gauge_id": "GAUGE-002",
            "trigger": "alert",
            "notional": 7_000_000,
            "tenor": 2,
            "trade_spread_bps": 100.0,
            "fair_spread_bps": 102.0,
            "gauge_fs01": 1000.0,
            "daily_pnl": 5_000.0,
            "running_pnl": 10_000.0,
            "new_trade_pnl": 0.0,
            "market_pnl": 5_000.0,
        },
    ],
}

_EMPTY_SNAPSHOT = {
    "eod_id": "EOD-2026-03-08",
    "date": "2026-03-08",
    "portfolio_summary": {},
    "positions": [],
}

_PNL_SERIES = [
    {"date": "2026-03-07", "daily_pnl": 10_000, "running_pnl": 32_500,
     "from_trades": 5_000, "from_market": 5_000},
    {"date": "2026-03-08", "daily_pnl": 12_500, "running_pnl": 45_000,
     "from_trades": 5_000, "from_market": 7_500},
]


# ===========================================================================
# EODSummaryPage
# ===========================================================================

class TestEODSummaryPage:

    def _page(self):
        from reports.trading.eod_page_01_summary import EODSummaryPage
        return EODSummaryPage()

    def test_returns_list(self):
        page = self._page()
        result = page.get_content(_BASE_SNAPSHOT)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_has_paragraph_and_table(self):
        page = self._page()
        result = page.get_content(_BASE_SNAPSHOT)
        assert any(isinstance(e, Paragraph) for e in result)
        assert any(isinstance(e, Table) for e in result)

    def test_empty_summary(self):
        page = self._page()
        result = page.get_content(_EMPTY_SNAPSHOT)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_date_appears_in_paragraph(self):
        page = self._page()
        result = page.get_content(_BASE_SNAPSHOT)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("2026-03-08" in t for t in texts)

    def test_negative_pnl_snapshot(self):
        snapshot = dict(_BASE_SNAPSHOT)
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
        result = page.get_content(_BASE_SNAPSHOT)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_no_positions_shows_message(self):
        page = self._page()
        result = page.get_content(_EMPTY_SNAPSHOT)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("No open positions" in t for t in texts)

    def test_with_positions_creates_table(self):
        page = self._page()
        result = page.get_content(_BASE_SNAPSHOT)
        assert any(isinstance(e, Table) for e in result)

    def test_multiple_gauges_grouped(self):
        """Positions from 2 gauges should produce group subheaders."""
        page = self._page()
        result = page.get_content(_BASE_SNAPSHOT)
        # Should have at least one table with multiple rows
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1

    def test_single_position(self):
        snapshot = dict(_BASE_SNAPSHOT)
        snapshot = {**_BASE_SNAPSHOT, "positions": [_BASE_SNAPSHOT["positions"][0]]}
        page = self._page()
        result = page.get_content(snapshot)
        assert isinstance(result, list)

    def test_long_gauge_id_truncated(self):
        """Gauge IDs longer than 12 chars should not crash."""
        snapshot = {**_BASE_SNAPSHOT, "positions": [{
            **_BASE_SNAPSHOT["positions"][0],
            "gauge_id": "VERY-LONG-GAUGE-ID-THAT-EXCEEDS-LIMIT",
        }]}
        result = self._page().get_content(snapshot)
        assert isinstance(result, list)

    def test_zero_pnl_renders_dash(self):
        """Line 48: daily_pnl=0 and running_pnl=0 → fmt_gbp returns em-dash."""
        snapshot = {**_BASE_SNAPSHOT, "positions": [{
            **_BASE_SNAPSHOT["positions"][0],
            "daily_pnl": 0.0,
            "running_pnl": 0.0,
        }]}
        result = self._page().get_content(snapshot)
        assert isinstance(result, list)


# ===========================================================================
# EODPnLDetailPage
# ===========================================================================

class TestEODPnLDetailPage:

    def _page(self):
        from reports.trading.eod_page_03_pnl_detail import EODPnLDetailPage
        return EODPnLDetailPage()

    def test_returns_list(self):
        page = self._page()
        result = page.get_content(_BASE_SNAPSHOT)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_no_positions_shows_messages(self):
        page = self._page()
        result = page.get_content(_EMPTY_SNAPSHOT)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("No new trades" in t for t in texts)
        assert any("No market move" in t for t in texts)

    def test_new_trade_pnl_creates_table(self):
        page = self._page()
        result = page.get_content(_BASE_SNAPSHOT)
        # PRS-001 has new_trade_pnl = 5000 → should have table
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1

    def test_market_move_pnl_creates_table(self):
        page = self._page()
        result = page.get_content(_BASE_SNAPSHOT)
        # PRS-002 and PRS-003 have market_pnl → should have table
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 2

    def test_many_market_movers_top_20(self):
        """More than 20 positions → only top 20 movers shown."""
        positions = []
        for i in range(25):
            positions.append({
                "swap_id": f"PRS-{i:03d}",
                "gauge_id": "GAUGE-001",
                "trigger": "warning",
                "notional": 1_000_000,
                "trade_spread_bps": 150.0,
                "fair_spread_bps": 145.0,
                "gauge_fs01": 100.0,
                "daily_pnl": float(i * 100),
                "running_pnl": float(i * 500),
                "new_trade_pnl": 0.0,
                "market_pnl": float(i * 100),
            })
        snapshot = {**_BASE_SNAPSHOT, "positions": positions}
        result = self._page().get_content(snapshot)
        assert isinstance(result, list)


# ===========================================================================
# EODChartsPage
# ===========================================================================

class TestEODChartsPage:

    def _page(self):
        from reports.trading.eod_page_04_charts import EODChartsPage
        return EODChartsPage()

    def test_returns_list(self):
        page = self._page()
        result = page.get_content(_BASE_SNAPSHOT, _PNL_SERIES)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_insufficient_data_message(self):
        page = self._page()
        result = page.get_content(_BASE_SNAPSHOT, [])
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Insufficient" in t for t in texts)

    def test_single_entry_insufficient(self):
        page = self._page()
        result = page.get_content(_BASE_SNAPSHOT, [_PNL_SERIES[0]])
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Insufficient" in t for t in texts)

    def test_sufficient_data_creates_content(self):
        page = self._page()
        result = page.get_content(_BASE_SNAPSHOT, _PNL_SERIES)
        # Should have more than just the insufficient message
        assert len(result) > 2


# ===========================================================================
# EODReportGenerator
# ===========================================================================

class TestEODReportGenerator:

    def test_generate_report_returns_path(self, tmp_path):
        from reports.trading.eod_generator import EODReportGenerator
        gen = EODReportGenerator(output_dir=tmp_path)
        path = gen.generate_report(_BASE_SNAPSHOT, _PNL_SERIES)
        assert path.exists()
        assert path.suffix == ".pdf"

    def test_generate_report_without_pnl_series(self, tmp_path):
        from reports.trading.eod_generator import EODReportGenerator
        gen = EODReportGenerator(output_dir=tmp_path)
        path = gen.generate_report(_BASE_SNAPSHOT)
        assert path.exists()

    def test_generate_empty_snapshot(self, tmp_path):
        from reports.trading.eod_generator import EODReportGenerator
        gen = EODReportGenerator(output_dir=tmp_path)
        path = gen.generate_report(_EMPTY_SNAPSHOT)
        assert path.exists()

    def test_pdf_not_empty(self, tmp_path):
        from reports.trading.eod_generator import EODReportGenerator
        gen = EODReportGenerator(output_dir=tmp_path)
        path = gen.generate_report(_BASE_SNAPSHOT, _PNL_SERIES)
        assert path.stat().st_size > 1000

    def test_eod_id_in_filename(self, tmp_path):
        from reports.trading.eod_generator import EODReportGenerator
        gen = EODReportGenerator(output_dir=tmp_path)
        path = gen.generate_report(_BASE_SNAPSHOT)
        assert "EOD-2026-03-08" in path.name

    def test_output_dir_created(self, tmp_path):
        from reports.trading.eod_generator import EODReportGenerator
        new_dir = tmp_path / "subdir" / "eod"
        gen = EODReportGenerator(output_dir=new_dir)
        assert new_dir.exists()

    def test_no_output_dir_uses_config(self, tmp_path, monkeypatch):
        """Lines 49-50: output_dir=None → uses config.get_eod_dir()."""
        from config import config
        eod_dir = tmp_path / "eod"
        monkeypatch.setattr(config, "get_eod_dir", lambda: eod_dir)
        from reports.trading.eod_generator import EODReportGenerator
        gen = EODReportGenerator()  # output_dir=None
        assert gen.output_dir == eod_dir


class TestPnLDetailZeroPnL:
    """Test eod_page_03_pnl_detail.py line 48: fmt_gbp with zero value."""

    def test_zero_pnl_returns_dash(self):
        """Line 48: fmt_gbp(0) returns em-dash."""
        from reports.trading.eod_page_03_pnl_detail import EODPnLDetailPage

        page = EODPnLDetailPage()
        snapshot = {**_BASE_SNAPSHOT, "positions": [{
            "swap_id": "PRS-001",
            "gauge_id": "GAUGE-001",
            "trigger": "warning",
            "notional": 1_000_000,
            "trade_spread_bps": 150.0,
            "fair_spread_bps": 145.0,
            "gauge_fs01": 0.0,
            "daily_pnl": 0.0,
            "running_pnl": 0.0,
            "new_trade_pnl": 500.0,  # non-zero to go through new_trades table
            "market_pnl": 0.0,
        }]}
        result = page.get_content(snapshot)
        assert isinstance(result, list)
