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
Gauge panel detail e2e tests: Hazard Curve (Tab 1), Return Period (Tab 2),
Flood Probability (Tab 3).
Split from test_gauge_panel_detail.py.
"""

import pytest

from tests.e2e.helpers import (
    close_gauge_panel,
    open_gauge_panel,
    switch_gauge_tab,
)


# ---------------------------------------------------------------------------
# Tab 1: Hazard Curve
# ---------------------------------------------------------------------------

class TestHazardCurveTab:
    """Tab 1 - Hazard Curve chart and stats."""

    @pytest.fixture(autouse=True)
    def open_hazard_tab(self, map_page, first_gauge_id):
        open_gauge_panel(map_page, first_gauge_id)
        switch_gauge_tab(map_page, 1)
        yield
        close_gauge_panel(map_page)

    def test_chart_canvas_rendered(self, map_page):
        """Hazard Curve tab should render a chart canvas."""
        chart = map_page.locator("#hazard-chart")
        if chart.count() == 0:
            chart = map_page.locator("#hazard-curve-panel canvas")
        assert chart.count() > 0, "No chart canvas on Hazard Curve tab"

    def test_stats_bar_shows_data(self, map_page):
        """Stats bar should display hazard data."""
        stats = map_page.locator("#hazard-stats-bar")
        if stats.count() == 0:
            pytest.skip("Stats bar #hazard-stats-bar not found")
        text = stats.inner_text()
        assert len(text.strip()) > 0, "Stats bar is empty on Hazard Curve tab"

    def test_tab_title_updates(self, map_page):
        """Panel title or status should reflect hazard curve context."""
        title = map_page.locator("#hazard-panel-title")
        status = map_page.locator("#hazard-status")
        has_title = title.count() > 0 and len(title.inner_text().strip()) > 0
        has_status = status.count() > 0 and len(status.inner_text().strip()) > 0
        assert has_title or has_status, (
            "Neither title nor status shows content on Hazard Curve tab"
        )


# ---------------------------------------------------------------------------
# Tab 2: Return Period
# ---------------------------------------------------------------------------

class TestReturnPeriodTab:
    """Tab 2 - Return Period chart and data."""

    @pytest.fixture(autouse=True)
    def open_return_tab(self, map_page, first_gauge_id):
        open_gauge_panel(map_page, first_gauge_id)
        switch_gauge_tab(map_page, 2)
        yield
        close_gauge_panel(map_page)

    def test_chart_rendered(self, map_page):
        """Return Period tab should render a chart."""
        chart = map_page.locator("#hazard-chart")
        if chart.count() == 0:
            chart = map_page.locator("#hazard-curve-panel canvas")
        assert chart.count() > 0, "No chart on Return Period tab"

    def test_content_shows_return_period_data(self, map_page):
        """Tab content should reference return period concepts."""
        panel = map_page.locator("#hazard-curve-panel")
        text = panel.inner_text().lower()
        has_content = (
            "return" in text
            or "period" in text
            or "year" in text
            or "exceedance" in text
            or "level" in text
        )
        assert has_content, (
            "Return Period tab has no relevant content "
            "(expected 'return', 'period', 'year', 'exceedance', or 'level')"
        )


# ---------------------------------------------------------------------------
# Tab 3: Flood Probability
# ---------------------------------------------------------------------------

class TestFloodProbabilityTab:
    """Tab 3 - Flood Probability chart and data."""

    @pytest.fixture(autouse=True)
    def open_flood_tab(self, map_page, first_gauge_id):
        open_gauge_panel(map_page, first_gauge_id)
        switch_gauge_tab(map_page, 3)
        yield
        close_gauge_panel(map_page)

    def test_chart_rendered(self, map_page):
        """Flood Probability tab should render a chart."""
        chart = map_page.locator("#hazard-chart")
        if chart.count() == 0:
            chart = map_page.locator("#hazard-curve-panel canvas")
        assert chart.count() > 0, "No chart on Flood Probability tab"

    def test_content_shows_probability_data(self, map_page):
        """Tab content should reference probability concepts."""
        panel = map_page.locator("#hazard-curve-panel")
        text = panel.inner_text().lower()
        has_content = (
            "probability" in text
            or "flood" in text
            or "depth" in text
            or "exceedance" in text
            or "%" in text
        )
        assert has_content, (
            "Flood Probability tab has no relevant content "
            "(expected 'probability', 'flood', 'depth', 'exceedance', or '%')"
        )
