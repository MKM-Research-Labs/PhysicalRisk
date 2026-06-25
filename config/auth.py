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

import os

# Flask session-signing key. The login flow stores the acting username in the
# signed session cookie, so a key is required. MUST be overridden via
# ``MKM_SECRET_KEY`` in any real deployment — the default is for local dev only.
SECRET_KEY = os.getenv("MKM_SECRET_KEY", "mkm-dev-insecure-secret-change-me")

# Stable function codes — reference these symbols at gate sites
# (``@require(FUNC_TRADE_PRS, WRITE)``) instead of the raw "FuncNNN" literal, so a
# rename is one edit and "what gates X" is a symbol search, not a grep for strings.
FUNC_ADMIN = "Func000"
FUNC_CREATE_PORTFOLIO = "Func001"
FUNC_UPLOAD_PORTFOLIO = "Func002"
FUNC_TRADE_PRS = "Func003"

# The Admin function — capability on it grants user/permission management.
ADMIN_FUNCTION = FUNC_ADMIN

# The only four capabilities. Any of write/create/delete implies read (enforced in
# the permission check), so "you can't act on what you can't see". The unpacked
# names are for use at gate sites alongside the FUNC_* codes.
CRUD_ACTIONS = ("read", "write", "create", "delete")
READ, WRITE, CREATE, DELETE = CRUD_ACTIONS

# (code, display name, sort_order). Only Func000–003 are live today; Func004+ are
# reserved placeholders, filled in as each area rolls out.
FUNCTIONS = (
    (FUNC_ADMIN, "Admin — user & permission management", 0),
    (FUNC_CREATE_PORTFOLIO, "Create synthetic portfolio", 1),
    (FUNC_UPLOAD_PORTFOLIO, "Upload real portfolio", 2),
    (FUNC_TRADE_PRS, "Trade PRS", 3),
)
