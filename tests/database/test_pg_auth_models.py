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

"""Pin the WP5 RBAC table shapes (function / app_user / permission / audit_log).
Application-level RBAC — see docs/db_users_and_permissions.md."""

from database._pg import AppUser, AuditLog, Function, Permission


def test_function_columns():
    cols = {c.name for c in Function.__table__.columns}
    assert cols == {"code", "name", "description", "is_active", "sort_order"}
    assert Function.__table__.c.code.primary_key


def test_app_user_columns():
    cols = {c.name for c in AppUser.__table__.columns}
    assert cols == {"id", "username", "display_name", "is_active",
                    "password_hash", "sso_subject", "created_by", "created_at"}
    assert AppUser.__table__.c.id.primary_key
    assert AppUser.__table__.c.username.unique


def test_permission_is_user_function_with_four_flags():
    pk = {c.name for c in Permission.__table__.primary_key.columns}
    assert pk == {"user_id", "function_code"}
    cols = {c.name for c in Permission.__table__.columns}
    assert {"can_read", "can_write", "can_create", "can_delete"} <= cols
    fk_targets = {fk.column.table.name for fk in Permission.__table__.foreign_keys}
    assert fk_targets == {"app_user", "function"}


def test_audit_log_columns_and_fk():
    cols = {c.name for c in AuditLog.__table__.columns}
    assert cols == {"id", "actor_user_id", "action", "function_code", "target", "ts"}
    assert AuditLog.__table__.c.id.primary_key
    fk_targets = {fk.column.table.name for fk in AuditLog.__table__.foreign_keys}
    assert fk_targets == {"app_user"}
