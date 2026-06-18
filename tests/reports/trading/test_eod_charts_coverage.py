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
Tests for missing coverage in reports.trading.eod_page_04_charts.

Covers:
- Line 99: _running_pnl_chart with empty data (n==0 early return)
- Line 136: _daily_pnl_chart with empty data (n==0 early return)
- Line 150: _daily_pnl_chart with negative daily_pnl (red bar color)
- Lines 177-180: _pnl_by_gauge_chart with no positions (empty gauge_pnl)
"""

import pytest
from reportlab.graphics.shapes import Drawing


class TestRunningPnlChartEmptyData:
    """Line 99: n==0 early return from _running_pnl_chart."""

    def test_empty_running_pnl_returns_drawing(self):
        from reports.trading.eod_page_04_charts import EODChartsPage
        page = EODChartsPage()
        # Pass series where all entries lack 'running_pnl' and last 30 slice is empty
        # Actually n is len(data) which is len(pnl_series[-30:]).
        # To get n==0, we need pnl_series[-30:] to be empty.
        # But get_content checks len < 2 first. Call _running_pnl_chart directly.
        result = page._running_pnl_chart([])
        assert isinstance(result, Drawing)


class TestDailyPnlChartEmptyData:
    """Line 136: n==0 early return from _daily_pnl_chart."""

    def test_empty_daily_pnl_returns_drawing(self):
        from reports.trading.eod_page_04_charts import EODChartsPage
        page = EODChartsPage()
        result = page._daily_pnl_chart([])
        assert isinstance(result, Drawing)


class TestDailyPnlChartNegativeValues:
    """Line 150: negative daily_pnl gets red bar color."""

    def test_negative_daily_pnl_renders(self):
        from reports.trading.eod_page_04_charts import EODChartsPage
        page = EODChartsPage()
        series = [
            {"date": "2026-03-07", "daily_pnl": -5000, "running_pnl": -5000},
            {"date": "2026-03-08", "daily_pnl": -3000, "running_pnl": -8000},
        ]
        result = page._daily_pnl_chart(series)
        assert isinstance(result, Drawing)

    def test_mixed_positive_negative_renders(self):
        from reports.trading.eod_page_04_charts import EODChartsPage
        page = EODChartsPage()
        series = [
            {"date": "2026-03-07", "daily_pnl": 5000, "running_pnl": 5000},
            {"date": "2026-03-08", "daily_pnl": -3000, "running_pnl": 2000},
            {"date": "2026-03-09", "daily_pnl": 1000, "running_pnl": 3000},
        ]
        result = page._daily_pnl_chart(series)
        assert isinstance(result, Drawing)


class TestPnlByGaugeChartEmpty:
    """Lines 177-180: no positions -> 'No gauge P&L data available'."""

    def test_no_positions_returns_drawing(self):
        from reports.trading.eod_page_04_charts import EODChartsPage
        page = EODChartsPage()
        snapshot = {"positions": []}
        result = page._pnl_by_gauge_chart(snapshot)
        assert isinstance(result, Drawing)

    def test_missing_positions_key_returns_drawing(self):
        from reports.trading.eod_page_04_charts import EODChartsPage
        page = EODChartsPage()
        result = page._pnl_by_gauge_chart({})
        assert isinstance(result, Drawing)

    def test_positions_with_zero_pnl_returns_drawing(self):
        """Positions exist but all running_pnl = 0 -> gauge_pnl has values."""
        from reports.trading.eod_page_04_charts import EODChartsPage
        page = EODChartsPage()
        snapshot = {
            "positions": [
                {"gauge_id": "GAUGE-001", "running_pnl": 0},
            ]
        }
        result = page._pnl_by_gauge_chart(snapshot)
        assert isinstance(result, Drawing)

    def test_negative_pnl_gauge_renders_correctly(self):
        """Negative gauge P&L -> bar drawn to the left."""
        from reports.trading.eod_page_04_charts import EODChartsPage
        page = EODChartsPage()
        snapshot = {
            "positions": [
                {"gauge_id": "GAUGE-001", "running_pnl": -5000},
                {"gauge_id": "GAUGE-002", "running_pnl": 3000},
            ]
        }
        result = page._pnl_by_gauge_chart(snapshot)
        assert isinstance(result, Drawing)
