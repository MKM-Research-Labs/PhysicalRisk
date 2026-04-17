"""Tests for terrain effect row in PRS waterfall renderer."""

import pytest

from visual.interactivity.property import phc_prs_render


class TestTerrainEffectRow:
    """Verify the terrain effect row appears in the waterfall decomposition."""

    @pytest.fixture
    def js(self):
        return phc_prs_render.get_js()

    def test_terrain_delta_variable(self, js):
        assert 'terrainDelta' in js

    def test_terrain_row_conditional(self, js):
        """Terrain row is gated behind the zone-mismatch + noise-floor check.

        The renderer only shows the terrain adjustment when the user has
        selected a counterfactual zone (zoneMatches is false) AND the delta
        exceeds the 0.05 bps noise floor — any residual pricer delta below
        that is suppressed as numerical noise, not a real adjustment.
        """
        assert 'if (!zoneMatches && Math.abs(terrainDelta) >= 0.05)' in js

    def test_terrain_effect_label(self, js):
        assert 'Terrain Effect' in js

    def test_terrain_row_in_path1(self, js):
        """terrainRow should be inserted in Path 1 (after Gauge Spread)."""
        # terrainRow appears after Path 1 header and Gauge Spread row
        idx_path1 = js.index('Path 1: Distance First')
        idx_terrain1 = js.index('terrainRow', idx_path1)
        idx_distance1 = js.index('distEff1', idx_terrain1)
        assert idx_terrain1 < idx_distance1

    def test_terrain_row_in_path2(self, js):
        """terrainRow should be inserted in Path 2 (after header)."""
        idx_path2 = js.index('Path 2: Elevation First')
        idx_terrain2 = js.index('terrainRow', idx_path2)
        idx_elev2 = js.index('elevEff2', idx_terrain2)
        assert idx_terrain2 < idx_elev2

    def test_adjusted_prop_spread_in_total(self, js):
        """Property Spread row should show adjustedPropSpread."""
        assert 'adjustedPropSpread.toFixed(1)' in js

    def test_terrain_colour_green_negative(self, js):
        """Negative terrain delta (risk reduction) should be green."""
        assert "#2E7D32" in js  # Green colour code

    def test_terrain_colour_orange_positive(self, js):
        """Positive terrain delta (risk increase) should be orange."""
        assert "#E65100" in js  # Orange colour code

    def test_terrain_row_background(self, js):
        """Terrain row should have purple-tinted background."""
        assert '#F3E5F5' in js

    def test_selected_zone_shown_in_detail(self, js):
        """Detail column should show the selected zone name."""
        # The terrainRow includes selectedZone in the detail column
        assert "selectedZone + '</td></tr>'" in js


class TestStatsBarZoneIndicator:
    """Verify zone indicator in the stats bar."""

    @pytest.fixture
    def js(self):
        return phc_prs_render.get_js()

    def test_zone_tag_present(self, js):
        assert 'zoneTag' in js

    def test_zone_tag_conditional(self, js):
        """Zone tag only shown when selected zone differs from actual."""
        assert 'selectedZone !== actualZone' in js

    def test_zone_tag_shows_vs_actual(self, js):
        """Zone tag should show 'vs' the actual zone."""
        assert '(vs ' in js

    def test_adjusted_spread_in_stats_bar(self, js):
        """Stats bar spread should use adjustedPropSpread."""
        # Find the bar.innerHTML section
        idx_bar = js.index('bar.innerHTML')
        idx_spread = js.index('adjustedPropSpread', idx_bar)
        assert idx_spread > idx_bar
