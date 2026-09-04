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

"""
Locator for the ``.port_admin`` credential file.

The **web** admin-password gate (``require_admin_password`` / ``X-Admin-Password``)
was retired in WP5: mutating endpoints are now gated by RBAC capability
(``@require(FUNC_TRADE_PRS, …)`` — see ``routes._rbac``). What remains here is only the
path helper, kept because the credential is still owned by the CLI
``python phys.py port`` first-run setup (``app/commands/port/auth.py``) and the test
suites redirect it via ``MKM_ADMIN_FILE_PATH``.
"""

import os
from pathlib import Path

from config import config


def _admin_file_path() -> Path:
    """Return path to the shared admin credential file.

    Checks ``MKM_ADMIN_FILE_PATH`` first so the E2E test suite can redirect
    the Flask subprocess to a tmp file without ever touching ``data/.port_admin``.
    Falls back to ``config.get_admin_credential_path()`` — the same
    accessor the CLI gate uses, so the two halves cannot drift apart.
    """
    override = os.environ.get("MKM_ADMIN_FILE_PATH")
    if override:
        return Path(override)
    return config.get_admin_credential_path()
