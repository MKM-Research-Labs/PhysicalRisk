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
Admin password gate for mutating Flask endpoints.

Reuses the salted SHA-256 hash stored at ``data/.port_admin`` by the
``python app.py port`` first-run setup flow, so Trading Desk Control tab
writes use the same credential as portfolio regeneration.

Password is provided by the client via the ``X-Admin-Password`` HTTP header.
"""

import hashlib
import json
import os
from functools import wraps
from pathlib import Path

from flask import jsonify, request

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


def require_admin_password(view_func):
    """Decorator: require ``X-Admin-Password`` header matching stored hash.

    Returns:
        401 if header missing or password wrong.
        503 if no admin credential has been initialised yet (run
            ``python app.py port`` once to set one).
    """

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        admin_file = _admin_file_path()
        if not admin_file.exists():
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": (
                            "Admin password not initialised. "
                            "Run 'python app.py port' once to set one."
                        ),
                    }
                ),
                503,
            )

        pw = request.headers.get("X-Admin-Password", "")
        if not pw:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Admin password required (X-Admin-Password header).",
                    }
                ),
                401,
            )

        with open(admin_file) as f:
            stored = json.load(f)

        h = hashlib.sha256((stored["salt"] + pw).encode()).hexdigest()
        if h != stored["hash"]:
            return (
                jsonify({"status": "error", "message": "Invalid admin password."}),
                401,
            )

        return view_func(*args, **kwargs)

    return wrapper
