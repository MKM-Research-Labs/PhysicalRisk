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

"""WP5 local-account auth — password hashing, login/logout/me, bootstrap admin.
The database RBAC calls are stubbed, so these need no live Postgres."""

import pytest
from flask import Flask

from routes import auth
from routes._passwords import hash_password, password_matches

# --- password hashing (pure) ------------------------------------------------

def test_hash_and_match_roundtrip():
    h = hash_password("s3cret")
    assert h != "s3cret"  # not stored in clear
    assert password_matches("s3cret", h) is True
    assert password_matches("wrong", h) is False


def test_password_matches_empty_hash_is_false():
    assert password_matches("anything", None) is False
    assert password_matches("anything", "") is False


# --- login / logout / me blueprint ------------------------------------------

@pytest.fixture
def client():
    app = Flask(__name__)
    app.secret_key = "test"  # noqa: S105
    app.register_blueprint(auth.auth_bp)
    return app.test_client()


def test_login_success_sets_session(client, monkeypatch):
    stored = hash_password("pw")
    monkeypatch.setattr("database.get_password_hash", lambda u: stored)
    resp = client.post("/auth/login", json={"username": "alice", "password": "pw"})
    assert resp.status_code == 200
    assert resp.get_json()["username"] == "alice"
    # session now carries the user -> /auth/me sees it
    monkeypatch.setattr("database.is_admin", lambda u: True)
    monkeypatch.setattr("database.get_user_permissions", lambda u: {"Func001": {}})
    me = client.get("/auth/me")
    assert me.status_code == 200
    body = me.get_json()
    assert body["username"] == "alice" and body["is_admin"] is True


def test_login_bad_password_401(client, monkeypatch):
    monkeypatch.setattr("database.get_password_hash", lambda u: hash_password("right"))
    resp = client.post("/auth/login", json={"username": "alice", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_user_401(client, monkeypatch):
    monkeypatch.setattr("database.get_password_hash", lambda u: None)
    resp = client.post("/auth/login", json={"username": "ghost", "password": "x"})
    assert resp.status_code == 401


def test_login_missing_fields_400(client):
    assert client.post("/auth/login", json={"username": "a"}).status_code == 400
    assert client.post("/auth/login", json={}).status_code == 400


def test_me_unauthenticated_401(client):
    assert client.get("/auth/me").status_code == 401


def test_logout_clears_session(client, monkeypatch):
    monkeypatch.setattr("database.get_password_hash", lambda u: hash_password("pw"))
    client.post("/auth/login", json={"username": "alice", "password": "pw"})
    assert client.post("/auth/logout").status_code == 200
    assert client.get("/auth/me").status_code == 401


# --- helpers ----------------------------------------------------------------

def test_login_user_helper(monkeypatch):
    monkeypatch.setattr("database.get_password_hash", lambda u: hash_password("pw"))
    assert auth.login_user("alice", "pw") is True
    assert auth.login_user("alice", "nope") is False


def test_set_password_hashes_before_store(monkeypatch):
    captured = {}
    monkeypatch.setattr("database.set_password_hash",
                        lambda u, h, **k: captured.update(user=u, hash=h))
    auth.set_password("alice", "pw")
    assert captured["user"] == "alice"
    assert password_matches("pw", captured["hash"])  # stored value is a hash


# --- bootstrap admin --------------------------------------------------------

def _stub_db(monkeypatch, *, existing):
    calls = {"perms": [], "created": []}
    monkeypatch.setattr("database.seed_function_registry", lambda: calls.setdefault("seeded", True))
    monkeypatch.setattr("database.get_user", lambda u: {"username": u} if existing else None)
    monkeypatch.setattr("database.create_user",
                        lambda u, **k: calls["created"].append(u))
    monkeypatch.setattr("database.set_password_hash", lambda u, h, **k: None)
    monkeypatch.setattr("database.set_permission",
                        lambda u, f, **k: calls["perms"].append((u, f, k)))
    return calls


def test_ensure_bootstrap_admin_creates_and_grants(monkeypatch):
    calls = _stub_db(monkeypatch, existing=False)
    created = auth.ensure_bootstrap_admin("root", "pw")
    assert created is True
    assert calls["created"] == ["root"]
    assert calls["seeded"] is True
    user, func, flags = calls["perms"][0]
    assert (user, func) == ("root", "Func000")
    assert flags == {"read": True, "write": True, "create": True, "delete": True}


def test_ensure_bootstrap_admin_idempotent(monkeypatch):
    calls = _stub_db(monkeypatch, existing=True)
    assert auth.ensure_bootstrap_admin("root", "pw") is False
    assert calls["created"] == []  # not re-created
    assert calls["perms"]          # but grant still (re)applied


def test_maybe_bootstrap_from_env_noop_when_unset(monkeypatch):
    monkeypatch.delenv("MKM_BOOTSTRAP_ADMIN_USER", raising=False)
    monkeypatch.delenv("MKM_BOOTSTRAP_ADMIN_PASSWORD", raising=False)
    called = []
    monkeypatch.setattr(auth, "ensure_bootstrap_admin", lambda *a: called.append(a))
    auth.maybe_bootstrap_admin_from_env()
    assert called == []


def test_maybe_bootstrap_from_env_runs_when_set(monkeypatch):
    monkeypatch.setenv("MKM_BOOTSTRAP_ADMIN_USER", "root")
    monkeypatch.setenv("MKM_BOOTSTRAP_ADMIN_PASSWORD", "pw")
    called = []
    monkeypatch.setattr(auth, "ensure_bootstrap_admin",
                        lambda u, p: called.append((u, p)) or True)
    auth.maybe_bootstrap_admin_from_env()
    assert called == [("root", "pw")]


def test_maybe_bootstrap_from_env_swallows_errors(monkeypatch):
    monkeypatch.setenv("MKM_BOOTSTRAP_ADMIN_USER", "root")
    monkeypatch.setenv("MKM_BOOTSTRAP_ADMIN_PASSWORD", "pw")

    def _boom(*a):
        raise RuntimeError("pg down")

    monkeypatch.setattr(auth, "ensure_bootstrap_admin", _boom)
    auth.maybe_bootstrap_admin_from_env()  # must not raise
