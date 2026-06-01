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
    prs_dir = output_dir / 'prs'
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


class TestPropertyBlotter:
    """Tests for GET /propertyts/blotter endpoint."""

    def test_blotter_returns_properties(self, pts_env_with_prs):
        client = pts_env_with_prs['client']
        resp = client.get('/api/v1/propertyts/blotter')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'success'
        assert len(data['properties']) == 1

        prop = data['properties'][0]
        assert prop['property_id'] == PROP_ID
        assert prop['property_value'] == 400000
        assert prop['river_distance_km'] == 0.25
        assert prop['elevation_m'] == 6.2  # relative_elevation(6.0, 3.0, 3.2)
        assert prop['ea_flood_zone'] == 'Zone 3'

    def test_blotter_includes_mortgage(self, pts_env_with_prs):
        client = pts_env_with_prs['client']
        resp = client.get('/api/v1/propertyts/blotter')
        data = resp.get_json()
        prop = data['properties'][0]
        assert prop['has_rloan'] is True
        assert prop['outstanding_balance'] == 280000
        assert prop['current_ltv'] == 70.0

    def test_blotter_summary(self, pts_env_with_prs):
        client = pts_env_with_prs['client']
        resp = client.get('/api/v1/propertyts/blotter')
        data = resp.get_json()
        s = data['summary']
        assert s['num_properties'] == 1
        assert s['total_property_value'] == 400000
        assert s['total_mortgage_exposure'] == 280000


class TestDerivativesInPortfolioImpact:
    """Tests for derivatives section in portfolio-impact."""

    def test_derivatives_present(self, pts_env_with_prs):
        client = pts_env_with_prs['client']
        storm_id = pts_env_with_prs['storm_id']
        resp = client.get(f'/api/v1/propertyts/{storm_id}/portfolio-impact')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'derivatives' in data

    def test_prs_payout_on_flooded_property(self, pts_env_with_prs):
        client = pts_env_with_prs['client']
        storm_id = pts_env_with_prs['storm_id']
        resp = client.get(f'/api/v1/propertyts/{storm_id}/portfolio-impact')
        data = resp.get_json()

        # Property was flooded, PRS should trigger
        prop = data['properties'][0]
        assert prop['prs_payout'] == 500000  # full notional
        assert len(prop['prs_trades']) == 1
        assert prop['prs_trades'][0]['swap_id'] == 'PRS-PROP-001'

    def test_net_pnl_computed(self, pts_env_with_prs):
        client = pts_env_with_prs['client']
        storm_id = pts_env_with_prs['storm_id']
        resp = client.get(f'/api/v1/propertyts/{storm_id}/portfolio-impact')
        data = resp.get_json()

        prop = data['properties'][0]
        # net_pnl = prs_payout - damage_amount
        expected_net = 500000 - prop['damage_amount']
        assert prop['net_pnl'] == expected_net

    def test_derivatives_summary(self, pts_env_with_prs):
        client = pts_env_with_prs['client']
        storm_id = pts_env_with_prs['storm_id']
        resp = client.get(f'/api/v1/propertyts/{storm_id}/portfolio-impact')
        data = resp.get_json()

        d = data['derivatives']
        assert d['total_prs_payout'] == 500000
        assert d['total_prs_notional'] == 500000
        assert d['num_trades_triggered'] == 1

    def test_no_prs_trades_returns_zero_payout(self, pts_env_with_prs):
        """When no PRS files exist, derivatives section shows zeros."""
        # Remove PRS files
        prs_dir = pts_env_with_prs['prs_dir']
        for f in prs_dir.glob('*.json'):
            f.unlink()

        client = pts_env_with_prs['client']
        storm_id = pts_env_with_prs['storm_id']
        resp = client.get(f'/api/v1/propertyts/{storm_id}/portfolio-impact')
        data = resp.get_json()

        prop = data['properties'][0]
        assert prop['prs_payout'] == 0
        assert prop['prs_trades'] == []
        assert prop['net_pnl'] == -prop['damage_amount']

        d = data['derivatives']
        assert d['total_prs_payout'] == 0
        assert d['num_trades_triggered'] == 0


