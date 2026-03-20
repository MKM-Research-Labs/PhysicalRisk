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
