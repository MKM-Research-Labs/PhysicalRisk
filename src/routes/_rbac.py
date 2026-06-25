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

"""RBAC route gates (WP5) — ``@require(func, action)`` and ``@require_admin``.

The enforcement half of WP5: given the acting user, check capability via the
``database`` RBAC API and return 401/403 otherwise. *Who* the acting user is comes
from a pluggable resolver (``set_current_user_resolver``) so the identity decision
(local password login vs SSO/OIDC) can be wired in later without touching these
decorators. Until login is wired, the default resolver reads ``flask.g.current_user``
/ ``session['username']`` — so these gates currently deny (401) unless a user is set.

These do NOT yet replace ``require_admin_password`` / ``data/.port_admin`` — that
swap happens once login lands. See docs/db_users_and_permissions.md.
"""

from functools import wraps

from flask import g, jsonify, session

import database
from config.auth import CRUD_ACTIONS

_resolver = None


def set_current_user_resolver(fn):
    """Install how the acting username is resolved from the request — the identity
    slice wires this to the chosen login mechanism. ``fn() -> username | None``.
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
