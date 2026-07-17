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

"""Application-level RBAC tables (WP5) — see docs/db_users_and_permissions.md.

Application-managed RBAC, NOT Postgres GRANTs: an Admin ticks Read/Write/Create/
Delete per (user, function). The web app connects as a single service login and
enforces these rows in app logic via the database utility — so the Admin manages
access live, no DBA. These share the same ``Base`` as the port tables, so one
``alembic upgrade`` provisions everything.
"""

from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ._models import Base


class Function(Base):
    """A gateable area of the app, addressed by a stable code (``Func001``). Adding a
    function later is one INSERT here — no schema change."""

    __tablename__ = "function"

    code: Mapped[str] = mapped_column(primary_key=True)          # e.g. 'Func001'
    name: Mapped[str]
    description: Mapped[str | None] = mapped_column(default=None)
    is_active: Mapped[bool] = mapped_column(default=True)
    sort_order: Mapped[int] = mapped_column(default=0)


class AppUser(Base):
    """A person who can act in the app — NOT the ``svc_app`` Postgres login."""

    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(default=None)
    is_active: Mapped[bool] = mapped_column(default=True)
    # Identity source is an open decision — local password hash OR an SSO subject.
    password_hash: Mapped[str | None] = mapped_column(default=None)
    sso_subject: Mapped[str | None] = mapped_column(default=None)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("app_user.id"), default=None)
    created_at: Mapped[datetime | None] = mapped_column(default=None)


class Permission(Base):
    """One row per (user, function) holding the four CRUD flags. A missing row means
    no access; any of W/C/D implies R is enforced in the check logic."""

    __tablename__ = "permission"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id"), primary_key=True)
    function_code: Mapped[str] = mapped_column(
        ForeignKey("function.code"), primary_key=True)
    can_read: Mapped[bool] = mapped_column(default=False)
    can_write: Mapped[bool] = mapped_column(default=False)
    can_create: Mapped[bool] = mapped_column(default=False)
    can_delete: Mapped[bool] = mapped_column(default=False)


class AuditLog(Base):
    """Append-only record of admin actions (user created, permission changed, …), so
    permission changes are themselves auditable."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("app_user.id"), default=None)
    action: Mapped[str]                                          # e.g. 'permission.set'
    function_code: Mapped[str | None] = mapped_column(default=None)
    target: Mapped[str | None] = mapped_column(default=None)     # e.g. target username
    ts: Mapped[datetime | None] = mapped_column(default=None)
