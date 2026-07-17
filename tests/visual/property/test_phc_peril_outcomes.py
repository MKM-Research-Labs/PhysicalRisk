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

"""Tests for the Stage 7 PRS peril-outcomes fan visualization.

Covers the standalone renderer module (phc_peril_outcomes), its wiring into
the parent panel, the Property sub-tab layout branch, and the Term Structure
peril overlay. These are JS-string contract tests (the panel emits JS text);
they guard the markers downstream charts depend on without a browser.
"""

import pytest

from visual.interactivity.property import (
    phc_peril_outcomes,
    phc_basis_property,
    phc_term,
)
from visual.interactivity.property.propertyhc import PropertyHazardCurvePanel


class TestPerilOutcomesModule:
    """The standalone peril-outcomes renderer JS fragment."""

    @pytest.fixture
    def js(self):
        return phc_peril_outcomes.get_js()

    def test_render_function_defined(self, js):
        assert "function _renderPerilOutcomes(canvasId)" in js

    def test_data_accessor_defined(self, js):
        assert "function _perilOutcomesData()" in js

    def test_chart_state_var(self, js):
        assert "var _perilOutcomesChart" in js

    def test_prefers_decomposition_mirror_then_prs_perils(self, js):
        # Prefer the BRI-adjusted node mirror, fall back to top-level prs_perils.
        assert "sd.peril_outcomes" in js
        assert "phcData.prs_perils" in js

    def test_all_four_outcomes_keyed(self, js):
        for key in ("flood_only", "wind_only", "flood_or_wind", "flood_and_wind"):
            assert key in js

    def test_reads_spread_and_count(self, js):
        assert "spread_bps" in js
        assert ".count" in js

    def test_flood_only_catchment_returns_without_drawing(self, js):
        # No peril data -> return false (caller keeps the flood-only layout).
        assert "if (!perils) return false" in js

    def test_bri_anchored_perils_appended_when_present(self, js):
        # bow/baw (BRI-resilient combined perils) are appended to the fan only
        # when present, so raw-flood-only payloads keep the four-bar layout.
        assert "perils.bri_or_wind" in js
        assert "perils.bri_and_wind" in js
        assert "order.push('bri_or_wind')" in js
        assert "order.push('bri_and_wind')" in js


class TestPerilFanPanelWiring:
    """The parent panel injects and cleans up the peril fan."""

    @pytest.fixture
    def js(self):
        return PropertyHazardCurvePanel().get_js()

    def test_module_injected(self, js):
        assert "function _renderPerilOutcomes(canvasId)" in js

    def test_chart_destroyed_in_hide_panel(self, js):
        assert "_perilOutcomesChart.destroy()" in js

    def test_chart_destroyed_on_sub_tab_switch(self, js):
        # renderBasisSubTab guards the destroy with a typeof check.
        assert "typeof _perilOutcomesChart !== 'undefined'" in js


class TestPropertySubTabPerilBranch:
    """The Property sub-tab renders the fan only when wind data is present."""

    @pytest.fixture
    def js(self):
        return phc_basis_property.get_js()

    def test_checks_peril_data_for_layout(self, js):
        assert "_perilOutcomesData" in js

    def test_renders_peril_canvas_when_present(self, js):
        assert "basis-prop-perils" in js
        assert "_renderPerilOutcomes('basis-prop-perils')" in js

    def test_keeps_waterfall_for_flood_only(self, js):
        # The flood-only branch still renders the waterfall full-height.
        assert "basis-prop-waterfall" in js

    def test_stats_bar_adds_union_when_present(self, js):
        assert "hasPerils" in js
        assert "Flood\\u222AWind:" in js


class TestTermStructurePerilOverlay:
    """The Term Structure tab overlays peril spreads when present."""

    @pytest.fixture
    def js(self):
        return phc_term.get_js()

    def test_reads_perils_term_structure(self, js):
        assert "ts.perils" in js

    def test_overlays_union_wind_joint_lines(self, js):
        assert "flood_or_wind" in js
        assert "wind_only" in js
        assert "flood_and_wind" in js

    def test_flood_spread_relabelled(self, js):
        # The base severe line is now labelled the flood spine.
        assert "Flood Spread (bp)" in js

    def test_overlays_bri_anchored_perils_from_decomposition(self, js):
        # bow/baw are not in ts.perils (raw-flood fan only); they overlay as
        # flat lines pulled from spread_decomposition when present.
        assert "spread_decomposition" in js
        assert "bow_spread_bps" in js
        assert "baw_spread_bps" in js
