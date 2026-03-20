# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage expansion tests for stress/scenario.py — lines 48, 81, 106,
109-110, 125, 133-137."""

import json
from unittest.mock import patch, MagicMock

import pytest

from .conftest import STORM_SEVERE, STORM_WARNING


class TestStressStormsNotFound:
    """Line 48: stress_storms.json not found returns 404."""

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
    """Line 81: no open trades at gauge returns 404."""

    @patch('routes.trading.stress.scenario._get_predictor')
    def test_gauge_with_no_trades_returns_404(self, mock_predictor,
                                                stress_client, stress_env):
        """Gauge that exists in storm data but has no trades returns 404."""
        pred = MagicMock()
        pred.predict.return_value = 0.3
        mock_predictor.return_value = pred
        # GAUGE-001 has trades, but this test uses a gauge that has no trades
        # but appears in storm gauge_responses. We write a new storms file.
        storms = {
            'metadata': {'generated': '2026-01-01'},
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
        # Write storm to stress_storms/ directory
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
    """Lines 106, 109-110: hydrograph padding and exception handling."""

    @patch('routes.trading.stress.scenario._get_predictor')
    def test_short_gaugets_padded_to_storm_hours(self, mock_predictor,
                                                    stress_client, stress_env):
        """When gaugets has fewer than STORM_HOURS readings, pads with last value (line 106-108)."""
        pred = MagicMock()
        pred.predict.return_value = 0.3
        pred._load_summary.return_value = {'gauges': []}
        mock_predictor.return_value = pred

        # Write gaugets file with only 10 readings (< 168)
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

    @patch('routes.trading.stress.scenario._get_predictor')
    def test_gaugets_bad_json_falls_back(self, mock_predictor,
                                           stress_client, stress_env):
        """When gaugets JSON is corrupt, exception caught (lines 109-110),
        falls back to synthesized hydrograph."""
        pred = MagicMock()
        pred.predict.return_value = 0.3
        pred._load_summary.return_value = {'gauges': []}
        mock_predictor.return_value = pred

        gaugets_dir = stress_env['gaugets_dir']
        (gaugets_dir / 'GAUGE-001.json').write_text('NOT VALID JSON!!!')

        resp = stress_client.post('/api/v1/trading/stress/run',
                                   json={'gauge_id': 'GAUGE-001',
                                         'storm_id': STORM_SEVERE})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert len(data['hourly']) == 168


class TestPredictorNotFound:
    """Line 125: predictor returns None -> 404."""

    def test_predictor_none_returns_404(self, stress_client, stress_env):
        """When _get_predictor returns None, returns 404."""
        with patch('routes.trading.stress.scenario._get_predictor',
                   return_value=None):
            resp = stress_client.post('/api/v1/trading/stress/run',
                                      json={'gauge_id': 'GAUGE-001',
                                            'storm_id': STORM_SEVERE})
            assert resp.status_code == 404
            data = json.loads(resp.data)
            assert 'models not found' in data.get('message', '').lower()


class TestModelAucFromSummary:
    """Lines 133-137: model_auc loaded from predictor summary."""

    @patch('routes.trading.stress.scenario._get_predictor')
    def test_model_auc_present_when_summary_has_gauge(self, mock_predictor,
                                                        stress_client, stress_env):
        """When predictor._load_summary has matching gauge, model_auc is set."""
        pred = MagicMock()
        pred.predict.return_value = 0.3
        pred._load_summary.return_value = {
            'gauges': [
                {
                    'gauge_id': 'GAUGE-001',
                    'status': 'trained',
                    'metrics': {'auc_roc': 0.95},
                },
            ],
        }
        mock_predictor.return_value = pred

        resp = stress_client.post('/api/v1/trading/stress/run',
                                   json={'gauge_id': 'GAUGE-001',
                                         'storm_id': STORM_SEVERE})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['model_auc'] == 0.95

    @patch('routes.trading.stress.scenario._get_predictor')
    def test_model_auc_none_when_summary_no_match(self, mock_predictor,
                                                     stress_client, stress_env):
        """When predictor._load_summary has no matching gauge, model_auc is None."""
        pred = MagicMock()
        pred.predict.return_value = 0.3
        pred._load_summary.return_value = {
            'gauges': [
                {
                    'gauge_id': 'GAUGE-OTHER',
                    'status': 'trained',
                    'metrics': {'auc_roc': 0.90},
                },
            ],
        }
        mock_predictor.return_value = pred

        resp = stress_client.post('/api/v1/trading/stress/run',
                                   json={'gauge_id': 'GAUGE-001',
                                         'storm_id': STORM_SEVERE})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['model_auc'] is None

    @patch('routes.trading.stress.scenario._get_predictor')
    def test_model_auc_none_when_summary_raises(self, mock_predictor,
                                                   stress_client, stress_env):
        """When predictor._load_summary raises, model_auc is None (lines 136-137)."""
        pred = MagicMock()
        pred.predict.return_value = 0.3
        pred._load_summary.side_effect = RuntimeError('no summary')
        mock_predictor.return_value = pred

        resp = stress_client.post('/api/v1/trading/stress/run',
                                   json={'gauge_id': 'GAUGE-001',
                                         'storm_id': STORM_SEVERE})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['model_auc'] is None

    @patch('routes.trading.stress.scenario._get_predictor')
    def test_model_auc_skips_untrained_gauge(self, mock_predictor,
                                               stress_client, stress_env):
        """When gauge status is not 'trained', model_auc remains None."""
        pred = MagicMock()
        pred.predict.return_value = 0.3
        pred._load_summary.return_value = {
            'gauges': [
                {
                    'gauge_id': 'GAUGE-001',
                    'status': 'failed',
                    'metrics': {'auc_roc': 0.85},
                },
            ],
        }
        mock_predictor.return_value = pred

        resp = stress_client.post('/api/v1/trading/stress/run',
                                   json={'gauge_id': 'GAUGE-001',
                                         'storm_id': STORM_SEVERE})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['model_auc'] is None
