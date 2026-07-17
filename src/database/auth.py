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

"""Public RBAC API (WP5) — application-level permission checks + admin management.

Backed directly by Postgres: the RBAC tables are not catchment artifacts, so they
do not go through the file/pg backend abstraction. Re-exported from ``database``.
See docs/db_users_and_permissions.md.
"""

from config.auth import ADMIN_FUNCTION, FUNCTIONS
from database._pg._auth import (  # noqa: F401  (re-exported)
    check_permission,
    create_user,
    get_password_hash,
    get_user,
    get_user_permissions,
    list_functions,
    list_users,
    seed_functions,
    set_password_hash,
    set_permission,
    set_user_active,
)


def seed_function_registry() -> None:
    """Idempotently load the canonical config.auth.FUNCTIONS into the function table."""
    seed_functions(FUNCTIONS)


def is_admin(username) -> bool:
    """True if the user holds any capability on the Admin function (Func000)."""
    return check_permission(username, ADMIN_FUNCTION, "read")
