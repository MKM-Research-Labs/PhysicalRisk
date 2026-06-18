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
Property panel e2e tests — mortgage detail and flood timeline.
"""

import pytest


class TestMortgageDetail:
    """Mortgage detail panel tests."""

    def _open_mortgage_panel(self, map_page, prop_id):
        """Try to open mortgage detail via available functions."""
        # Try viewRLoanDetail
        has_fn = map_page.evaluate(
            "() => typeof window.viewRLoanDetail === 'function'"
        )
        if has_fn:
            map_page.evaluate(f"window.viewRLoanDetail('{prop_id}')")
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
        """Timeline chart canvas should be present when flood data exists."""
        self._open_storm_panel(map_page, first_property_id)
        panel = map_page.locator("#prop-storm-panel")
        panel.wait_for(state="visible", timeout=10_000)

        tab = panel.locator(".prop-storm-tab[data-idx='1']")
        if tab.count() == 0:
            pytest.skip("Flood Timeline tab not found")
        tab.click()
        map_page.wait_for_timeout(5_000)

        # Canvas is only created when propStormData has flood events
        chart = map_page.locator("#prop-timeline-chart")
        content = map_page.locator("#prop-storm-content")
        content_text = content.inner_text(timeout=5_000).lower()
        if "no flood" in content_text or "no data" in content_text:
            pytest.skip("No flood events for this property")
        assert chart.count() > 0, "No #prop-timeline-chart canvas found"
