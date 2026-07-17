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
Trading Desk — Client tab e2e tests.

Verifies the Client (property PRS) tab renders in the trading desk panel
with the expected structure: summary bar, table, and trade rows.
"""

import pytest


class TestClientTabExists:
    """Client tab should appear in the trading desk tab bar."""

    def test_client_tab_button_present(self, map_page):
        """The Client tab button should exist in the tab bar."""
        map_page.locator("text=Π").first.click()
        map_page.locator("#trading-desk-panel").wait_for(
            state="visible", timeout=5_000
        )

        client_tab = map_page.locator("#td-tab-client")
        assert client_tab.count() > 0, "No #td-tab-client button found"

    def test_client_tab_is_first(self, map_page):
        """Client tab should be the leftmost tab (before Blotter)."""
        map_page.locator("text=Π").first.click()
        map_page.locator("#trading-desk-panel").wait_for(
            state="visible", timeout=5_000
        )

        tabs = map_page.locator("[id^='td-tab-']")
        first_tab = tabs.first
        assert 'client' in (first_tab.get_attribute('id') or ''), \
            f"First tab should be client, got {first_tab.get_attribute('id')}"


class TestClientTab:
    """Client tab content and rendering."""

    @pytest.fixture(autouse=True)
    def open_client_tab(self, map_page):
        """Open trading desk and switch to client tab."""
        map_page.evaluate("""() => {
            ['trading-desk-panel', 'hazard-curve-panel', 'property-hc-panel',
             'prop-storm-panel', 'storm-portfolio-panel', 'gauge-pdf-panel',
             'mortgage-detail-panel', 'mg-panel', 'property-pdf-panel'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.style.display = 'none';
            });
        }""")
        map_page.wait_for_timeout(500)

        map_page.locator("text=Π").first.click()
        map_page.locator("#trading-desk-panel").wait_for(
            state="visible", timeout=10_000
        )
        map_page.wait_for_timeout(3_000)

        client_tab = map_page.locator("#td-tab-client")
        if client_tab.count() > 0:
            client_tab.click(force=True)
            map_page.wait_for_timeout(3_000)
        yield
        map_page.evaluate("""() => {
            const el = document.getElementById('trading-desk-panel');
            if (el) el.style.display = 'none';
        }""")

    def test_client_view_visible(self, map_page):
        """The client content area should be visible when tab is active."""
        client_view = map_page.locator("#td-client-view")
        if client_view.count() == 0:
            map_page.wait_for_timeout(3_000)
        assert client_view.count() > 0, "No #td-client-view element found"

    def test_client_has_summary_bar(self, map_page):
        """Client tab should have a summary bar."""
        bar = map_page.locator("#td-client-summary-bar")
        assert bar.count() > 0, "No #td-client-summary-bar found"

    def test_client_has_table(self, map_page):
        """Client tab should have a table container."""
        wrap = map_page.locator("#td-client-table-wrap")
        assert wrap.count() > 0, "No #td-client-table-wrap found"

    def test_client_table_has_rows(self, map_page):
        """If property PRS trades exist, the table should have rows."""
        map_page.wait_for_timeout(3_000)
        rows = map_page.locator("#td-client-table-wrap tr")
        # At minimum we expect a header row
        assert rows.count() >= 1, "No rows in client table"

    def test_client_summary_shows_property_trades_label(self, map_page):
        """Summary bar should contain 'Property' text."""
        bar = map_page.locator("#td-client-summary-bar")
        if bar.count() > 0:
            text = bar.inner_text()
            assert "property" in text.lower(), \
                f"Summary bar should mention property trades, got: {text}"
