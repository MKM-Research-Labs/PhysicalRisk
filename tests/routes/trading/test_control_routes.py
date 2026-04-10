# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Unit tests for routes/trading/control.py — GET/POST/reset endpoints.

Uses the trading_env fixture pattern from conftest.py.
"""

import json

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_CONTROL = {
    "version": "1.0.0",
    "sections": {
        "storm_generation": {"event_window_hours": 168},
        "hydrograph_synthesis": {"saturation_beta": 0.2},
        "gauge_propagation": {"default_roughness": 0.04},
        "spatial_correlation": {"spatial_corr_enabled": True},
        "stress_catalogue": {"stress_storms_min_count": 50},
    },
}


@pytest.fixture
def control_env(trading_env):
    """Trading env with storm_control.json written."""
    p = trading_env['input_dir'] / 'storm_control.json'
    p.write_text(json.dumps(SAMPLE_CONTROL))
    return trading_env


@pytest.fixture
def control_client(control_env):
    """Flask test client with storm_control.json available."""
    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()


@pytest.fixture
def no_control_client(trading_env):
    """Flask test client without storm_control.json."""
    # Ensure no storm_control.json exists
    p = trading_env['input_dir'] / 'storm_control.json'
    if p.exists():
        p.unlink()
    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()


# ---------------------------------------------------------------------------
# GET /trading/control/params
# ---------------------------------------------------------------------------

class TestGetControlParams:
    """GET /trading/control/params endpoint."""

    def test_returns_200(self, control_client):
        """control.py line 27: returns 200 with JSON params."""
        r = control_client.get('/api/v1/trading/control/params')
        assert r.status_code == 200

    def test_returns_success_status(self, control_client):
        """control.py line 33: response has status='success'."""
        r = control_client.get('/api/v1/trading/control/params')
        data = r.get_json()
        assert data['status'] == 'success'

    def test_returns_source_json(self, control_client):
        """control.py line 32: source='json' when file exists."""
        r = control_client.get('/api/v1/trading/control/params')
        data = r.get_json()
        assert data['source'] == 'json'

    def test_returns_source_defaults_when_missing(self, no_control_client):
        """control.py line 30: source='defaults' when file missing."""
        r = no_control_client.get('/api/v1/trading/control/params')
        data = r.get_json()
        assert data['source'] == 'defaults'

    def test_returns_params_with_sections(self, control_client):
        """Params should contain all five sections."""
        r = control_client.get('/api/v1/trading/control/params')
        data = r.get_json()
        sections = data['params']['sections']
        assert 'storm_generation' in sections
        assert 'hydrograph_synthesis' in sections
        assert 'gauge_propagation' in sections
        assert 'spatial_correlation' in sections
        assert 'stress_catalogue' in sections

    def test_returns_version(self, control_client):
        """Params should include version string."""
        r = control_client.get('/api/v1/trading/control/params')
        data = r.get_json()
        assert data['params']['version'] == '1.0.0'

    def test_defaults_have_all_sections(self, no_control_client):
        """When file missing, defaults should have all five sections."""
        r = no_control_client.get('/api/v1/trading/control/params')
        data = r.get_json()
        sections = data['params']['sections']
        assert set(sections.keys()) == {
            'storm_generation', 'hydrograph_synthesis', 'gauge_propagation',
            'spatial_correlation', 'stress_catalogue',
        }


# ---------------------------------------------------------------------------
# POST /trading/control/params
# ---------------------------------------------------------------------------

class TestSaveControlParams:
    """POST /trading/control/params endpoint."""

    def test_returns_200_on_valid_body(self, control_client):
        """control.py line 43: successful save returns 200."""
        r = control_client.post(
            '/api/v1/trading/control/params',
            data=json.dumps(SAMPLE_CONTROL),
            content_type='application/json',
        )
        assert r.status_code == 200

    def test_returns_success_message(self, control_client):
        """control.py line 43: returns success message."""
        r = control_client.post(
            '/api/v1/trading/control/params',
            data=json.dumps(SAMPLE_CONTROL),
            content_type='application/json',
        )
        data = r.get_json()
        assert data['status'] == 'success'
        assert 'saved' in data['message'].lower()

    def test_persists_to_disk(self, control_env, control_client):
        """Saved params should be persisted to storm_control.json."""
        modified = json.loads(json.dumps(SAMPLE_CONTROL))
        modified['sections']['storm_generation']['event_window_hours'] = 200
        control_client.post(
            '/api/v1/trading/control/params',
            data=json.dumps(modified),
            content_type='application/json',
        )
        # Re-read from disk
        p = control_env['input_dir'] / 'storm_control.json'
        saved = json.loads(p.read_text())
        assert saved['sections']['storm_generation']['event_window_hours'] == 200

    def test_round_trip_get_after_post(self, control_client):
        """POST then GET should return the saved values."""
        modified = json.loads(json.dumps(SAMPLE_CONTROL))
        modified['sections']['stress_catalogue']['stress_storms_min_count'] = 99
        control_client.post(
            '/api/v1/trading/control/params',
            data=json.dumps(modified),
            content_type='application/json',
        )
        r = control_client.get('/api/v1/trading/control/params')
        data = r.get_json()
        assert data['params']['sections']['stress_catalogue']['stress_storms_min_count'] == 99

    def test_rejects_empty_body(self, control_client):
        """control.py line 37: empty body returns 400."""
        r = control_client.post(
            '/api/v1/trading/control/params',
            data='',
            content_type='application/json',
        )
        assert r.status_code == 400

    def test_rejects_invalid_structure(self, control_client):
        """control.py line 40: missing sections returns 400."""
        r = control_client.post(
            '/api/v1/trading/control/params',
            data=json.dumps({"foo": "bar"}),
            content_type='application/json',
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# POST /trading/control/reset
# ---------------------------------------------------------------------------

class TestResetControlParams:
    """POST /trading/control/reset endpoint."""

    def test_returns_200(self, control_client):
        """control.py line 49: reset returns 200."""
        r = control_client.post('/api/v1/trading/control/reset')
        assert r.status_code == 200

    def test_returns_success(self, control_client):
        """control.py line 49: returns status=success."""
        r = control_client.post('/api/v1/trading/control/reset')
        data = r.get_json()
        assert data['status'] == 'success'

    def test_returns_default_params(self, control_client):
        """control.py line 49: returns the defaults in response."""
        r = control_client.post('/api/v1/trading/control/reset')
        data = r.get_json()
        params = data['params']
        assert 'sections' in params
        assert 'version' in params

    def test_overwrites_custom_values(self, control_env, control_client):
        """Reset should overwrite previously saved custom values."""
        # Save custom
        modified = json.loads(json.dumps(SAMPLE_CONTROL))
        modified['sections']['storm_generation']['event_window_hours'] = 999
        control_client.post(
            '/api/v1/trading/control/params',
            data=json.dumps(modified),
            content_type='application/json',
        )
        # Reset
        control_client.post('/api/v1/trading/control/reset')
        # GET should return defaults
        r = control_client.get('/api/v1/trading/control/params')
        data = r.get_json()
        import config.port as cp
        assert data['params']['sections']['storm_generation']['event_window_hours'] == cp.EVENT_WINDOW_HOURS

    def test_reset_file_persisted(self, control_env, control_client):
        """Reset should write defaults to disk."""
        control_client.post('/api/v1/trading/control/reset')
        p = control_env['input_dir'] / 'storm_control.json'
        assert p.exists()
        saved = json.loads(p.read_text())
        assert saved['version'] == '1.0.0'
        assert len(saved['sections']) == 5
