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
Gauge panel e2e tests — open via JS, verify tabs render, data loads.
"""

import pytest


class TestGaugePanelOpens:
    """Opening the gauge detail panel via JavaScript call."""

    def test_open_gauge_panel_via_js(self, map_page, first_gauge_id):
        """Calling window.viewHazardCurve(gaugeId) should open the panel."""
        # Ensure the function is available
        has_fn = map_page.evaluate("() => typeof window.viewHazardCurve === 'function'")
        if not has_fn:
            # Try the direct object method
            has_fn = map_page.evaluate(
                "() => window.GaugeHazardCurve && typeof window.GaugeHazardCurve.show === 'function'"
            )
            if has_fn:
                map_page.evaluate(f"window.GaugeHazardCurve.show('{first_gauge_id}')")
            else:
                pytest.skip("Neither viewHazardCurve nor GaugeHazardCurve.show available")
        else:
            map_page.evaluate(f"window.viewHazardCurve('{first_gauge_id}')")

        panel = map_page.locator("#hazard-curve-panel")
        panel.wait_for(state="visible", timeout=10_000)
        assert panel.is_visible()

    def test_panel_title_shows_gauge_name(self, map_page, first_gauge_id):
        """The panel title should contain the gauge name or ID."""
        has_fn = map_page.evaluate("() => typeof window.viewHazardCurve === 'function'")
        if has_fn:
            map_page.evaluate(f"window.viewHazardCurve('{first_gauge_id}')")
        else:
            map_page.evaluate(f"window.GaugeHazardCurve.show('{first_gauge_id}')")

        panel = map_page.locator("#hazard-curve-panel")
        panel.wait_for(state="visible", timeout=10_000)

        # A missing title element is worse than an empty one, and the guard
        # let it pass. The test is named for the title showing the gauge, so
        # it now requires the element and the text.
        title = map_page.locator("#hazard-panel-title")
        assert title.count() > 0, "Gauge panel has no #hazard-panel-title"
        text = title.inner_text()
        assert len(text) > 0, "Panel title is empty"

    def test_panel_has_tab_bar(self, map_page, first_gauge_id):
        """Gauge panel should have multiple tabs."""
        has_fn = map_page.evaluate("() => typeof window.viewHazardCurve === 'function'")
        if has_fn:
            map_page.evaluate(f"window.viewHazardCurve('{first_gauge_id}')")
        else:
            map_page.evaluate(f"window.GaugeHazardCurve.show('{first_gauge_id}')")

        panel = map_page.locator("#hazard-curve-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tabs = panel.locator(".hazard-tab")
        assert tabs.count() >= 4, f"Only {tabs.count()} tabs found"


class TestGaugePanelTabs:
    """Switching between gauge panel tabs."""

    @pytest.fixture(autouse=True)
    def open_panel(self, map_page, first_gauge_id):
        """Open gauge panel before each test."""
        has_fn = map_page.evaluate("() => typeof window.viewHazardCurve === 'function'")
        if has_fn:
            map_page.evaluate(f"window.viewHazardCurve('{first_gauge_id}')")
        else:
            map_page.evaluate(f"window.GaugeHazardCurve.show('{first_gauge_id}')")
        map_page.locator("#hazard-curve-panel").wait_for(
            state="visible", timeout=10_000
        )
        map_page.wait_for_timeout(6_000)  # Wait for async data load

        # CHECK for error notifications BEFORE dismissing them
        errors = map_page.evaluate("""() => {
            const notifs = document.querySelectorAll('.notif-message');
            const errors = [];
            notifs.forEach(n => {
                const text = n.textContent.toLowerCase();
                if (text.includes('fail') || text.includes('error') ||
                    text.includes('unable')) {
                    errors.push(n.textContent.trim());
                }
            });
            return errors;
        }""")
        assert len(errors) == 0, (
            f"Data load errors after opening gauge panel: {errors}"
        )

        # Dismiss overlays that can intercept pointer events
        map_page.evaluate("""() => {
            const m = document.getElementById('td-closeout-modal');
            if (m) m.style.display = 'none';
            const pdf = document.getElementById('gauge-pdf-panel');
            if (pdf) pdf.style.display = 'none';
        }""")
        yield
        # Close panel via JS to avoid notification overlay blocking × button
        map_page.evaluate("""() => {
            document.querySelectorAll('.notif-message, [id*="notif"]').forEach(n => n.remove());
            const p = document.getElementById('hazard-curve-panel');
            if (p) p.style.display = 'none';
        }""")

    def test_prs_tab_renders(self, map_page):
        """PRS Pricing tab (tab 0) should show controls."""
        tab = map_page.locator(".hazard-tab[data-tab='0']")
        # The tab's absence is the failure this test exists to catch,
        # so it asserts rather than passing quietly. Guarded on
        # count() > 0, it reported a green run when the PRS Pricing tab
        # had gone missing entirely.
        assert tab.count() > 0, "No PRS Pricing tab in the gauge panel"
        tab.click(force=True)
        map_page.wait_for_timeout(3_000)
        # Should have chart or controls
        chart = map_page.locator("#hazard-chart")
        controls = map_page.locator("#hazard-controls")
        assert chart.count() > 0 or controls.count() > 0

    def test_hazard_curve_tab_renders(self, map_page):
        """Hazard Curve tab (tab 1) should show a chart."""
        tab = map_page.locator(".hazard-tab[data-tab='1']")
        # The tab's absence is the failure this test exists to catch,
        # so it asserts rather than passing quietly. Guarded on
        # count() > 0, it reported a green run when the Hazard Curve tab
        # had gone missing entirely.
        assert tab.count() > 0, "No Hazard Curve tab in the gauge panel"
        tab.click(force=True)
        map_page.wait_for_timeout(3_000)
        chart = map_page.locator("#hazard-chart")
        assert chart.count() > 0, "No chart canvas on hazard curve tab"

    def test_stress_tab_renders(self, map_page):
        """Stress Test tab (tab 5) should show storm selector."""
        tab = map_page.locator(".hazard-tab[data-tab='5']")
        # The tab's absence is the failure this test exists to catch,
        # so it asserts rather than passing quietly. Guarded on
        # count() > 0, it reported a green run when the Stress Test tab
        # had gone missing entirely.
        assert tab.count() > 0, "No Stress Test tab in the gauge panel"
        tab.click()
        map_page.wait_for_timeout(6_000)

        # Should have a storm dropdown or chart
        panel = map_page.locator("#hazard-curve-panel")
        text = panel.inner_text()
        has_content = (
            "storm" in text.lower() or
            "flood" in text.lower() or
            "probability" in text.lower()
        )
        assert has_content, "Stress tab has no storm/flood content"

    def test_historical_tab_renders(self, map_page):
        """Historical tab (tab 4) should show timeseries data."""
        tab = map_page.locator(".hazard-tab[data-tab='4']")
        # The tab's absence is the failure this test exists to catch,
        # so it asserts rather than passing quietly. Guarded on
        # count() > 0, it reported a green run when the Historical tab
        # had gone missing entirely.
        assert tab.count() > 0, "No Historical tab in the gauge panel"
        tab.click()
        map_page.wait_for_timeout(6_000)

        panel = map_page.locator("#hazard-curve-panel")
        text = panel.inner_text()
        has_content = (
            "historical" in text.lower() or
            "daily" in text.lower() or
            "level" in text.lower()
        )
        assert has_content, "Historical tab has no timeseries content"


class TestGaugePanelBlotterLink:
    """The 'Gauge Blotter' link should navigate to the trading desk."""

    def _open_gauge_panel(self, map_page, gauge_id):
        has_fn = map_page.evaluate("() => typeof window.viewHazardCurve === 'function'")
        if has_fn:
            map_page.evaluate(f"window.viewHazardCurve('{gauge_id}')")
        else:
            map_page.evaluate(f"window.GaugeHazardCurve.show('{gauge_id}')")
        map_page.locator("#hazard-curve-panel").wait_for(
            state="visible", timeout=10_000
        )

    def test_blotter_link_exists(self, map_page, first_traded_gauge_id):
        """Panel should have a blotter link button."""
        self._open_gauge_panel(map_page, first_traded_gauge_id)

        link = map_page.locator("#hazard-blotter-link")
        assert link.count() > 0, "No blotter link in gauge panel"

    def test_blotter_link_opens_trading_desk(self, map_page, first_traded_gauge_id):
        """Clicking the blotter link should open the trading desk."""
        self._open_gauge_panel(map_page, first_traded_gauge_id)

        # first_traded_gauge_id is sourced from active-gauges, so this gauge
        # has open trades and the link must be present and enabled. Guarding
        # on that meant the test passed when the link was missing — which is
        # the regression it is named for.
        link = map_page.locator("#hazard-blotter-link")
        assert link.count() > 0, "Gauge panel has no #hazard-blotter-link"
        assert link.is_visible(), (
            "Blotter link is hidden for a gauge that has open trades"
        )

        link.click()
        map_page.wait_for_timeout(3_000)

        # Trading desk should now be visible
        td = map_page.locator("#trading-desk-panel")
        assert td.count() > 0 and td.is_visible(), (
            "Trading desk did not open from blotter link"
        )
