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

"""
Locator for the ``data/.port_admin`` credential file.

The **web** admin-password gate (``require_admin_password`` / ``X-Admin-Password``)
was retired in WP5: mutating endpoints are now gated by RBAC capability
(``@require("Func003", …)`` — see ``routes._rbac``). What remains here is only the
path helper, kept because ``data/.port_admin`` is still owned by the CLI
``python app.py port`` first-run setup (``app/commands/port/auth.py``) and the test
suites redirect it via ``MKM_ADMIN_FILE_PATH``.
"""

import os
from pathlib import Path

_ADMIN_FILE = Path("data/.port_admin")


def _admin_file_path() -> Path:
    """Return path to the shared admin credential file.

    Checks ``MKM_ADMIN_FILE_PATH`` first so the E2E test suite can redirect
    the Flask subprocess to a tmp file without ever touching ``data/.port_admin``.
    Falls back to the real file for all non-test runs.
    """
    override = os.environ.get("MKM_ADMIN_FILE_PATH")
    if override:
        return Path(override)
    return _ADMIN_FILE
