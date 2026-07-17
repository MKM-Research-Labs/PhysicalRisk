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

"""Local-account login for WP5 RBAC.

Verifies credentials against the per-user hash and, on success, records the acting
username in the Flask session — which is exactly what ``_rbac.get_current_user``
reads, so the ``@require`` gates light up. This is the local-password identity
source; an SSO/OIDC variant would set the same session key from the IdP subject.
"""

import logging
import os

from flask import Blueprint, jsonify, request, session

import database
from config.auth import ADMIN_FUNCTION

from ._passwords import hash_password, password_matches

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


def login_user(username, password) -> bool:
    """True iff ``password`` matches the stored hash for the (active) user."""
    return password_matches(password, database.get_password_hash(username))


def set_password(username, password, *, actor=None) -> None:
    """Hash and store a user's password (the only path plaintext takes to the DB)."""
    database.set_password_hash(username, hash_password(password), actor=actor)


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"status": "error",
                        "message": "username and password required"}), 400
    if not login_user(username, password):
        return jsonify({"status": "error", "message": "invalid credentials"}), 401
    session["username"] = username
    return jsonify({"status": "ok", "username": username}), 200


@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    return jsonify({"status": "ok"}), 200


@auth_bp.route("/auth/me", methods=["GET"])
def me():
    username = session.get("username")
    if not username:
        return jsonify({"status": "error", "message": "not authenticated"}), 401
    return jsonify({"status": "ok", "username": username,
                    "is_admin": database.is_admin(username),
                    "permissions": database.get_user_permissions(username)}), 200


def ensure_bootstrap_admin(username, password) -> bool:
    """Idempotently ensure a first Admin exists: seed the function registry, create
    the user if absent, (re)set their password, and grant full Func000. Returns True
    if the user was newly created. Safe to call repeatedly."""
    database.seed_function_registry()
    created = database.get_user(username) is None
    if created:
        database.create_user(username, display_name=username)
    set_password(username, password)
    database.set_permission(username, ADMIN_FUNCTION, read=True, write=True,
                            create=True, delete=True)
    return created


def maybe_bootstrap_admin_from_env() -> None:
    """If MKM_BOOTSTRAP_ADMIN_USER / _PASSWORD are set, ensure that admin exists.
    Defensive — never lets a bootstrap hiccup take down server start."""
    username = os.environ.get("MKM_BOOTSTRAP_ADMIN_USER")
    password = os.environ.get("MKM_BOOTSTRAP_ADMIN_PASSWORD")
    if not username or not password:
        return
    try:
        created = ensure_bootstrap_admin(username, password)
        logger.info("Bootstrap admin %r %s",
                    username, "created" if created else "ensured")
    except Exception:  # noqa: BLE001 — bootstrap must never block server start
        logger.exception("Bootstrap admin setup failed for %r", username)
