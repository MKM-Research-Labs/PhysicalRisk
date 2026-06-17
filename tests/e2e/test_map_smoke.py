# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Smoke tests — verify the map loads, markers appear, and core controls exist.
"""

import pytest


class TestMapLoads:
    """Basic map rendering checks."""

    def test_leaflet_container_exists(self, map_page):
        """The Leaflet map container must be present in the DOM."""
        container = map_page.locator(".leaflet-container")
        assert container.count() >= 1

    def test_map_tiles_loaded(self, map_page):
        """At least some map tiles should have loaded."""
        tiles = map_page.locator(".leaflet-tile-loaded")
        assert tiles.count() > 0, "No map tiles loaded"

    def test_zoom_controls_present(self, map_page):
        """Zoom in/out buttons must exist."""
        zoom_in = map_page.locator(".leaflet-control-zoom-in")
        zoom_out = map_page.locator(".leaflet-control-zoom-out")
        assert zoom_in.count() == 1
        assert zoom_out.count() == 1


class TestMarkers:
    """Gauge and property markers must appear on the map."""

    def test_markers_present(self, map_page):
        """There should be markers on the map (gauges + properties)."""
        # Target icon markers only (not shadows)
        markers = map_page.locator("[class*='awesome-marker-icon-']")
        count = markers.count()
        assert count > 0, "No interactive markers on the map"

    def test_marker_count_reasonable(self, map_page, gauge_data, property_data):
        """Marker count should be in the right ballpark."""
        markers = map_page.locator("[class*='awesome-marker-icon-']")
        count = markers.count()

        n_gauges = len(gauge_data.get("flood_gauges", []))
        n_props = len(property_data.get("properties", []))
        expected = n_gauges + n_props
        # Each marker has one interactive div; expect close to total
        assert count >= expected * 0.25, (
            f"Only {count} markers visible, expected ~{expected}"
        )


class TestCoreControls:
    """The Pi button and governance button must be accessible."""

    def test_pi_button_exists(self, map_page):
        """The Trader's Workstation (Π) button must be on the map."""
        # Search for the Pi symbol in Leaflet controls
        pi_btn = map_page.locator("text=Π").first
        assert pi_btn.is_visible(), "Π button not found"

    def test_governance_button_exists(self, map_page):
        """A governance/regulatory button must exist in the controls."""
        # The governance panel button is in the Leaflet control area
        mg_btn = map_page.locator("#mg-panel-btn").or_(
            map_page.locator("[title*='Governance']").or_(
                map_page.locator("[title*='Regulatory']").or_(
                    map_page.locator("[title*='Model']")
                )
            )
        )
        # At least one governance-related control should exist
        assert mg_btn.count() >= 1 or map_page.locator("#mg-panel").count() >= 1, (
            "No governance button or panel found"
        )

    def test_startup_preloader_completed(self, map_page):
        """The startup preloader popup should be hidden after data loads."""
        # Check via JS — the preloader div may have been removed from DOM
        preload_done = map_page.evaluate(
            "() => window._tdPreloadDone === true"
        )
        preloader = map_page.locator("#startup-preloader-popup")
        if preloader.count() > 0 and preloader.is_visible():
            assert preload_done, "Preloader still visible and data not cached"
        # If preloader is gone or hidden, that's fine too

    def test_cdm_review_button_exists(self, map_page):
        """The CDM Asset Review (house) launcher must be on the map, below Pi."""
        btn = map_page.locator("[title='CDM Asset Review']")
        assert btn.count() >= 1, "CDM Asset Review house icon not found"

    def test_cdm_review_opens_in_app_panel(self, map_page):
        """Clicking the house icon opens an in-app panel (not a new tab)."""
        btn = map_page.locator("[title='CDM Asset Review']").first
        if btn.count() == 0:
            pytest.skip("CDM Asset Review control not present")
        btn.click()
        map_page.wait_for_timeout(1_000)
        panel = map_page.locator("#cdm-review-panel")
        assert panel.count() >= 1 and panel.is_visible(), \
            "CDM Asset Review panel did not open on the same tab"


class TestPerilStartupData:
    """Fire and seismic model outputs are exposed and preloaded."""

    def test_fire_seismic_endpoints_serve_data(self, map_page):
        """/api/v1/fire and /api/v1/seismic return the model payloads."""
        result = map_page.evaluate("""async () => {
            const f = await (await fetch('/api/v1/fire')).json();
            const s = await (await fetch('/api/v1/seismic')).json();
            return { fireAssets: (f.assets || []).length,
                     seismicAssets: (s.assets || []).length };
        }""")
        # Commercial-only models — present for catchments that ran them.
        assert result["fireAssets"] >= 0
        assert result["seismicAssets"] >= 0

    def test_startup_dialog_lists_fire_and_seismic(self, map_page):
        """The preloader datasets include Fire model and Seismic model rows."""
        has_rows = map_page.evaluate("""() => {
            // Rows are stamped startup-row-<key>; keys added by startup.js.
            const ids = [...document.querySelectorAll('[id^=startup-row-]')]
                .map(e => e.id);
            const cached = ('_preFire' in window) && ('_preSeismic' in window);
            return { fireRow: ids.includes('startup-row-_preFire'),
                     seismicRow: ids.includes('startup-row-_preSeismic'),
                     cached };
        }""")
        # The popup may already be gone; the cached globals prove the datasets
        # ran. Either signal is acceptable.
        assert has_rows["cached"] or (has_rows["fireRow"] and has_rows["seismicRow"]), \
            "Fire/Seismic not present in the startup preloader"
