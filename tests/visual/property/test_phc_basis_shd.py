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
        assert "basis-shd-scatter" in js

    def test_scatter_chart_type(self, js):
        assert "type: 'scatter'" in js

    def test_colour_gradient_for_depth(self, js):
        """Blue gradient for depth, grey for zero."""
        assert "'#BDBDBD'" in js  # grey for zero

    def test_distance_decay_curve_drawn(self, js):
        """Decay curve: retention = 1 - d/25."""
        assert "1 - d / 25" in js

    def test_gauge_marker_at_origin(self, js):
        assert "'#4CAF50'" in js  # green gauge marker

    def test_property_marker(self, js):
        assert "'#F44336'" in js  # red property marker

    def test_selected_storm_highlight(self, js):
        """Selected storm gets a highlight circle."""
        assert "'#FF9800'" in js  # orange highlight

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

    def test_tooltip_shows_retention(self, js):
        assert "Retention:" in js

    def test_tooltip_shows_flood_depth(self, js):
        assert "Flood depth:" in js
