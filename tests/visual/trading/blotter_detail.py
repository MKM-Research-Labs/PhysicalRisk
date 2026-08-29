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

"""Detailed regression tests for Blotter tab (td_blotter.py) JS generation.

Protects against regressions in filter bar, P&L display, signed notionals,
hazard rate arrows, and trade click-through.
"""

import pytest


@pytest.fixture(scope='module')
def blotter_js():
    """Get blotter tab JS once for all tests."""
    from visual.interactivity.trading import blotter
    return blotter.get_js()


class TestFilterBar:
    """Filter bar must have all dropdowns and functions."""

    def test_filter_function_exists(self, blotter_js):
        """tdFilterChanged function exists."""
        assert 'tdFilterChanged' in blotter_js

    def test_get_filtered_trades(self, blotter_js):
        """getFilteredTrades function exists."""
        assert 'getFilteredTrades' in blotter_js

    def test_external_filter_api(self, blotter_js):
        """tdApplyFilter exposed on window for external callers."""
        assert 'tdApplyFilter' in blotter_js

    def test_clear_filters(self, blotter_js):
        """tdClearFilters function exists."""
        assert 'tdClearFilters' in blotter_js

    def test_remove_single_filter(self, blotter_js):
        """tdRemoveFilter function exists."""
        assert 'tdRemoveFilter' in blotter_js


class TestNewPRSButton:
    """New PRS button appears when filtered to a single gauge."""

    def test_new_prs_function_exists(self, blotter_js):
        """tdNewPRS function must be defined."""
        assert 'tdNewPRS' in blotter_js

    def test_new_prs_button_label(self, blotter_js):
        """Button label must be 'New PRS'."""
        assert 'New PRS' in blotter_js

    def test_new_prs_conditional_on_gauge_filter(self, blotter_js):
        """Button only renders when tdBlotterFilters.gauge_id is set."""
        assert 'tdBlotterFilters.gauge_id' in blotter_js

    def test_new_prs_hides_trading_desk(self, blotter_js):
        """tdNewPRS must hide trading desk before opening gauge panel."""
        assert 'TradingDesk.hide' in blotter_js

    def test_new_prs_opens_gauge_hazard_curve(self, blotter_js):
        """tdNewPRS must call GaugeHazardCurve.show with filtered gauge."""
        assert 'GaugeHazardCurve.show' in blotter_js

    def test_new_prs_fallback_to_view_hazard(self, blotter_js):
        """tdNewPRS falls back to viewHazardCurve if GaugeHazardCurve unavailable."""
        assert 'viewHazardCurve' in blotter_js

    def test_new_prs_button_styled_blue(self, blotter_js):
        """New PRS button must be the accent blue — primary action."""
        idx = blotter_js.index('New PRS')
        snippet = blotter_js[max(0, idx - 200):idx + 50]
        assert 'var(--accent-mid)' in snippet, "New PRS button must be the accent blue"

    def test_new_prs_button_after_clear(self, blotter_js):
        """New PRS button must appear after Clear button in filter bar HTML."""
        assert blotter_js.index('clearBtn') < blotter_js.index('newPrsBtn')


class TestSortAndNavigation:
    """Sort toggle and trade click-through."""

    def test_sort_toggle(self, blotter_js):
        """tdToggleSort function exists."""
        assert 'tdToggleSort' in blotter_js

    def test_trade_view_click(self, blotter_js):
        """tdViewTrade function for click-through to PRS pricing."""
        assert 'tdViewTrade' in blotter_js


class TestPnLBar:
    """P&L bar must show all required metrics."""

    def test_pnl_bar_running(self, blotter_js):
        """Shows Running P&L."""
        assert 'Running' in blotter_js

    def test_pnl_bar_daily(self, blotter_js):
        """Shows daily P&L metric."""
        assert 'dailyPnl' in blotter_js

    def test_pnl_bar_from_market(self, blotter_js):
        """Shows From Market metric."""
        assert 'From Market' in blotter_js
        assert 'fromMarket' in blotter_js

    def test_pnl_bar_net_notional(self, blotter_js):
        """Shows signed net notional."""
        assert 'netNotional' in blotter_js
        assert 'fmtGBP(netNotional)' in blotter_js


class TestSignedNotionals:
    """Signed notional logic: payer → negative, receiver → positive."""

    def test_is_payer_referenced(self, blotter_js):
        """is_payer field used to determine sign."""
        assert 'is_payer' in blotter_js

    def test_signed_notional_direction(self, blotter_js):
        """Payer notional should be negated."""
        assert 'is_payer' in blotter_js
        assert 'Math.abs' in blotter_js


class TestHazardRateArrows:
    """Hazard column must show up/down arrows for rate changes."""

    def test_prev_fair_spread_comparison(self, blotter_js):
        """Blotter compares to prev_fair_spread_bps."""
        assert 'prev_fair_spread_bps' in blotter_js

    def test_up_arrow(self, blotter_js):
        """Shows up arrow for rate increase."""
        assert '\\u25b2' in blotter_js

    def test_down_arrow(self, blotter_js):
        """Shows down arrow for rate decrease."""
        assert '\\u25bc' in blotter_js


class TestMarketPnLColumn:
    """Market P&L column must be present."""

    def test_market_pnl_column(self, blotter_js):
        """Blotter has market_pnl column."""
        assert 'market_pnl' in blotter_js

    def test_mkt_pnl_label(self, blotter_js):
        """Blotter shows Mkt P&L label."""
        assert 'Mkt P' in blotter_js


class TestBlotterEndpoints:
    """Blotter must fetch from correct endpoint."""

    def test_blotter_fetches_correct_endpoint(self, blotter_js):
        """Hits /api/v1/trading/blotter."""
        assert '/api/v1/trading/blotter' in blotter_js

    def test_close_endpoint(self, blotter_js):
        """Close-out hits /trading/close/."""
        assert '/trading/close/' in blotter_js


class TestTableStructure:
    """Table column headers must be present."""

    def test_maturity_formatting(self, blotter_js):
        """fmtMaturity function exists."""
        assert 'fmtMaturity' in blotter_js

    def test_gauge_fs01_column(self, blotter_js):
        """gauge_fs01 column present."""
        assert 'gauge_fs01' in blotter_js
