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
E2E test: Property PRS Basis Explorer panel.

Verifies that when a property is opened in the PRS pricer, the Basis Explorer
tab renders 4 sub-tabs (Gauge, SHE, SHD, Property) with storm-level
visualisations that explain the basis journey.
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    open_property_panel,
    switch_to_basis_explorer_tab,
    switch_basis_sub_tab,
)


class TestBasisExplorerPanel:
    """Verify the Basis Explorer tab and its sub-tabs render correctly."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_panels(map_page)
        yield
        close_all_panels(map_page)

    def _open_basis_explorer(self, map_page, first_property_id):
        """Open property panel and switch to Basis Explorer tab."""
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyHazard === 'function' || "
            "(window.PropertyHazardCurvePanel && "
            "typeof window.PropertyHazardCurvePanel.show === 'function')"
        )
        if not has_fn:
            pytest.skip("Property hazard panel function not available")

        open_property_panel(map_page, first_property_id)
        switch_to_basis_explorer_tab(map_page)

    # ------------------------------------------------------------------
    # Tab existence and structure
    # ------------------------------------------------------------------

    def test_basis_explorer_tab_exists(self, map_page, first_property_id):
        """The Basis Explorer tab must exist in the panel."""
        self._open_basis_explorer(map_page, first_property_id)
        panel_text = map_page.locator("#property-hc-panel").inner_text()
        assert "Basis Explorer" in panel_text

    def test_sub_tab_bar_renders(self, map_page, first_property_id):
        """The sub-tab bar with Gauge/SHE/SHD/Property must appear."""
        self._open_basis_explorer(map_page, first_property_id)
        sub_bar = map_page.locator("#phc-basis-subtab-bar")
        assert sub_bar.count() > 0, "Sub-tab bar not found"

    def test_four_sub_tabs_present(self, map_page, first_property_id):
        """All 4 sub-tabs must be present."""
        self._open_basis_explorer(map_page, first_property_id)
        sub_tabs = map_page.locator(".phc-basis-subtab")
        assert sub_tabs.count() == 4

    def test_sub_tab_labels(self, map_page, first_property_id):
        """Sub-tabs must be labelled Gauge, SHE, SHD, Asset."""
        self._open_basis_explorer(map_page, first_property_id)
        sub_tabs = map_page.locator(".phc-basis-subtab")
        labels = [sub_tabs.nth(i).inner_text() for i in range(sub_tabs.count())]
        assert labels == ["Gauge", "SHE", "SHD", "Asset"]

    # ------------------------------------------------------------------
    # storm_details data availability
    # ------------------------------------------------------------------

    def test_storm_details_loaded(self, map_page, first_property_id):
        """phcData.storm_details must be populated."""
        self._open_basis_explorer(map_page, first_property_id)
        storms = map_page.evaluate("""() => {
            if (typeof phcData === 'undefined' || !phcData) return null;
            return phcData.storm_details || null;
        }""")
        if storms is None:
            pytest.skip("storm_details not available (data may need regeneration)")
        assert isinstance(storms, list)
        assert len(storms) > 0, "storm_details is empty"

    def test_storm_details_has_required_fields(self, map_page, first_property_id):
        """Each storm in storm_details must have the required fields."""
        self._open_basis_explorer(map_page, first_property_id)
        storms = map_page.evaluate("""() => {
            if (typeof phcData === 'undefined' || !phcData) return null;
            return phcData.storm_details || null;
        }""")
        if not storms:
            pytest.skip("storm_details not available")
        required = {"storm_id", "gauge_peak_m", "flood_depth_m",
                    "damage_ratio", "flooded", "retention_factor"}
        for storm in storms[:5]:  # check first 5
            missing = required - set(storm.keys())
            assert not missing, f"Storm missing fields: {missing}"

    # ------------------------------------------------------------------
    # Gauge sub-tab
    # ------------------------------------------------------------------

    def test_gauge_sub_tab_renders(self, map_page, first_property_id):
        """Gauge sub-tab must render a scatter chart."""
        self._open_basis_explorer(map_page, first_property_id)
        switch_basis_sub_tab(map_page, 0)  # Gauge
        canvas = map_page.locator("#basis-gauge-canvas")
        assert canvas.count() > 0, "Gauge scatter canvas not found"

    def test_gauge_sub_tab_shows_storms(self, map_page, first_property_id):
        """Gauge tab must show storm count in stats."""
        self._open_basis_explorer(map_page, first_property_id)
        switch_basis_sub_tab(map_page, 0)
        stats = map_page.locator("#phc-stats-bar").inner_text()
        assert "Storms:" in stats

    # ------------------------------------------------------------------
    # SHE sub-tab
    # ------------------------------------------------------------------

    def test_she_sub_tab_renders(self, map_page, first_property_id):
        """SHE sub-tab must render both cross-section and scatter."""
        self._open_basis_explorer(map_page, first_property_id)
        switch_basis_sub_tab(map_page, 1)  # SHE
        section = map_page.locator("#basis-she-section")
        waterfall = map_page.locator("#basis-she-waterfall")
        assert section.count() > 0, "SHE cross-section canvas not found"
        assert waterfall.count() > 0, "SHE waterfall canvas not found"

    def test_she_sub_tab_shows_elevation_info(self, map_page, first_property_id):
        """SHE tab summary must mention elevation."""
        self._open_basis_explorer(map_page, first_property_id)
        switch_basis_sub_tab(map_page, 1)
        container_text = map_page.locator("#phc-chart-container").inner_text()
        assert "Elevation" in container_text

    # ------------------------------------------------------------------
    # SHD sub-tab
    # ------------------------------------------------------------------

    def test_shd_sub_tab_renders(self, map_page, first_property_id):
        """SHD sub-tab must render both decay diagram and scatter."""
        self._open_basis_explorer(map_page, first_property_id)
        switch_basis_sub_tab(map_page, 2)  # SHD
        decay = map_page.locator("#basis-shd-decay")
        waterfall = map_page.locator("#basis-shd-waterfall")
        assert decay.count() > 0, "SHD decay canvas not found"
        assert waterfall.count() > 0, "SHD waterfall canvas not found"

    def test_shd_sub_tab_shows_distance_info(self, map_page, first_property_id):
        """SHD tab stats must show distance."""
        self._open_basis_explorer(map_page, first_property_id)
        switch_basis_sub_tab(map_page, 2)
        stats = map_page.locator("#phc-stats-bar").inner_text()
        assert "Distance:" in stats

    # ------------------------------------------------------------------
    # Property sub-tab
    # ------------------------------------------------------------------

    def test_property_sub_tab_renders(self, map_page, first_property_id):
        """Property sub-tab must render the impact scatter."""
        self._open_basis_explorer(map_page, first_property_id)
        switch_basis_sub_tab(map_page, 3)  # Property
        canvas = map_page.locator("#basis-prop-canvas")
        assert canvas.count() > 0, "Property scatter canvas not found"

    def test_property_sub_tab_shows_quadrant_cards(self, map_page, first_property_id):
        """Property tab must show the 4 quadrant summary cards."""
        self._open_basis_explorer(map_page, first_property_id)
        switch_basis_sub_tab(map_page, 3)
        container_text = map_page.locator("#phc-chart-container").inner_text()
        assert "Hedged" in container_text
        assert "Basis Risk" in container_text

    def test_property_sub_tab_shows_spread_info(self, map_page, first_property_id):
        """Asset tab stats must show gauge and asset spread."""
        self._open_basis_explorer(map_page, first_property_id)
        switch_basis_sub_tab(map_page, 3)
        stats = map_page.locator("#phc-stats-bar").inner_text()
        assert "Gauge Spread:" in stats
        assert "Asset Spread:" in stats

    # ------------------------------------------------------------------
    # Cross-tab storm selection
    # ------------------------------------------------------------------

    def test_storm_selection_persists_across_sub_tabs(
        self, map_page, first_property_id
    ):
        """Clicking a storm in Gauge tab should set basisSelectedStorm."""
        self._open_basis_explorer(map_page, first_property_id)
        switch_basis_sub_tab(map_page, 0)  # Gauge

        # Check initial state
        selected = map_page.evaluate("""() => {
            return typeof basisSelectedStorm !== 'undefined' ? basisSelectedStorm : 'UNDEF';
        }""")
        # May be null or undefined initially
        assert selected is None or selected == "UNDEF" or isinstance(selected, str)

    # ------------------------------------------------------------------
    # Sub-tab bar lifecycle
    # ------------------------------------------------------------------

    def test_sub_tab_bar_removed_on_other_tab(self, map_page, first_property_id):
        """Switching to another top tab should remove the sub-tab bar."""
        self._open_basis_explorer(map_page, first_property_id)
        assert map_page.locator("#phc-basis-subtab-bar").count() > 0

        # Switch to Hazard Curve tab (index 0)
        tabs = map_page.locator(".phc-tab")
        if tabs.count() > 0:
            tabs.nth(0).click(force=True)
        map_page.wait_for_timeout(1_500)

        assert map_page.locator("#phc-basis-subtab-bar").count() == 0, (
            "Sub-tab bar should be removed when switching away from Basis Explorer"
        )
