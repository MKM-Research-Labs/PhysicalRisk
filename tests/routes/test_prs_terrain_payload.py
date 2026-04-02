"""Tests for terrain fields in PRS commit payload and CDM record."""

import pytest

from visual.interactivity.property import phc_prs
from routes.prs.blueprint import prs_bp


class TestCommitPayloadJS:
    """Verify terrain fields are included in the JS commit payload."""

    @pytest.fixture
    def js(self):
        return phc_prs.get_js()

    def test_ea_flood_zone_in_payload(self, js):
        assert 'ea_flood_zone: result.selectedZone' in js

    def test_ea_flood_zone_actual_in_payload(self, js):
        assert 'ea_flood_zone_actual: result.actualZone' in js

    def test_terrain_delta_bps_in_payload(self, js):
        assert 'terrain_delta_bps: result.terrainDelta' in js

    def test_backward_compat_fallback(self, js):
        """Terrain fields should use || fallback for missing values."""
        assert "result.selectedZone || ''" in js
        assert "result.actualZone || ''" in js
        assert "result.terrainDelta || 0" in js


class TestCDMRecordTerrainFields:
    """Verify CDM record construction includes terrain fields in the route."""

    def test_blueprint_source_has_ea_flood_zone(self):
        """The blueprint source should include EAFloodZone in Pricing section."""
        import inspect
        source = inspect.getsource(prs_bp.deferred_functions[0])
        # The commit function is the first deferred function
        # Check the route module source instead
        from routes.prs import blueprint
        source = inspect.getsource(blueprint)
        assert '"EAFloodZone"' in source

    def test_blueprint_source_has_ea_flood_zone_actual(self):
        from routes.prs import blueprint
        import inspect
        source = inspect.getsource(blueprint)
        assert '"EAFloodZoneActual"' in source

    def test_blueprint_source_has_terrain_delta_bps(self):
        from routes.prs import blueprint
        import inspect
        source = inspect.getsource(blueprint)
        assert '"TerrainDeltaBps"' in source

    def test_terrain_fields_use_data_get(self):
        """Terrain fields should use data.get() with defaults for backward compat."""
        from routes.prs import blueprint
        import inspect
        source = inspect.getsource(blueprint)
        assert 'data.get("ea_flood_zone", "")' in source
        assert 'data.get("ea_flood_zone_actual", "")' in source
        assert 'data.get("terrain_delta_bps", 0)' in source
