# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for flood_zone in propertyhc output and terrain grid in metadata."""

import json

import pytest

from config.models import EA_FLOOD_ZONE_RATES
from port.src.property.propertyhc import PropertyHazardCurveGenerator


class TestFloodZoneInOutput:
    """Verify flood_zone is propagated from property timeseries to propertyhc output."""

    def test_flood_zone_present_in_result(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        stats = gen.generate()
        hc_path = output_dir / 'propertyhc.json'
        with open(hc_path) as f:
            data = json.load(f)
        for prop_id, pc in data['property_hazard_curves'].items():
            assert 'flood_zone' in pc, f"{prop_id} missing flood_zone"

    def test_flood_zone_values_correct(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()
        hc_path = output_dir / 'propertyhc.json'
        with open(hc_path) as f:
            data = json.load(f)
        curves = data['property_hazard_curves']
        assert curves['PROP-001']['flood_zone'] == 'Zone 2'
        assert curves['PROP-002']['flood_zone'] == 'Zone 1'
        assert curves['PROP-003']['flood_zone'] == 'Zone 3a'

    def test_flood_zone_default_when_missing(self, output_dir):
        """Property without flood_zone in source data should default to Zone 1."""
        # Create a property without flood_zone
        pts_dir = output_dir / 'propertyts'
        prop_no_zone = {
            "property_id": "PROP-NOZONE",
            "location": {"lat": 51.5, "lon": -0.1},
            "elevation_m": 5.0,
            "floor_level_m": 0.2,
            "nearest_gauges": [
                {"gauge_id": "GAUGE-001", "distance_m": 500, "gauge_elevation_m": 3.5},
            ],
            "flood_events": [
                {"storm_id": "S1", "flood_depth_m": 0.3, "flooded": True, "damage_ratio": 0.1},
                {"storm_id": "S2", "flood_depth_m": 0.5, "flooded": True, "damage_ratio": 0.2},
                {"storm_id": "S3", "flood_depth_m": 0.7, "flooded": True, "damage_ratio": 0.3},
            ],
            "summary": {"property_id": "PROP-NOZONE", "floods_at_nearest_gauge": 10, "floods_at_property": 3},
        }
        with open(pts_dir / "PROP-NOZONE.json", "w") as f:
            json.dump(prop_no_zone, f)

        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()
        hc_path = output_dir / 'propertyhc.json'
        with open(hc_path) as f:
            data = json.load(f)
        assert data['property_hazard_curves']['PROP-NOZONE']['flood_zone'] == 'Zone 1'

    def test_flood_zone_is_valid_zone_name(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()
        hc_path = output_dir / 'propertyhc.json'
        with open(hc_path) as f:
            data = json.load(f)
        valid_zones = set(EA_FLOOD_ZONE_RATES.keys())
        for prop_id, pc in data['property_hazard_curves'].items():
            assert pc['flood_zone'] in valid_zones, (
                f"{prop_id} has invalid zone: {pc['flood_zone']}"
            )


class TestTerrainGridInMetadata:
    """Verify terrain grid is embedded in propertyhc.json metadata."""

    def test_terrain_grid_present(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()
        hc_path = output_dir / 'propertyhc.json'
        with open(hc_path) as f:
            data = json.load(f)
        assert 'terrain_grid' in data['metadata']

    def test_terrain_grid_has_distances(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()
        hc_path = output_dir / 'propertyhc.json'
        with open(hc_path) as f:
            grid = json.load(f)['metadata']['terrain_grid']
        assert 'distances' in grid
        assert len(grid['distances']) == 21

    def test_terrain_grid_has_elevations(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()
        hc_path = output_dir / 'propertyhc.json'
        with open(hc_path) as f:
            grid = json.load(f)['metadata']['terrain_grid']
        assert 'elevations' in grid
        assert len(grid['elevations']) == 11

    def test_terrain_grid_has_all_zones(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()
        hc_path = output_dir / 'propertyhc.json'
        with open(hc_path) as f:
            grid = json.load(f)['metadata']['terrain_grid']
        assert set(grid['zones'].keys()) == set(EA_FLOOD_ZONE_RATES.keys())

    def test_terrain_grid_zone_has_grid_array(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()
        hc_path = output_dir / 'propertyhc.json'
        with open(hc_path) as f:
            grid = json.load(f)['metadata']['terrain_grid']
        for zone_name, zone_data in grid['zones'].items():
            assert 'grid' in zone_data, f"{zone_name} missing grid"
            assert 'rate' in zone_data, f"{zone_name} missing rate"
            assert len(zone_data['grid']) == 21, f"{zone_name} wrong distance dim"
            for row in zone_data['grid']:
                assert len(row) == 11, f"{zone_name} wrong elevation dim"
