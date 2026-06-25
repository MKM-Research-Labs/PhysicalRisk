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

"""WP5 Admin UI routes — gated API + page assets. Database calls stubbed (no pg)."""

import pytest
from flask import Flask

from routes import _rbac, admin


@pytest.fixture
def client():
    app = Flask(__name__)
    app.secret_key = "test"  # noqa: S105
    app.register_blueprint(admin.admin_bp)
    return app.test_client()


@pytest.fixture(autouse=True)
def _as_admin(monkeypatch):
    """Acting user is an admin unless a test overrides it."""
    _rbac.set_current_user_resolver(lambda: "root")
    monkeypatch.setattr("database.is_admin", lambda u: True)
    monkeypatch.setattr("database.get_user", lambda u: {"id": 1, "username": u})
    yield
    _rbac.set_current_user_resolver(None)


# --- gating -----------------------------------------------------------------

def test_api_requires_admin(client, monkeypatch):
    monkeypatch.setattr("database.is_admin", lambda u: False)
    assert client.get("/admin/api/users").status_code == 403


def test_api_requires_auth(client):
    _rbac.set_current_user_resolver(lambda: None)
    assert client.get("/admin/api/users").status_code == 401


# --- page assets ------------------------------------------------------------

def test_admin_page_served(client):
    resp = client.get("/admin")
    assert resp.status_code == 200
    assert b"Permission Admin" in resp.data


def test_admin_js_served(client):
    resp = client.get("/admin/admin.js")
    assert resp.status_code == 200
    assert "javascript" in resp.headers["Content-Type"]


# --- read endpoints ---------------------------------------------------------

def test_api_functions(client, monkeypatch):
    monkeypatch.setattr("database.list_functions",
                        lambda active_only=True: [{"code": "Func000", "name": "Admin"}])
    body = client.get("/admin/api/functions").get_json()
    assert body["functions"][0]["code"] == "Func000"


def test_api_users_embeds_permissions(client, monkeypatch):
    monkeypatch.setattr("database.list_users",
                        lambda: [{"id": 2, "username": "bob", "is_active": True}])
    monkeypatch.setattr("database.get_user_permissions",
                        lambda u: {"Func003": {"read": True}})
    users = client.get("/admin/api/users").get_json()["users"]
    assert users[0]["permissions"]["Func003"]["read"] is True


# --- create user ------------------------------------------------------------

def test_create_user_success(client, monkeypatch):
    monkeypatch.setattr("database.get_user", lambda u: None)  # doesn't exist yet
    created = {}
    monkeypatch.setattr("database.create_user",
                        lambda u, **k: created.update(user=u, kw=k))
    monkeypatch.setattr("routes.admin.set_password", lambda u, p, **k: created.update(pw=True))
    resp = client.post("/admin/api/users",
                       json={"username": "carol", "password": "pw"})
    assert resp.status_code == 201
    assert created["user"] == "carol" and created["pw"] is True


def test_create_user_missing_fields(client):
    assert client.post("/admin/api/users", json={"username": "x"}).status_code == 400


def test_create_user_duplicate(client, monkeypatch):
    monkeypatch.setattr("database.get_user", lambda u: {"id": 9, "username": u})
    resp = client.post("/admin/api/users", json={"username": "bob", "password": "pw"})
    assert resp.status_code == 409


# --- set password -----------------------------------------------------------

def test_set_password_success(client, monkeypatch):
    seen = {}
    monkeypatch.setattr("routes.admin.set_password", lambda u, p, **k: seen.update(u=u, p=p))
    resp = client.post("/admin/api/users/bob/password", json={"password": "new"})
    assert resp.status_code == 200 and seen == {"u": "bob", "p": "new"}


def test_set_password_missing(client):
    assert client.post("/admin/api/users/bob/password", json={}).status_code == 400


def test_set_password_unknown_user(client, monkeypatch):
    monkeypatch.setattr("database.get_user", lambda u: None)
    resp = client.post("/admin/api/users/ghost/password", json={"password": "x"})
    assert resp.status_code == 404


# --- enable / disable -------------------------------------------------------

def test_set_active_success(client, monkeypatch):
    seen = {}
    monkeypatch.setattr("database.set_user_active",
                        lambda u, a, **k: seen.update(u=u, a=a))
    resp = client.post("/admin/api/users/bob/active", json={"is_active": False})
    assert resp.status_code == 200 and seen == {"u": "bob", "a": False}


def test_set_active_unknown_user(client, monkeypatch):
    def _raise(u, a, **k):
        raise ValueError("unknown")
    monkeypatch.setattr("database.set_user_active", _raise)
    resp = client.post("/admin/api/users/ghost/active", json={"is_active": True})
    assert resp.status_code == 404


# --- set permission ---------------------------------------------------------

def test_set_permission_success(client, monkeypatch):
    seen = {}
    monkeypatch.setattr("database.set_permission",
                        lambda u, f, **k: seen.update(u=u, f=f, flags=k))
    resp = client.post("/admin/api/permissions",
                       json={"username": "bob", "function_code": "Func003",
                             "read": True, "create": True})
    assert resp.status_code == 200
    assert seen["u"] == "bob" and seen["f"] == "Func003"
    assert seen["flags"]["read"] is True and seen["flags"]["create"] is True
    assert seen["flags"]["write"] is False and seen["flags"]["delete"] is False


def test_set_permission_missing_fields(client):
    assert client.post("/admin/api/permissions",
                       json={"username": "bob"}).status_code == 400


def test_set_permission_unknown_user(client, monkeypatch):
    def _raise(u, f, **k):
        raise ValueError("unknown")
    monkeypatch.setattr("database.set_permission", _raise)
    resp = client.post("/admin/api/permissions",
                       json={"username": "ghost", "function_code": "Func001"})
    assert resp.status_code == 404
