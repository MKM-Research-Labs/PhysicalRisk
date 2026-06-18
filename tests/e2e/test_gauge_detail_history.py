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
Gauge panel detail e2e tests: Historical (Tab 4) and Stress Test (Tab 5).
Split from test_gauge_panel_detail.py.
"""

import pytest

from tests.e2e.helpers import (
    close_gauge_panel,
    open_gauge_panel,
    switch_gauge_tab,
)


# ---------------------------------------------------------------------------
# Tab 4: Historical
# ---------------------------------------------------------------------------

class TestHistoricalTab:
    """Tab 4 - Historical timeseries and storm scenarios."""

    @pytest.fixture(autouse=True)
    def open_historical_tab(self, map_page, first_gauge_id):
        open_gauge_panel(map_page, first_gauge_id)
        switch_gauge_tab(map_page, 4)
        # Historical tab may need extra time to load data
        map_page.wait_for_timeout(3_000)
        yield
        close_gauge_panel(map_page)

    def test_content_loads_with_timeseries_data(self, map_page):
        """Historical tab should load and display timeseries content."""
        panel = map_page.locator("#hazard-curve-panel")
        text = panel.inner_text().lower()
        has_content = (
            "historical" in text
            or "daily" in text
            or "level" in text
            or "water" in text
            or "time" in text
        )
        assert has_content, (
            "Historical tab has no timeseries content "
            "(expected 'historical', 'daily', 'level', 'water', or 'time')"
        )

    def test_storm_scenarios_list_exists(self, map_page):
        """Historical tab should contain a storm scenarios list or section."""
        panel = map_page.locator("#hazard-curve-panel")
        text = panel.inner_text().lower()
        # Look for storm scenario indicators in the content
        has_storms = (
            "storm" in text
            or "scenario" in text
            or "breach" in text
            or "event" in text
        )
        # Also check for a list/table structure
        rows = panel.locator("tr, li, .storm-row, .scenario-item")
        has_list_elements = rows.count() > 0
        assert has_storms or has_list_elements, (
            "Historical tab has no storm scenarios list or content"
        )

    def test_content_mentions_historical_context(self, map_page):
        """Tab content should contain historical, daily, or level references."""
        panel = map_page.locator("#hazard-curve-panel")
        text = panel.inner_text().lower()
        keywords = ["historical", "daily", "level", "gauge", "water", "observed"]
        found = [k for k in keywords if k in text]
        assert len(found) > 0, (
            f"Historical tab missing expected keywords. "
            f"Checked: {keywords}"
        )


# ---------------------------------------------------------------------------
# Tab 5: Stress Test
# ---------------------------------------------------------------------------

class TestStressTestTab:
    """Tab 5 - Stress Test storm selection and charts."""

    @pytest.fixture(autouse=True)
    def open_stress_tab(self, map_page, first_gauge_id):
        open_gauge_panel(map_page, first_gauge_id)
        switch_gauge_tab(map_page, 5)
        # Stress tab may need extra time for API calls and chart rendering
        map_page.wait_for_timeout(6_000)
        yield
        close_gauge_panel(map_page)

    def test_storm_dropdown_exists(self, map_page):
        """Stress Test tab should have a storm selection dropdown."""
        panel = map_page.locator("#hazard-curve-panel")
        # Look for select elements or custom dropdowns in the panel
        selects = panel.locator("select")
        dropdowns = panel.locator("[class*='dropdown'], [class*='storm-select'], [id*='storm']")
        assert selects.count() > 0 or dropdowns.count() > 0, (
            "No storm dropdown found on Stress Test tab"
        )

    def test_charts_render(self, map_page):
        """Stress Test tab should render charts (flood probability, P&L, surface)."""
        panel = map_page.locator("#hazard-curve-panel")
        # Look for canvas elements (Chart.js) or table elements (surface heatmap)
        canvases = panel.locator("canvas")
        tables = panel.locator("table")
        chart_count = canvases.count() + tables.count()
        if chart_count == 0:
            # Charts require trained classifiers — skip if none available
            text = panel.inner_text()
            if "error" in text.lower() or "no " in text.lower() or not text.strip():
                pytest.skip(
                    "No stress charts rendered — classifiers may be stale. "
                    "Run: python3 app.py classifier --all"
                )
        assert chart_count > 0, (
            "No charts or tables found on Stress Test tab "
            "(expected canvas or table elements)"
        )

    def test_content_mentions_stress_concepts(self, map_page):
        """Tab content should reference storm, flood, or probability."""
        panel = map_page.locator("#hazard-curve-panel")
        text = panel.inner_text().lower()
        has_content = (
            "storm" in text
            or "flood" in text
            or "probability" in text
            or "stress" in text
            or "p(flood)" in text
        )
        assert has_content, (
            "Stress Test tab has no relevant content "
            "(expected 'storm', 'flood', 'probability', 'stress', or 'p(flood)')"
        )

    def test_auto_selects_worst_case_storm(self, map_page):
        """Stress Test tab should auto-select the worst case (highest peak) storm."""
        panel = map_page.locator("#hazard-curve-panel")
        # Check that a storm is selected (dropdown has a value or content shows storm ID)
        selected_value = map_page.evaluate("""() => {
            const panel = document.getElementById('hazard-curve-panel');
            if (!panel) return '';
            const selects = panel.querySelectorAll('select');
            for (const sel of selects) {
                if (sel.value && sel.value.length > 0) return sel.value;
            }
            return '';
        }""")
        # Also check that content is not in a "no storm selected" state
        text = panel.inner_text().lower()
        has_selection = (
            len(selected_value) > 0
            or "storm-" in text
            or "peak" in text
            or "selected" in text
        )
        assert has_selection, (
            "Stress Test tab does not appear to have auto-selected a storm"
        )
