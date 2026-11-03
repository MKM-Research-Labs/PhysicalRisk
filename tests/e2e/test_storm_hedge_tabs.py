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
Storm Portfolio table -- e2e tests: the REIT's Hedges tab (its hedge book
with the market-maker) and the Hedge Payout tab (what the book pays in the
selected storm), and the Summary's hedge payout card.
"""

import os

import pytest

from .conftest import close_all_storm_panels, close_storm_portfolio, open_storm_portfolio

_SHOTS = os.environ.get("MKM_E2E_SCREENSHOT_DIR")


def _shot(page, name):
    if _SHOTS:
        page.locator("#storm-portfolio-panel").screenshot(path=os.path.join(_SHOTS, name))


def _has_reit_hedges(page):
    return page.evaluate("""async () => {
        var base = (window.__BACKEND_CONFIG || {}).url || '';
        var sid = document.getElementById('sp-storm-select').value;
        var d = await (await fetch(base + '/api/v1/propertyts/' + sid + '/hedges')).json();
        return d.status === 'success' && (d.reit || {}).num_hedges > 0;
    }""")


@pytest.fixture
def table_view(map_page):
    close_all_storm_panels(map_page)
    open_storm_portfolio(map_page)
    map_page.locator("#sp-tab-table").click(force=True)
    map_page.locator("#sp-sub-hedges").wait_for(state="attached", timeout=30_000)
    map_page.wait_for_function(
        "() => (document.getElementById('sp-storm-select') || {}).value", timeout=60_000)
    if not _has_reit_hedges(map_page):
        pytest.skip("No REIT hedges in this catchment's book")
    yield map_page
    close_storm_portfolio(map_page)


def _open(page, sub, text):
    page.locator(f"#sp-sub-{sub}").click(force=True)
    page.locator("#sp-table-container", has_text=text).wait_for(timeout=120_000)


class TestStormHedgeTabs:

    def test_tab_order(self, table_view):
        labels = table_view.evaluate(
            "() => Array.from(document.querySelectorAll('#sp-sub-tab-bar button'))"
            ".map(b => b.textContent)")
        assert labels.index("Hedges") == labels.index("Commercial") + 1
        assert labels.index("Hedge Payout") == labels.index("Loan/Mortgage") + 1
        assert labels.index("Summary") == labels.index("Hedge Payout") + 1

    def test_hedges_tab_lists_the_reit_book(self, table_view):
        _open(table_view, "hedges", "REIT hedge book")
        container = table_view.locator("#sp-table-container")
        assert "market-maker lay-off" in container.inner_text().lower()
        assert container.locator("table").first.locator("tbody tr").count() > 0
        assert "hedged notional" in table_view.locator("#sp-summary").inner_text().lower()
        _shot(table_view, "hedges_tab.png")

    def test_payout_tab_shows_storm_payouts(self, table_view):
        _open(table_view, "payout", "REIT hedges")
        cards = table_view.locator("#sp-summary").inner_text().lower()
        assert "hedges triggered" in cards
        assert "reit payout" in cards
        _shot(table_view, "hedge_payout_tab.png")

    def test_summary_has_hedge_payout(self, table_view):
        _open(table_view, "summary", "Hedge Payout to REIT")
        text = table_view.locator("#sp-table-container").inner_text().lower()
        assert "hedge npv" not in text
        assert "model pending" not in text  # wind comes from the typhoon
        _shot(table_view, "summary_tab.png")
