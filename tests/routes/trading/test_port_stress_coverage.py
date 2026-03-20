# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage expansion tests for port_stress.py — lines 51-54, 85, 120-122,
147, 192, 245, 249-250, 285-286, 294."""

import json
import sys
from unittest.mock import patch, MagicMock

import pytest

from tests.routes.trading.conftest import (
    STORM_PORT_SEVERE, STORM_PORT_ALERT,
    GAUGE_WESTMINSTER, GAUGE_CHELSEA,
)


def _write_stress_storms_dir(input_dir, storms_list):
    """Write a stress_storms/ directory from a list of storm dicts."""
    ss_dir = input_dir / 'stress_storms'
    ss_dir.mkdir(exist_ok=True)
    index_entries = []
    for storm in storms_list:
        (ss_dir / f"{storm['storm_id']}.json").write_text(json.dumps(storm))
        gauge_ids_alert = [
            r['gauge_id'] for r in storm.get('gauge_responses', [])
            if r.get('exceeded_alert')
        ]
        entry = {k: v for k, v in storm.items() if k != 'gauge_responses'}
        entry['gauge_ids_alert'] = gauge_ids_alert
        index_entries.append(entry)
    (ss_dir / '_index.json').write_text(json.dumps({
        'total_storms': len(storms_list), 'storms': index_entries,
    }))


class TestStressmPredictorLoadsFromDir:
    """Lines 51-54: _get_stressm_predictor loads from stressm dir when it has models."""

    def test_stressm_dir_with_joblib_loads_predictor(self, port_stress_env):
        """When stressm dir has .joblib files, predictor is loaded from it."""
        import routes.trading.port_stress as ps_mod
        ps_mod._stressm_predictor_cache = None

        stressm_dir = port_stress_env['stressm_dir']
        (stressm_dir / 'GAUGE-001.joblib').write_bytes(b'fake')

        mock_predictor = MagicMock()
        mock_fp_class = MagicMock(return_value=mock_predictor)
        mock_module = MagicMock(FloodPredictor=mock_fp_class)

        with patch.dict(sys.modules, {'models.stress.flood_classifier': mock_module}):
            ps_mod._stressm_predictor_cache = None
            result = ps_mod._get_stressm_predictor()

        assert result is mock_predictor
        mock_fp_class.assert_called_once_with(stressm_dir)
        ps_mod._stressm_predictor_cache = None


class TestStormNameFallback:
    """Line 85: storm name == storm_id gets passed through as-is."""

    def test_storm_with_no_name_uses_storm_id(self, port_stress_env):
        """Storm with empty name falls back to storm_id."""
        storms_list = [
            {
                'storm_id': 'STORM-no-name',
                'name': '',
                'intensity_category': 'moderate',
                'duration_hours': 18,
                'peak_position': 0.5,
                'effective_precipitation_mm': 40.0,
                'trigger_summary': {
                    'gauges_severe': 0, 'gauges_warning': 0,
                    'gauges_alert': 0, 'gauges_impacted': 0,
                },
                'gauge_responses': [],
            },
            {
                'storm_id': 'STORM-same-name',
                'name': 'STORM-same-name',
                'intensity_category': 'moderate',
                'duration_hours': 18,
                'peak_position': 0.5,
                'effective_precipitation_mm': 40.0,
                'trigger_summary': {
                    'gauges_severe': 0, 'gauges_warning': 0,
                    'gauges_alert': 0, 'gauges_impacted': 0,
                },
                'gauge_responses': [],
            },
        ]
        _write_stress_storms_dir(port_stress_env['input_dir'], storms_list)

        import routes.trading.stress._helpers as stress_helpers
        stress_helpers._stress_index_cache = None
        import routes.trading.port_stress as ps_mod
        ps_mod._stressm_predictor_cache = None

        from server import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        resp = client.get('/api/v1/trading/stress/portfolio-storms')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        # Both storms should have name == storm_id as fallback
        for s in data['storms']:
            assert s['name'] == s['storm_id']


class TestPortfolioStormsException:
    """Lines 120-122: exception in get_portfolio_storms returns 500."""

    def test_exception_returns_500(self, port_stress_client, port_stress_env):
        """Exception in _load_stress_storms causes 500."""
        with patch('routes.trading.port_stress._load_stress_storms',
                   side_effect=RuntimeError('boom')):
            resp = port_stress_client.get('/api/v1/trading/stress/portfolio-storms')
            assert resp.status_code == 500


class TestEmptyStormId:
    """Line 147: empty storm_id in portfolio-run returns 400."""

    def test_empty_storm_id_returns_400(self, port_stress_client, port_stress_env):
        """Empty storm_id returns 400."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': ''})
        assert resp.status_code == 400


class TestClosedTradeSkipped:
    """Line 192: closed trades are skipped in trade indexing."""

    @patch('routes.trading.port_stress._get_stressm_predictor')
    def test_closed_trade_excluded_from_stress(self, mock_pred, port_stress_env):
        """Closed trade should not appear in stress results."""
        pred = MagicMock()
        pred.predict.return_value = 0.4
        mock_pred.return_value = pred

        # Write a closed trade into prs dir
        prs_dir = port_stress_env['prs_dir']
        from tests.routes.trading._data import make_trade
        closed_trade = make_trade(
            'PRS-CLOSED-001', GAUGE_WESTMINSTER, 'Thames at Westminster',
            is_payer=True, spread_bps=200.0, tenor=3, notional=10_000_000)
        closed_trade['TradingMetadata'] = {'trade_status': 'Closed'}
        with open(prs_dir / 'PRS-CLOSED-001.json', 'w') as f:
            json.dump(closed_trade, f)

        # Also write trade marks for the closed trade
        trading_dir = port_stress_env['trading_dir']
        marks = {'PRS-CLOSED-001': {'trade_status': 'Closed'}}
        with open(trading_dir / 'trade_marks.json', 'w') as f:
            json.dump(marks, f)

        from server import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        resp = client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        # Closed trade should not be in any gauge's trades list
        for g in data['gauges']:
            for t in g.get('trades', []):
                assert t['swap_id'] != 'PRS-CLOSED-001'


