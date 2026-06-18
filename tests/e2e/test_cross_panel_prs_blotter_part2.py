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
Cross-panel e2e tests: PRS pricer ↔ blotter ↔ storm scenarios.

Tests the connected user journeys that a client demo would follow:
- Gauge PRS commit → blotter shows trade → blotter button active
- Property storm scenarios → PRS Pricing tab → gauge PRS opens
- Nav menu → gauge PRS → commit → nav menu → blotter shows trade
- Storm scenarios tabs remain consistent when flipping between them
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    close_gauge_panel,
    open_gauge_panel,
    switch_gauge_tab,
)


CLOSE_ALL_JS = """() => {
    ['trading-desk-panel', 'hazard-curve-panel', 'property-hc-panel',
     'prop-storm-panel', 'mortgage-detail-panel'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
}"""


class TestPropertyStormToPRS:
    """Property storm scenarios → PRS Pricing tab → PRS pricer opens."""

    def _open_storm_panel(self, map_page, prop_id):
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyStorms === 'function'"
        )
        if not has_fn:
            pytest.skip("viewPropertyStorms not available")
        map_page.evaluate(f"window.viewPropertyStorms('{prop_id}')")
        map_page.wait_for_timeout(4_000)

    def test_01_storm_panel_has_prs_tab(self, map_page, first_property_id):
        """Storm panel should have PRS Pricing action tab."""
        self._open_storm_panel(map_page, first_property_id)
        tab = map_page.locator(".prop-storm-tab[data-idx='6']")
        assert tab.count() > 0, "PRS Pricing tab (idx 6) not found"
        text = tab.inner_text().lower()
        assert "prs" in text, f"Tab doesn't mention PRS: '{text}'"
        map_page.evaluate(CLOSE_ALL_JS)

    def test_02_prs_tab_opens_property_hazard_panel(self, map_page, first_property_id):
        """Clicking PRS Pricing tab should open the property hazard panel."""
        self._open_storm_panel(map_page, first_property_id)

        tab = map_page.locator(".prop-storm-tab[data-idx='6']")
        if tab.count() == 0:
            pytest.skip("PRS Pricing tab not found")
        tab.click()
        map_page.wait_for_timeout(5_000)

        phc = map_page.locator("#property-hc-panel")
        assert phc.count() > 0 and phc.is_visible(), (
            "Property hazard panel not visible after clicking PRS Pricing tab"
        )
        map_page.evaluate(CLOSE_ALL_JS)

    def test_03_storm_flood_history_click_opens_timeline(self, map_page, first_property_id):
        """Clicking a storm in Flood History should open Flood Timeline."""
        self._open_storm_panel(map_page, first_property_id)

        # Switch to Flood History tab (idx 3)
        hist_tab = map_page.locator(".prop-storm-tab[data-idx='3']")
        if hist_tab.count() == 0:
            pytest.skip("Flood History tab not found")
        hist_tab.click()
        map_page.wait_for_timeout(3_000)

        # The Flood Timeline is a hydrograph, so it can only render for a
        # storm that actually flooded this property. The Flood History
        # table also lists wind-only typhoon events (depth 0), which have
        # no hydrograph. Click the first row whose depth column is > 0; if
        # the property is wind-dominated with no floods, there's nothing
        # to open, so skip rather than assert a timeline that can't exist.
        clicked = map_page.evaluate("""() => {
            var rows = document.querySelectorAll('#prop-storm-content table tbody tr');
            for (var i = 0; i < rows.length; i++) {
                var depthCell = rows[i].querySelectorAll('td')[2];
                if (depthCell && parseFloat(depthCell.textContent) > 0) {
                    rows[i].click();
                    return true;
                }
            }
            return false;
        }""")
        if not clicked:
            pytest.skip("No flooded history rows — no hydrograph timeline")
        map_page.wait_for_timeout(3_000)

        # Should now be on Flood Timeline (idx 1)
        timeline_chart = map_page.locator("#prop-timeline-chart")
        timeline_select = map_page.locator("#prop-timeline-select")
        has_timeline = timeline_chart.count() > 0 or timeline_select.count() > 0
        assert has_timeline, "Flood Timeline not shown after clicking storm row"

        map_page.evaluate(CLOSE_ALL_JS)


