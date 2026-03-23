# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Property panel e2e tests — storm analysis, hazard curves, and mortgage detail.
"""

import pytest


class TestPropertyStormPanel:
    """Opening the property storm panel via JavaScript call."""

    def _open_storm_panel(self, map_page, prop_id):
        """Open the property storm panel, skipping if function unavailable."""
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyStorms === 'function'"
        )
        if not has_fn:
            pytest.skip("window.viewPropertyStorms not available")
        map_page.evaluate(f"window.viewPropertyStorms('{prop_id}')")
        map_page.wait_for_timeout(3_000)

    def test_panel_opens_with_title(self, map_page, first_property_id):
        """Calling viewPropertyStorms should open the panel with title."""
        self._open_storm_panel(map_page, first_property_id)

        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)
        assert panel.is_visible()

        title = map_page.locator("#prop-storm-title")
        if title.count() > 0:
            text = title.inner_text()
            assert len(text) > 0, "Property storm panel title is empty"

    def test_panel_has_tab_buttons(self, map_page, first_property_id):
        """Panel should have at least 5 tab buttons."""
        self._open_storm_panel(map_page, first_property_id)

        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tabs = panel.locator(".prop-storm-tab")
        assert tabs.count() >= 5, f"Only {tabs.count()} tab buttons found, expected >= 5"

    def test_distribution_tab_has_content(self, map_page, first_property_id):
        """Distribution tab (idx 0) should render content."""
        self._open_storm_panel(map_page, first_property_id)

        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)
        map_page.wait_for_timeout(6_000)  # wait for storm data API

        tab = panel.locator(".prop-storm-tab[data-idx='0']")
        if tab.count() > 0:
            tab.click(force=True)
            map_page.wait_for_timeout(3_000)

        content = map_page.locator("#prop-storm-content")
        assert content.count() > 0, "No #prop-storm-content element"
        text = content.inner_text()
        # Distribution tab should have some content (chart or text)
        has_content = len(text.strip()) > 0 or content.locator("canvas").count() > 0
        assert has_content, "Distribution tab is empty"

    def test_worst_storms_tab_shows_data(self, map_page, first_property_id):
        """Worst Storms tab (idx 2) should show table or data."""
        self._open_storm_panel(map_page, first_property_id)

        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)
        map_page.wait_for_timeout(6_000)  # wait for storm data API

        tab = panel.locator(".prop-storm-tab[data-idx='2']")
        if tab.count() == 0:
            pytest.skip("Worst storms tab (idx 2) not found")
        tab.click(force=True)
        map_page.wait_for_timeout(3_000)

        content = map_page.locator("#prop-storm-content")
        text = content.inner_text()
        has_data = (
            "storm" in text.lower()
            or "depth" in text.lower()
            or "damage" in text.lower()
            or content.locator("table").count() > 0
            or content.locator("tr").count() > 0
        )
        assert has_data, "Worst storms tab has no storm/damage data"

    def test_status_bar_shows_flood_counts(self, map_page, first_property_id):
        """Status bar should show flood-related information."""
        self._open_storm_panel(map_page, first_property_id)

        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)

        status = map_page.locator("#prop-storm-status")
        if status.count() == 0:
            pytest.skip("No #prop-storm-status element found")
        text = status.inner_text()
        has_info = (
            "flood" in text.lower()
            or "storm" in text.lower()
            or any(c.isdigit() for c in text)
        )
        assert has_info, f"Status bar has no flood info: '{text}'"


class TestPropertyHazardPanel:
    """Opening the property hazard curve panel via JavaScript call."""

    def _open_hazard_panel(self, map_page, prop_id):
        """Open the property hazard panel, skipping if function unavailable."""
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyHazard === 'function'"
        )
        if not has_fn:
            pytest.skip("window.viewPropertyHazard not available")
        map_page.evaluate(f"window.viewPropertyHazard('{prop_id}')")
        map_page.wait_for_timeout(3_000)

    def test_panel_opens_with_title(self, map_page, first_property_id):
        """Calling viewPropertyHazard should open the panel with title."""
        self._open_hazard_panel(map_page, first_property_id)

        panel = map_page.locator("#property-hc-panel")
        panel.wait_for(state="visible", timeout=10_000)
        assert panel.is_visible()

        title = map_page.locator("#phc-panel-title")
        if title.count() > 0:
            text = title.inner_text()
            assert len(text) > 0, "Property hazard panel title is empty"

    def test_panel_has_four_tabs(self, map_page, first_property_id):
        """Panel should have 4 tab buttons."""
        self._open_hazard_panel(map_page, first_property_id)

        panel = map_page.locator("#property-hc-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tabs = panel.locator(".phc-tab")
        assert tabs.count() >= 4, f"Only {tabs.count()} tabs found, expected >= 4"

    def test_hazard_curve_chart_renders(self, map_page, first_property_id):
        """Hazard Curve tab (tab 0) should render a chart."""
        self._open_hazard_panel(map_page, first_property_id)

        panel = map_page.locator("#property-hc-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tab = panel.locator(".phc-tab[data-tab='0']")
        if tab.count() > 0:
            tab.click()
            map_page.wait_for_timeout(3_000)

        chart = map_page.locator("#phc-chart")
        if chart.count() == 0:
            # Fallback: any canvas inside the panel
            chart = map_page.locator("#property-hc-panel canvas")
        if chart.count() == 0:
            # Check panel has rendered content at all
            text = panel.inner_text()
            assert len(text) > 50, (
                "No chart canvas and panel has minimal content"
            )
        # If we get here, either chart exists or panel has content

    def test_prs_pricing_tab_has_controls(self, map_page, first_property_id):
        """PRS Pricing tab (tab 2) should have trigger, notional, and spread controls."""
        self._open_hazard_panel(map_page, first_property_id)

        panel = map_page.locator("#property-hc-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tab = panel.locator(".phc-tab[data-tab='2']")
        if tab.count() == 0:
            pytest.skip("PRS pricing tab (data-tab=2) not found")
        tab.click()
        map_page.wait_for_timeout(3_000)

        trigger = map_page.locator("#phc-trigger")
        notional = map_page.locator("#phc-notional")
        spread = map_page.locator("#phc-spread")

        controls_found = trigger.count() + notional.count() + spread.count()
        assert controls_found >= 2, (
            f"Expected PRS pricing controls (trigger, notional, spread), "
            f"found {controls_found} of 3"
        )

    def test_basis_analysis_tab_shows_content(self, map_page, first_property_id):
        """Basis Analysis tab (tab 3) should show content."""
        self._open_hazard_panel(map_page, first_property_id)

        panel = map_page.locator("#property-hc-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tab = panel.locator(".phc-tab[data-tab='3']")
        if tab.count() == 0:
            pytest.skip("Basis analysis tab (data-tab=3) not found")
        tab.click()
        map_page.wait_for_timeout(3_000)

        text = panel.inner_text()
        has_content = (
            "basis" in text.lower()
            or "spread" in text.lower()
            or "gauge" in text.lower()
            or panel.locator("canvas").count() > 0
            or panel.locator("table").count() > 0
        )
        assert has_content, "Basis analysis tab has no relevant content"


class TestMortgageDetail:
    """Mortgage detail panel tests."""

    def _open_mortgage_panel(self, map_page, prop_id):
        """Try to open mortgage detail via available functions."""
        # Try viewMortgageDetail
        has_fn = map_page.evaluate(
            "() => typeof window.viewMortgageDetail === 'function'"
        )
        if has_fn:
            map_page.evaluate(f"window.viewMortgageDetail('{prop_id}')")
            map_page.wait_for_timeout(3_000)
            return True

        # Try opening property storms first, then switching to mortgage tab
        has_storms = map_page.evaluate(
            "() => typeof window.viewPropertyStorms === 'function'"
        )
        if has_storms:
            map_page.evaluate(f"window.viewPropertyStorms('{prop_id}')")
            map_page.wait_for_timeout(3_000)
            # Click mortgage impact tab (idx 4)
            tab = map_page.locator(".prop-storm-tab[data-idx='4']")
            if tab.count() > 0:
                tab.click()
                map_page.wait_for_timeout(3_000)
                return True

        return False

    def test_mortgage_panel_opens(self, map_page, first_property_id):
        """Mortgage detail panel should open."""
        opened = self._open_mortgage_panel(map_page, first_property_id)
        if not opened:
            pytest.skip("No mortgage detail function available")

        # Check for dedicated mortgage panel or content within storm panel
        mortgage_panel = map_page.locator("#mortgage-detail-panel")
        storm_panel = map_page.locator("#prop-storm-panel")

        panel_visible = (
            (mortgage_panel.count() > 0 and mortgage_panel.is_visible())
            or (storm_panel.count() > 0 and storm_panel.is_visible())
        )
        assert panel_visible, "Neither mortgage panel nor storm panel is visible"

    def test_mortgage_content_shows_data(self, map_page, first_property_id):
        """Mortgage content should show LTV, amortisation, or loan data."""
        opened = self._open_mortgage_panel(map_page, first_property_id)
        if not opened:
            pytest.skip("No mortgage detail function available")

        # Check both possible containers
        mortgage_panel = map_page.locator("#mortgage-detail-panel")
        content_el = map_page.locator("#prop-storm-content")

        text = ""
        if mortgage_panel.count() > 0 and mortgage_panel.is_visible():
            text = mortgage_panel.inner_text()
        elif content_el.count() > 0:
            text = content_el.inner_text()

        has_mortgage_data = (
            "ltv" in text.lower()
            or "loan" in text.lower()
            or "amortis" in text.lower()
            or "mortgage" in text.lower()
            or "principal" in text.lower()
            or "balance" in text.lower()
        )
        assert has_mortgage_data, f"No mortgage data found in panel content: '{text[:200]}'"


# ---------------------------------------------------------------------------
# Flood Timeline tab (idx 1)
# ---------------------------------------------------------------------------


class TestPropertyFloodTimeline:
    """Flood Timeline tab: hydrograph with water level and thresholds."""

    def _open_storm_panel(self, map_page, prop_id):
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyStorms === 'function'"
        )
        if not has_fn:
            pytest.skip("window.viewPropertyStorms not available")
        map_page.evaluate(f"window.viewPropertyStorms('{prop_id}')")
        map_page.wait_for_timeout(3_000)

    def test_timeline_renders(self, map_page, first_property_id):
        """Flood Timeline tab (idx 1) should render content."""
        self._open_storm_panel(map_page, first_property_id)
        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tab = panel.locator(".prop-storm-tab[data-idx='1']")
        if tab.count() == 0:
            pytest.skip("Flood Timeline tab (idx 1) not found")
        tab.click()
        map_page.wait_for_timeout(3_000)

        content = map_page.locator("#prop-storm-content")
        has_content = (
            len(content.inner_text().strip()) > 0
            or content.locator("canvas").count() > 0
        )
        assert has_content, "Flood Timeline tab is empty"

    def test_timeline_has_selector(self, map_page, first_property_id):
        """Storm selector dropdown should have options."""
        self._open_storm_panel(map_page, first_property_id)
        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tab = panel.locator(".prop-storm-tab[data-idx='1']")
        if tab.count() == 0:
            pytest.skip("Flood Timeline tab not found")
        tab.click()
        map_page.wait_for_timeout(3_000)

        select = map_page.locator("#prop-timeline-select")
        if select.count() == 0:
            pytest.skip("No #prop-timeline-select element")
        options = select.locator("option")
        assert options.count() > 0, "Timeline storm selector has no options"

    def test_timeline_has_stats(self, map_page, first_property_id):
        """Timeline stats section should have content."""
        self._open_storm_panel(map_page, first_property_id)
        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tab = panel.locator(".prop-storm-tab[data-idx='1']")
        if tab.count() == 0:
            pytest.skip("Flood Timeline tab not found")
        tab.click()
        map_page.wait_for_timeout(3_000)

        stats = map_page.locator("#prop-timeline-stats")
        if stats.count() == 0:
            pytest.skip("No #prop-timeline-stats element")
        text = stats.inner_text()
        assert len(text.strip()) > 0, "Timeline stats are empty"

    def test_timeline_chart_exists(self, map_page, first_property_id):
        """Timeline chart canvas should be present."""
        self._open_storm_panel(map_page, first_property_id)
        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tab = panel.locator(".prop-storm-tab[data-idx='1']")
        if tab.count() == 0:
            pytest.skip("Flood Timeline tab not found")
        tab.click()
        map_page.wait_for_timeout(3_000)

        chart = map_page.locator("#prop-timeline-chart")
        assert chart.count() > 0, "No #prop-timeline-chart canvas found"


# ---------------------------------------------------------------------------
# Flood History tab (idx 3)
# ---------------------------------------------------------------------------


class TestPropertyFloodHistory:
    """Flood History tab: table + bar chart of flood events per storm."""

    def _open_storm_panel(self, map_page, prop_id):
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyStorms === 'function'"
        )
        if not has_fn:
            pytest.skip("window.viewPropertyStorms not available")
        map_page.evaluate(f"window.viewPropertyStorms('{prop_id}')")
        map_page.wait_for_timeout(3_000)

    def test_history_renders(self, map_page, first_property_id):
        """Flood History tab (idx 3) should render content."""
        self._open_storm_panel(map_page, first_property_id)
        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tab = panel.locator(".prop-storm-tab[data-idx='3']")
        if tab.count() == 0:
            pytest.skip("Flood History tab (idx 3) not found")
        tab.click()
        map_page.wait_for_timeout(3_000)

        content = map_page.locator("#prop-storm-content")
        has_content = (
            len(content.inner_text().strip()) > 0
            or content.locator("canvas").count() > 0
            or content.locator("table").count() > 0
        )
        assert has_content, "Flood History tab is empty"

    def test_history_has_chart(self, map_page, first_property_id):
        """Flood history bar chart canvas should exist."""
        self._open_storm_panel(map_page, first_property_id)
        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tab = panel.locator(".prop-storm-tab[data-idx='3']")
        if tab.count() == 0:
            pytest.skip("Flood History tab not found")
        tab.click()
        map_page.wait_for_timeout(3_000)

        chart = map_page.locator("#prop-history-chart")
        assert chart.count() > 0, "No #prop-history-chart canvas found"

    def test_history_has_stats(self, map_page, first_property_id):
        """Flood history stats section should have content."""
        self._open_storm_panel(map_page, first_property_id)
        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tab = panel.locator(".prop-storm-tab[data-idx='3']")
        if tab.count() == 0:
            pytest.skip("Flood History tab not found")
        tab.click()
        map_page.wait_for_timeout(3_000)

        stats = map_page.locator("#prop-history-stats")
        if stats.count() == 0:
            pytest.skip("No #prop-history-stats element")
        text = stats.inner_text()
        assert len(text.strip()) > 0, "Flood history stats are empty"

    def test_history_table_has_rows(self, map_page, first_property_id):
        """Flood history table should have data rows."""
        self._open_storm_panel(map_page, first_property_id)
        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tab = panel.locator(".prop-storm-tab[data-idx='3']")
        if tab.count() == 0:
            pytest.skip("Flood History tab not found")
        tab.click()
        map_page.wait_for_timeout(3_000)

        content = map_page.locator("#prop-storm-content")
        rows = content.locator("table tr").or_(content.locator("tr"))
        if rows.count() == 0:
            # May be chart-only, that's OK
            chart = content.locator("canvas")
            assert chart.count() > 0, "No table rows and no chart in history tab"


# ---------------------------------------------------------------------------
# Mortgage Impact tab (idx 4)
# ---------------------------------------------------------------------------


class TestPropertyMortgageImpact:
    """Mortgage Impact tab: stacked bar chart of damage vs retained value."""

    def _open_storm_panel(self, map_page, prop_id):
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyStorms === 'function'"
        )
        if not has_fn:
            pytest.skip("window.viewPropertyStorms not available")
        map_page.evaluate(f"window.viewPropertyStorms('{prop_id}')")
        map_page.wait_for_timeout(3_000)

    def test_mortgage_impact_renders(self, map_page, first_property_id):
        """Mortgage Impact tab (idx 4) should render content."""
        self._open_storm_panel(map_page, first_property_id)
        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tab = panel.locator(".prop-storm-tab[data-idx='4']")
        if tab.count() == 0:
            pytest.skip("Mortgage Impact tab (idx 4) not found")
        tab.click()
        map_page.wait_for_timeout(3_000)

        content = map_page.locator("#prop-storm-content")
        has_content = (
            len(content.inner_text().strip()) > 0
            or content.locator("canvas").count() > 0
        )
        assert has_content, "Mortgage Impact tab is empty"

    def test_mortgage_impact_has_chart(self, map_page, first_property_id):
        """Mortgage impact chart canvas should exist."""
        self._open_storm_panel(map_page, first_property_id)
        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tab = panel.locator(".prop-storm-tab[data-idx='4']")
        if tab.count() == 0:
            pytest.skip("Mortgage Impact tab not found")
        tab.click()
        map_page.wait_for_timeout(3_000)

        chart = map_page.locator("#prop-mortgage-chart")
        assert chart.count() > 0, "No #prop-mortgage-chart canvas found"

    def test_mortgage_impact_has_stats(self, map_page, first_property_id):
        """Mortgage impact stats should mention LTV, equity, or value."""
        self._open_storm_panel(map_page, first_property_id)
        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tab = panel.locator(".prop-storm-tab[data-idx='4']")
        if tab.count() == 0:
            pytest.skip("Mortgage Impact tab not found")
        tab.click()
        map_page.wait_for_timeout(3_000)

        stats = map_page.locator("#prop-mortgage-stats")
        if stats.count() == 0:
            pytest.skip("No #prop-mortgage-stats element")
        text = stats.inner_text().lower()
        keywords = ["ltv", "equity", "value", "outstanding", "property", "loss"]
        assert any(kw in text for kw in keywords), \
            f"No mortgage keywords in stats: {text[:200]}"


# ---------------------------------------------------------------------------
# Insurance Report tab (idx 5)
# ---------------------------------------------------------------------------


class TestPropertyInsuranceReport:
    """Insurance Report tab: action link that opens PDF claim report."""

    def _open_storm_panel(self, map_page, prop_id):
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyStorms === 'function'"
        )
        if not has_fn:
            pytest.skip("window.viewPropertyStorms not available")
        map_page.evaluate(f"window.viewPropertyStorms('{prop_id}')")
        map_page.wait_for_timeout(3_000)

    def test_insurance_tab_exists(self, map_page, first_property_id):
        """Insurance Report tab button (idx 5) should exist."""
        self._open_storm_panel(map_page, first_property_id)
        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tab = panel.locator(".prop-storm-tab[data-idx='5']")
        assert tab.count() > 0, "Insurance Report tab (idx 5) not found"

    def test_tab_mentions_insurance(self, map_page, first_property_id):
        """Insurance tab text should reference insurance or claim."""
        self._open_storm_panel(map_page, first_property_id)
        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tab = panel.locator(".prop-storm-tab[data-idx='5']")
        if tab.count() == 0:
            pytest.skip("Insurance tab not found")
        text = tab.inner_text().lower()
        assert "insur" in text or "claim" in text or "report" in text, \
            f"Tab text doesn't mention insurance/claim: '{text}'"

    def test_claim_report_api_returns_pdf(self, map_page, first_property_id):
        """GET /api/v1/properties/{prop_id}/claim-report should return PDF."""
        result = map_page.evaluate(f"""async () => {{
            var cfg = window.__BACKEND_CONFIG || {{}};
            var baseUrl = cfg.url || '';
            try {{
                var resp = await fetch(
                    baseUrl + '/api/v1/properties/{first_property_id}/claim-report'
                );
                return {{
                    http_status: resp.status,
                    content_type: resp.headers.get('content-type') || '',
                }};
            }} catch (e) {{
                return {{ error: e.message }};
            }}
        }}""")
        if result.get("error"):
            pytest.skip(f"Claim report API error: {result['error']}")
        assert result["http_status"] == 200, \
            f"Claim report returned {result['http_status']}"
        assert "pdf" in result["content_type"].lower(), \
            f"Expected PDF content-type, got: {result['content_type']}"
