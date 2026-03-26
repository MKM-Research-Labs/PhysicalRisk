# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Governance e2e tests: Field Lineage tab/API and Audit Reports tab/API.
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    get_governance_content_text,
    open_governance,
    switch_governance_tab,
)


# ---------------------------------------------------------------------------
# Field Lineage tab
# ---------------------------------------------------------------------------


class TestFieldLineageTab:
    """Field Lineage tab: BCBS 239 P3 field traceability."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_panels(map_page)
        open_governance(map_page)
        switch_governance_tab(map_page, "field-lineage")
        map_page.wait_for_timeout(6_000)  # API fetch + render
        yield
        close_all_panels(map_page)

    def test_tab_content_loads(self, map_page):
        """Field Lineage tab should render content."""
        content = map_page.locator("#mg-content")
        assert content.count() > 0
        text = content.inner_text()
        assert len(text.strip()) > 0, "Field Lineage tab is empty"

    def test_content_mentions_field_keywords(self, map_page):
        """Should mention field lineage terms."""
        text = get_governance_content_text(map_page)
        keywords = ["field", "lineage", "report", "source", "bcbs",
                     "traceability", "section"]
        assert any(kw in text for kw in keywords), \
            f"No field lineage keywords found: {text[:200]}"

    def test_has_report_cards_or_search(self, map_page):
        """Should have report cards grid or search bar."""
        content = map_page.locator("#mg-content")
        inputs = content.locator("input")
        # Report cards typically rendered as clickable divs
        text = content.inner_text().lower()
        has_reports = (
            inputs.count() > 0  # search bar
            or "report" in text
            or "gauge" in text
            or "property" in text
        )
        assert has_reports, "No report cards or search bar in field lineage"

    def test_shows_field_counts(self, map_page):
        """Should display total field and report counts."""
        text = get_governance_content_text(map_page)
        has_counts = (
            "field" in text
            and any(c.isdigit() for c in text)
        )
        assert has_counts, f"No field counts found: {text[:200]}"


# ---------------------------------------------------------------------------
# Field Lineage API tests
# ---------------------------------------------------------------------------


class TestFieldLineageAPI:
    """Direct API tests for field lineage endpoints."""

    def test_field_lineage_api_returns_data(self, map_page):
        """GET /api/v1/governance/field-lineage should return registry."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/field-lineage'
            );
            var data = await resp.json();
            return {
                http_status: resp.status,
                has_reports: !!data.reports && Object.keys(data.reports).length > 0,
                total_fields: data.total_fields || 0,
            };
        }""")
        assert result["http_status"] == 200, \
            f"Field lineage API returned {result['http_status']}"
        assert result["has_reports"], "No reports returned"
        assert result["total_fields"] > 0, "Zero fields returned"

    def test_field_search_api(self, map_page):
        """GET /api/v1/governance/field-lineage/lookup should search fields."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/field-lineage/lookup?search=gauge'
            );
            var data = await resp.json();
            return {
                http_status: resp.status,
                result_count: (data.results || []).length,
            };
        }""")
        assert result["http_status"] == 200, \
            f"Field search API returned {result['http_status']}"
        assert result["result_count"] > 0, \
            "Search for 'gauge' returned no results"


# ---------------------------------------------------------------------------
# Audit Reports tab
# ---------------------------------------------------------------------------


class TestAuditReportsTab:
    """Audit Reports tab: test suite status + audit evidence package."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_panels(map_page)
        open_governance(map_page)
        switch_governance_tab(map_page, "audit-reports")
        map_page.wait_for_timeout(6_000)  # API fetch + render
        yield
        close_all_panels(map_page)

    def test_tab_content_loads(self, map_page):
        """Audit Reports tab should render content."""
        content = map_page.locator("#mg-content")
        assert content.count() > 0
        text = content.inner_text()
        assert len(text.strip()) > 0, "Audit Reports tab is empty"

    def test_content_mentions_audit_keywords(self, map_page):
        """Should mention audit or test terms."""
        text = get_governance_content_text(map_page)
        keywords = ["test", "audit", "coverage", "report", "passed",
                     "evidence", "artefact", "suite"]
        assert any(kw in text for kw in keywords), \
            f"No audit keywords found: {text[:200]}"

    def test_has_test_summary_or_file_cards(self, map_page):
        """Should show test summary counts or audit file cards."""
        content = map_page.locator("#mg-content")
        text = content.inner_text().lower()
        buttons = content.locator("button")
        has_content = (
            "passed" in text
            or "failed" in text
            or "total" in text
            or ".pdf" in text
            or ".xml" in text
            or buttons.count() > 0  # run tests button or file action buttons
        )
        assert has_content, "No test summary or file cards in audit reports"

    def test_has_artefact_files(self, map_page):
        """Should list audit artefact files (PDFs, XML, coverage)."""
        text = get_governance_content_text(map_page)
        file_keywords = ["coverage", "junit", "pdf", "report", "xml",
                         "latex", "duplication", "hardcoding"]
        found = [kw for kw in file_keywords if kw in text]
        assert len(found) >= 2, \
            f"Only {len(found)} file types found: {found}. Text: {text[:200]}"


# ---------------------------------------------------------------------------
# Audit Reports API tests
# ---------------------------------------------------------------------------


class TestAuditReportsAPI:
    """Direct API tests for audit report endpoints."""

    def test_audit_reports_api_returns_files(self, map_page):
        """GET /api/v1/governance/audit-reports should list artefacts."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/audit-reports'
            );
            var data = await resp.json();
            return {
                http_status: resp.status,
                report_count: (data.reports || []).length,
                has_coverage: !!data.coverage_available,
            };
        }""")
        assert result["http_status"] == 200, \
            f"Audit reports API returned {result['http_status']}"
        assert result["report_count"] > 0, "No audit artefact files returned"

    def test_test_summary_api(self, map_page):
        """GET /api/v1/governance/test-report/summary should return results."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/test-report/summary'
            );
            var data = await resp.json();
            return {
                http_status: resp.status,
                has_summary: !!data.summary,
                total: (data.summary || {}).total || 0,
            };
        }""")
        assert result["http_status"] == 200, \
            f"Test summary API returned {result['http_status']}"
        assert result["has_summary"], "No test summary in response"
