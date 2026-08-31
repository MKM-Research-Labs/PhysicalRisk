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

"""Tests for Basis Explorer — SHD (distance) sub-tab JS output."""

import pytest

from visual.interactivity.property import phc_basis_shd


class TestBasisSHDJS:
    """Verify the SHD sub-tab JS contains required elements."""

    @pytest.fixture
    def js(self):
        return phc_basis_shd.get_js()

    def test_render_function_defined(self, js):
        assert "function renderBasisSHD()" in js

    def test_distance_decay_function_defined(self, js):
        assert "function _drawDistanceDecay(" in js

    def test_reads_storm_details(self, js):
        assert "phcData.storm_details" in js

    def test_reads_distance_km(self, js):
        assert "distance_km" in js

    def test_reads_retention_factor(self, js):
        assert "retention_factor" in js

    def test_sorts_by_flood_depth(self, js):
        assert "flood_depth_m" in js
        assert "sort(" in js

    def test_two_canvas_layout(self, js):
        assert "basis-shd-decay" in js
        assert "basis-shd-waterfall" in js

    def test_waterfall_render_call(self, js):
        assert "_renderSpreadWaterfall" in js

    def test_storm_data_classification(self, js):
        """Storm data sorted by flood depth."""
        assert "flood_depth_m" in js

    def test_distance_decay_curve_drawn(self, js):
        """Decay curve: retention = 1 - d/25."""
        assert "1 - d / 25" in js

    def test_gauge_marker_at_origin(self, js):
        assert "Theme.value('green-bright')" in js  # green gauge marker

    def test_property_marker(self, js):
        assert "Theme.value('red-bright')" in js  # red property marker

    def test_selected_storm_highlight(self, js):
        """Selected storm gets a highlight circle."""
        assert "Theme.value('amber-bright')" in js  # orange highlight

    def test_click_sets_selected_storm(self, js):
        assert "basisSelectedStorm" in js

    def test_shd_spread_in_stats(self, js):
        assert "shd_spread_bps" in js

    def test_chart_variable_declared(self, js):
        assert "var basisSHDChart" in js

    def test_summary_shows_with_depth_count(self, js):
        assert "withDepthCount" in js

    def test_summary_shows_avg_retention(self, js):
        assert "avgRetention" in js

    def test_axes_drawn(self, js):
        assert "'Distance (km)'" in js
        assert "'Retention Factor'" in js

    def test_retention_in_summary(self, js):
        assert "Avg retention" in js

    def test_waterfall_renders_spread(self, js):
        assert "_renderSpreadWaterfall" in js
        assert "'basis-shd-waterfall'" in js
