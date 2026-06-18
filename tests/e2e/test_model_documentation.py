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
E2E tests — verify model documentation availability and the consolidated
Docs tab (Core Documentation, Test Results, Analysis) for each model.
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers (reuse patterns from test_governance.py)
# ---------------------------------------------------------------------------

def _close_all_panels(page):
    """Close all panels and context menus to reset state."""
    page.evaluate("""() => {
        ['trading-desk-panel','hazard-curve-panel','property-hc-panel',
         'prop-storm-panel','mortgage-detail-panel','mg-panel','property-pdf-panel'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
        document.querySelectorAll('.ctx-menu').forEach(m => m.remove());
    }""")


def _open_governance_panel(page):
    """Open the governance panel using button click or JS fallback."""
    _close_all_panels(page)
    mg_btn = page.locator("#mg-panel-btn")
    if mg_btn.count() == 0:
        mg_btn = (
            page.locator("[title*='Governance']")
            .or_(page.locator("[title*='Regulatory']"))
            .or_(page.locator("[title*='Model']"))
        )
    if mg_btn.count() > 0:
        mg_btn.first.click(force=True)
        page.wait_for_timeout(1_500)

    panel = page.locator("#mg-panel")
    if not panel.is_visible():
        page.evaluate("""() => {
            const el = document.getElementById('mg-panel');
            if (el) el.style.display = 'block';
        }""")
        page.wait_for_timeout(900)


def _switch_tab(page, tab_name):
    """Switch to a governance tab by clicking the button or using JS."""
    tab_btn = page.locator(f"#mg-tab-{tab_name}")
    if tab_btn.count() > 0:
        tab_btn.first.click(force=True)
    else:
        page.evaluate(f"typeof switchMgTab === 'function' && switchMgTab('{tab_name}')")
    page.wait_for_timeout(1_500)


def _open_first_model(page):
    """Open the first model from the inventory table."""
    _open_governance_panel(page)
    _switch_tab(page, "inventory")
    page.wait_for_timeout(2_000)

    # Click the first model row in the inventory table
    row = page.locator("#mg-content table tbody tr").first
    if row.count() > 0:
        row.click(force=True)
        page.wait_for_timeout(2_000)
        return True
    return False


def _switch_detail_tab(page, tab_id):
    """Switch to a model detail sub-tab."""
    btn = page.locator(f"#mg-dtab-{tab_id}")
    if btn.count() > 0:
        btn.first.click(force=True)
    else:
        page.evaluate(f"window.MG && window.MG.switchDetailTab('{tab_id}')")
    page.wait_for_timeout(1_500)


# ---------------------------------------------------------------------------
# Tests: Docs tab structure
# ---------------------------------------------------------------------------

