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

"""Tests for property data loading, ID consistency, and route endpoints."""

import json

import pytest


class TestPropertyIDConsistency:
    """Test that property IDs are consistent across all data files."""

    def test_propertyts_ids_match_property_portfolio(self, fully_populated_data_dir):
        """Property IDs in propertyts/ files must exist in property.json."""
        with open(fully_populated_data_dir / 'property.json', 'r') as f:
            portfolio = json.load(f)

        portfolio_ids = set()
        for prop in portfolio.get('properties', []):
            pid = prop.get('PropertyHeader', {}).get('Header', {}).get('PropertyID')
            if pid:
                portfolio_ids.add(pid)

        pts_dir = fully_populated_data_dir / 'propertyts'
        if not pts_dir.exists():
            pytest.skip("No propertyts directory")

        pts_ids = set()
        for pf in pts_dir.glob('PROP-*.json'):
            with open(pf, 'r') as f:
                data = json.load(f)
            pts_ids.add(data.get('property_id', pf.stem))

        orphaned = pts_ids - portfolio_ids
        assert not orphaned, (
            f"Property IDs in propertyts/ not found in property.json: {orphaned}. "
            f"This usually means propertyts was generated from a different property.json. "
            f"Regenerate with: python app.py port --propertyts"
        )

    def test_propertyhc_ids_match_property_portfolio(self, fully_populated_data_dir):
        """Property IDs in propertyhc.json must exist in property.json."""
        with open(fully_populated_data_dir / 'property.json', 'r') as f:
            portfolio = json.load(f)

        portfolio_ids = set()
        for prop in portfolio.get('properties', []):
            pid = prop.get('PropertyHeader', {}).get('Header', {}).get('PropertyID')
            if pid:
                portfolio_ids.add(pid)

        hc_path = fully_populated_data_dir / 'propertyhc.json'
        if not hc_path.exists():
            pytest.skip("No propertyhc.json")

        with open(hc_path, 'r') as f:
            hc_data = json.load(f)

        hc_ids = set(hc_data.get('property_hazard_curves', {}).keys())

        orphaned = hc_ids - portfolio_ids
        assert not orphaned, (
            f"Property IDs in propertyhc.json not found in property.json: {orphaned}. "
            f"Regenerate with: python app.py port --propertyhc"
        )

    def test_propertyhc_ids_subset_of_propertyts(self, fully_populated_data_dir):
        """Properties with hazard curves should also have timeseries data."""
        hc_path = fully_populated_data_dir / 'propertyhc.json'
        pts_dir = fully_populated_data_dir / 'propertyts'

        if not hc_path.exists() or not pts_dir.exists():
            pytest.skip("Missing propertyhc.json or propertyts/")

        with open(hc_path, 'r') as f:
            hc_data = json.load(f)
        hc_ids = set(hc_data.get('property_hazard_curves', {}).keys())

        pts_ids = {pf.stem for pf in pts_dir.glob('PROP-*.json')}

        missing = hc_ids - pts_ids
        assert not missing, (
            f"Properties with hazard curves but no timeseries file: {missing}"
        )