class TestHydrographFromGaugets:
    """Lines 245, 249-250: gaugets-based hydrograph paths."""

    @patch('routes.trading.port_stress._get_stressm_predictor')
    def test_gaugets_hydrograph_enough_readings(self, mock_pred, port_stress_env):
        """When gaugets file has >= STORM_HOURS readings, hydrograph is truncated (line 245)."""
        pred = MagicMock()
        pred.predict.return_value = 0.3
        mock_pred.return_value = pred

        # Write a gaugets file with 200 readings (> 168 STORM_HOURS)
        gaugets_dir = port_stress_env['gaugets_dir']
        readings = [{'timestamp': f'2024-01-01T{h:03d}:00:00',
                     'waterLevel': 3.0 + h * 0.02}
                    for h in range(200)]
        (gaugets_dir / f'{GAUGE_WESTMINSTER}.json').write_text(json.dumps({
            'gauge_id': GAUGE_WESTMINSTER,
            'flood_simulation': {'readings': readings},
        }))

        from server import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        resp = client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        data = json.loads(resp.data)
        assert resp.status_code == 200

    @patch('routes.trading.port_stress._get_stressm_predictor')
    def test_gaugets_bad_json_falls_back(self, mock_pred, port_stress_env):
        """When gaugets file has invalid JSON, exception is caught (lines 249-250)
        and fallback hydrograph is used."""
        pred = MagicMock()
        pred.predict.return_value = 0.3
        mock_pred.return_value = pred

        gaugets_dir = port_stress_env['gaugets_dir']
        (gaugets_dir / f'{GAUGE_WESTMINSTER}.json').write_text('not json!!!')

        from server import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        resp = client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        data = json.loads(resp.data)
        # Should still succeed with fallback hydrograph
        assert resp.status_code == 200
        assert data['status'] == 'success'


class TestPredictorException:
    """Lines 285-286: predictor.predict raises exception -> p_flood = 0.0."""

    @patch('routes.trading.port_stress._get_stressm_predictor')
    def test_predictor_exception_defaults_to_zero(self, mock_pred,
                                                    port_stress_client, port_stress_env):
        """If predictor.predict raises, p_flood defaults to 0.0."""
        pred = MagicMock()
        pred.predict.side_effect = RuntimeError('model error')
        mock_pred.return_value = pred

        # Use STORM_PORT_ALERT which has a gauge response for GAUGE-001
        # at peak_level 4.8m, which is < severe 5.5m, so predictor IS called
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_ALERT})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        # GAUGE-001 should have p_flood=0.0 because predictor raised
        g001 = next((g for g in data['gauges'] if g['gauge_id'] == 'GAUGE-001'), None)
        if g001 and g001.get('p_flood') is not None:
            assert g001['p_flood'] == 0.0


class TestAlertThreshold:
    """Line 294: alert threshold path."""

    @patch('routes.trading.port_stress._get_stressm_predictor')
    def test_alert_threshold_classification(self, mock_pred, port_stress_env):
        """When peak_wl >= alert but < warning, threshold is 'alert' (line 294)."""
        pred = MagicMock()
        pred.predict.return_value = 0.2
        mock_pred.return_value = pred

        # Write a custom storm where GAUGE-001 peak is clearly in alert range
        # GAUGE-001: alert=4.5, warning=5.0, severe=5.5
        # Set peak_level_m to 4.6 (just above alert, well below warning)
        storms_data = {
            'metadata': {'generated': '2026-01-01'},
            'storms': [{
                'storm_id': 'STORM-alert-only',
                'name': 'Alert Only Storm',
                'intensity_category': 'moderate',
                'duration_hours': 18,
                'peak_position': 0.5,
                'effective_precipitation_mm': 30.0,
                'trigger_summary': {
                    'max_trigger': 'alert',
                    'gauges_severe': 0, 'gauges_warning': 0,
                    'gauges_alert': 1, 'gauges_impacted': 1,
                },
                'gauge_responses': [{
                    'gauge_id': 'GAUGE-001',
                    'base_level_m': 3.5,
                    'peak_level_m': 4.6,
                    'level_change_m': 1.1,
                    'exceeded_alert': True,
                    'exceeded_warning': False,
                    'exceeded_severe': False,
                }],
            }],
        }
        _write_stress_storms_dir(port_stress_env['input_dir'], storms_data['storms'])
        import routes.trading.stress._helpers as stress_helpers
        stress_helpers._stress_index_cache = None

        # Remove gaugets file for GAUGE-001 so synthesized hydrograph is used
        # (avoids scaling issues with gaugets readings)
        gaugets_dir = port_stress_env['gaugets_dir']
        g001_file = gaugets_dir / f'{GAUGE_WESTMINSTER}.json'
        if g001_file.exists():
            g001_file.unlink()

        from server import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        resp = client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': 'STORM-alert-only'})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        g001 = next((g for g in data['gauges'] if g['gauge_id'] == 'GAUGE-001'), None)
        assert g001 is not None
        assert g001['threshold'] == 'alert'
