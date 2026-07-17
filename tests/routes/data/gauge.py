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

"""Tests for gauge data loading, ID consistency, and route endpoints."""

import json

import pytest


class TestGaugeIDConsistency:
    """Test that gauge IDs are consistent across all data files."""

    def test_gaugets_ids_match_gauge_portfolio(self, fully_populated_data_dir):
        """Gauge IDs in gaugets/ files must exist in gauge.json."""
        with open(fully_populated_data_dir / 'gauge.json', 'r') as f:
            gauges = json.load(f)

        portfolio_ids = set()
        for g in gauges.get('floodGauges', gauges.get('flood_gauges', [])):
            gid = g.get('FloodGauge', {}).get('Header', {}).get('GaugeID')
            if gid:
                portfolio_ids.add(gid)

        gaugets_dir = fully_populated_data_dir / 'gaugets'
        if not gaugets_dir.exists():
            pytest.skip("No gaugets directory")

        gaugets_ids = {gf.stem for gf in gaugets_dir.glob('GAUGE-*.json')}

        orphaned = gaugets_ids - portfolio_ids
        assert not orphaned, (
            f"Gauge IDs in gaugets/ not found in gauge.json: {orphaned}"
        )

    def test_gaugehc_ids_match_gauge_portfolio(self, fully_populated_data_dir):
        """Gauge IDs in gaugehc.json must exist in gauge.json."""
        with open(fully_populated_data_dir / 'gauge.json', 'r') as f:
            gauges = json.load(f)

        portfolio_ids = set()
        for g in gauges.get('floodGauges', gauges.get('flood_gauges', [])):
            gid = g.get('FloodGauge', {}).get('Header', {}).get('GaugeID')
            if gid:
                portfolio_ids.add(gid)

        hc_path = fully_populated_data_dir / 'gaugehc.json'
        if not hc_path.exists():
            pytest.skip("No gaugehc.json")

        with open(hc_path, 'r') as f:
            hc_data = json.load(f)

        hc_ids = set(hc_data.get('hazard_curves', {}).keys())

        orphaned = hc_ids - portfolio_ids
        assert not orphaned, (
            f"Gauge IDs in gaugehc.json not found in gauge.json: {orphaned}"
        )

    def test_gaugets_internal_id_matches_filename(self, fully_populated_data_dir):
        """Each gaugets file's internal gauge_id must match its filename."""
        gaugets_dir = fully_populated_data_dir / 'gaugets'
        if not gaugets_dir.exists():
            pytest.skip("No gaugets directory")

        for gf in gaugets_dir.glob('GAUGE-*.json'):
            with open(gf, 'r') as f:
                data = json.load(f)
            internal_id = data.get('gauge_id')
            if internal_id:
                assert internal_id == gf.stem, (
                    f"File {gf.name} has internal gauge_id={internal_id}, "
                    f"expected {gf.stem}"
                )


