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

"""WP5 RBAC permission logic — live Postgres, each test in a rolled-back transaction."""

import pytest

import database
from config.auth import ADMIN_FUNCTION, FUNCTIONS
from database._pg import engine as _eng


def _postgres_available() -> bool:
    try:
        _eng.reset_engine()
        from sqlalchemy import text
        with _eng.get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        _eng.reset_engine()


pytestmark = pytest.mark.skipif(not _postgres_available(), reason="no live Postgres")


@pytest.fixture(autouse=True)
def _rbac_txn():
    """Each test runs in a rolled-back pg transaction so nothing persists. Under
    MKM_TEST_BACKEND=pg the autouse pg-isolation already bound one — reuse it;
    otherwise (file backend, pg available) set up our own."""
    if _eng._test_connection is not None:
        yield
        return
    _eng.reset_engine()
    conn = _eng.get_engine().connect()
    trans = conn.begin()
    _eng.bind_test_connection(conn)
    try:
        yield
    finally:
        _eng.bind_test_connection(None)
        trans.rollback()
        conn.close()
        _eng.reset_engine()


def test_seed_functions_idempotent_and_list():
    database.seed_function_registry()
    database.seed_function_registry()  # idempotent
    codes = [f["code"] for f in database.list_functions()]
    assert ADMIN_FUNCTION in codes
    assert codes == sorted(codes, key=lambda c: c)  # admin sorts first (order 0)
    assert len(codes) == len(FUNCTIONS)


def test_create_and_get_user():
    database.create_user("alice", display_name="Alice")
    u = database.get_user("alice")
    assert u["username"] == "alice"
    assert u["display_name"] == "Alice"
    assert u["is_active"] is True
    assert database.get_user("nobody") is None


def test_set_permission_and_check_each_action():
    database.seed_function_registry()
    database.create_user("bob")
    database.set_permission("bob", "Func003", read=True, write=True,
                            create=True, delete=True)
    for action in ("read", "write", "create", "delete"):
        assert database.check_permission("bob", "Func003", action) is True
    # No row for Func001 -> denied.
    assert database.check_permission("bob", "Func001", "read") is False


def test_write_create_delete_imply_read():
    database.seed_function_registry()
    database.create_user("carol")
    database.set_permission("carol", "Func001", create=True)  # create only
    assert database.check_permission("carol", "Func001", "read") is True
    assert database.check_permission("carol", "Func001", "create") is True
    assert database.check_permission("carol", "Func001", "write") is False


def test_read_only_grant_denies_mutations():
    database.seed_function_registry()
    database.create_user("dave")
    database.set_permission("dave", "Func003", read=True)
    assert database.check_permission("dave", "Func003", "read") is True
    for action in ("write", "create", "delete"):
        assert database.check_permission("dave", "Func003", action) is False


def test_missing_user_and_unknown_action():
    assert database.check_permission("ghost", "Func001", "read") is False
    with pytest.raises(ValueError):
        database.check_permission("ghost", "Func001", "teleport")


def test_inactive_user_denied():
    database.seed_function_registry()
    database.create_user("evan")
    database.set_permission("evan", "Func001", read=True)
    assert database.check_permission("evan", "Func001", "read") is True
    database.set_user_active("evan", False)
    assert database.check_permission("evan", "Func001", "read") is False


def test_is_admin():
    database.seed_function_registry()
    database.create_user("admin1")
    database.create_user("plain")
    database.set_permission("admin1", ADMIN_FUNCTION, read=True, write=True,
                            create=True, delete=True)
    assert database.is_admin("admin1") is True
    assert database.is_admin("plain") is False


def test_get_user_permissions():
    database.seed_function_registry()
    database.create_user("fran")
    database.set_permission("fran", "Func001", read=True, write=True)
    database.set_permission("fran", "Func003", read=True)
    perms = database.get_user_permissions("fran")
    assert perms["Func001"] == {"read": True, "write": True,
                                "create": False, "delete": False}
    assert perms["Func003"]["read"] is True
    assert database.get_user_permissions("nobody") == {}


def test_set_permission_unknown_user_raises():
    database.seed_function_registry()
    with pytest.raises(ValueError):
        database.set_permission("nobody", "Func001", read=True)


def test_set_user_active_unknown_user_raises():
    with pytest.raises(ValueError):
        database.set_user_active("nobody", False)


def test_list_functions_active_only_filter():
    database.seed_function_registry()
    all_fns = database.list_functions(active_only=False)
    active = database.list_functions(active_only=True)
    assert len(all_fns) >= len(active)
    assert all(f["is_active"] for f in active)


def test_list_users():
    database.create_user("amy")
    database.create_user("zed")
    names = [u["username"] for u in database.list_users()]
    assert "amy" in names and "zed" in names
    assert names == sorted(names)  # ordered by username


def test_set_and_get_password_hash():
    database.create_user("gita")
    assert database.get_password_hash("gita") is None
    database.set_password_hash("gita", "HASHED")
    assert database.get_password_hash("gita") == "HASHED"


def test_get_password_hash_inactive_and_unknown_return_none():
    database.create_user("ivan")
    database.set_password_hash("ivan", "HASHED")
    database.set_user_active("ivan", False)
    assert database.get_password_hash("ivan") is None      # inactive
    assert database.get_password_hash("nobody") is None     # unknown


def test_set_password_hash_unknown_user_raises():
    with pytest.raises(ValueError):
        database.set_password_hash("nobody", "HASHED")


def test_bootstrap_admin_then_login_end_to_end():
    """Real pg path: ensure_bootstrap_admin -> login_user verifies + is_admin."""
    from routes import auth
    created = auth.ensure_bootstrap_admin("root", "s3cret")
    assert created is True
    assert auth.login_user("root", "s3cret") is True
    assert auth.login_user("root", "wrong") is False
    assert database.is_admin("root") is True
    # idempotent re-run keeps it working
    assert auth.ensure_bootstrap_admin("root", "s3cret") is False
    assert database.is_admin("root") is True
