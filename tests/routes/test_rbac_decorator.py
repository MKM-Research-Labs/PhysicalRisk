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

"""WP5 RBAC route gates — @require / @require_admin. The database RBAC calls are
stubbed, so these test the decorator logic alone (no live Postgres needed)."""

import pytest
from flask import Flask, g

from routes import _rbac


@pytest.fixture
def app():
    application = Flask(__name__)
    application.secret_key = "test"  # noqa: S105 — session signing for the test only

    @application.route("/trade", methods=["POST"])
    @_rbac.require("Func003", "create")
    def trade():
        return {"ok": True}

    @application.route("/admin", methods=["POST"])
    @_rbac.require_admin
    def admin():
        return {"ok": True}

    return application


@pytest.fixture(autouse=True)
def _reset_resolver():
    yield
    _rbac.set_current_user_resolver(None)


def _as(user):
    _rbac.set_current_user_resolver(lambda: user)


def test_require_unknown_action_raises_at_decoration():
    with pytest.raises(ValueError):
        _rbac.require("Func003", "teleport")


def test_require_401_when_unauthenticated(app):
    _as(None)
    resp = app.test_client().post("/trade")
    assert resp.status_code == 401


def test_require_403_without_capability(app, monkeypatch):
    _as("bob")
    monkeypatch.setattr("database.check_permission", lambda u, f, a: False)
    resp = app.test_client().post("/trade")
    assert resp.status_code == 403
    assert "Func003" in resp.get_json()["message"]


def test_require_allows_with_capability(app, monkeypatch):
    _as("bob")
    seen = {}

    def _check(user, func, action):
        seen.update(user=user, func=func, action=action)
        return True

    monkeypatch.setattr("database.check_permission", _check)
    resp = app.test_client().post("/trade")
    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True}
    assert seen == {"user": "bob", "func": "Func003", "action": "create"}


def test_require_admin_401_403_and_allow(app, monkeypatch):
    _as(None)
    assert app.test_client().post("/admin").status_code == 401

    _as("carol")
    monkeypatch.setattr("database.is_admin", lambda u: False)
    assert app.test_client().post("/admin").status_code == 403

    monkeypatch.setattr("database.is_admin", lambda u: True)
    assert app.test_client().post("/admin").status_code == 200


def test_get_current_user_default_reads_g(app):
    with app.test_request_context("/"):
        g.current_user = "dave"
        assert _rbac.get_current_user() == "dave"


def test_get_current_user_default_reads_session(app):
    with app.test_request_context("/") as ctx:
        ctx.session["username"] = "erin"
        assert _rbac.get_current_user() == "erin"


def test_get_current_user_none_when_absent(app):
    with app.test_request_context("/"):
        assert _rbac.get_current_user() is None


def test_resolver_overrides_default():
    _as("frank")
    assert _rbac.get_current_user() == "frank"
