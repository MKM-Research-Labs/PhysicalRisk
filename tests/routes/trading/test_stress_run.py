# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for POST /trading/stress/run endpoint -- scenario execution."""

import json

import pytest

from .conftest import STORM_SEVERE, STORM_WARNING


class TestRunStress:
    """POST /trading/stress/run endpoint tests."""

    def test_run_stress_missing_params(self, stress_client, stress_env):
        """Missing gauge_id or storm_id returns 400."""
        resp = stress_client.post('/api/v1/trading/stress/run',
                                  json={'gauge_id': 'GAUGE-001'})
        assert resp.status_code == 400

    def test_run_stress_no_body(self, stress_client, stress_env):
        """No JSON body returns error."""
        resp = stress_client.post('/api/v1/trading/stress/run',
                                  content_type='application/json')
        assert resp.status_code in (400, 500)

    def test_run_stress_returns_hourly(self, stress_client, stress_env):
        """POST returns 168-hour forecast array."""
        resp = stress_client.post('/api/v1/trading/stress/run',
                                  json={'gauge_id': 'GAUGE-001',
                                        'storm_id': STORM_SEVERE})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert len(data['hourly']) == 168

    def test_run_stress_hourly_fields(self, stress_client, stress_env):
        """Each hour has water_level, p_flood, portfolio fields."""
        resp = stress_client.post('/api/v1/trading/stress/run',
                                  json={'gauge_id': 'GAUGE-001',
                                        'storm_id': STORM_WARNING})
        data = json.loads(resp.data)
        for h in data['hourly']:
            assert 'hour' in h
            assert 'water_level' in h
            assert 'p_flood' in h
            assert 'portfolio_cash' in h
            assert 'portfolio_stress_pnl' in h
            assert 'per_trade' in h

    def test_run_stress_trade_summary(self, stress_client, stress_env):
        """Response includes per-trade summary."""
        resp = stress_client.post('/api/v1/trading/stress/run',
                                  json={'gauge_id': 'GAUGE-001',
                                        'storm_id': STORM_SEVERE})
        data = json.loads(resp.data)
        assert 'trades' in data
        assert len(data['trades']) == 2  # 2 trades at GAUGE-001
        for t in data['trades']:
            assert 'swap_id' in t
            assert 'notional' in t
            assert 'mtm' in t
            assert 'triggered_hour' in t

    def test_run_stress_portfolio_summary(self, stress_client, stress_env):
        """Response includes portfolio-level stress summary."""
        resp = stress_client.post('/api/v1/trading/stress/run',
                                  json={'gauge_id': 'GAUGE-001',
                                        'storm_id': STORM_SEVERE})
        data = json.loads(resp.data)
        summary = data['summary']
        assert 'num_trades' in summary
        assert 'total_notional' in summary
        assert 'total_mtm' in summary
        assert 'peak_p_flood' in summary
        assert 'num_triggered' in summary
        assert 'first_trigger_hour' in summary
        # model_auc is present at top level (may be None if no summary)
        assert 'model_auc' in data

    def test_run_stress_knock_out(self, stress_client, stress_env):
        """Severe storm triggers knock-out (P(flood)=100%)."""
        resp = stress_client.post('/api/v1/trading/stress/run',
                                  json={'gauge_id': 'GAUGE-001',
                                        'storm_id': STORM_SEVERE})
        data = json.loads(resp.data)
        # STORM_SEVERE peaks at 6.0m > severe threshold 5.5m -> triggers knock-out
        # At the breach hour p_flood = 1.0; after KO, p_flood is blanked (None)
        peak_hours = [h for h in data['hourly']
                      if h['water_level'] >= 5.5]
        if peak_hours:
            first_breach = peak_hours[0]['hour']
            # Breach hour itself should have p_flood = 1.0
            assert data['hourly'][first_breach]['p_flood'] == 1.0
            # Hours after KO should be blanked (None)
            first_trigger = data['summary']['first_trigger_hour']
            if first_trigger is not None:
                for h in data['hourly']:
                    if h['hour'] > first_trigger:
                        assert h['p_flood'] is None

    def test_run_stress_probability_surface(self, stress_client, stress_env):
        """Response includes probability surface grid."""
        resp = stress_client.post('/api/v1/trading/stress/run',
                                  json={'gauge_id': 'GAUGE-001',
                                        'storm_id': STORM_SEVERE})
        data = json.loads(resp.data)
        assert 'probability_surface' in data
        surface = data['probability_surface']
        assert 'water_levels' in surface
        assert 'hours' in surface
        assert 'probabilities' in surface
        # Water levels descending
        assert surface['water_levels'] == sorted(surface['water_levels'],
                                                  reverse=True)
        # Hours at 4-hour intervals
        assert surface['hours'][0] == 0
        assert all(surface['hours'][i+1] - surface['hours'][i] == 4
                   for i in range(len(surface['hours']) - 1))
        # Grid dimensions match
        assert len(surface['probabilities']) == len(surface['water_levels'])
        assert len(surface['probabilities'][0]) == len(surface['hours'])

    def test_surface_shows_full_168h(self, stress_client, stress_env):
        """Surface must cover full 168h storm horizon regardless of KO.

        User needs scrollable table showing the complete storm history.
        KO should NOT trim columns -- post-KO cells shown as null/blank.
        """
        resp = stress_client.post('/api/v1/trading/stress/run',
                                  json={'gauge_id': 'GAUGE-001',
                                        'storm_id': STORM_SEVERE})
        data = json.loads(resp.data)
        surface = data['probability_surface']
        # Must always go to H164 (last 4h interval before H168)
        assert max(surface['hours']) >= 164, \
            "Surface must show full 168h -- user needs scrollable complete history"

    def test_surface_caps_at_severe(self, stress_client, stress_env):
        """Surface water levels cap at severe -- no rows above severe."""
        resp = stress_client.post('/api/v1/trading/stress/run',
                                  json={'gauge_id': 'GAUGE-001',
                                        'storm_id': STORM_SEVERE})
        data = json.loads(resp.data)
        severe = data.get('severe_level', 0)
        if severe > 0:
            surface = data['probability_surface']
            assert max(surface['water_levels']) <= severe

    def test_run_stress_invalid_storm(self, stress_client, stress_env):
        """Non-existent storm returns 404."""
        resp = stress_client.post('/api/v1/trading/stress/run',
                                  json={'gauge_id': 'GAUGE-001',
                                        'storm_id': 'STORM-INVALID'})
        assert resp.status_code == 404
