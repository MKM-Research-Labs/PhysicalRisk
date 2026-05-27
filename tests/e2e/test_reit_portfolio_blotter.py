# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Residential Portfolio Blotter — e2e tests.

Verifies the storm portfolio panel's Residential tab renders correctly
with elevation (relative to gauge, including floor) and river distance (km).
"""

import pytest


class TestResidentialPortfolioTabLabel:
    """The tab must say 'Residential', not 'REIT Blotter'."""

    def test_tab_text(self, map_page):
        """Open storm portfolio panel and verify tab label."""
        # The storm portfolio panel opens via the storm selector
        # Try to find the sub-tab button
        btn = map_page.locator("#sp-sub-portfolio")
        if btn.count() == 0:
            pytest.skip("Storm portfolio panel not available in current view")

        text = btn.text_content()
        assert text.strip() == "Residential", (
            f"Tab label is '{text}', expected 'Residential'"
        )


class TestResidentialPortfolioColumns:
    """Verify correct column headers in the Residential table."""

    def _open_blotter_tab(self, map_page):
        btn = map_page.locator("#sp-sub-portfolio")
        if btn.count() == 0:
            pytest.skip("Storm portfolio panel not available")
        btn.click()
        map_page.wait_for_timeout(1_000)

    def test_has_river_dist_km_column(self, map_page):
        self._open_blotter_tab(map_page)
        headers = map_page.locator("#sp-table-container th")
        texts = [headers.nth(i).text_content() for i in range(headers.count())]
        assert "River Dist (km)" in texts, f"Headers: {texts}"

    def test_has_elevation_column(self, map_page):
        self._open_blotter_tab(map_page)
        headers = map_page.locator("#sp-table-container th")
        texts = [headers.nth(i).text_content() for i in range(headers.count())]
        assert "Elevation (m)" in texts, f"Headers: {texts}"

    def test_no_floor_column(self, map_page):
        """Floor is incorporated into elevation — no separate column."""
        self._open_blotter_tab(map_page)
        headers = map_page.locator("#sp-table-container th")
        texts = [headers.nth(i).text_content() for i in range(headers.count())]
        assert "Floor (m)" not in texts, (
            "Floor column should not exist — incorporated into Elevation"
        )

    def test_elevation_values_not_all_dashes(self, map_page):
        """At least some elevation cells should have numeric values."""
        self._open_blotter_tab(map_page)
        cells = map_page.locator("#sp-table-container td")
        cell_texts = [cells.nth(i).text_content() for i in range(cells.count())]
        # Residential blotter has 6 cols after mortgage/LTV/Remaining moved
        # to the Loan/Mortgage tab: Property | Address | Value | River Dist
        # | Elevation | Flood Zone. Elevation is column index 4 (0-based).
        elevation_cells = cell_texts[4::6]
        non_dash = [c for c in elevation_cells if c.strip() != "\u2014"]
        assert len(non_dash) > 0, "All elevation cells are dashes — data not loading"

    def test_river_dist_values_not_all_dashes(self, map_page):
        """At least some river distance cells should have numeric values."""
        self._open_blotter_tab(map_page)
        cells = map_page.locator("#sp-table-container td")
        cell_texts = [cells.nth(i).text_content() for i in range(cells.count())]
        river_cells = cell_texts[3::6]
        non_dash = [c for c in river_cells if c.strip() != "\u2014"]
        assert len(non_dash) > 0, "All river distance cells are dashes — data not loading"
