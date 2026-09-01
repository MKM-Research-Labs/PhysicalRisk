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
Residential Portfolio Blotter — e2e tests.

Verifies the storm portfolio panel's Residential tab renders correctly
with elevation (relative to gauge, including floor) and river distance (km).

These tests previously never ran. Each looked for ``#sp-sub-portfolio`` and
skipped when it was absent — but nothing ever opened the storm portfolio panel,
and the ``map_page`` fixture explicitly closes ``storm-portfolio-panel`` between
tests, so the control could never exist and all six skipped on every run while
reporting green. They now open the panel the same way test_storm_portfolio_*
does, and a missing control is an assertion failure rather than a skip: the
sub-tab's absence is precisely the regression these tests exist to catch.
"""

import pytest

from .conftest import close_all_storm_panels, open_storm_portfolio, close_storm_portfolio

# Residential blotter columns after mortgage/LTV/Remaining moved to the
# Loan/Mortgage tab: Property | Address | Value | River Dist | Elevation | Zone.
_COLUMNS = 6
_RIVER_DIST_COL = 3
_ELEVATION_COL = 4
_EM_DASH = "—"


class _ResidentialTabBase:
    """Opens the storm portfolio panel and selects the Residential sub-tab."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_storm_panels(map_page)
        open_storm_portfolio(map_page)
        yield
        close_storm_portfolio(map_page)

    def _sub_tab(self, map_page):
        btn = map_page.locator("#sp-sub-portfolio")
        assert btn.count() > 0, (
            "Residential sub-tab (#sp-sub-portfolio) not found in the open "
            "storm portfolio panel — the tab is missing, not the panel"
        )
        return btn

    def _open_blotter_tab(self, map_page):
        self._sub_tab(map_page).click()
        map_page.wait_for_timeout(1_000)

    def _header_texts(self, map_page):
        headers = map_page.locator("#sp-table-container th")
        return [headers.nth(i).text_content() for i in range(headers.count())]

    def _column_values(self, map_page, index):
        cells = map_page.locator("#sp-table-container td")
        texts = [cells.nth(i).text_content() for i in range(cells.count())]
        return texts[index::_COLUMNS]


class TestResidentialPortfolioTabLabel(_ResidentialTabBase):
    """The tab must say 'Residential', not 'REIT Blotter'."""

    def test_tab_text(self, map_page):
        text = self._sub_tab(map_page).text_content()
        assert text.strip() == "Residential", (
            f"Tab label is '{text}', expected 'Residential'"
        )


class TestResidentialPortfolioColumns(_ResidentialTabBase):
    """Verify correct column headers in the Residential table."""

    def test_has_river_dist_km_column(self, map_page):
        self._open_blotter_tab(map_page)
        texts = self._header_texts(map_page)
        assert "River Dist (km)" in texts, f"Headers: {texts}"

    def test_has_elevation_column(self, map_page):
        self._open_blotter_tab(map_page)
        texts = self._header_texts(map_page)
        assert "Elevation (m)" in texts, f"Headers: {texts}"

    def test_no_floor_column(self, map_page):
        """Floor is incorporated into elevation — no separate column."""
        self._open_blotter_tab(map_page)
        texts = self._header_texts(map_page)
        assert "Floor (m)" not in texts, (
            "Floor column should not exist — incorporated into Elevation"
        )

    def test_table_has_rows(self, map_page):
        """Guards the column-value tests below: an empty table would make
        'no dashes' vacuously true, which is the failure mode this whole file
        was suffering from."""
        self._open_blotter_tab(map_page)
        cells = map_page.locator("#sp-table-container td")
        assert cells.count() >= _COLUMNS, (
            f"Residential table has {cells.count()} cells — expected at least "
            f"one full row of {_COLUMNS}"
        )

    def test_elevation_values_not_all_dashes(self, map_page):
        """At least some elevation cells should have numeric values."""
        self._open_blotter_tab(map_page)
        values = self._column_values(map_page, _ELEVATION_COL)
        assert values, "No elevation cells found"
        non_dash = [c for c in values if c.strip() != _EM_DASH]
        assert non_dash, "All elevation cells are dashes — data not loading"

    def test_river_dist_values_not_all_dashes(self, map_page):
        """At least some river distance cells should have numeric values."""
        self._open_blotter_tab(map_page)
        values = self._column_values(map_page, _RIVER_DIST_COL)
        assert values, "No river distance cells found"
        non_dash = [c for c in values if c.strip() != _EM_DASH]
        assert non_dash, "All river distance cells are dashes — data not loading"
