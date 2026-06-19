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

"""Tests for REIT portfolio view: blotter, derivatives, and basis endpoints."""

import json
from datetime import date, timedelta

import pytest

from tests.routes.propertyts._helpers import STORM_ID, SEQ_ID, PROP_ID


def _make_property_prs(swap_id, gauge_id, property_id, notional,
                       spread_bps=150.0):
    """Create a PropertyPRS CDM trade."""
    today = date.today().isoformat()
    end = (date.today() + timedelta(days=365 * 5)).isoformat()
    return {
        'PhysicalSwap': {
            'Header': {
                'SwapID': swap_id,
                'TradeType': 'PropertyPRS',
                'CounterPartyName': 'Thames REIT plc',
                'ValuationDate': today,
                'TradeStatus': 'Committed',
            },
            'LegData': {
                'Notional': notional,
                'Payer': True,
                'Currency': 'GBP',
            },
            'ScheduleData': {
                'StartDate': today,
                'EndDate': end,
                'Tenor': '6M',
            },
            'Pricing': {
                'SpreadBps': spread_bps,
                'RiskyAnnuity': 4.5,
                'TriggerLevel': 'severe',
            },
            'GaugeSet': {
                'GaugeBasket': [{
                    'GaugeID': gauge_id,
                    'GaugeName': f'Gauge {gauge_id}',
                    'Weight': 1.0,
                }]
            },
            'PropertySet': {
                'PropertyID': property_id,
                'PropertyAddress': '10 River Lane',
                'PropertyValue': 400000,
            },
        }
    }


@pytest.fixture
def pts_env_with_prs(tmp_path, monkeypatch):
    """Propertyts environment with PRS trades for derivative testing."""
    from config import config

    pts_dir = tmp_path / 'propertyts'
    pts_dir.mkdir()
    gaugets_dir = tmp_path / 'gaugets'
    gaugets_dir.mkdir()
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    prs_dir = tmp_path / 'prs'  # database resolves prs_trade under input_dir/prs
    prs_dir.mkdir()

    # Property flood file — synthetic gauge first, then real gauge
    prop_data = {
        'property_id': PROP_ID,
        'location': {'lat': 51.5, 'lon': -0.12},
        'elevation_m': 3.0,
        'floor_level_m': 3.2,
        'nearest_gauges': [
            {'gauge_id': 'SYNTH-001', 'distance_m': 200, 'gauge_elevation_m': 3.0},
            {'gauge_id': 'GAUGE-001', 'distance_m': 500, 'gauge_elevation_m': 3.0},
        ],
        'summary': {'storms_flooded': 1, 'max_depth_m': 0.5},
        'flood_events': [{
            'storm_id': SEQ_ID,
            'flooded': True,
            'exceeded_severe': True,
            'flood_depth_m': 0.5,
            'damage_ratio': 0.1,
            'interpolated_wse_m': 5.5,
            'retention_factor': 0.92,
        }],
    }
    (pts_dir / f'{PROP_ID}.json').write_text(json.dumps(prop_data))

    # property.json with location and risk data
    property_data = {'properties': [{
        'PropertyHeader': {
            'Header': {'PropertyID': PROP_ID},
            'Location': {
                'BuildingNumber': '10',
                'StreetName': 'River Lane',
                'Postcode': 'SW1A 1AA',
                'LatitudeDegrees': 51.5,
                'LongitudeDegrees': -0.12,
            },
            'Valuation': {'PropertyValue': 400000},
            'Construction': {'FloorLevelMeters': 3.2},
            'RiskAssessment': {
                'GroundLevelMeters': 6.0,
                'RiverDistanceMeters': 250,
                'EAFloodZone': 'Zone 3',
            },
            'ReferenceGauges': ['GAUGE-001'],
        },
    }]}
    (tmp_path / 'property.json').write_text(json.dumps(property_data))

    # loan.json
    rloan_data = {'loans': [{
        'RLoan': {
            'Header': {'RLoanID': 'MORT-001', 'PropertyID': PROP_ID},
            'CurrentStatus': {
                'OutstandingBalance': 280000,
                'CurrentLTV': 70.0,
                'RemainingTerm': 240,
            },
        }
    }]}
    (tmp_path / 'loan.json').write_text(json.dumps(rloan_data))

    # PRS trade linked to PROP-001
    trade = _make_property_prs('PRS-PROP-001', 'GAUGE-001', PROP_ID, 500000)
    (prs_dir / 'PRS-PROP-001.json').write_text(json.dumps(trade))

    # gaugehc.json — thresholds for synthetic and real gauges
    gaugehc_data = {'hazard_curves': {
        'SYNTH-001': {
            'gauge_id': 'SYNTH-001',
            'gauge_name': 'Synth Near River',
            'flood_alert_m': 4.0,
            'flood_warning_m': 4.5,
            'severe_flood_warning_m': 5.0,
            'elevation_m': 3.0,
            'latitude': 51.5,
            'longitude': -0.12,
        },
        'GAUGE-001': {
            'gauge_id': 'GAUGE-001',
            'gauge_name': 'Test Gauge',
            'flood_alert_m': 4.0,
            'flood_warning_m': 4.5,
            'severe_flood_warning_m': 5.0,
            'elevation_m': 3.0,
            'latitude': 51.5,
            'longitude': -0.1,
        },
    }}
    (tmp_path / 'gaugehc.json').write_text(json.dumps(gaugehc_data))

    # stress_storms/_index.json + individual storm file
    ss_dir = tmp_path / 'stress_storms'
    ss_dir.mkdir()
    (ss_dir / '_index.json').write_text(json.dumps({'storms': [{
        'storm_id': SEQ_ID,
        'name': 'Moderate',
        'intensity_category': 'moderate',
        'trigger_summary': {'gauges_severe': 1},
    }]}))
    # Individual storm file with gauge_responses
    (ss_dir / f'{SEQ_ID}.json').write_text(json.dumps({
        'storm_id': SEQ_ID,
        'name': 'Moderate',
        'intensity_category': 'moderate',
        'duration_hours': 24,
        'gauge_responses': [{
            'gauge_id': 'GAUGE-001',
            'storm_id': SEQ_ID,
            'peak_level_m': 5.8,
            'exceeded_alert': True,
            'exceeded_warning': True,
            'exceeded_severe': True,
        }],
    }))

    # storm_sequences.json
    (tmp_path / 'storm_sequences.json').write_text(json.dumps({
        'num_sequences': 1,
        'sequences': [{'sequence_id': SEQ_ID, 'sequence_type': 'isolated'}],
    }))

    monkeypatch.setattr(config, 'get_input_dir', lambda: tmp_path)
    monkeypatch.setattr(config, 'get_gaugets_dir', lambda: gaugets_dir)
    monkeypatch.setattr(config, 'get_input_path', lambda fname: tmp_path / fname)
    monkeypatch.setattr(config, 'get_reports_dir',
                        lambda subdir=None: (output_dir / subdir) if subdir else output_dir)

    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    return {
        'client': app.test_client(),
        'prs_dir': prs_dir,
        'storm_id': SEQ_ID,
    }


