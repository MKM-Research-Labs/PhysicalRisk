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

"""Tests for gauge hazard curve panel sub-modules (Historical + Stress)."""

import pytest


class TestHistoricalTab:
    """Test Historical Data tab (ghc_historical.py)."""

    def test_historical_renders(self):
        """Historical tab JS should render without errors."""
        from visual.interactivity.gauge.gaugehc import ghc_historical
        js = ghc_historical.get_js()
        assert len(js) > 0

    def test_historical_has_time_series_chart(self):
        """Should render a time series chart."""
        from visual.interactivity.gauge.gaugehc import ghc_historical
        js = ghc_historical.get_js()
        assert 'hist-timeseries-chart' in js
        assert 'renderHistorical' in js

    def test_historical_fetches_gauge_history(self):
        """Should fetch from /api/v1/gauges/<gauge_id>/history."""
        from visual.interactivity.gauge.gaugehc import ghc_historical
        js = ghc_historical.get_js()
        assert '/api/v1/gauges/' in js
        assert '/history' in js

    def test_historical_has_storm_scenarios(self):
        """Right panel should show storm scenarios list."""
        from visual.interactivity.gauge.gaugehc import ghc_historical
        js = ghc_historical.get_js()
        assert 'hist-storms-panel' in js
        assert 'hist-storms-list' in js
        assert 'Flood Storm Scenarios' in js

    def test_historical_fetches_stress_storms(self):
        """Should fetch from /api/v1/trading/stress/storms."""
        from visual.interactivity.gauge.gaugehc import ghc_historical
        js = ghc_historical.get_js()
        assert '/api/v1/trading/stress/storms' in js

    def test_historical_storm_click_navigates_to_stress(self):
        """Storm row click should navigate to Stress Test tab."""
        from visual.interactivity.gauge.gaugehc import ghc_historical
        js = ghc_historical.get_js()
        assert '_navigateToStress' in js
        assert '_stressStormHint' in js
        assert 'switchTab(5)' in js

    def test_historical_renders_storm_list(self):
        """Should have function to render storm list."""
        from visual.interactivity.gauge.gaugehc import ghc_historical
        js = ghc_historical.get_js()
        assert '_renderStormList' in js
        assert 'hist-storm-row' in js

    def test_historical_uses_event_listeners(self):
        """Should use addEventListener (not inline onclick) for storms."""
        from visual.interactivity.gauge.gaugehc import ghc_historical
        js = ghc_historical.get_js()
        assert 'addEventListener' in js

    def test_historical_shows_trigger_colors(self):
        """Storm rows should show trigger-colored dots."""
        from visual.interactivity.gauge.gaugehc import ghc_historical
        js = ghc_historical.get_js()
        assert '#FFC107' in js  # Alert
        assert '#FF9800' in js  # Warning
        assert '#F44336' in js  # Severe

    def test_historical_shows_flood_stages(self):
        """Chart should show flood stage threshold lines."""
        from visual.interactivity.gauge.gaugehc import ghc_historical
        js = ghc_historical.get_js()
        assert 'FloodAlert' in js
        assert 'FloodWarning' in js
        assert 'SevereFloodWarning' in js


class TestStressTestTab:
    """Test Stress Test tab (ghc_stress.py)."""

    def test_stress_renders(self):
        """Stress test JS should render without errors."""
        from visual.interactivity.gauge.gaugehc import ghc_stress
        js = ghc_stress.get_js()
        assert len(js) > 0

    def test_stress_has_storm_selector(self):
        """Should have storm selector dropdown."""
        from visual.interactivity.gauge.gaugehc import ghc_stress
        js = ghc_stress.get_js()
        assert 'stress-storm-select' in js
        assert '_populateStormSelect' in js

    def test_stress_fetches_storms(self):
        """Should fetch from /api/v1/trading/stress/storms."""
        from visual.interactivity.gauge.gaugehc import ghc_stress
        js = ghc_stress.get_js()
        assert '/api/v1/trading/stress/storms' in js

    def test_stress_runs_scenario(self):
        """Should POST to /api/v1/trading/stress/run."""
        from visual.interactivity.gauge.gaugehc import ghc_stress
        js = ghc_stress.get_js()
        assert '/api/v1/trading/stress/run' in js
        assert '_runStressScenario' in js

    def test_stress_has_chart_tabs(self):
        """Should have two chart sub-tabs: Flood Probability and Stress P&L."""
        from visual.interactivity.gauge.gaugehc import ghc_stress
        js = ghc_stress.get_js()
        assert 'Flood Probability' in js
        assert 'Stress P' in js  # Stress P&L (HTML-encoded)
        assert 'stress-ctab-0' in js
        assert 'stress-ctab-1' in js

    def test_stress_uses_event_listeners_for_tabs(self):
        """Chart tab clicks should use addEventListener (IIFE-safe)."""
        from visual.interactivity.gauge.gaugehc import ghc_stress
        js = ghc_stress.get_js()
        assert 'addEventListener' in js

    def test_stress_storm_hint_pickup(self):
        """Should pick up _stressStormHint from Historical tab."""
        from visual.interactivity.gauge.gaugehc import ghc_stress
        js = ghc_stress.get_js()
        assert '_stressStormHint' in js
        # Should clear hint after use
        assert '_stressStormHint = null' in js

    def test_stress_trade_table(self):
        """Should render trade table at peak hour."""
        from visual.interactivity.gauge.gaugehc import ghc_stress
        js = ghc_stress.get_js()
        assert 'stress-table-wrap' in js
        assert '_renderStressTable' in js

    def test_stress_has_cash_price_concept(self):
        """Should use cash pricing formula."""
        from visual.interactivity.gauge.gaugehc import ghc_stress
        js = ghc_stress.get_js()
        assert 'cash_price' in js or 'cashPrice' in js or 'portfolio_cash' in js

    def test_stress_shows_p_flood(self):
        """Should show P(flood) in chart."""
        from visual.interactivity.gauge.gaugehc import ghc_stress
        js = ghc_stress.get_js()
        assert 'p_flood' in js


