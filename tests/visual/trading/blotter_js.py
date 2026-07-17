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

"""Tests for blotter and market P&L JavaScript rendering."""


class TestBlotterSignedNotionals:
    """Test signed notional logic in blotter JS."""

    def test_signed_notional_payer_negative(self):
        """Payer (Pay) should show negative notional."""
        from visual.interactivity.trading import blotter
        js = blotter.get_js()
        # The signed notional logic: is_payer → negative
        assert 'is_payer' in js
        assert 'netNotional' in js

    def test_net_notional_in_pnl_bar(self):
        """P&L bar should display net notional (signed sum)."""
        from visual.interactivity.trading import blotter
        js = blotter.get_js()
        assert 'netNotional' in js
        assert 'fmtGBP(netNotional)' in js


class TestMarketPnLDisplay:
    """Regression: Market P&L must flow through from engine to blotter UI."""

    def test_blotter_has_market_pnl_column(self):
        """Blotter must have a Mkt P&L column."""
        from visual.interactivity.trading import blotter
        js = blotter.get_js()
        assert "'market_pnl'" in js or '"market_pnl"' in js, \
            "Blotter must have market_pnl column"
        assert 'Mkt P' in js, "Blotter must show 'Mkt P&L' label"

    def test_blotter_has_from_market_in_pnl_bar(self):
        """P&L bar must show 'From Market' metric."""
        from visual.interactivity.trading import blotter
        js = blotter.get_js()
        assert 'From Market' in js, "P&L bar must show 'From Market'"
        assert 'fromMarket' in js, "P&L bar must compute fromMarket from filtered trades"

    def test_hazard_column_up_down_arrows(self):
        """Hazard column must show up/down arrows when fair != prev_fair."""
        from visual.interactivity.trading import blotter
        js = blotter.get_js()
        assert 'prev_fair_spread_bps' in js, \
            "Blotter must compare to prev_fair_spread_bps"
        # Up arrow (▲) and down arrow (▼) unicode
        assert '\\u25b2' in js, "Must show up arrow for rate increase"
        assert '\\u25bc' in js, "Must show down arrow for rate decrease"

    def test_commit_shows_pnl_impact(self):
        """Market tab commit notification must show P&L impact."""
        from visual.interactivity.trading import market
        js = market.get_js()
        assert 'total_pnl_impact' in js, \
            "Commit notification must show net P&L impact"
        assert 'gross_pnl_impact' in js, \
            "Commit notification must show gross P&L impact"


class TestGrossMarketPnL:
    """Regression: Gross market P&L must be computed and returned."""
