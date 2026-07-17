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

"""Tests for Market tab, Curves tab, and Aggregate map JavaScript rendering."""


class TestCommitButtonPresence:
    """Regression: Commit button must ALWAYS be present on the Market tab."""

    def test_commit_button_in_html(self):
        """Market tab must contain a visible commit button with correct ID."""
        from visual.interactivity.trading import market
        js = market.get_js()
        assert 'td-commit-btn' in js, "Commit button ID missing from Market tab"

    def test_commit_button_not_hidden(self):
        """Commit button must NOT have display:none in its own style."""
        from visual.interactivity.trading import market
        js = market.get_js()
        btn_idx = js.index('td-commit-btn')
        # Only check the button's own inline style (after the id), not neighbours
        own_style = js[btn_idx:btn_idx + 250]
        assert 'display:none' not in own_style, \
            "Commit button must not be hidden by default"

    def test_commit_button_calls_commit_function(self):
        """Commit button must call tdCommitMarket()."""
        from visual.interactivity.trading import market
        js = market.get_js()
        assert 'tdCommitMarket()' in js or 'tdCommitMarket(' in js, \
            "Commit button must call tdCommitMarket"

    def test_commit_function_exists(self):
        """tdCommitMarket function must be defined."""
        from visual.interactivity.trading import market
        js = market.get_js()
        assert 'tdCommitMarket = function' in js or \
               'function tdCommitMarket' in js, \
            "tdCommitMarket function not defined"

    def test_commit_posts_to_endpoint(self):
        """Commit function must POST to hazard-term-structure/commit."""
        from visual.interactivity.trading import market
        js = market.get_js()
        assert '/trading/hazard-term-structure/commit' in js, \
            "Commit must POST to hazard-term-structure/commit endpoint"

    def test_commit_refreshes_blotter(self):
        """After commit, must switch to blotter tab (which loads blotter data)."""
        from visual.interactivity.trading import market
        js = market.get_js()
        assert "switchTab('blotter')" in js, \
            "Commit must switch to blotter tab to show updated P&L"


class TestCurvesTabRedesign:
    """Test the redesigned Curves tab (all 40 gauge hazard curves)."""

    def test_curves_renders(self):
        """Curves sub-module should render without errors."""
        from visual.interactivity.trading import curves
        js = curves.get_js()
        assert len(js) > 0

    def test_curves_has_trigger_selector(self):
        """Curves tab should have alert/warning/severe trigger selector."""
        from visual.interactivity.trading import curves
        js = curves.get_js()
        assert 'td-curve-trigger' in js
        assert 'severe' in js
        assert 'warning' in js
        assert 'alert' in js

    def test_curves_uses_market_state(self):
        """Curves tab should fetch from market-state endpoint."""
        from visual.interactivity.trading import curves
        js = curves.get_js()
        assert '/api/v1/trading/market-state' in js

    def test_curves_hsl_colours(self):
        """Curves tab should use HSL for distinct line colours."""
        from visual.interactivity.trading import curves
        js = curves.get_js()
        assert 'hsl(' in js

    def test_curves_all_gauges_chart(self):
        """Curves tab should show all gauges on one chart."""
        from visual.interactivity.trading import curves
        js = curves.get_js()
        assert 'tdRenderAllCurves' in js
        assert 'tdCurveAllData' in js
        assert 'Hazard Term Structures' in js

    def test_curves_strips_thames_prefix(self):
        """Legend should strip 'Thames ' prefix for brevity."""
        from visual.interactivity.trading import curves
        js = curves.get_js()
        assert 'Thames' in js  # The replace pattern


class TestMapClickThrough:
    """Test Aggregate View click-through to GaugeHazardCurve."""

    def test_map_view_hazard_curve(self):
        """Map should have tdViewHazardCurve navigating to gauge panel."""
        from visual.interactivity.trading import aggregate
        js = aggregate.get_js()
        assert 'window.tdViewHazardCurve' in js
        assert 'GaugeHazardCurve' in js

    def test_map_new_trade_link(self):
        """Map should have New Trade link."""
        from visual.interactivity.trading import aggregate
        js = aggregate.get_js()
        assert 'window.tdNewTrade' in js
        assert 'New Trade' in js

    def test_map_hides_trading_desk(self):
        """Click-through should hide trading desk before opening gauge."""
        from visual.interactivity.trading import aggregate
        js = aggregate.get_js()
        assert 'TradingDesk.hide' in js
