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
Counterparty e2e tests — API endpoints and PRS dropdown integration.

Counterparties have no dedicated panel; they appear as dropdown options
in the PRS pricing tab of gauge and property hazard curve panels.
"""

import pytest


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


class TestCounterpartyAPI:
    """Verify counterparty API endpoints return valid data."""

    def test_list_counterparties_returns_data(self, map_page):
        """GET /api/v1/counterparties should return counterparty list."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(baseUrl + '/api/v1/counterparties');
            var data = await resp.json();
            return {
                http_status: resp.status,
                api_status: data.status,
                count: (data.counterparties || []).length,
            };
        }""")
        assert result["http_status"] == 200, \
            f"Counterparties API returned {result['http_status']}"
        assert result["api_status"] == "success"
        assert result["count"] > 0, "No counterparties returned"

    def test_counterparty_summary_fields(self, map_page):
        """Each counterparty summary should have required fields."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(baseUrl + '/api/v1/counterparties');
            var data = await resp.json();
            var ctpys = data.counterparties || [];
            if (ctpys.length === 0) return { skip: true };
            var first = ctpys[0];
            return {
                has_id: !!first.counterparty_id,
                has_name: !!first.name,
                has_short_name: !!first.short_name,
                has_type: !!first.type,
                has_status: !!first.status,
                has_rating: !!first.credit_rating,
                count: ctpys.length,
            };
        }""")
        if result.get("skip"):
            pytest.skip("No counterparties available")
        assert result["has_id"], "Missing counterparty_id"
        assert result["has_name"], "Missing name"
        assert result["has_short_name"], "Missing short_name"
        assert result["has_type"], "Missing type"
        assert result["has_status"], "Missing status"
        assert result["has_rating"], "Missing credit_rating"

    def test_get_counterparty_detail(self, map_page):
        """GET /api/v1/counterparties/<id> should return full detail."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            // First get a valid ID
            var resp1 = await fetch(baseUrl + '/api/v1/counterparties');
            var data1 = await resp1.json();
            var ctpys = data1.counterparties || [];
            if (ctpys.length === 0) return { skip: true };
            var ctpyId = ctpys[0].counterparty_id;
            // Fetch detail
            var resp2 = await fetch(
                baseUrl + '/api/v1/counterparties/' + ctpyId
            );
            var data2 = await resp2.json();
            var ctpy = data2.counterparty || {};
            var cset = ctpy.CounterpartySet || ctpy;
            var party = cset.Party || {};
            var platform = cset._platform || {};
            return {
                http_status: resp2.status,
                api_status: data2.status,
                has_party_id: !!party.PartyID,
                has_party_name: !!party.PartyName,
                has_platform: Object.keys(platform).length > 0,
            };
        }""")
        if result.get("skip"):
            pytest.skip("No counterparties available")
        assert result["http_status"] == 200, \
            f"Detail API returned {result['http_status']}"
        assert result["api_status"] == "success"
        assert result["has_party_id"], "Detail missing Party.PartyID"
        assert result["has_party_name"], "Detail missing Party.PartyName"
        assert result["has_platform"], "Detail missing _platform section"

    def test_nonexistent_counterparty_returns_404(self, map_page):
        """GET /api/v1/counterparties/CTPY-NONEXISTENT should return 404."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/counterparties/CTPY-NONEXISTENT'
            );
            return { http_status: resp.status };
        }""")
        assert result["http_status"] == 404, \
            f"Expected 404, got {result['http_status']}"

    def test_counterparty_types_diverse(self, map_page):
        """Should have multiple counterparty types (banks, insurers, etc.)."""
        result = map_page.evaluate("""async () => {
            var cfg = window.__BACKEND_CONFIG || {};
            var baseUrl = cfg.url || '';
            var resp = await fetch(baseUrl + '/api/v1/counterparties');
            var data = await resp.json();
            var types = new Set();
            (data.counterparties || []).forEach(c => {
                if (c.type) types.add(c.type);
            });
            return {
                type_count: types.size,
                types: Array.from(types),
            };
        }""")
        assert result["type_count"] >= 2, \
            f"Only {result['type_count']} type(s): {result['types']}"


# ---------------------------------------------------------------------------
# PRS dropdown integration
# ---------------------------------------------------------------------------


class TestCounterpartyInPRS:
    """Counterparty dropdown in gauge PRS pricing tab."""

    def _open_gauge_prs(self, map_page, gauge_id):
        """Open gauge hazard panel and switch to PRS tab."""
        has_fn = map_page.evaluate(
            "() => typeof window.viewHazardCurve === 'function'"
        )
        if not has_fn:
            pytest.skip("window.viewHazardCurve not available")
        map_page.evaluate(f"window.viewHazardCurve('{gauge_id}')")
        panel = map_page.locator("#hazard-curve-panel")
        panel.wait_for(state="visible", timeout=10_000)
        map_page.wait_for_timeout(6_000)  # data load

        # Click PRS tab (tab 0)
        prs_tab = panel.locator(".hazard-tab[data-tab='0']")
        if prs_tab.count() > 0:
            prs_tab.click(force=True)
            map_page.wait_for_timeout(3_000)

    def test_prs_has_counterparty_dropdown(self, map_page, first_gauge_id):
        """PRS pricing tab should have a counterparty selector."""
        self._open_gauge_prs(map_page, first_gauge_id)

        select = map_page.locator("#prs-counterparty")
        assert select.count() > 0, "No #prs-counterparty dropdown found"

    def test_counterparty_dropdown_has_options(self, map_page, first_gauge_id):
        """Counterparty dropdown should have real options loaded from API."""
        self._open_gauge_prs(map_page, first_gauge_id)

        select = map_page.locator("#prs-counterparty")
        if select.count() == 0:
            pytest.skip("No counterparty dropdown")
        options = select.locator("option")
        # Should have at least a few counterparties
        assert options.count() >= 2, \
            f"Only {options.count()} option(s) in counterparty dropdown"

    def test_counterparty_options_show_rating(self, map_page, first_gauge_id):
        """Dropdown options should show short name and credit rating."""
        self._open_gauge_prs(map_page, first_gauge_id)

        select = map_page.locator("#prs-counterparty")
        if select.count() == 0:
            pytest.skip("No counterparty dropdown")
        # Get text of all options
        result = map_page.evaluate("""() => {
            var sel = document.getElementById('prs-counterparty');
            if (!sel) return { texts: [] };
            var texts = [];
            for (var i = 0; i < sel.options.length; i++) {
                texts.push(sel.options[i].text);
            }
            return { texts: texts };
        }""")
        texts = result.get("texts", [])
        # At least one option should contain a rating in parentheses
        has_rating = any("(" in t and ")" in t for t in texts)
        assert has_rating, \
            f"No options with credit rating format 'Name (Rating)': {texts[:5]}"

    def test_selecting_counterparty_updates_pricing(self, map_page, first_gauge_id):
        """Changing counterparty selection should not crash the panel."""
        self._open_gauge_prs(map_page, first_gauge_id)

        select = map_page.locator("#prs-counterparty")
        if select.count() == 0:
            pytest.skip("No counterparty dropdown")
        options_count = select.locator("option").count()
        if options_count < 2:
            pytest.skip("Not enough counterparty options to change")

        # Select second option
        map_page.evaluate("""() => {
            var sel = document.getElementById('prs-counterparty');
            if (sel && sel.options.length >= 2) {
                sel.selectedIndex = 1;
                sel.dispatchEvent(new Event('change'));
            }
        }""")
        map_page.wait_for_timeout(1_500)

        # Panel should still be visible (no crash)
        panel = map_page.locator("#hazard-curve-panel")
        assert panel.is_visible(), "Panel crashed after counterparty change"
