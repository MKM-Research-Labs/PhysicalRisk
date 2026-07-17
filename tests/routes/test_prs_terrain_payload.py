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
