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

"""Tests for Basis Explorer tab wiring in propertyhc.py.

Verifies the parent panel correctly integrates the 4 basis sub-tabs
(Gauge, SHE, SHD, Property) as a nested tab group within the
Basis Explorer top-level tab.
"""

import pytest

from visual.interactivity.property.propertyhc import PropertyHazardCurvePanel


class TestBasisExplorerTabWiring:
    """Verify the Basis Explorer tab and sub-tab wiring in the panel JS."""

    @pytest.fixture
    def js(self):
        panel = PropertyHazardCurvePanel()
        return panel.get_js()

    def test_top_level_tab_renamed(self, js):
        """Tab bar label is Basis Explorer, not Basis Analysis."""
        assert "'Basis Explorer'" in js
        # Legacy phc_basis module JS still contains "Basis Analysis" in comments,
        # but the tab label array must use "Basis Explorer"
        assert "'Basis Analysis'" not in js

    def test_sub_tab_names_defined(self, js):
        assert "'Gauge'" in js
        assert "'SHE'" in js
        assert "'SHD'" in js
        assert "'Property'" in js

    def test_sub_tab_names_array(self, js):
        assert "basisSubTabNames" in js

    def test_basis_active_sub_tab_state(self, js):
        assert "var basisActiveSubTab" in js

    def test_basis_selected_storm_state(self, js):
        assert "var basisSelectedStorm" in js

    def test_render_basis_explorer_function(self, js):
        assert "function renderBasisExplorer()" in js

    def test_render_basis_sub_tab_function(self, js):
        assert "function renderBasisSubTab(idx)" in js

    def test_sub_tab_bar_created(self, js):
        assert "phc-basis-subtab-bar" in js

    def test_sub_tab_bar_styling(self, js):
        assert "phc-basis-subtab" in js

    def test_switch_tab_calls_basis_explorer(self, js):
        assert "renderBasisExplorer()" in js

    def test_sub_tab_dispatches_gauge(self, js):
        assert "renderBasisGauge()" in js

    def test_sub_tab_dispatches_she(self, js):
        assert "renderBasisSHE()" in js

    def test_sub_tab_dispatches_shd(self, js):
        assert "renderBasisSHD()" in js

    def test_sub_tab_dispatches_property(self, js):
        assert "renderBasisProperty()" in js

    def test_sub_tab_bar_removed_on_tab_switch(self, js):
        """Sub-tab bar should be removed when switching to non-basis tabs."""
        assert "existingSubBar" in js or "subBar.remove()" in js

    def test_charts_destroyed_on_sub_tab_switch(self, js):
        """All basis charts destroyed before rendering new sub-tab."""
        assert "basisGaugeChart.destroy()" in js
        assert "basisSHEChart.destroy()" in js
        assert "basisSHDChart.destroy()" in js
        assert "basisPropertyChart.destroy()" in js

    def test_hide_panel_cleans_up_basis_state(self, js):
        """hidePanel must reset basis state and destroy charts."""
        # Find the hidePanel section and verify it cleans up
        assert "basisSelectedStorm = null" in js
        assert "basisActiveSubTab = 0" in js

    def test_container_flex_column_for_basis(self, js):
        """Chart container set to flex-column for basis layouts."""
        assert "flexDirection" in js

    def test_container_style_reset_for_non_basis(self, js):
        """Chart container style reset when switching to non-basis tabs."""
        # ensureCanvas resets flex styles
        assert "container.style.display = ''" in js


class TestBasisExplorerSubModuleImports:
    """Verify all basis sub-module JS is injected into the panel."""

    @pytest.fixture
    def js(self):
        panel = PropertyHazardCurvePanel()
        return panel.get_js()

    def test_gauge_module_injected(self, js):
        assert "var basisGaugeChart" in js

    def test_she_module_injected(self, js):
        assert "var basisSHEChart" in js

    def test_shd_module_injected(self, js):
        assert "var basisSHDChart" in js

    def test_property_module_injected(self, js):
        assert "var basisPropertyChart" in js

    def test_elevation_section_available(self, js):
        assert "_drawElevationSection" in js

    def test_distance_decay_available(self, js):
        assert "_drawDistanceDecay" in js


class TestBasisExplorerPanelConfig:
    """Verify panel configuration still works with the new tabs."""

    def test_default_panel_dimensions(self):
        panel = PropertyHazardCurvePanel()
        assert panel.panel_width == "1100px"
        assert panel.panel_height == "92vh"

    def test_custom_panel_dimensions(self):
        panel = PropertyHazardCurvePanel(panel_width="1400px", panel_height="900px")
        js = panel.get_js()
        assert "1400px" in js
        assert "900px" in js

    def test_panel_has_four_top_level_tabs(self):
        panel = PropertyHazardCurvePanel()
        js = panel.get_js()
        # Count tab names in the tabs array
        assert js.count("'Hazard Curve'") >= 1
        assert js.count("'Term Structure'") >= 1
        assert js.count("'PRS Pricing'") >= 1
        assert js.count("'Basis Explorer'") >= 1
