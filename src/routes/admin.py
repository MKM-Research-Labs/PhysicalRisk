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

"""WP5 Admin UI — the user × function CRUD grid + its JSON API.

Every data endpoint is gated by ``@require_admin`` (capability on Func000). The page
itself is an unguarded shell; its JS authenticates via ``/auth/*`` and then calls the
gated API, so a non-admin simply sees access-denied. See docs/db_users_and_permissions.md.
"""

import logging

from flask import Blueprint, jsonify, request, send_file

import database
from config import config

from ._rbac import get_current_user, require_admin
from .auth import set_password

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__)

_ASSETS = config.get_static_dir() / "admin"


def _actor_id():
    """The acting admin's user id (for audit attribution), or None."""
    user = get_current_user()
    record = database.get_user(user) if user else None
    return record["id"] if record else None


@admin_bp.route("/admin")
def admin_page():
    return send_file(_ASSETS / "admin.html")


@admin_bp.route("/admin/admin.js")
def admin_js():
    return send_file(_ASSETS / "admin.js", mimetype="application/javascript")


@admin_bp.route("/admin/api/functions")
@require_admin
def api_functions():
    return jsonify({"functions": database.list_functions(active_only=False)})


@admin_bp.route("/admin/api/users")
@require_admin
def api_users():
    users = database.list_users()
    for user in users:
        user["permissions"] = database.get_user_permissions(user["username"])
    return jsonify({"users": users})


@admin_bp.route("/admin/api/users", methods=["POST"])
@require_admin
def api_create_user():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"status": "error",
                        "message": "username and password required"}), 400
    if database.get_user(username) is not None:
        return jsonify({"status": "error", "message": "user already exists"}), 409
    actor = _actor_id()
    database.create_user(username, display_name=data.get("display_name") or username,
                         created_by=actor)
    set_password(username, password, actor=actor)
    return jsonify({"status": "ok", "username": username}), 201


@admin_bp.route("/admin/api/users/<username>/password", methods=["POST"])
@require_admin
def api_set_password(username):
    data = request.get_json(silent=True) or {}
    password = data.get("password") or ""
    if not password:
        return jsonify({"status": "error", "message": "password required"}), 400
    if database.get_user(username) is None:
        return jsonify({"status": "error", "message": "unknown user"}), 404
    set_password(username, password, actor=_actor_id())
    return jsonify({"status": "ok"}), 200


@admin_bp.route("/admin/api/users/<username>/active", methods=["POST"])
@require_admin
def api_set_active(username):
    data = request.get_json(silent=True) or {}
    is_active = bool(data.get("is_active"))
    try:
        database.set_user_active(username, is_active, actor=_actor_id())
    except ValueError:
        return jsonify({"status": "error", "message": "unknown user"}), 404
    return jsonify({"status": "ok", "is_active": is_active}), 200


@admin_bp.route("/admin/api/permissions", methods=["POST"])
@require_admin
def api_set_permission():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    function_code = data.get("function_code")
    if not username or not function_code:
        return jsonify({"status": "error",
                        "message": "username and function_code required"}), 400
    try:
        database.set_permission(
            username, function_code,
            read=bool(data.get("read")), write=bool(data.get("write")),
            create=bool(data.get("create")), delete=bool(data.get("delete")),
            actor=_actor_id())
    except ValueError:
        return jsonify({"status": "error", "message": "unknown user"}), 404
    return jsonify({"status": "ok"}), 200
