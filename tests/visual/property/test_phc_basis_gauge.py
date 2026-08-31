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

"""Tests for Basis Explorer — Gauge sub-tab JS output."""

import pytest

from visual.interactivity.property import phc_basis_gauge


class TestBasisGaugeJS:
    """Verify the Gauge sub-tab JS contains required elements."""

    @pytest.fixture
    def js(self):
        return phc_basis_gauge.get_js()

    def test_render_function_defined(self, js):
        assert "function renderBasisGauge()" in js

    def test_reads_storm_details(self, js):
        assert "phcData.storm_details" in js

    def test_reads_nearest_gauges(self, js):
        assert "phcData.nearest_gauges" in js

    def test_reads_gauge_thresholds(self, js):
        assert "gauge_thresholds" in js

    def test_threshold_lines_for_severe(self, js):
        assert "severeLevel" in js
        assert "severeLine" in js

    def test_threshold_lines_for_warning(self, js):
        assert "warningLevel" in js
        assert "warningLine" in js

    def test_threshold_lines_for_alert(self, js):
        assert "alertLevel" in js
        assert "alertLine" in js

    def test_scatter_chart_type(self, js):
        assert "type: 'scatter'" in js

    def test_storm_click_sets_selected(self, js):
        assert "basisSelectedStorm" in js

    def test_click_triggers_rerender(self, js):
        assert "renderBasisSubTab(basisActiveSubTab)" in js

    def test_sorts_by_peak_level(self, js):
        assert "gauge_peak_m" in js
        assert "sort(" in js

    def test_severe_count_in_summary(self, js):
        assert "severeCount" in js

    def test_uses_exceeded_severe_flag(self, js):
        """Uses exceeded_severe from storm_details, not threshold comparison."""
        assert "exceeded_severe" in js

    def test_colours_by_severity(self, js):
        """Severe storms red, others grey."""
        assert "Theme.value('red-bright')" in js  # red
        assert "Theme.value('faint')" in js  # grey

    def test_tooltip_shows_storm_id(self, js):
        assert "Storm " in js
        assert "stormId" in js

    def test_stats_bar_updated(self, js):
        assert "phc-stats-bar" in js

    def test_chart_variable_declared(self, js):
        assert "var basisGaugeChart" in js

    def test_chart_destroyed_before_render(self, js):
        assert "basisGaugeChart.destroy()" in js