class TestPropertyTSRoutes:
    """Test property flood timeseries API endpoints."""

    def test_propertyts_summary(self, full_client):
        """GET /api/v1/propertyts/summary returns portfolio flood summary."""
        response = full_client.get('/api/v1/propertyts/summary')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'data' in data

    def test_property_floods_existing(self, full_client):
        """GET /api/v1/properties/<id>/floods returns flood events for known property."""
        response = full_client.get('/api/v1/properties/PROP-001/floods')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'data' in data
        assert len(data['data']['flood_events']) == 4

    def test_property_floods_not_found(self, full_client):
        """GET /api/v1/properties/<id>/floods returns 404 for unknown property."""
        response = full_client.get('/api/v1/properties/NONEXISTENT/floods')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'

    def test_property_storms_existing(self, full_client):
        """GET /api/v1/properties/<id>/storms returns storm analysis data."""
        response = full_client.get('/api/v1/properties/PROP-001/storms')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['property_id'] == 'PROP-001'
        assert 'flood_events' in data
        assert 'nearest_gauges' in data
        assert len(data['flood_events']) == 4

    def test_property_storms_not_found(self, full_client):
        """GET /api/v1/properties/<id>/storms returns 404 for unknown property."""
        response = full_client.get('/api/v1/properties/NONEXISTENT/storms')

        assert response.status_code == 404

    def test_property_storms_zero_floods(self, full_client):
        """Property with zero flood events should return empty array, not error."""
        response = full_client.get('/api/v1/properties/PROP-003/storms')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['property_id'] == 'PROP-003'
        assert 'flood_events' in data
        assert len(data['flood_events']) == 0
        assert data['summary']['total_floods'] == 0

    def test_property_floods_few_events(self, full_client):
        """Property with few flood events should still return data from propertyts."""
        response = full_client.get('/api/v1/properties/PROP-002/floods')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert len(data['data']['flood_events']) == 1

    def test_list_flood_storms(self, full_client):
        """GET /api/v1/propertyts/storms returns ALL storms from storm_sequences.json."""
        response = full_client.get('/api/v1/propertyts/storms')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'storms' in data

        # Must return ALL 8 storms (4 flooding + 4 non-flooding)
        assert data['count'] == 8, (
            f"Expected all 8 storms from storm_sequences.json, got {data['count']}. "
            "The endpoint must return every storm, not just flooding ones."
        )

        # Verify storm structure includes metadata fields
        storm = data['storms'][0]
        assert 'storm_id' in storm
        assert 'properties_flooded' in storm
        assert 'max_depth_m' in storm
        assert 'name' in storm
        assert 'intensity_category' in storm
        assert 'effective_precipitation_mm' in storm
        assert 'gauges_severe' in storm

    def test_list_flood_storms_includes_non_flooding(self, full_client):
        """Non-flooding storms must appear in the list with properties_flooded=0."""
        response = full_client.get('/api/v1/propertyts/storms')
        data = json.loads(response.data)

        storm_map = {s['storm_id']: s for s in data['storms']}

        # STORM-005 to STORM-008 have no propertyts flood events
        for sid in ['STORM-005', 'STORM-006', 'STORM-007', 'STORM-008']:
            assert sid in storm_map, f"{sid} missing from storm list"
            assert storm_map[sid]['properties_flooded'] == 0

        # STORM-001 and STORM-002 do have flooding
        assert storm_map['STORM-001']['properties_flooded'] > 0
        assert storm_map['STORM-002']['properties_flooded'] > 0


class TestPropertyHCRoutes:
    """Test property hazard curve API endpoints."""

    def test_propertyhc_summary(self, full_client):
        """GET /api/v1/propertyhc/summary returns portfolio hazard summary."""
        response = full_client.get('/api/v1/propertyhc/summary')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'data' in data
        assert 'distribution' in data['data']
        assert data['data']['distribution']['num_properties'] >= 1

    def test_property_hazard_existing(self, full_client):
        """GET /api/v1/properties/<id>/hazard returns hazard data for property with curves."""
        response = full_client.get('/api/v1/properties/PROP-001/hazard')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'data' in data
        assert data['data']['flood_count'] >= 3

    def test_property_hazard_not_in_curves(self, full_client):
        """GET /api/v1/properties/<id>/hazard returns 404 for property without curves."""
        # PROP-002 has < 3 floods, so no hazard curve
        response = full_client.get('/api/v1/properties/PROP-002/hazard')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert '< 3 flood events' in data['message'] or 'not found' in data['message']

    def test_property_hazard_nonexistent(self, full_client):
        """GET /api/v1/properties/<id>/hazard returns 404 for unknown property."""
        response = full_client.get('/api/v1/properties/NONEXISTENT/hazard')

        assert response.status_code == 404

    def test_propertyhc_basis(self, full_client):
        """GET /api/v1/propertyhc/basis returns basis table."""
        response = full_client.get('/api/v1/propertyhc/basis')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'basis_table' in data
        assert data['count'] >= 1

        entry = data['basis_table'][0]
        assert 'property_id' in entry
        assert 'avg_basis_bps' in entry
        assert 'nearest_gauges' in entry


class TestMissingDataHandling:
    """Test that endpoints handle missing data files gracefully."""

    def test_propertyhc_summary_no_file(self, client):
        """PropertyHC summary returns 404 with helpful message when file missing."""
        response = client.get('/api/v1/propertyhc/summary')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'not yet generated' in data['message'].lower() or 'not' in data['message'].lower()

    def test_propertyts_summary_no_dir(self, client):
        """PropertyTS summary returns 404 when directory missing."""
        response = client.get('/api/v1/propertyts/summary')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'

    def test_property_hazard_no_file(self, client):
        """Property hazard returns 404 when propertyhc.json missing."""
        response = client.get('/api/v1/properties/PROP-001/hazard')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
