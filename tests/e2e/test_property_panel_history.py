# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Property panel e2e tests — flood history, mortgage impact, and insurance report.
"""

import pytest


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