class TestDocsTabStructure:
    """Verify the consolidated Docs tab has three sections."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        _close_all_panels(map_page)
        yield
        _close_all_panels(map_page)

    def test_docs_tab_exists(self, map_page):
        """Model detail should have a 'Docs' tab (not separate Documentation/Test Results)."""
        opened = _open_first_model(map_page)
        if not opened:
            pytest.skip("No models in inventory to test")

        docs_tab = map_page.locator("#mg-dtab-docs")
        assert docs_tab.count() > 0, "Docs tab button not found in model detail"

        # Verify old separate tabs are gone
        testresults_tab = map_page.locator("#mg-dtab-testresults")
        assert testresults_tab.count() == 0, "Old 'Test Results' tab should not exist"

    def test_docs_tab_has_three_sections(self, map_page):
        """Docs tab should show Core Documentation, Test Results, Analysis sub-tabs."""
        opened = _open_first_model(map_page)
        if not opened:
            pytest.skip("No models in inventory to test")

        _switch_detail_tab(map_page, "docs")

        # Check for the three sub-tab buttons
        core_btn = map_page.locator("#mg-docs-btn-core-docs")
        test_btn = map_page.locator("#mg-docs-btn-test-results")
        analysis_btn = map_page.locator("#mg-docs-btn-analysis")

        assert core_btn.count() > 0, "Core Documentation sub-tab not found"
        assert test_btn.count() > 0, "Test Results sub-tab not found"
        assert analysis_btn.count() > 0, "Analysis sub-tab not found"

    def test_core_docs_section_visible_by_default(self, map_page):
        """Core Documentation section should be visible by default when Docs tab opens."""
        opened = _open_first_model(map_page)
        if not opened:
            pytest.skip("No models in inventory to test")

        _switch_detail_tab(map_page, "docs")

        core_sec = map_page.locator("#mg-docs-sec-core-docs")
        assert core_sec.count() > 0, "Core docs section container not found"
        # Should be visible (display:flex, not display:none)
        display = core_sec.evaluate("el => getComputedStyle(el).display")
        assert display != "none", "Core Documentation section should be visible by default"

    def test_test_results_section_hidden_by_default(self, map_page):
        """Test Results section should be hidden by default."""
        opened = _open_first_model(map_page)
        if not opened:
            pytest.skip("No models in inventory to test")

        _switch_detail_tab(map_page, "docs")

        test_sec = map_page.locator("#mg-docs-sec-test-results")
        assert test_sec.count() > 0, "Test results section container not found"
        display = test_sec.evaluate("el => getComputedStyle(el).display")
        assert display == "none", "Test Results section should be hidden by default"

    def test_switching_to_test_results(self, map_page):
        """Clicking Test Results sub-tab should show that section and hide others."""
        opened = _open_first_model(map_page)
        if not opened:
            pytest.skip("No models in inventory to test")

        _switch_detail_tab(map_page, "docs")

        # Click Test Results sub-tab
        test_btn = map_page.locator("#mg-docs-btn-test-results")
        if test_btn.count() > 0:
            test_btn.click(force=True)
            map_page.wait_for_timeout(500)

        test_sec = map_page.locator("#mg-docs-sec-test-results")
        core_sec = map_page.locator("#mg-docs-sec-core-docs")

        test_display = test_sec.evaluate("el => getComputedStyle(el).display")
        core_display = core_sec.evaluate("el => getComputedStyle(el).display")

        assert test_display != "none", "Test Results section should be visible after clicking"
        assert core_display == "none", "Core Documentation should be hidden after switching"

    def test_switching_to_analysis(self, map_page):
        """Clicking Analysis sub-tab should show that section."""
        opened = _open_first_model(map_page)
        if not opened:
            pytest.skip("No models in inventory to test")

        _switch_detail_tab(map_page, "docs")

        analysis_btn = map_page.locator("#mg-docs-btn-analysis")
        if analysis_btn.count() > 0:
            analysis_btn.click(force=True)
            map_page.wait_for_timeout(500)

        analysis_sec = map_page.locator("#mg-docs-sec-analysis")
        display = analysis_sec.evaluate("el => getComputedStyle(el).display")
        assert display != "none", "Analysis section should be visible after clicking"


# ---------------------------------------------------------------------------
# Tests: Documentation availability per model
# ---------------------------------------------------------------------------

class TestModelDocumentationAvailability:
    """Verify documentation PDFs are available for models via API."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        _close_all_panels(map_page)
        yield
        _close_all_panels(map_page)

    def test_documentation_pdf_endpoint_exists(self, map_page, base_url):
        """Documentation PDF endpoint should return 200 for at least one model."""
        # Test with a known model (PRS Pricing - MKM-PR-001)
        resp = map_page.evaluate("""async (baseUrl) => {
            try {
                const r = await fetch(baseUrl + '/api/v1/governance/models/MKM-PR-001/documentation/pdf', {method: 'HEAD'});
                return {status: r.status, ok: r.ok};
            } catch(e) { return {status: 0, ok: false, error: e.message}; }
        }""", base_url)
        assert resp["ok"], f"Documentation PDF not available for MKM-PR-001 (status {resp['status']})"

    def test_test_results_pdf_endpoint_exists(self, map_page, base_url):
        """Test results PDF endpoint should return 200 for at least one model."""
        resp = map_page.evaluate("""async (baseUrl) => {
            try {
                const r = await fetch(baseUrl + '/api/v1/governance/models/MKM-PR-001/test-results/pdf', {method: 'HEAD'});
                return {status: r.status, ok: r.ok};
            } catch(e) { return {status: 0, ok: false, error: e.message}; }
        }""", base_url)
        # Test results may not exist if tests haven't been run with --pdf
        # So we just verify the endpoint responds (200 or 404, not 500)
        assert resp["status"] in (200, 404), f"Unexpected status {resp['status']} for test results endpoint"

    def test_analysis_pdf_endpoint_exists(self, map_page, base_url):
        """Analysis PDF endpoint should respond (200 or 404) for a known model."""
        resp = map_page.evaluate("""async (baseUrl) => {
            try {
                const r = await fetch(baseUrl + '/api/v1/governance/models/MKM-PR-001/analysis/pdf', {method: 'HEAD'});
                return {status: r.status, ok: r.ok};
            } catch(e) { return {status: 0, ok: false, error: e.message}; }
        }""", base_url)
        assert resp["status"] in (200, 404), f"Unexpected status {resp['status']} for analysis endpoint"

    def test_all_models_have_doc_directory(self, map_page, base_url):
        """Every model in inventory should have a documentation directory mapping."""
        # Fetch model inventory
        models = map_page.evaluate("""async (baseUrl) => {
            try {
                const r = await fetch(baseUrl + '/api/v1/governance/models');
                const data = await r.json();
                return (data.models || []).map(m => m.model_id);
            } catch(e) { return []; }
        }""", base_url)

        if not models:
            pytest.skip("No models returned from inventory API")

        # Check documentation endpoint for each model
        results = map_page.evaluate("""async (args) => {
            const [baseUrl, modelIds] = args;
            const results = {};
            for (const mid of modelIds) {
                try {
                    const r = await fetch(baseUrl + '/api/v1/governance/models/' + mid + '/documentation/pdf', {method: 'HEAD'});
                    results[mid] = r.status;
                } catch(e) { results[mid] = 0; }
            }
            return results;
        }""", [base_url, models])

        # All models should return 200 (doc exists) or 404 (no doc yet), not 500
        for model_id, status in results.items():
            assert status in (200, 404), \
                f"Model {model_id}: unexpected status {status} from documentation endpoint"

        # At least some models should have docs
        has_docs = sum(1 for s in results.values() if s == 200)
        assert has_docs >= 1, "No models have documentation PDFs available"