class TestStormScenarioTabConsistency:
    """Storm scenario tabs should show consistent data when switching."""

    def _open_storm_panel(self, map_page, prop_id):
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyStorms === 'function'"
        )
        if not has_fn:
            pytest.skip("viewPropertyStorms not available")
        map_page.evaluate(f"window.viewPropertyStorms('{prop_id}')")
        map_page.wait_for_timeout(4_000)

    def test_distribution_and_history_show_same_flood_count(self, map_page, first_property_id):
        """Distribution and Flood History must show the same number of floods."""
        self._open_storm_panel(map_page, first_property_id)

        # Distribution tab (idx 0) — count events
        map_page.locator(".prop-storm-tab[data-idx='0']").click()
        map_page.wait_for_timeout(2_000)
        dist_count = map_page.evaluate("""() => {
            var stats = document.getElementById('prop-dist-stats');
            if (!stats) return null;
            var match = stats.textContent.match(/Events:\\s*(\\d+)/);
            return match ? parseInt(match[1]) : null;
        }""")

        # Flood History tab (idx 3) — count rows
        map_page.locator(".prop-storm-tab[data-idx='3']").click()
        map_page.wait_for_timeout(2_000)
        hist_count = map_page.evaluate("""() => {
            var stats = document.getElementById('prop-history-stats');
            if (!stats) return null;
            var match = stats.textContent.match(/Floods:\\s*(\\d+)/);
            return match ? parseInt(match[1]) : null;
        }""")

        if dist_count is None or hist_count is None:
            pytest.skip("Could not extract flood counts from stats")

        assert dist_count == hist_count, (
            f"Distribution shows {dist_count} events but "
            f"Flood History shows {hist_count} floods"
        )

        map_page.evaluate(CLOSE_ALL_JS)

    def test_header_flood_count_matches_history(self, map_page, first_property_id):
        """Header 'N property floods' must match Flood History event count."""
        self._open_storm_panel(map_page, first_property_id)

        header_count = map_page.evaluate("""() => {
            var status = document.getElementById('prop-storm-status');
            if (!status) return null;
            var match = status.textContent.match(/(\\d+)\\s*property flood/);
            return match ? parseInt(match[1]) : null;
        }""")

        # Flood History count
        map_page.locator(".prop-storm-tab[data-idx='3']").click()
        map_page.wait_for_timeout(2_000)
        hist_count = map_page.evaluate("""() => {
            var stats = document.getElementById('prop-history-stats');
            if (!stats) return null;
            var match = stats.textContent.match(/Floods:\\s*(\\d+)/);
            return match ? parseInt(match[1]) : null;
        }""")

        if header_count is None or hist_count is None:
            pytest.skip("Could not extract counts")

        assert header_count == hist_count, (
            f"Header says {header_count} property floods but "
            f"Flood History shows {hist_count}"
        )

        map_page.evaluate(CLOSE_ALL_JS)

    def test_worst_storms_are_subset_of_history(self, map_page, first_property_id):
        """Worst Storms top bars should all appear in Flood History."""
        self._open_storm_panel(map_page, first_property_id)

        # Get Worst Storms storm IDs (idx 2)
        map_page.locator(".prop-storm-tab[data-idx='2']").click()
        map_page.wait_for_timeout(2_000)
        worst_ids = map_page.evaluate("""() => {
            var chart = window.currentChart;
            if (!chart || !chart.data) return [];
            return chart.data.labels || [];
        }""")

        # Get Flood History storm IDs (idx 3)
        map_page.locator(".prop-storm-tab[data-idx='3']").click()
        map_page.wait_for_timeout(2_000)
        hist_ids = map_page.evaluate("""() => {
            var rows = document.querySelectorAll('#prop-storm-content table tr td:first-child');
            return Array.from(rows).map(td => td.textContent.trim());
        }""")

        if not worst_ids or not hist_ids:
            pytest.skip("Could not extract storm IDs")

        # Worst storms labels may be truncated — check prefix match
        for ws_id in worst_ids[:5]:
            found = any(h.startswith(ws_id) or ws_id.startswith(h) for h in hist_ids)
            assert found, (
                f"Worst storm '{ws_id}' not found in Flood History. "
                f"History has {len(hist_ids)} entries."
            )

        map_page.evaluate(CLOSE_ALL_JS)


class TestNavMenuToPanel:
    """Nav menu select → panel opens → correct gauge/property."""

    def _is_any_panel_visible(self, map_page, panel_ids):
        """Check if any of the given panel IDs is visible using computed style.

        Note: offsetParent is null for position:fixed elements, so we check
        offsetWidth/offsetHeight > 0 instead.
        """
        return map_page.evaluate("""(panelIds) => {
            return panelIds.some(id => {
                var el = document.getElementById(id);
                if (!el) return false;
                var cs = window.getComputedStyle(el);
                return cs.display !== 'none' && cs.visibility !== 'hidden'
                    && (el.offsetWidth > 0 || el.offsetHeight > 0);
            });
        }""", panel_ids)

    # Note: the nav-dropdown → panel flows (test_nav_gauge_select_opens_panel /
    # test_nav_property_select_opens_panel) were removed with the top-left
    # gauge/property dropdowns — that navigation moved to the CDM Asset Review
    # workstream. Panel-opening is still covered via markers / context menus.
