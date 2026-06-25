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

"""Application-level RBAC queries (WP5) — the only place that touches the RBAC tables.

Pure Postgres (RBAC is not a catchment artifact, so it does not go through the
file/pg backend abstraction): the web app connects as a single service login and
checks these rows in app logic. The public surface is re-exported from
``database.auth``. See docs/db_users_and_permissions.md.
"""

from datetime import datetime, timezone

from sqlalchemy import select

from ._auth_models import AppUser, AuditLog, Function, Permission
from .engine import get_session

# action name -> the column that grants it directly.
_ACTION_COLUMN = {
    "read": "can_read", "write": "can_write",
    "create": "can_create", "delete": "can_delete",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def seed_functions(functions) -> None:
    """Upsert the function registry rows (idempotent): insert missing, refresh name
    and sort order on existing. ``functions`` = iterable of (code, name, sort_order)."""
    with get_session() as session:
        for code, name, sort_order in functions:
            row = session.get(Function, code)
            if row is None:
                session.add(Function(code=code, name=name, sort_order=sort_order,
                                     is_active=True))
            else:
                row.name, row.sort_order = name, sort_order
        session.commit()


def list_functions(active_only: bool = True) -> list:
    """The function registry, ordered for the admin grid."""
    with get_session() as session:
        rows = session.scalars(
            select(Function).order_by(Function.sort_order, Function.code)).all()
        return [{"code": r.code, "name": r.name, "is_active": r.is_active,
                 "sort_order": r.sort_order}
                for r in rows if r.is_active or not active_only]


def create_user(username, *, display_name=None, created_by=None,
                password_hash=None, sso_subject=None) -> int:
    """Create an app user and return its id."""
    with get_session() as session:
        user = AppUser(username=username, display_name=display_name,
                       created_by=created_by, password_hash=password_hash,
                       sso_subject=sso_subject, is_active=True, created_at=_now())
        session.add(user)
        session.commit()
        return user.id


def get_user(username) -> dict | None:
    """A user's public fields, or None if absent."""
    with get_session() as session:
        user = session.scalar(select(AppUser).where(AppUser.username == username))
        if user is None:
            return None
        return {"id": user.id, "username": user.username,
                "display_name": user.display_name, "is_active": user.is_active}


def set_user_active(username, is_active: bool, *, actor=None) -> None:
    """Enable/disable a user (a disabled user fails every permission check)."""
    with get_session() as session:
        user = session.scalar(select(AppUser).where(AppUser.username == username))
        if user is None:
            raise ValueError(f"unknown user: {username}")
        user.is_active = is_active
        session.add(AuditLog(actor_user_id=actor,
                             action="user.enable" if is_active else "user.disable",
                             target=username, ts=_now()))
        session.commit()


def set_permission(username, function_code, *, read=False, write=False,
                   create=False, delete=False, actor=None) -> None:
    """Set a user's four CRUD flags on a function (upsert) and audit the change."""
    with get_session() as session:
        user = session.scalar(select(AppUser).where(AppUser.username == username))
        if user is None:
            raise ValueError(f"unknown user: {username}")
        perm = session.get(Permission, (user.id, function_code))
        if perm is None:
            perm = Permission(user_id=user.id, function_code=function_code)
            session.add(perm)
        perm.can_read, perm.can_write = read, write
        perm.can_create, perm.can_delete = create, delete
        session.add(AuditLog(actor_user_id=actor, action="permission.set",
                             function_code=function_code, target=username, ts=_now()))
        session.commit()


def check_permission(username, function_code, action) -> bool:
    """True iff the user is active and holds ``action`` on ``function_code``.

    Any of write/create/delete implies read. A missing user, inactive user, or
    missing permission row all deny."""
    if action not in _ACTION_COLUMN:
        raise ValueError(f"unknown action: {action!r}")
    with get_session() as session:
        user = session.scalar(
            select(AppUser).where(AppUser.username == username,
                                  AppUser.is_active.is_(True)))
        if user is None:
            return False
        perm = session.get(Permission, (user.id, function_code))
        if perm is None:
            return False
        if action == "read":
            return bool(perm.can_read or perm.can_write
                        or perm.can_create or perm.can_delete)
        return bool(getattr(perm, _ACTION_COLUMN[action]))


def get_user_permissions(username) -> dict:
    """All of a user's permission rows as ``{function_code: {read, write, create,
    delete}}`` (empty if the user is unknown)."""
    with get_session() as session:
        user = session.scalar(select(AppUser).where(AppUser.username == username))
        if user is None:
            return {}
        perms = session.scalars(
            select(Permission).where(Permission.user_id == user.id)).all()
        return {p.function_code: {"read": p.can_read, "write": p.can_write,
                                  "create": p.can_create, "delete": p.can_delete}
                for p in perms}
