# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Unit tests for routes/trading/control.py — GET/POST/reset endpoints (part 1).

Covers both behaviour and the admin-password gate (shared with
``python app.py port``) on the mutating endpoints.
"""

import hashlib
import json
import os

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

ADMIN_PW = "testpw123"


@pytest.fixture
def admin_file(tmp_path, monkeypatch):
    """Create a .port_admin file with a known password and patch the decorator to use it."""
    admin_path = tmp_path / ".port_admin"
    salt = os.urandom(16).hex()
    h = hashlib.sha256((salt + ADMIN_PW).encode()).hexdigest()
    admin_path.write_text(json.dumps({"salt": salt, "hash": h}))

    import routes.trading._admin_auth as auth
    monkeypatch.setattr(auth, "_admin_file_path", lambda: admin_path)
    return admin_path


@pytest.fixture
def control_env(trading_env):
    """Trading env with storm_control.json written."""
    p = trading_env['input_dir'] / 'storm_control.json'
    p.write_text(json.dumps(SAMPLE_CONTROL))
    return trading_env


@pytest.fixture
def control_client(control_env, admin_file):
    """Flask test client with storm_control.json and admin password available."""
    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()


@pytest.fixture
def no_control_client(trading_env, admin_file):
    """Flask test client without storm_control.json but with admin password."""
    p = trading_env['input_dir'] / 'storm_control.json'
    if p.exists():
        p.unlink()
    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()


@pytest.fixture
def no_admin_client(control_env, tmp_path, monkeypatch):
    """Flask test client where no admin password has been set (no .port_admin file)."""
    missing = tmp_path / ".port_admin_missing"
    # Ensure it definitely does not exist
    if missing.exists():
        missing.unlink()
    import routes.trading._admin_auth as auth
    monkeypatch.setattr(auth, "_admin_file_path", lambda: missing)
    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()


def _auth_headers(password=ADMIN_PW):
    return {
        'Content-Type': 'application/json',
        'X-Admin-Password': password,
    }


# ---------------------------------------------------------------------------
# GET /trading/control/params  (no auth required — read-only)
# ---------------------------------------------------------------------------

class TestGetControlParams:
    """GET /trading/control/params endpoint — read-only, no auth."""

    def test_returns_200(self, control_client):
        r = control_client.get('/api/v1/trading/control/params')
        assert r.status_code == 200

    def test_returns_success_status(self, control_client):
        r = control_client.get('/api/v1/trading/control/params')
        assert r.get_json()['status'] == 'success'

    def test_returns_source_json(self, control_client):
        r = control_client.get('/api/v1/trading/control/params')
        assert r.get_json()['source'] == 'json'

    def test_returns_source_defaults_when_missing(self, no_control_client):
        r = no_control_client.get('/api/v1/trading/control/params')
        assert r.get_json()['source'] == 'defaults'

    def test_returns_params_with_sections(self, control_client):
        r = control_client.get('/api/v1/trading/control/params')
        sections = r.get_json()['params']['sections']
        assert set(sections.keys()) >= {
            'storm_generation', 'hydrograph_synthesis', 'gauge_propagation',
            'spatial_correlation', 'stress_catalogue',
        }

    def test_returns_version(self, control_client):
        r = control_client.get('/api/v1/trading/control/params')
        assert r.get_json()['params']['version'] == '1.0.0'

    def test_defaults_have_all_sections(self, no_control_client):
        r = no_control_client.get('/api/v1/trading/control/params')
        sections = r.get_json()['params']['sections']
        assert set(sections.keys()) == {
            'storm_generation', 'hydrograph_synthesis', 'gauge_propagation',
            'spatial_correlation', 'stress_catalogue',
        }


# ---------------------------------------------------------------------------
# POST /trading/control/params  (admin-gated)
# ---------------------------------------------------------------------------

class TestSaveControlParams:
    """POST /trading/control/params endpoint — admin-gated."""

    def test_returns_200_on_valid_body(self, control_client):
        r = control_client.post(
            '/api/v1/trading/control/params',
            data=json.dumps(SAMPLE_CONTROL),
            headers=_auth_headers(),
        )
        assert r.status_code == 200

    def test_returns_success_message(self, control_client):
        r = control_client.post(
            '/api/v1/trading/control/params',
            data=json.dumps(SAMPLE_CONTROL),
            headers=_auth_headers(),
        )
        data = r.get_json()
        assert data['status'] == 'success'
        assert 'saved' in data['message'].lower()

    def test_persists_to_disk(self, control_env, control_client):
        modified = json.loads(json.dumps(SAMPLE_CONTROL))
        modified['sections']['storm_generation']['event_window_hours'] = 200
        control_client.post(
            '/api/v1/trading/control/params',
            data=json.dumps(modified),
            headers=_auth_headers(),
        )
        p = control_env['input_dir'] / 'storm_control.json'
        saved = json.loads(p.read_text())
        assert saved['sections']['storm_generation']['event_window_hours'] == 200

    def test_round_trip_get_after_post(self, control_client):
        modified = json.loads(json.dumps(SAMPLE_CONTROL))
        modified['sections']['stress_catalogue']['stress_storms_min_count'] = 99
        control_client.post(
            '/api/v1/trading/control/params',
            data=json.dumps(modified),
            headers=_auth_headers(),
        )
        r = control_client.get('/api/v1/trading/control/params')
        data = r.get_json()
        assert data['params']['sections']['stress_catalogue']['stress_storms_min_count'] == 99

    def test_rejects_empty_body(self, control_client):
        r = control_client.post(
            '/api/v1/trading/control/params',
            data='',
            headers=_auth_headers(),
        )
        assert r.status_code == 400

    def test_rejects_invalid_structure(self, control_client):
        r = control_client.post(
            '/api/v1/trading/control/params',
            data=json.dumps({"foo": "bar"}),
            headers=_auth_headers(),
        )
        assert r.status_code == 400
