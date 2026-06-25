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

"""RBAC function registry + capability vocabulary (WP5).

Stable function codes (``FuncNNN``) and the four CRUD capabilities. Adding a
function later is one entry here + a seed into the ``function`` table — no schema
change. See docs/db_users_and_permissions.md.
"""

# The Admin function — capability on it grants user/permission management.
ADMIN_FUNCTION = "Func000"

# The only four capabilities. Any of write/create/delete implies read (enforced in
# the permission check), so "you can't act on what you can't see".
CRUD_ACTIONS = ("read", "write", "create", "delete")

# (code, display name, sort_order). Only Func000–003 are live today; Func004+ are
# reserved placeholders, filled in as each area rolls out.
FUNCTIONS = (
    (ADMIN_FUNCTION, "Admin — user & permission management", 0),
    ("Func001", "Create synthetic portfolio", 1),
    ("Func002", "Upload real portfolio", 2),
    ("Func003", "Trade PRS", 3),
)
