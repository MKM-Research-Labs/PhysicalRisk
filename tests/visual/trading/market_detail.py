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

"""Detailed regression tests for Market tab (td_market.py) JS generation.

Protects against regressions like the vanishing commit button, missing
endpoints, and broken dirty-state tracking.
"""

import pytest


@pytest.fixture(scope='module')
def market_js():
    """Get market tab JS once for all tests."""
    from visual.interactivity.trading import market
    return market.get_js()


class TestCommitButton:
    """Regression: Commit button must ALWAYS be present and functional."""

    def test_commit_button_id_present(self, market_js):
        """td-commit-btn ID present in output."""
        assert 'td-commit-btn' in market_js

    def test_commit_button_not_hidden(self, market_js):
        """Commit button must NOT have display:none in its own style."""
        btn_idx = market_js.index('td-commit-btn')
        own_style = market_js[btn_idx:btn_idx + 250]
        assert 'display:none' not in own_style

    def test_commit_function_defined(self, market_js):
        """tdCommitMarket function must exist."""
        assert 'tdCommitMarket' in market_js

    def test_commit_button_calls_function(self, market_js):
        """Button must call tdCommitMarket()."""
        assert 'tdCommitMarket()' in market_js


class TestCommitEndpoints:
    """Commit must POST to correct endpoints."""

    def test_commit_posts_yield_curve(self, market_js):
        """Hits /trading/yield-curve/commit."""
        assert '/trading/yield-curve/commit' in market_js

    def test_commit_posts_hazard_ts(self, market_js):
        """Hits /trading/hazard-term-structure/commit."""
        assert '/trading/hazard-term-structure/commit' in market_js

    def test_commit_shows_pnl_impact(self, market_js):
        """Commit notification shows P&L impact."""
        assert 'total_pnl_impact' in market_js
        assert 'gross_pnl_impact' in market_js

    def test_commit_switches_to_blotter(self, market_js):
        """After commit, switches to blotter tab."""
        assert "switchTab('blotter')" in market_js


class TestResetEndpoints:
    """Reset buttons must hit correct endpoints."""

    def test_reset_yield_curve_endpoint(self, market_js):
        """Hits /trading/yield-curve/reset."""
        assert '/trading/yield-curve/reset' in market_js

    def test_reset_hazard_ts_endpoint(self, market_js):
        """Hits /trading/hazard-term-structure/reset."""
        assert '/trading/hazard-term-structure/reset' in market_js

    def test_reset_function_exists(self, market_js):
        """tdResetCurve function exists."""
        assert 'tdResetCurve' in market_js


class TestDirtyStateTracking:
    """Dirty-state flags must be tracked for uncommitted changes."""

    def test_yield_dirty_flag(self, market_js):
        """tdYieldDirty variable tracks yield curve changes."""
        assert 'tdYieldDirty' in market_js

    def test_hazard_dirty_keys(self, market_js):
        """tdHazardDirtyKeys tracks per-gauge hazard changes."""
        assert 'tdHazardDirtyKeys' in market_js

    def test_uncommitted_label(self, market_js):
        """Shows UNCOMMITTED label when dirty."""
        assert 'UNCOMMITTED' in market_js


