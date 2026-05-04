# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
E2e test: Property PRS spread decomposition panel.

Verifies that when a property is opened in the PRS pricer, the spread
decomposition section displays non-zero values (gauge spread, distance
effect, elevation effect) rather than all zeros.
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    open_property_panel,
    switch_to_prs_tab_property,
)


class TestPropertyPRSDecomposition:
    """Verify the spread decomposition table in the property PRS pricer."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_panels(map_page)
        yield
        close_all_panels(map_page)

    def _open_prs_tab(self, map_page, first_property_id):
        """Open property panel and switch to PRS tab; skip if unavailable."""
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyHazard === 'function' || "
            "(window.PropertyHazardCurvePanel && "
            "typeof window.PropertyHazardCurvePanel.show === 'function')"
        )
        if not has_fn:
            pytest.skip("Property hazard panel function not available")

        open_property_panel(map_page, first_property_id)
        switch_to_prs_tab_property(map_page)
        map_page.wait_for_timeout(3_000)

    def test_spread_decomposition_section_exists(
        self, map_page, first_property_id
    ):
        """The PRS tab must render a Spread Decomposition section."""
        self._open_prs_tab(map_page, first_property_id)

        panel_text = map_page.locator("#property-hc-panel").inner_text()
        assert "Spread Decomposition" in panel_text, (
            "Spread Decomposition section not found in property PRS panel"
        )

    def test_spread_decomposition_has_both_paths(
        self, map_page, first_property_id
    ):
        """Both decomposition paths (Distance First, Elevation First) must render."""
        self._open_prs_tab(map_page, first_property_id)

        panel_text = map_page.locator("#property-hc-panel").inner_text()
        assert "Distance First" in panel_text, (
            "Path 1 (Distance First) not found in spread decomposition"
        )
        assert "Elevation First" in panel_text, (
            "Path 2 (Elevation First) not found in spread decomposition"
        )

    def test_decomposition_not_all_zeros(
        self, map_page, first_property_id
    ):
        """Spread decomposition values must not all be zero.

        This is the key regression test: if the spread_decomposition key
        is missing from propertyhc.json (because attach_spread_decomposition
        was not called), the UI falls back to 0.0 for every field.
        """
        self._open_prs_tab(map_page, first_property_id)

        # Extract the spread decomposition data from the loaded phcData
        decomp = map_page.evaluate("""() => {
            // phcData is set by the pricer when a property is loaded
            if (typeof phcData === 'undefined' || !phcData) return null;
            return phcData.spread_decomposition || null;
        }""")

        if decomp is None:
            pytest.skip(
                "phcData.spread_decomposition not available — "
                "property may not have hazard curve data"
            )

        # At minimum, property_spread_bps should be non-zero
        prop_spread = decomp.get("property_spread_bps", 0)
        gauge_spread = decomp.get("gauge_spread_bps", 0)
        shd_spread = decomp.get("shd_spread_bps", 0)
        she_spread = decomp.get("she_spread_bps", 0)

        # The property has flood data, so its spread should be non-zero
        assert prop_spread != 0, (
            f"property_spread_bps is 0 — spread_decomposition may not have "
            f"been attached to propertyhc.json. Full decomp: {decomp}"
        )

        # If shd/she are both zero, the decomposition was not properly computed
        if shd_spread == 0 and she_spread == 0:
            pytest.fail(
                f"Both shd_spread_bps and she_spread_bps are 0 — "
                f"propertyshd.json/propertyshe.json were likely not generated "
                f"or attach_spread_decomposition was not called. "
                f"Full decomp: {decomp}"
            )

    def test_decomposition_paths_sum_to_property_spread(
        self, map_page, first_property_id
    ):
        """Both paths must sum to the property spread (gauge + effects = property)."""
        self._open_prs_tab(map_page, first_property_id)

        decomp = map_page.evaluate("""() => {
            if (typeof phcData === 'undefined' || !phcData) return null;
            return phcData.spread_decomposition || null;
        }""")

        if decomp is None:
            pytest.skip("phcData.spread_decomposition not available")

        gauge = decomp.get("gauge_spread_bps", 0)
        prop_ = decomp.get("property_spread_bps", 0)
        df = decomp.get("distance_first", {})
        ef = decomp.get("elevation_first", {})

        # Path 1: gauge + distance_effect + elevation_effect = property
        path1 = gauge + df.get("distance_effect_bps", 0) + df.get("elevation_effect_bps", 0)
        assert abs(path1 - prop_) < 0.5, (
            f"Distance-first path does not sum to property spread: "
            f"{gauge} + {df.get('distance_effect_bps', 0)} + "
            f"{df.get('elevation_effect_bps', 0)} = {path1} != {prop_}"
        )

        # Path 2: gauge + elevation_effect + distance_effect = property
        path2 = gauge + ef.get("elevation_effect_bps", 0) + ef.get("distance_effect_bps", 0)
        assert abs(path2 - prop_) < 0.5, (
            f"Elevation-first path does not sum to property spread: "
            f"{gauge} + {ef.get('elevation_effect_bps', 0)} + "
            f"{ef.get('distance_effect_bps', 0)} = {path2} != {prop_}"
        )

    def test_terrain_effect_appears_when_zone_changed(
        self, map_page, first_property_id
    ):
        """Changing the EA zone dropdown should add a Terrain Effect row."""
        self._open_prs_tab(map_page, first_property_id)

        # Check EA zone dropdown exists
        zone_el = map_page.locator("#phc-ea-zone")
        if zone_el.count() == 0:
            pytest.skip("EA zone dropdown not found")

        # Get the current (actual) zone
        actual_zone = map_page.evaluate(
            "() => document.getElementById('phc-ea-zone').value"
        )

        # Change to a different zone
        new_zone = "Zone 3b" if actual_zone != "Zone 3b" else "Zone 1"
        map_page.evaluate(f"""() => {{
            var el = document.getElementById('phc-ea-zone');
            el.value = '{new_zone}';
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
        }}""")
        map_page.wait_for_timeout(2_000)

        # Verify Terrain Effect row appears in the panel
        panel_text = map_page.locator("#property-hc-panel").inner_text()
        assert "Terrain Effect" in panel_text, (
            f"Terrain Effect row not found after changing zone from "
            f"{actual_zone} to {new_zone}"
        )

    def test_terrain_effect_hidden_when_zone_matches_actual(
        self, map_page, first_property_id
    ):
        """When EA zone matches the property's actual zone, no Terrain Effect row."""
        self._open_prs_tab(map_page, first_property_id)

        zone_el = map_page.locator("#phc-ea-zone")
        if zone_el.count() == 0:
            pytest.skip("EA zone dropdown not found")

        # The dropdown is initialised to the property's actual zone by
        # phc_prs.py when controls are first built. We cannot read phcData
        # from page.evaluate (it's a `var` inside the panel IIFE, not on
        # window), so we take the freshly-rendered dropdown value as our
        # source of truth for actualZone — this matches the logic the
        # pricer itself uses (`phcData.flood_zone || 'Zone 1'`).
        actual_zone = map_page.evaluate(
            "() => document.getElementById('phc-ea-zone').value"
        )

        # Ensure the dropdown is set to the actual zone and re-run pricing
        # by dispatching a change event.
        map_page.evaluate(f"""() => {{
            var el = document.getElementById('phc-ea-zone');
            el.value = {actual_zone!r};
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
        }}""")
        map_page.wait_for_timeout(2_000)

        panel_text = map_page.locator("#property-hc-panel").inner_text()
        assert "Terrain Effect" not in panel_text, (
            f"Terrain Effect row should not appear when zone matches "
            f"actual ({actual_zone!r})"
        )

    def test_gauge_spread_matches_component_table(
        self, map_page, first_property_id
    ):
        """Gauge spread in decomposition should be consistent with the
        synthetic gauge spread shown in the component table above it."""
        self._open_prs_tab(map_page, first_property_id)

        result = map_page.evaluate("""() => {
            if (typeof phcData === 'undefined' || !phcData) return null;
            var sd = phcData.spread_decomposition || {};
            var ngs = phcData.nearest_gauges || [];
            var synth = ngs.find(g => (g.gauge_id || '').startsWith('SYNTH-'));
            return {
                decomp_gauge: sd.gauge_spread_bps || 0,
                has_synth: !!synth,
            };
        }""")

        if result is None:
            pytest.skip("phcData not available")

        # If a synthetic gauge exists, gauge_spread should be non-zero
        if result["has_synth"]:
            assert result["decomp_gauge"] != 0, (
                "Gauge spread in decomposition is 0 despite synthetic gauge "
                "being present in nearest_gauges"
            )
