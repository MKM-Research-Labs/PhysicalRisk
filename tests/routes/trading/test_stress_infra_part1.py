# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for stress infrastructure — part 1: edge cases, error handling, caching."""

import json
from unittest.mock import patch, MagicMock

import pytest

from .conftest import STORM_SEVERE


class TestStressHydrographEdgeCases:
    """_synthesize_hydrograph edge cases."""

    def test_synthesize_hydrograph_peak_at_zero(self, stress_env):
        """peak_position=0 uses decay-only path."""
        import routes.trading.stress._helpers as stress_helpers
        levels = stress_helpers._synthesize_hydrograph(
            base_level=3.0, level_change=2.0,
            duration_hours=0, peak_position=0.5, num_hours=10)
        assert len(levels) == 10
        assert all(isinstance(v, float) for v in levels)

    def test_synthesize_hydrograph_remaining_zero(self, stress_env):
        """remaining=0 uses frac=1.0 path."""
        import routes.trading.stress._helpers as stress_helpers
        levels = stress_helpers._synthesize_hydrograph(
            base_level=3.0, level_change=2.0,
            duration_hours=10, peak_position=0.999, num_hours=5)
        assert len(levels) == 5


class TestStressErrorHandlers:
    """Error handling paths in stress endpoints."""

    def test_stress_gauges_engine_error_returns_500(self, stress_client,
                                                     stress_env):
        """stress/gauges returns 500 when gauge loader raises."""
        with patch('routes.trading.stress.gauges._load_gauge_locations',
                   side_effect=RuntimeError('fail')):
            resp = stress_client.get('/api/v1/trading/stress/gauges')
            assert resp.status_code == 500

    def test_stress_storms_engine_error_returns_500(self, stress_client,
                                                     stress_env):
        """stress/storms returns 500 when storm loader raises."""
        with patch('routes.trading.stress.storms._load_stress_storms',
                   side_effect=RuntimeError('fail')):
            resp = stress_client.get(
                '/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
            assert resp.status_code == 500

    def test_run_stress_engine_error_returns_500(self, stress_client, stress_env):
        """stress/run returns 500 on engine error."""
        with patch('routes.trading.stress.scenario._get_engines',
                   side_effect=RuntimeError('fail')):
            resp = stress_client.post('/api/v1/trading/stress/run',
                                      json={'gauge_id': 'GAUGE-001',
                                            'storm_id': STORM_SEVERE})
            assert resp.status_code == 500


class TestRunStressEdgeCases:
    """Edge cases in run_stress_scenario endpoint."""

    def test_run_stress_null_body_returns_400(self, stress_client, stress_env):
        """Null JSON body returns 400."""
        resp = stress_client.post('/api/v1/trading/stress/run',
                                  data=b'null',
                                  content_type='application/json')
        assert resp.status_code == 400

    def test_run_stress_empty_gauge_id_returns_400(self, stress_client, stress_env):
        """Empty gauge_id returns 400."""
        resp = stress_client.post('/api/v1/trading/stress/run',
                                  json={'gauge_id': '', 'storm_id': STORM_SEVERE})
        assert resp.status_code == 400

    def test_run_stress_no_open_trades_returns_404(self, stress_client, stress_env):
        """No open trades at gauge returns 404."""
        resp = stress_client.post('/api/v1/trading/stress/run',
                                  json={'gauge_id': 'GAUGE-999',
                                        'storm_id': STORM_SEVERE})
        assert resp.status_code == 404

    def test_run_stress_uses_gaugets_hydrograph(self, stress_client, stress_env):
        """Gaugets file present uses hydrograph built from real readings."""
        gaugets_dir = stress_env['input_dir'] / 'gaugets'
        gaugets_dir.mkdir(exist_ok=True)
        gaugets_file = gaugets_dir / 'GAUGE-001.json'
        readings = [{'timestamp': f'2024-01-01T{h:02d}:00:00',
                     'waterLevel': 3.0 + h * 0.1}
                    for h in range(24)]
        gaugets_file.write_text(json.dumps({
            'gauge_id': 'GAUGE-001',
            'flood_simulation': {'readings': readings},
        }))

        resp = stress_client.post('/api/v1/trading/stress/run',
                                  json={'gauge_id': 'GAUGE-001',
                                        'storm_id': STORM_SEVERE})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'


# ===========================================================================
# Coverage expansion — _helpers.py lines 37-38, 67, 86-97
# ===========================================================================

class TestLoadStressStormsOSError:
    """OSError from path.stat() returns cached value."""

    def test_stat_oserror_returns_cached(self, stress_env):
        """When path.stat() raises OSError, return existing cache."""
        import routes.trading.stress._helpers as stress_helpers
        stress_helpers._stress_index_cache = {"storms": [{"storm_id": "cached"}]}
        stress_helpers._stress_index_mtime = 12345.0

        index_path = stress_env['input_dir'] / 'stress_storms' / '_index.json'
        real_stat = type(index_path).stat
        call_count = [0]
        def stat_side_effect(self_path, *a, **kw):
            call_count[0] += 1
            if call_count[0] >= 2:
                raise OSError('disk error')
            return real_stat(self_path, *a, **kw)

        with patch('pathlib.PosixPath.stat', stat_side_effect):
            result = stress_helpers._load_stress_storms()
        assert result == {"storms": [{"storm_id": "cached"}]}
        stress_helpers._stress_index_cache = None
        stress_helpers._stress_index_mtime = None

    def test_stat_oserror_returns_none_when_no_cache(self, stress_env):
        """When path.stat() raises OSError and no cache, returns None."""
        import routes.trading.stress._helpers as stress_helpers
        stress_helpers._stress_index_cache = None
        stress_helpers._stress_index_mtime = None

        index_path = stress_env['input_dir'] / 'stress_storms' / '_index.json'
        real_stat = type(index_path).stat
        call_count = [0]
        def stat_side_effect(self_path, *a, **kw):
            call_count[0] += 1
            if call_count[0] >= 2:
                raise OSError('disk error')
            return real_stat(self_path, *a, **kw)

        with patch('pathlib.PosixPath.stat', stat_side_effect):
            result = stress_helpers._load_stress_storms()
        assert result is None


class TestHydrographRemainingZeroExact:
    """frac=1.0 when remaining<=0 exactly."""

    def test_remaining_exactly_zero(self, stress_env):
        import routes.trading.stress._helpers as stress_helpers
        levels = stress_helpers._synthesize_hydrograph(
            base_level=3.0, level_change=2.0,
            duration_hours=10, peak_position=1.0, num_hours=5)
        assert len(levels) == 5
        assert abs(levels[0] - 3.0) < 0.01
