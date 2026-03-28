# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage expansion tests for stress/scenario.py — storms not found,
no trades, hydrograph padding, model_auc, threshold classification."""

import json
from unittest.mock import patch, MagicMock

import pytest

from .conftest import STORM_SEVERE, STORM_WARNING


class TestStressStormsNotFound:
    """stress_storms.json not found returns 404."""

    def test_stress_run_no_storms_file(self, trading_client, trading_env):
        """When stress_storms.json is absent, returns 404."""
        import routes.trading.stress._helpers as stress_helpers
        stress_helpers._stress_storms_cache = None
        stress_helpers._stress_storms_mtime = None
        resp = trading_client.post('/api/v1/trading/stress/run',
                                    json={'gauge_id': 'GAUGE-001',
                                          'storm_id': 'STORM-any'})
        assert resp.status_code == 404
        data = json.loads(resp.data)
        assert 'not found' in data.get('message', '').lower()


class TestNoOpenTradesAtGauge:
    """No open trades at gauge returns 404."""

    def test_gauge_with_no_trades_returns_404(self, stress_client, stress_env):
        """Gauge that exists in storm data but has no trades returns 404."""
        storms = {
            'storms': [{
                'storm_id': 'STORM-notrades',
                'name': 'No Trades Storm',
                'intensity_category': 'moderate',
                'duration_hours': 24,
                'peak_position': 0.4,
                'trigger_summary': {'max_trigger': 'warning'},
                'gauge_responses': [{
                    'gauge_id': 'GAUGE-NO-TRADES',
                    'base_level_m': 3.0,
                    'peak_level_m': 5.2,
                    'level_change_m': 2.2,
                }],
            }],
        }
        ss_dir = stress_env['input_dir'] / 'stress_storms'
        ss_dir.mkdir(exist_ok=True)
        storm = storms['storms'][0]
        (ss_dir / f"{storm['storm_id']}.json").write_text(json.dumps(storm))
        gauge_ids_alert = [
            r['gauge_id'] for r in storm.get('gauge_responses', [])
            if r.get('exceeded_alert')
        ]
        entry = {k: v for k, v in storm.items() if k != 'gauge_responses'}
        entry['gauge_ids_alert'] = gauge_ids_alert
        (ss_dir / '_index.json').write_text(json.dumps({
            'total_storms': 1, 'storms': [entry],
        }))
        import routes.trading.stress._helpers as stress_helpers
        stress_helpers._stress_index_cache = None

        resp = stress_client.post('/api/v1/trading/stress/run',
                                   json={'gauge_id': 'GAUGE-NO-TRADES',
                                         'storm_id': 'STORM-notrades'})
        assert resp.status_code == 404
        data = json.loads(resp.data)
        assert 'No open trades' in data.get('message', '')


class TestHydrographPadding:
    """Hydrograph padding and exception handling."""

    def test_short_gaugets_padded_to_storm_hours(self, stress_client, stress_env):
        """When gaugets has fewer than STORM_HOURS readings, pads with last value."""
        gaugets_dir = stress_env['gaugets_dir']
        readings = [{'timestamp': f'2024-01-01T{h:02d}:00:00',
                     'waterLevel': 3.0 + h * 0.3}
                    for h in range(10)]
        (gaugets_dir / 'GAUGE-001.json').write_text(json.dumps({
            'gauge_id': 'GAUGE-001',
            'flood_simulation': {'readings': readings},
        }))

        resp = stress_client.post('/api/v1/trading/stress/run',
                                   json={'gauge_id': 'GAUGE-001',
                                         'storm_id': STORM_SEVERE})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert len(data['hourly']) == 168

    def test_gaugets_bad_json_returns_404(self, stress_client, stress_env):
        """When gaugets JSON is corrupt, route returns 404."""
        gaugets_dir = stress_env['gaugets_dir']
        (gaugets_dir / 'GAUGE-001.json').write_text('NOT VALID JSON!!!')

        resp = stress_client.post('/api/v1/trading/stress/run',
                                   json={'gauge_id': 'GAUGE-001',
                                         'storm_id': STORM_SEVERE})
        assert resp.status_code == 404
        data = json.loads(resp.data)
        assert data['status'] == 'error'
        assert 'gaugets' in data['message'].lower()


class TestModelAucNone:
    """model_auc is always None now (predictor removed)."""

    def test_model_auc_is_none(self, stress_client, stress_env):
        """model_auc should be None since predictor is removed."""
        resp = stress_client.post('/api/v1/trading/stress/run',
                                   json={'gauge_id': 'GAUGE-001',
                                         'storm_id': STORM_SEVERE})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['model_auc'] is None


class TestPFloodPolyUsed:
    """Stress scenario now uses p_flood_poly for P(flood) computation."""

    def test_pflood_values_in_range(self, stress_client, stress_env):
        """All hourly P(flood) values should be in [0, 1]."""
        resp = stress_client.post('/api/v1/trading/stress/run',
                                   json={'gauge_id': 'GAUGE-001',
                                         'storm_id': STORM_SEVERE})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        for h in data['hourly']:
            assert 0.0 <= h['p_flood'] <= 1.0

    def test_severe_breach_latches_to_one(self, stress_client, stress_env):
        """Once water exceeds severe, P(flood) should stay at 1.0."""
        resp = stress_client.post('/api/v1/trading/stress/run',
                                   json={'gauge_id': 'GAUGE-001',
                                         'storm_id': STORM_SEVERE})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        # Find first hour where p_flood = 1.0, then all subsequent should also be 1.0
        found_one = False
        for h in data['hourly']:
            if h['p_flood'] == 1.0:
                found_one = True
            if found_one:
                assert h['p_flood'] == 1.0
