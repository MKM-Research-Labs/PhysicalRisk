# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for portfolio stress infrastructure — error handling, caching."""

import json
import time
from unittest.mock import patch, MagicMock

import pytest

from tests.routes.trading.conftest import STORM_PORT_SEVERE, STORM_PORT_ALERT


class TestPortfolioStressErrors:
    """Error handling paths in portfolio stress endpoints."""

    def test_no_json_body_returns_error(self, port_stress_client, port_stress_env):
        """POST with no body returns 400 or 500."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            content_type='application/json')
        assert resp.status_code in (400, 500)

    def test_engine_error_returns_500(self, port_stress_client, port_stress_env):
        """patch _get_engines to raise RuntimeError -> 500."""
        with patch('routes.trading.port_stress._routes._get_engines',
                   side_effect=RuntimeError('engine fail')):
            resp = port_stress_client.post(
                '/api/v1/trading/stress/portfolio-run',
                json={'storm_id': STORM_PORT_SEVERE})
            assert resp.status_code == 500

    def test_missing_storms_file_returns_404(self, trading_client, trading_env):
        """No stress_storms/ + cache cleared -> portfolio-run returns 404."""
        import routes.trading.stress._helpers as stress_helpers
        stress_helpers._stress_index_cache = None
        resp = trading_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        assert resp.status_code == 404


class TestStressStormsCacheInvalidation:
    """_load_stress_storms() must reload when the index file changes on disk."""

    def test_cache_reloads_on_mtime_change(self, tmp_path):
        """Replacing stress_storms/_index.json on disk is picked up on next
        request without restarting the server (mtime-based invalidation)."""
        import routes.trading.stress._helpers as h

        ss_dir = tmp_path / 'stress_storms'
        ss_dir.mkdir()
        index = ss_dir / '_index.json'
        index.write_text(json.dumps({'storms': [{'storm_id': 'STORM-aaaaaaaa',
                                                  'name': 'Alpha'}]}))

        original_fn = h._load_stress_storms.__globals__['config'].get_input_dir
        h._load_stress_storms.__globals__['config'].get_input_dir = lambda: tmp_path

        h._stress_index_cache = None
        h._stress_index_mtime = None

        try:
            data1 = h._load_stress_storms()
            assert len(data1['storms']) == 1

            import time; time.sleep(0.01)
            index.write_text(json.dumps({'storms': [
                {'storm_id': 'STORM-aaaaaaaa', 'name': 'Alpha'},
                {'storm_id': 'STORM-bbbbbbbb', 'name': 'Beta'},
            ]}))

            data2 = h._load_stress_storms()
            assert len(data2['storms']) == 2, \
                "Cache must invalidate when _index.json mtime changes"
        finally:
            h._load_stress_storms.__globals__['config'].get_input_dir = original_fn
            h._stress_index_cache = None
            h._stress_index_mtime = None

    def test_cache_not_reloaded_when_mtime_unchanged(self, tmp_path):
        """If the index has not changed, the cached object is returned."""
        import routes.trading.stress._helpers as h

        ss_dir = tmp_path / 'stress_storms'
        ss_dir.mkdir()
        index = ss_dir / '_index.json'
        index.write_text(json.dumps({'storms': [{'storm_id': 'STORM-aaaaaaaa',
                                                  'name': 'Alpha'}]}))

        original_fn = h._load_stress_storms.__globals__['config'].get_input_dir
        h._load_stress_storms.__globals__['config'].get_input_dir = lambda: tmp_path
        h._stress_index_cache = None
        h._stress_index_mtime = None

        try:
            data1 = h._load_stress_storms()
            id1 = id(data1)
            data2 = h._load_stress_storms()
            assert id(data1) == id(data2), \
                "Identical mtime must return the same cached object"
        finally:
            h._load_stress_storms.__globals__['config'].get_input_dir = original_fn
            h._stress_index_cache = None
            h._stress_index_mtime = None
