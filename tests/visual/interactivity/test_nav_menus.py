# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Tests for navigation dropdown menus (top-left gauge/property selectors).

Validates:
- JS generation includes correct data access paths for preloader globals
- Gauge field names match API contract (gaugeId, not gauge_id)
- Property field names match API contract (property_id)
- Synthetic gauge filtering uses correct field name
- Menu items reuse context menu definitions without duplication
- Data lineage: loader → API → preloader → nav menu JS
"""

import json

import pytest


class TestNavMenuGaugeDataContract:
    """Gauge data contract: loader → API response → nav menu JS."""

    def test_gauge_loader_returns_gaugeId_field(self):
        """GaugeLoader.get_entity_summary must produce 'gaugeId' key."""
        from loaders.gauge_loader import GaugeLoader
        from config import config

        gauge_path = config.get_input_dir()
        if not gauge_path.exists():
            pytest.skip("gauge.json not found")
        loader = GaugeLoader(gauge_path)
        summaries = loader.list_all()
        assert len(summaries) > 0, "No gauges loaded"

        sample = summaries[0]
        assert 'gaugeId' in sample, (
            f"Gauge summary missing 'gaugeId' key. "
            f"Available keys: {list(sample.keys())}"
        )
        assert 'name' in sample, (
            f"Gauge summary missing 'name' key. "
            f"Available keys: {list(sample.keys())}"
        )

    def test_gauge_loader_has_synth_gauges(self):
        """Loader should return both real and synthetic gauges."""
        from loaders.gauge_loader import GaugeLoader
        from config import config

        gauge_path = config.get_input_dir()
        if not gauge_path.exists():
            pytest.skip("gauge.json not found")
        loader = GaugeLoader(gauge_path)
        summaries = loader.list_all()

        synth = [g for g in summaries if (g.get('gaugeId') or '').startswith('SYNTH-')]
        real = [g for g in summaries if not (g.get('gaugeId') or '').startswith('SYNTH-')]
        assert len(synth) > 0, "No synthetic gauges found"
        assert len(real) > 0, "No real gauges found"

    def test_nav_js_accesses_gaugeId_not_gauge_id(self):
        """Nav menu JS must use 'gaugeId' (API contract), not 'gauge_id'."""
        from visual.interactivity.context_menus import ContextMenuHandler

        handler = ContextMenuHandler()
        js = handler._build_nav_menus_js()

        # Must filter synthetics using gaugeId
        assert 'g.gaugeId' in js or "g['gaugeId']" in js or 'gaugeId' in js, (
            "Nav JS does not reference 'gaugeId' — gauge items won't load"
        )
        # Must NOT use gauge_id (wrong field name from different context)
        assert 'g.gauge_id' not in js, (
            "Nav JS uses 'g.gauge_id' but API returns 'gaugeId'"
        )

    def test_nav_js_uses_gauge_name_field(self):
        """Nav menu JS must use 'name' for gauge display name."""
        from visual.interactivity.context_menus import ContextMenuHandler

        handler = ContextMenuHandler()
        js = handler._build_nav_menus_js()
        assert '.name' in js or "['name']" in js, (
            "Nav JS doesn't reference gauge 'name' field"
        )


class TestNavMenuPropertyDataContract:
    """Property data contract: summary API → preloader → nav menu JS."""

    def test_property_summary_has_property_id(self):
        """Portfolio flood summary properties must have 'property_id'."""
        from config import config
        pts_dir = config.get_input_path('propertyts')
        summary_path = pts_dir / 'portfolio_flood_summary.json'
        if not summary_path.exists():
            pytest.skip("portfolio_flood_summary.json not found")

        with open(summary_path) as f:
            data = json.load(f)

        properties = data.get('properties', [])
        assert len(properties) > 0, "No properties in summary"
        assert 'property_id' in properties[0], (
            f"Property missing 'property_id'. Keys: {list(properties[0].keys())}"
        )

    def test_nav_js_accesses_correct_preloader_path(self):
        """Nav JS must access _prePropertyTS.data.properties for property list."""
        from visual.interactivity.context_menus import ContextMenuHandler

        handler = ContextMenuHandler()
        js = handler._build_nav_menus_js()

        # The preloader stores raw API response: {status, data: {summary, properties}}
        assert '_prePropertyTS' in js, "Nav JS doesn't reference _prePropertyTS"
        assert '.properties' in js, "Nav JS doesn't access .properties array"

    def test_nav_js_uses_property_id_field(self):
        """Nav menu JS must use 'property_id' for property IDs."""
        from visual.interactivity.context_menus import ContextMenuHandler

        handler = ContextMenuHandler()
        js = handler._build_nav_menus_js()
        assert 'property_id' in js, (
            "Nav JS doesn't reference 'property_id'"
        )


class TestNavMenuActionLineage:
    """Action functions in nav menu must match context menu definitions."""

    def test_gauge_nav_actions_match_context_menu(self):
        """Gauge nav menu must use the same actions as the right-click menu."""
        from visual.interactivity.context_menus import (
            ContextMenuHandler, DEFAULT_GAUGE_MENU)

        handler = ContextMenuHandler()
        js = handler._build_nav_menus_js()

        for item in DEFAULT_GAUGE_MENU:
            assert item['action'] in js, (
                f"Gauge action '{item['action']}' missing from nav menu JS"
            )

    def test_property_nav_actions_match_context_menu(self):
        """Property nav menu must use the same actions as the right-click menu."""
        from visual.interactivity.context_menus import (
            ContextMenuHandler, DEFAULT_PROPERTY_MENU)

        handler = ContextMenuHandler()
        js = handler._build_nav_menus_js()

        for item in DEFAULT_PROPERTY_MENU:
            assert item['action'] in js, (
                f"Property action '{item['action']}' missing from nav menu JS"
            )

    def test_nav_menu_items_serialized_from_python(self):
        """Menu items must be serialized from Python lists, not hardcoded in JS."""
        from visual.interactivity.context_menus import (
            ContextMenuHandler, DEFAULT_GAUGE_MENU, DEFAULT_PROPERTY_MENU)

        handler = ContextMenuHandler()
        js = handler._build_nav_menus_js()

        # The JS should contain the JSON-serialized menu items
        gauge_json = json.dumps(DEFAULT_GAUGE_MENU)
        prop_json = json.dumps(DEFAULT_PROPERTY_MENU)
        assert gauge_json in js, "Gauge menu items not serialized from Python list"
        assert prop_json in js, "Property menu items not serialized from Python list"


class TestNavMenuSyntheticFiltering:
    """Synthetic gauges must be filtered from the nav menu."""

    def test_synthetic_filter_uses_correct_prefix(self):
        """Filter must check for 'SYNTH' prefix on gaugeId."""
        from visual.interactivity.context_menus import ContextMenuHandler

        handler = ContextMenuHandler()
        js = handler._build_nav_menus_js()
        assert 'SYNTH' in js, "Synthetic gauge filter not present"
