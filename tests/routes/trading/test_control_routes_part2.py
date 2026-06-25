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

"""
Unit tests for routes/trading/control.py — GET/POST/reset endpoints (part 2).

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
# POST /trading/control/reset  (admin-gated)
# ---------------------------------------------------------------------------

class TestResetControlParams:
    """POST /trading/control/reset endpoint — admin-gated."""

    def test_returns_200(self, control_client):
        r = control_client.post(
            '/api/v1/trading/control/reset',
            headers={'X-Admin-Password': ADMIN_PW},
        )
        assert r.status_code == 200

    def test_returns_success(self, control_client):
        r = control_client.post(
            '/api/v1/trading/control/reset',
            headers={'X-Admin-Password': ADMIN_PW},
        )
        assert r.get_json()['status'] == 'success'

    def test_returns_default_params(self, control_client):
        r = control_client.post(
            '/api/v1/trading/control/reset',
            headers={'X-Admin-Password': ADMIN_PW},
        )
        params = r.get_json()['params']
        assert 'sections' in params
        assert 'version' in params

    def test_overwrites_custom_values(self, control_env, control_client):
        modified = json.loads(json.dumps(SAMPLE_CONTROL))
        modified['sections']['storm_generation']['event_window_hours'] = 999
        control_client.post(
            '/api/v1/trading/control/params',
            data=json.dumps(modified),
            headers=_auth_headers(),
        )
        control_client.post(
            '/api/v1/trading/control/reset',
            headers={'X-Admin-Password': ADMIN_PW},
        )
        r = control_client.get('/api/v1/trading/control/params')
        data = r.get_json()
        import config.port as cp
        assert data['params']['sections']['storm_generation']['event_window_hours'] == cp.EVENT_WINDOW_HOURS

    def test_reset_file_persisted(self, control_env, control_client):
        control_client.post(
            '/api/v1/trading/control/reset',
            headers={'X-Admin-Password': ADMIN_PW},
        )
        p = control_env['input_dir'] / 'storm_control.json'
        assert p.exists()
        saved = json.loads(p.read_text())
        assert saved['version'] == '1.0.0'
        assert len(saved['sections']) == 5


# ---------------------------------------------------------------------------
# Admin password gate
# ---------------------------------------------------------------------------

class TestRbacGate:
    """Mutating endpoints are gated by @require('Func003', ...) (WP5): 401 if not
    signed in, 403 without the Func003 capability. Replaces the retired admin-password
    gate. The conftest autouse grants capability by default; these tests override it."""

    def test_save_401_when_unauthenticated(self, control_client, monkeypatch):
        from routes import _rbac
        monkeypatch.setattr(_rbac, "_resolver", lambda: None)
        r = control_client.post(
            '/api/v1/trading/control/params',
            data=json.dumps(SAMPLE_CONTROL),
            content_type='application/json',
        )
        assert r.status_code == 401

    def test_save_403_without_capability(self, control_client, monkeypatch):
        monkeypatch.setattr("database.check_permission", lambda u, f, a: False)
        r = control_client.post(
            '/api/v1/trading/control/params',
            data=json.dumps(SAMPLE_CONTROL),
            content_type='application/json',
        )
        assert r.status_code == 403

    def test_reset_401_when_unauthenticated(self, control_client, monkeypatch):
        from routes import _rbac
        monkeypatch.setattr(_rbac, "_resolver", lambda: None)
        assert control_client.post('/api/v1/trading/control/reset').status_code == 401

    def test_reset_403_without_capability(self, control_client, monkeypatch):
        monkeypatch.setattr("database.check_permission", lambda u, f, a: False)
        assert control_client.post('/api/v1/trading/control/reset').status_code == 403

    def test_get_still_works_without_auth(self, control_client, monkeypatch):
        """GET remains public — only mutating endpoints are gated."""
        from routes import _rbac
        monkeypatch.setattr(_rbac, "_resolver", lambda: None)
        r = control_client.get('/api/v1/trading/control/params')
        assert r.status_code == 200