class TestDataFormatValidation:
    """Test that data files have correct structure and required fields."""

    def test_propertyts_file_structure(self, fully_populated_data_dir):
        """PropertyTS files must have required fields."""
        pts_dir = fully_populated_data_dir / 'propertyts'
        if not pts_dir.exists():
            pytest.skip("No propertyts directory")

        required_keys = {'property_id', 'location', 'elevation_m', 'flood_events'}
        location_keys = {'lat', 'lon'}

        for pf in pts_dir.glob('PROP-*.json'):
            with open(pf, 'r') as f:
                data = json.load(f)

            missing = required_keys - set(data.keys())
            assert not missing, f"{pf.name} missing required keys: {missing}"

            loc = data.get('location', {})
            missing_loc = location_keys - set(loc.keys())
            assert not missing_loc, f"{pf.name} location missing: {missing_loc}"

            for event in data.get('flood_events', []):
                assert 'storm_id' in event, f"{pf.name} flood event missing storm_id"
                assert 'flood_depth_m' in event, f"{pf.name} flood event missing flood_depth_m"
                assert 'damage_ratio' in event, f"{pf.name} flood event missing damage_ratio"

    def test_propertyhc_file_structure(self, fully_populated_data_dir):
        """PropertyHC file must have required structure."""
        hc_path = fully_populated_data_dir / 'propertyhc.json'
        if not hc_path.exists():
            pytest.skip("No propertyhc.json")

        with open(hc_path, 'r') as f:
            data = json.load(f)

        assert 'property_hazard_curves' in data, "Missing property_hazard_curves key"
        assert 'metadata' in data, "Missing metadata key"

        for prop_id, curve in data['property_hazard_curves'].items():
            assert 'flood_count' in curve, f"{prop_id} missing flood_count"
            assert curve['flood_count'] >= 3, (
                f"{prop_id} has only {curve['flood_count']} floods, need >= 3 for GEV"
            )

    def test_gaugehc_file_structure(self, fully_populated_data_dir):
        """GaugeHC file must have required structure."""
        hc_path = fully_populated_data_dir / 'gaugehc.json'
        if not hc_path.exists():
            pytest.skip("No gaugehc.json")

        with open(hc_path, 'r') as f:
            data = json.load(f)

        assert 'hazard_curves' in data, "Missing hazard_curves key"

        required_fields = {'gev_location', 'gev_scale', 'gev_shape'}
        for gauge_id, curve in data['hazard_curves'].items():
            missing = required_fields - set(curve.keys())
            assert not missing, f"Gauge {gauge_id} missing GEV params: {missing}"

    def test_gaugets_file_structure(self, fully_populated_data_dir):
        """Gaugets files must have required structure."""
        gaugets_dir = fully_populated_data_dir / 'gaugets'
        if not gaugets_dir.exists():
            pytest.skip("No gaugets directory")

        for gf in gaugets_dir.glob('GAUGE-*.json'):
            with open(gf, 'r') as f:
                data = json.load(f)

            assert 'flood_simulation' in data, f"{gf.name} missing flood_simulation"
            sim = data['flood_simulation']
            assert 'readings' in sim, f"{gf.name} flood_simulation missing readings"
            assert isinstance(sim['readings'], list), f"{gf.name} readings must be list"


class TestGaugeHazardRoutes:
    """Test gauge hazard curve API endpoints."""

    def test_gauge_hazard_existing(self, full_client):
        """GET /api/v1/gauges/<id>/hazard returns hazard data for known gauge."""
        response = full_client.get('/api/v1/gauges/GAUGE-001/hazard')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['gauge_id'] == 'GAUGE-001'
        assert 'gev_parameters' in data
        assert 'curve_points' in data
        assert 'return_period_levels' in data
        assert 'term_structures' in data
        assert 'annual_flood_probs' in data

    def test_gauge_hazard_gev_params(self, full_client):
        """GEV parameters should be present and numeric."""
        response = full_client.get('/api/v1/gauges/GAUGE-001/hazard')
        data = json.loads(response.data)

        gev = data['gev_parameters']
        assert gev['location'] is not None
        assert gev['scale'] is not None
        assert gev['shape'] is not None
        assert isinstance(gev['location'], (int, float))
        assert isinstance(gev['scale'], (int, float))

    def test_gauge_hazard_not_found(self, full_client):
        """GET /api/v1/gauges/<id>/hazard returns 404 for gauge without hazard data."""
        response = full_client.get('/api/v1/gauges/GAUGE-003/hazard')

        assert response.status_code == 404

    def test_gauge_hazard_nonexistent_gauge(self, full_client):
        """GET /api/v1/gauges/<id>/hazard returns 404 for nonexistent gauge."""
        response = full_client.get('/api/v1/gauges/NONEXISTENT/hazard')

        assert response.status_code == 404

    def test_gauge_storms_existing(self, full_client):
        """GET /api/v1/gauges/<id>/storms returns storm data for known gauge."""
        response = full_client.get('/api/v1/gauges/GAUGE-001/storms')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'flood_simulation' in data
        assert 'storm_responses' in data
