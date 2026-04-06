"""Tests for Basis Explorer — SHE (elevation) sub-tab JS output."""

import pytest

from visual.interactivity.property import phc_basis_she


class TestBasisSHEJS:
    """Verify the SHE sub-tab JS contains required elements."""

    @pytest.fixture
    def js(self):
        return phc_basis_she.get_js()

    def test_render_function_defined(self, js):
        assert "function renderBasisSHE()" in js

    def test_elevation_section_function_defined(self, js):
        assert "function _drawElevationSection(" in js

    def test_reads_storm_details(self, js):
        assert "phcData.storm_details" in js

    def test_reads_property_elevation(self, js):
        assert "phcData.elevation_m" in js

    def test_reads_floor_level(self, js):
        assert "phcData.floor_level_m" in js

    def test_reads_gauge_elevation(self, js):
        assert "gauge_elevation_m" in js

    def test_height_diff_calculated(self, js):
        assert "heightDiff" in js

    def test_flood_threshold_calculated(self, js):
        assert "floodThreshold" in js

    def test_bankfull_offset(self, js):
        """Bankfull level uses 0.5m offset from severe."""
        assert "severeLevel - 0.5" in js

    def test_reaches_property_classification(self, js):
        assert "reachesProperty" in js

    def test_two_canvas_layout(self, js):
        assert "basis-she-section" in js
        assert "basis-she-waterfall" in js

    def test_waterfall_render_call(self, js):
        assert "_renderSpreadWaterfall" in js

    def test_storm_classification(self, js):
        """Storm data classifies by reach and severity."""
        assert "reachesProperty" in js
        assert "reachCount" in js

    def test_summary_shows_elevation_effect(self, js):
        assert "Elevation Effect" in js

    def test_cross_section_draws_ground(self, js):
        assert "gaugeElev" in js
        assert "propElev" in js
        assert "ctx.fill()" in js

    def test_cross_section_draws_water(self, js):
        assert "rgba(33, 150, 243" in js  # blue water fill

    def test_cross_section_severe_line(self, js):
        assert "'Severe'" in js

    def test_floor_level_drawn(self, js):
        assert "'Floor +" in js

    def test_click_sets_selected_storm(self, js):
        assert "basisSelectedStorm" in js

    def test_she_spread_in_stats(self, js):
        assert "she_spread_bps" in js

    def test_chart_variable_declared(self, js):
        assert "var basisSHEChart" in js

    def test_summary_shows_counts(self, js):
        assert "reachCount" in js
        assert "severeCount" in js
