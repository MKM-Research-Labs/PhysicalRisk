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

"""RBAC route gates (WP5) — ``@require(func, action)`` and ``@require_admin``.

The enforcement half of WP5: given the acting user, check capability via the
``database`` RBAC API and return 401/403 otherwise. *Who* the acting user is comes
from a pluggable resolver (``set_current_user_resolver``) so the identity source
(local password login vs SSO/OIDC) can change without touching these decorators; the
default reads ``flask.g.current_user`` / ``session['username']``, which ``routes.auth``
login populates.

These gates have **replaced** the retired ``require_admin_password`` /
``X-Admin-Password`` web gate on the 16 mutating trading/prs endpoints (WP5.1). See
docs/db_users_and_permissions.md.
"""

from functools import wraps

from flask import g, jsonify, session

import database
from config.auth import CRUD_ACTIONS

_resolver = None


def set_current_user_resolver(fn):
    """Install how the acting username is resolved from the request — the identity
    slice wired this to local-password login (``routes.auth``); ``fn() -> username | None``.
    Pass ``None`` to restore the default (Flask ``g`` / session)."""
    global _resolver
    _resolver = fn


def get_current_user():
    """The acting username, or ``None`` if unauthenticated. Default reads
    ``flask.g.current_user`` then ``session['username']``; overridable above."""
    if _resolver is not None:
        return _resolver()
    return getattr(g, "current_user", None) or session.get("username")


def _deny(message, code):
    return jsonify({"status": "error", "message": message}), code


def require(function_code, action):
    """Decorator: 401 if unauthenticated, 403 unless the acting user holds
    ``action`` on ``function_code``, else run the view."""
    if action not in CRUD_ACTIONS:
        raise ValueError(f"unknown action: {action!r}")

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                return _deny("Authentication required.", 401)
            if not database.check_permission(user, function_code, action):
                return _deny(
                    f"Forbidden: requires {action} on {function_code}.", 403)
            return view_func(*args, **kwargs)

        return wrapper

    return decorator


def require_admin(view_func):
    """Decorator: 401 if unauthenticated, 403 unless the acting user is an Admin
    (capability on Func000), else run the view."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return _deny("Authentication required.", 401)
        if not database.is_admin(user):
            return _deny("Forbidden: admin only.", 403)
        return view_func(*args, **kwargs)

    return wrapper
