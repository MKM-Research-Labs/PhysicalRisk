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
E2E tests: gauge PRS Pricing tab — market hazard curve data lineage.

Verifies that market hazard term structure data flows from the API
through to the PRS Pricing chart. This is the client-side counterpart
of tests/routes/lineage/test_hazard_to_pricer.py (backend lineage).

Tests the full chain:
  /api/v1/trading/hazard-term-structure → _mktHazardTS JS variable
  → PRS Pricing chart datasets → rendered chart has non-zero data
"""

import pytest

from tests.e2e.helpers import close_gauge_panel, open_gauge_panel


class TestGaugePRSMarketCurve:
    """PRS Pricing tab must display market hazard curve data."""

    @pytest.fixture(autouse=True)
    def open_prs_tab(self, map_page, first_gauge_id):
        open_gauge_panel(map_page, first_gauge_id)
        # PRS Pricing is tab 0
        tab = map_page.locator(".hazard-tab[data-tab='0']")
        if tab.count() == 0:
            pytest.skip("PRS Pricing tab not found")
        tab.click(force=True)
        map_page.wait_for_timeout(5_000)
        yield
        close_gauge_panel(map_page)

    def test_hazard_term_structure_api_reachable(self, map_page):
        """The hazard-term-structure API must be reachable from the browser."""
        result = map_page.evaluate("""async () => {
            try {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                var resp = await fetch(baseUrl + '/api/v1/trading/hazard-term-structure');
                var data = await resp.json();
                return {
                    status: data.status,
                    gauge_count: data.hazard_term_structure
                        ? Object.keys(data.hazard_term_structure).length : 0,
                    http_status: resp.status
                };
            } catch (e) {
                return { error: e.message };
            }
        }""")
        assert 'error' not in result, f"API fetch failed: {result.get('error')}"
        assert result['status'] == 'success', f"API returned: {result}"
        assert result['gauge_count'] > 0, "API returned empty hazard_term_structure"

    def test_mkt_hazard_ts_populated(self, map_page):
        """_mktHazardTS JS variable must be non-null after panel loads."""
        result = map_page.evaluate("""() => {
            if (typeof window._mktHazardTS === 'undefined' || window._mktHazardTS === null) return { exists: false };
            return {
                exists: true,
                gauge_count: Object.keys(window._mktHazardTS).length
            };
        }""")
        assert result['exists'], (
            "_mktHazardTS is null — market hazard data not loaded. "
            "Check _fetchMarketHazardTS() in ghc_hazard.py"
        )
        assert result['gauge_count'] > 0, (
            "_mktHazardTS is empty object — API returned no gauges"
        )

    def test_mkt_hazard_ts_has_current_gauge(self, map_page, first_gauge_id):
        """_mktHazardTS must contain data for the open gauge."""
        result = map_page.evaluate(f"""() => {{
            if (!window._mktHazardTS) return {{ has_gauge: false, reason: 'null' }};
            var gid = '{first_gauge_id}';
            var gData = window._mktHazardTS[gid];
            if (!gData) return {{ has_gauge: false, reason: 'missing_gauge', available: Object.keys(window._mktHazardTS).slice(0,5) }};
            return {{
                has_gauge: true,
                has_severe: !!gData.severe,
                has_warning: !!gData.warning,
                has_alert: !!gData.alert,
                severe_1y: gData.severe ? gData.severe['1'] : null
            }};
        }}""")
        assert result['has_gauge'], (
            f"_mktHazardTS missing {first_gauge_id}: {result}"
        )
        assert result['has_severe'], (
            f"_mktHazardTS[{first_gauge_id}] missing 'severe' key"
        )
        assert result['severe_1y'] is not None and result['severe_1y'] > 0, (
            f"_mktHazardTS[{first_gauge_id}].severe['1'] is zero or null"
        )

    def test_prs_hazard_chart_has_data(self, map_page):
        """The PRS hazard curve chart (left panel) must have non-zero data points."""
        result = map_page.evaluate("""() => {
            var chart = window._prsHazardCurveChart;
            if (!chart) return { exists: false, reason: 'no_chart_instance' };
            var datasets = chart.data.datasets || [];
            if (datasets.length === 0) return { exists: true, reason: 'no_datasets' };
            var hazardDs = datasets[0];
            var data = hazardDs.data || [];
            var nonNull = data.filter(function(d) { return d !== null && d > 0; });
            return {
                exists: true,
                label: hazardDs.label,
                data_length: data.length,
                non_null_count: nonNull.length,
                sample: data.slice(0, 5)
            };
        }""")
        assert result['exists'], f"Chart not found: {result.get('reason')}"
        assert result['non_null_count'] > 0, (
            f"Hazard curve chart has no data points. "
            f"Dataset: '{result.get('label')}', data: {result.get('sample')}. "
            f"This means _mktHazardTS data is not reaching the chart renderer."
        )

    def test_pv_premium_chart_has_data_on_open(self, map_page):
        """PV Premium bars (blue) must have non-zero values on initial open."""
        result = map_page.evaluate("""() => {
            var chart = window.currentChart || null;
            // currentChart is the cashflow bar chart in the hazard-chart canvas
            if (!chart || !chart.data || !chart.data.datasets) return { exists: false, reason: 'no_chart' };
            var premDs = chart.data.datasets.find(function(ds) {
                return ds.label && ds.label.indexOf('Premium') !== -1;
            });
            if (!premDs) return { exists: true, reason: 'no_premium_dataset', labels: chart.data.datasets.map(function(d) { return d.label; }) };
            var data = premDs.data || [];
            var nonZero = data.filter(function(d) { return d > 0; });
            return {
                exists: true,
                has_premium: true,
                data_length: data.length,
                non_zero_count: nonZero.length,
                sample: data.slice(0, 3)
            };
        }""")
        if not result.get('exists'):
            pytest.skip(f"Chart not available: {result.get('reason')}")
        if not result.get('has_premium'):
            pytest.fail(
                f"No PV Premium dataset found. Datasets: {result.get('labels')}"
            )
        assert result['non_zero_count'] > 0, (
            f"PV Premium bars are all zero on initial open. "
            f"Spread may not have been auto-populated before chart render. "
            f"Sample: {result.get('sample')}"
        )

    def test_prs_hazard_chart_values_are_reasonable(self, map_page):
        """Chart values should be in a reasonable bps range (1-10000)."""
        result = map_page.evaluate("""() => {
            var chart = window._prsHazardCurveChart;
            if (!chart || !chart.data.datasets || chart.data.datasets.length === 0) return null;
            var data = chart.data.datasets[0].data || [];
            var valid = data.filter(function(d) { return d !== null && d > 0; });
            if (valid.length === 0) return null;
            return {
                min: Math.min.apply(null, valid),
                max: Math.max.apply(null, valid),
                count: valid.length
            };
        }""")
        if result is None:
            pytest.skip("No chart data to validate")
        assert result['min'] >= 1.0, f"Hazard rate too low: {result['min']} bps"
        assert result['max'] <= 10000.0, f"Hazard rate too high: {result['max']} bps"