class TestActionButtonFormat:
    """History, PL Hist, Commit, Reset must match header tab group format exactly."""

    def test_buttons_in_shared_container(self, market_js):
        """All four buttons must sit inside a single flex container (group)."""
        assert ('display:flex;border:1px solid var(--line-strong);border-radius:4px;'
                'overflow:hidden;') in market_js, \
            "Buttons must be in a bordered group container matching header tabs"

    def test_history_button_grey_not_blue(self, market_js):
        """History button must be the sunken grey — inactive, like an unselected tab."""
        idx = market_js.index('td-history-btn')
        snippet = market_js[idx:idx+300]
        assert 'var(--sunken)' in snippet, "History button must be grey, not blue"
        assert 'var(--accent)' not in snippet, "History must NOT be blue — only Commit is"

    def test_plhist_button_grey_not_blue(self, market_js):
        """PL Hist button must be the sunken grey — inactive, like an unselected tab."""
        idx = market_js.index('td-plhist-btn')
        snippet = market_js[idx:idx+300]
        assert 'var(--sunken)' in snippet, "PL Hist button must be grey, not blue"
        assert 'var(--accent)' not in snippet, "PL Hist must NOT be blue — only Commit is"

    def test_commit_button_blue(self, market_js):
        """Commit button must be the accent blue — primary action, like an active tab."""
        idx = market_js.index('td-commit-btn')
        snippet = market_js[idx:idx+300]
        assert 'var(--accent)' in snippet, "Commit button must be the accent blue"
        assert 'color:var(--inverse)' in snippet, "Commit button text must be inverse ink"

    def test_reset_button_grey(self, market_js):
        """Reset button must be the sunken grey — inactive."""
        commit_idx = market_js.index('tdResetCurve')
        snippet = market_js[commit_idx:commit_idx+200]
        assert 'var(--sunken)' in snippet, "Reset button must be grey"

    def test_button_padding_matches_tabs(self, market_js):
        """All buttons must use padding:4px 14px matching header tab buttons."""
        count = market_js.count('padding:4px 14px')
        assert count >= 4, \
            f"Expected >=4 buttons with 'padding:4px 14px', found {count}"

    def test_button_font_matches_tabs(self, market_js):
        """All buttons must use font-size:11px;font-weight:600 matching header tabs."""
        count = market_js.count('font-size:11px')
        assert count >= 4, \
            f"Expected >=4 elements with font-size:11px in market JS, found {count}"

    def test_no_individual_border_radius_on_buttons(self, market_js):
        """Individual buttons must NOT have border-radius — container provides the rounding."""
        for btn_id in ['td-history-btn', 'td-plhist-btn', 'td-commit-btn']:
            idx = market_js.index(btn_id)
            snippet = market_js[idx:idx+250]
            assert 'border-radius' not in snippet, \
                f"{btn_id} must not have individual border-radius — use container overflow:hidden"


class TestNewTradeButton:
    """New Trade button must appear left of History and open PRS screen."""

    def test_new_trade_button_present(self, market_js):
        """td-newtrade-btn must exist in Market tab."""
        assert 'td-newtrade-btn' in market_js, \
            "New Trade button (id=td-newtrade-btn) missing from Market tab"

    def test_new_trade_button_label(self, market_js):
        """Button text must be 'New Trade'."""
        assert 'New Trade' in market_js

    def test_new_trade_left_of_history(self, market_js):
        """New Trade button must appear to the LEFT of History in the DOM."""
        nt_idx = market_js.index('td-newtrade-btn')
        hist_idx = market_js.index('td-history-btn')
        assert nt_idx < hist_idx, \
            "New Trade button must appear before History button in the HTML"

    def test_new_trade_calls_function(self, market_js):
        """Button must call tdMarketNewTrade()."""
        assert 'tdMarketNewTrade' in market_js

    def test_new_trade_function_opens_prs(self, market_js):
        """tdMarketNewTrade must hide trading desk and call viewHazardCurve."""
        assert 'viewHazardCurve' in market_js
        assert 'tdSelectedGauge' in market_js

    def test_new_trade_button_grey(self, market_js):
        """New Trade button must be the sunken grey — non-primary action."""
        idx = market_js.index('td-newtrade-btn')
        snippet = market_js[idx:idx + 300]
        assert 'var(--sunken)' in snippet, "New Trade button must be grey"
        assert 'var(--accent)' not in snippet, "New Trade must NOT be blue"

    def test_no_border_radius_on_new_trade_btn(self, market_js):
        """New Trade button must not have its own border-radius (container clips it)."""
        idx = market_js.index('td-newtrade-btn')
        snippet = market_js[idx:idx + 250]
        assert 'border-radius' not in snippet


class TestMarketUIStructure:
    """Market tab UI structure must be present."""

    def test_mode_selector(self, market_js):
        """Curve mode selector with yield/hazard options."""
        assert 'td-curve-mode' in market_js
        assert 'Yield Curve' in market_js
        assert 'Hazard' in market_js

    def test_gauge_list_function(self, market_js):
        """renderGaugeList function exists."""
        assert 'renderGaugeList' in market_js

    def test_market_canvas(self, market_js):
        """Chart canvas element present."""
        assert 'td-market-canvas' in market_js

    def test_cleanup_function(self, market_js):
        """tdCleanupMarketCharts exists."""
        assert 'tdCleanupMarketCharts' in market_js