class TestGaugeGraphInteractionConfigure:
    """Tests for gaugeha.GaugeGraphInteraction.configure() and get_statistics()."""

    def test_configure_panel_width(self):
        """Lines 283-284: configure(panel_width=...) updates panel_width."""
        from visual.interactivity.gauge.gaugeha import GaugeGraphInteraction
        obj = GaugeGraphInteraction()
        obj.configure(panel_width="800px")
        assert obj.panel_width == "800px"

    def test_configure_panel_height(self):
        """Lines 285-286: configure(panel_height=...) updates panel_height."""
        from visual.interactivity.gauge.gaugeha import GaugeGraphInteraction
        obj = GaugeGraphInteraction()
        obj.configure(panel_height="600px")
        assert obj.panel_height == "600px"

    def test_get_statistics(self):
        """Line 290: get_statistics() returns dict with panel_width and panel_height."""
        from visual.interactivity.gauge.gaugeha import GaugeGraphInteraction
        obj = GaugeGraphInteraction(panel_width="700px", panel_height="500px")
        stats = obj.get_statistics()
        assert stats["panel_width"] == "700px"
        assert stats["panel_height"] == "500px"


class TestGaugeHazardCurveConfigure:
    """Tests for gaugehc.GaugeHazardCurve.configure() and get_statistics()."""

    def test_configure_panel_width(self):
        """Lines 478-479: configure(panel_width=...) updates panel_width."""
        from visual.interactivity.gauge.gaugehc import GaugeHazardCurve
        obj = GaugeHazardCurve()
        obj.configure(panel_width="900px")
        assert obj.panel_width == "900px"

    def test_configure_panel_height(self):
        """Lines 480-481: configure(panel_height=...) updates panel_height."""
        from visual.interactivity.gauge.gaugehc import GaugeHazardCurve
        obj = GaugeHazardCurve()
        obj.configure(panel_height="700px")
        assert obj.panel_height == "700px"

    def test_get_statistics(self):
        """Line 485: get_statistics() returns dict."""
        from visual.interactivity.gauge.gaugehc import GaugeHazardCurve
        obj = GaugeHazardCurve()
        stats = obj.get_statistics()
        assert "panel_width" in stats
        assert "panel_height" in stats


class TestGaugeStormAnalysisConfigure:
    """Tests for gaugesa.GaugeStormAnalysis.configure() and get_statistics()."""

    def test_configure_panel_width(self):
        """Lines 268-269: configure(panel_width=...) updates panel_width."""
        from visual.interactivity.gauge.gaugesa import GaugeStormAnalysis
        obj = GaugeStormAnalysis()
        obj.configure(panel_width="850px")
        assert obj.panel_width == "850px"

    def test_configure_panel_height(self):
        """Lines 270-271: configure(panel_height=...) updates panel_height."""
        from visual.interactivity.gauge.gaugesa import GaugeStormAnalysis
        obj = GaugeStormAnalysis()
        obj.configure(panel_height="650px")
        assert obj.panel_height == "650px"

    def test_get_statistics(self):
        """Line 275: get_statistics() returns dict."""
        from visual.interactivity.gauge.gaugesa import GaugeStormAnalysis
        obj = GaugeStormAnalysis()
        stats = obj.get_statistics()
        assert "panel_width" in stats
        assert "panel_height" in stats
