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

"""Public RBAC API (WP5) — application-level permission checks + admin management.

Backed directly by Postgres: the RBAC tables are not catchment artifacts, so they
do not go through the file/pg backend abstraction. Re-exported from ``database``.
See docs/db_users_and_permissions.md.
"""

from config.auth import ADMIN_FUNCTION, FUNCTIONS
from database._pg._auth import (  # noqa: F401  (re-exported)
    check_permission,
    create_user,
    get_user,
    get_user_permissions,
    list_functions,
    seed_functions,
    set_permission,
    set_user_active,
)


def seed_function_registry() -> None:
    """Idempotently load the canonical config.auth.FUNCTIONS into the function table."""
    seed_functions(FUNCTIONS)


def is_admin(username) -> bool:
    """True if the user holds any capability on the Admin function (Func000)."""
    return check_permission(username, ADMIN_FUNCTION, "read")
