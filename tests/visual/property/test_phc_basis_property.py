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

"""Tests for Basis Explorer — Property (impact) sub-tab JS output."""

import pytest

from visual.interactivity.property import phc_basis_property


class TestBasisPropertyJS:
    """Verify the Property sub-tab JS contains required elements."""

    @pytest.fixture
    def js(self):
        return phc_basis_property.get_js()

    def test_render_function_defined(self, js):
        assert "function renderBasisProperty()" in js

    def test_reads_storm_details(self, js):
        assert "phcData.storm_details" in js

    def test_reads_spread_decomposition(self, js):
        assert "phcData.spread_decomposition" in js

    def test_uses_exceeded_severe_flag(self, js):
        assert "exceeded_severe" in js

    def test_scatter_chart_type(self, js):
        assert "type: 'scatter'" in js

    def test_x_axis_is_gauge_peak(self, js):
        assert "Gauge Peak Water Level" in js

    def test_y_axis_is_asset_flood_depth(self, js):
        # Renamed from "Property Flood Depth" -> "Asset Flood Depth"
        # in the Property->Asset terminology pass (commit d3db6d5e).
        assert "Asset Flood Depth" in js

    def test_quadrant_hedged(self, js):
        assert "qTopRight" in js
        assert "Hedged" in js

    def test_quadrant_basis_risk(self, js):
        assert "qBottomRight" in js
        assert "Basis Risk" in js

    def test_quadrant_unhedged(self, js):
        assert "qTopLeft" in js
        assert "Unhedged" in js

    def test_quadrant_no_event(self, js):
        assert "qBottomLeft" in js
        assert "No Event" in js

    def test_severe_vertical_annotation(self, js):
        assert "severeLine" in js
        assert "Gauge Severe Trigger" in js

    def test_colour_by_damage_ratio(self, js):
        assert "damageRatio" in js
        assert "Theme.value('amber-mid')" in js  # light orange
        assert "Theme.value('amber-bright')" in js  # orange
        assert "Theme.value('red-bright')" in js  # red
        assert "Theme.value('red-deep')" in js  # dark red

    def test_summary_cards_rendered(self, js):
        assert "var(--ok-bg)" in js  # green card bg
        assert "var(--warn-bg-warm)" in js  # orange card bg
        assert "var(--danger-bg-soft)" in js  # red card bg

    def test_click_sets_selected_storm(self, js):
        assert "basisSelectedStorm" in js

    def test_tooltip_shows_quadrant_info(self, js):
        assert "Basis risk:" in js or "basis risk" in js
        assert "Hedged" in js

    def test_gauge_spread_in_stats(self, js):
        assert "gauge_spread_bps" in js

    def test_property_spread_in_stats(self, js):
        assert "property_spread_bps" in js

    def test_chart_variable_declared(self, js):
        assert "var basisPropertyChart" in js

    def test_basis_computed(self, js):
        assert "propSpread - gaugeSpread" in js