class TestStormBasis:
    """Tests for GET /propertyts/<storm_id>/basis endpoint."""

    def test_basis_returns_gauges(self, pts_env_with_prs):
        client = pts_env_with_prs['client']
        storm_id = pts_env_with_prs['storm_id']
        resp = client.get(f'/api/v1/propertyts/{storm_id}/basis')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'success'
        assert len(data['gauges']) >= 1

    def test_synthetic_gauge_present(self, pts_env_with_prs):
        client = pts_env_with_prs['client']
        storm_id = pts_env_with_prs['storm_id']
        resp = client.get(f'/api/v1/propertyts/{storm_id}/basis')
        data = resp.get_json()

        gauge_ids = [g['gauge_id'] for g in data['gauges']]
        assert 'SYNTH-001' in gauge_ids

    def test_transmission_computed(self, pts_env_with_prs):
        client = pts_env_with_prs['client']
        storm_id = pts_env_with_prs['storm_id']
        resp = client.get(f'/api/v1/propertyts/{storm_id}/basis')
        data = resp.get_json()

        synth = [g for g in data['gauges'] if g['gauge_id'] == 'SYNTH-001'][0]
        assert synth['properties_linked'] == 1
        assert synth['properties_flooded'] == 1
        assert synth['transmission_pct'] == 100.0

    def test_threshold_from_exceeded_severe(self, pts_env_with_prs):
        client = pts_env_with_prs['client']
        storm_id = pts_env_with_prs['storm_id']
        resp = client.get(f'/api/v1/propertyts/{storm_id}/basis')
        data = resp.get_json()

        synth = [g for g in data['gauges'] if g['gauge_id'] == 'SYNTH-001'][0]
        assert synth['threshold'] == 'severe'

    def test_real_gauge_peak_populated(self, pts_env_with_prs):
        client = pts_env_with_prs['client']
        storm_id = pts_env_with_prs['storm_id']
        resp = client.get(f'/api/v1/propertyts/{storm_id}/basis')
        data = resp.get_json()

        synth = [g for g in data['gauges'] if g['gauge_id'] == 'SYNTH-001'][0]
        assert synth['real_gauge_id'] == 'GAUGE-001'
        assert synth['real_gauge_peak_m'] == 5.8

    def test_summary_totals(self, pts_env_with_prs):
        client = pts_env_with_prs['client']
        storm_id = pts_env_with_prs['storm_id']
        resp = client.get(f'/api/v1/propertyts/{storm_id}/basis')
        data = resp.get_json()

        s = data['summary']
        assert s['num_synthetic_gauges'] >= 1
        assert s['total_flooded'] == 1
        assert s['total_properties'] == 1
        assert s['portfolio_transmission_pct'] == 100.0

    def test_avg_retention_populated(self, pts_env_with_prs):
        client = pts_env_with_prs['client']
        storm_id = pts_env_with_prs['storm_id']
        resp = client.get(f'/api/v1/propertyts/{storm_id}/basis')
        data = resp.get_json()

        synth = [g for g in data['gauges'] if g['gauge_id'] == 'SYNTH-001'][0]
        assert synth['avg_retention'] == 0.92
