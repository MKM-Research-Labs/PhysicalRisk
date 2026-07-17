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
Governance e2e tests: Data Lineage tab, Data Lineage API, and Provenance Trace API.
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    get_governance_content_text,
    open_governance,
    switch_governance_tab,
)


# ---------------------------------------------------------------------------
# Data Lineage tab
# ---------------------------------------------------------------------------


class TestDataLineageTab:
    """Data Lineage tab: pipeline DAG, staleness table, provenance trace."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_panels(map_page)
        open_governance(map_page)
        switch_governance_tab(map_page, "lineage")
        map_page.wait_for_timeout(6_000)  # API fetch + DAG render
        yield
        close_all_panels(map_page)

    def test_tab_content_loads(self, map_page):
        """Data Lineage tab should render content."""
        content = map_page.locator("#mg-content")
        assert content.count() > 0
        text = content.inner_text()
        assert len(text.strip()) > 0, "Data Lineage tab is empty"

    def test_content_mentions_lineage_keywords(self, map_page):
        """Should mention pipeline or lineage terms."""
        text = get_governance_content_text(map_page)
        keywords = ["pipeline", "lineage", "step", "gauge", "property",
                     "blotter", "hazard", "fresh", "stale"]
        assert any(kw in text for kw in keywords), \
            f"No lineage keywords found: {text[:200]}"

    def test_has_pipeline_steps(self, map_page):
        """Should display pipeline step names."""
        text = get_governance_content_text(map_page)
        # At least some of the 10 pipeline steps should appear
        steps = ["gauges", "properties", "mortgages", "hazard",
                 "propertyts", "propertyhc", "blotter"]
        found = [s for s in steps if s in text]
        assert len(found) >= 3, \
            f"Only {len(found)} pipeline steps found in content: {found}"

    def test_has_staleness_info(self, map_page):
        """Should show staleness status (fresh/stale/missing)."""
        text = get_governance_content_text(map_page)
        keywords = ["fresh", "stale", "missing", "status", "last run", "health"]
        assert any(kw in text for kw in keywords), \
            f"No staleness info found: {text[:200]}"


# ---------------------------------------------------------------------------
# Data Lineage API tests
# ---------------------------------------------------------------------------


class TestDataLineageAPI:
    """Direct API tests for data lineage endpoints."""

    def test_lineage_api_returns_data(self, map_page):
        """GET /api/v1/governance/data-lineage should return pipeline data."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/data-lineage'
            );
            var data = await resp.json();
            return {
                http_status: resp.status,
                has_steps: (data.pipeline_steps || []).length > 0,
                has_summary: !!data.summary,
            };
        }""")
        assert result["http_status"] == 200, \
            f"Lineage API returned {result['http_status']}"
        assert result["has_steps"], "No pipeline steps returned"

    def test_staleness_api_returns_data(self, map_page):
        """GET /api/v1/governance/data-lineage/staleness should return health."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/data-lineage/staleness'
            );
            var data = await resp.json();
            return {
                http_status: resp.status,
                has_steps: (data.steps || []).length > 0,
                has_health: 'health_pct' in data,
            };
        }""")
        assert result["http_status"] == 200, \
            f"Staleness API returned {result['http_status']}"


# ---------------------------------------------------------------------------
# Provenance Trace API
# ---------------------------------------------------------------------------


class TestProvenanceTraceAPI:
    """Provenance trace: search for entity IDs across pipeline data files."""

    def test_trace_gauge_returns_steps(self, map_page, first_gauge_id):
        """Tracing a gauge ID should return multiple pipeline steps."""
        result = map_page.evaluate(f"""async () => {{
            var cfg = window.__BACKEND_CONFIG || {{}};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/data-lineage/trace?data_type=gauge&data_id={first_gauge_id}'
            );
            var data = await resp.json();
            return {{
                http_status: resp.status,
                found: data.found,
                trace_count: (data.trace || []).length,
                steps: (data.trace || []).map(function(t) {{ return t.step; }}),
                has_context: (data.trace || []).some(function(t) {{ return !!t.context; }}),
            }};
        }}""")
        assert result["http_status"] == 200
        assert result["found"], f"Gauge {first_gauge_id} not found in trace"
        assert result["trace_count"] >= 2, \
            f"Expected >=2 trace steps, got {result['trace_count']}: {result['steps']}"
        assert result["has_context"], "Trace entries missing context descriptions"

    def test_trace_property_returns_steps(self, map_page, first_property_id):
        """Tracing a property ID should return pipeline steps."""
        result = map_page.evaluate(f"""async () => {{
            var cfg = window.__BACKEND_CONFIG || {{}};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/data-lineage/trace?data_type=property&data_id={first_property_id}'
            );
            var data = await resp.json();
            return {{
                http_status: resp.status,
                found: data.found,
                trace_count: (data.trace || []).length,
            }};
        }}""")
        assert result["http_status"] == 200
        assert result["found"], f"Property {first_property_id} not found in trace"
        assert result["trace_count"] >= 1

    def test_trace_nonexistent_returns_empty(self, map_page):
        """Tracing a fake ID should return found=false."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/data-lineage/trace?data_type=gauge&data_id=GAUGE-NONEXISTENT'
            );
            var data = await resp.json();
            return {
                http_status: resp.status,
                found: data.found,
                trace_count: (data.trace || []).length,
            };
        }""")
        assert result["http_status"] == 200
        assert not result["found"]
        assert result["trace_count"] == 0

    def test_trace_missing_params_returns_400(self, map_page):
        """Trace with missing params should return 400."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/data-lineage/trace?data_type=gauge'
            );
            return { http_status: resp.status };
        }""")
        assert result["http_status"] == 400
