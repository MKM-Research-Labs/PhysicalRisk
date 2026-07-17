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
Storm Portfolio panel -- e2e tests: Panel open, Table, Sim, Visual tabs.
"""

import pytest

from .conftest import close_all_storm_panels, open_storm_portfolio, close_storm_portfolio


# ---------------------------------------------------------------------------
# Panel-level tests
# ---------------------------------------------------------------------------


class TestStormPortfolioOpens:
    """Storm Portfolio panel opens and has expected structure."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_storm_panels(map_page)
        open_storm_portfolio(map_page)
        yield
        close_storm_portfolio(map_page)

    def test_panel_opens(self, map_page):
        """The storm portfolio panel should be visible."""
        panel = map_page.locator("#storm-portfolio-panel")
        assert panel.is_visible(), "Storm portfolio panel not visible"

    def test_has_storm_selector(self, map_page):
        """Storm selector dropdown should have at least one option."""
        select = map_page.locator("#sp-storm-select")
        assert select.count() > 0, "No #sp-storm-select found"
        options = select.locator("option")
        assert options.count() > 0, "Storm selector has no options"

    def test_has_four_tab_buttons(self, map_page):
        """All four tab buttons should exist."""
        for tab_id in ["sp-tab-table", "sp-tab-sim", "sp-tab-vis", "sp-tab-var"]:
            btn = map_page.locator(f"#{tab_id}")
            assert btn.count() > 0, f"Tab button #{tab_id} not found"

    def test_stats_bar_present(self, map_page):
        """Stats bar should be present in the panel."""
        bar = map_page.locator("#sp-stats-bar")
        assert bar.count() > 0, "No #sp-stats-bar found"

    def test_has_sort_selector(self, map_page):
        """Sort dropdown should exist with three options."""
        select = map_page.locator("#sp-sort-select")
        assert select.count() > 0, "No #sp-sort-select found"
        options = select.locator("option")
        assert options.count() == 3, \
            f"Sort selector should have 3 options, got {options.count()}"

    def test_sort_selector_default_is_damage(self, map_page):
        """Default sort should be 'Damage cost'."""
        select = map_page.locator("#sp-sort-select")
        if select.count() > 0:
            val = select.input_value()
            assert val == "damage", f"Default sort should be 'damage', got '{val}'"

    def test_has_percentile_selector(self, map_page):
        """Percentile selector dropdown should exist."""
        select = map_page.locator("#sp-pct-sel")
        assert select.count() > 0, "No #sp-pct-sel found"


# ---------------------------------------------------------------------------
# Table tab
# ---------------------------------------------------------------------------


class TestSPTableTab:
    """Table tab: summary cards + property damage table."""

    @pytest.fixture(autouse=True)
    def open_table_tab(self, map_page):
        close_all_storm_panels(map_page)
        open_storm_portfolio(map_page)
        map_page.locator("#sp-tab-table").click(force=True)
        map_page.wait_for_timeout(3_000)
        yield
        close_storm_portfolio(map_page)

    def test_table_view_visible(self, map_page):
        """Table content area should be visible."""
        view = map_page.locator("#sp-table-view")
        assert view.count() > 0 and view.is_visible(), \
            "No visible #sp-table-view"

    def test_has_summary_cards(self, map_page):
        """Summary cards row should have content."""
        summary = map_page.locator("#sp-summary")
        if summary.count() > 0:
            text = summary.inner_text()
            assert len(text.strip()) > 0, "Summary cards are empty"

    def test_has_property_table(self, map_page):
        """Property table container should have table rows."""
        container = map_page.locator("#sp-table-container")
        if container.count() > 0:
            rows = container.locator("tr")
            assert rows.count() > 0, "No table rows in #sp-table-container"

    def test_content_has_keywords(self, map_page):
        """Table view should mention portfolio-related terms."""
        view = map_page.locator("#sp-table-view")
        if view.count() == 0:
            pytest.skip("No #sp-table-view element")
        text = view.inner_text().lower()
        keywords = ["damage", "property", "portfolio", "value", "depth"]
        assert any(kw in text for kw in keywords), \
            f"No expected keywords in table view: {text[:200]}"


# ---------------------------------------------------------------------------
# Sim tab (map animation)
# ---------------------------------------------------------------------------


class TestSPSimTab:
    """Sim tab: embedded Leaflet map with frame-by-frame flood animation."""

    @pytest.fixture(autouse=True)
    def open_sim_tab(self, map_page):
        close_all_storm_panels(map_page)
        open_storm_portfolio(map_page)
        map_page.locator("#sp-tab-sim").click(force=True)
        map_page.wait_for_timeout(6_000)  # map init is slow
        yield
        close_storm_portfolio(map_page)

    def test_sim_view_visible(self, map_page):
        """Sim content area should be visible."""
        view = map_page.locator("#sp-sim-view")
        assert view.count() > 0 and view.is_visible(), \
            "No visible #sp-sim-view"

    def test_has_map_container(self, map_page):
        """Map container should exist."""
        container = map_page.locator("#sp-sim-map-container")
        assert container.count() > 0, "No #sp-sim-map-container found"

    def test_has_play_button(self, map_page):
        """Play/pause button should be visible."""
        btn = map_page.locator("#sp-sim-play-btn")
        assert btn.count() > 0, "No #sp-sim-play-btn found"

    def test_has_leaflet_or_canvas(self, map_page):
        """Should contain a Leaflet map or canvas element."""
        view = map_page.locator("#sp-sim-view")
        leaflet = view.locator(".leaflet-container")
        canvas = view.locator("canvas")
        assert leaflet.count() > 0 or canvas.count() > 0, \
            "No Leaflet map or canvas in sim view"


# ---------------------------------------------------------------------------
# Visual tab (multi-line chart)
# ---------------------------------------------------------------------------


class TestSPVisualTab:
    """Visual tab: multi-line gauge hydrograph chart with filters."""

    @pytest.fixture(autouse=True)
    def open_vis_tab(self, map_page):
        close_all_storm_panels(map_page)
        open_storm_portfolio(map_page)
        map_page.locator("#sp-tab-vis").click(force=True)
        map_page.wait_for_timeout(6_000)
        yield
        close_storm_portfolio(map_page)

    def test_vis_view_visible(self, map_page):
        """Visual content area should be visible."""
        view = map_page.locator("#sp-vis-view")
        assert view.count() > 0 and view.is_visible(), \
            "No visible #sp-vis-view"

    def test_has_chart_canvas(self, map_page):
        """Chart canvas or chart wrapper should exist."""
        canvas = map_page.locator("#sp-sim-canvas")
        wrap = map_page.locator("#sp-sim-chart-wrap")
        if canvas.count() == 0 and wrap.count() > 0:
            # Canvas is created dynamically when a storm is selected;
            # the wrapper existing proves the Visual tab rendered.
            pass
        else:
            assert canvas.count() > 0 or wrap.count() > 0, \
                "No #sp-sim-canvas or #sp-sim-chart-wrap found"

    def test_has_filter_row(self, map_page):
        """Filter row should exist."""
        row = map_page.locator("#sp-vis-filter-row")
        assert row.count() > 0, "No #sp-vis-filter-row found"

    def test_filter_has_controls(self, map_page):
        """Filter row should contain buttons or select elements."""
        row = map_page.locator("#sp-vis-filter-row")
        if row.count() == 0:
            pytest.skip("No filter row")
        buttons = row.locator("button")
        selects = row.locator("select")
        assert buttons.count() > 0 or selects.count() > 0, \
            "No controls in filter row"
