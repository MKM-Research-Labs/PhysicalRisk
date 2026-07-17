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

"""Admin-password gate for the port command.

Protects production data from accidental or unauthorised overwrites. The
password is set on first run and stored as a salted SHA-256 hash in
``data/.port_admin``. Tests authenticate via the ``MKM_PORT_ADMIN_PASSWORD``
env var rather than mocking out the gate.
"""

import getpass
import hashlib
import json
import os
import sys
from pathlib import Path

_ADMIN_FILE = Path('data/.port_admin')


def _authenticate():
    """Require admin password before port generation."""
    if not _ADMIN_FILE.exists():
        _set_password()
        return
    _verify_password()


def _set_password():
    """First-time password creation."""
    print("\nMKM Portfolio Generator — Admin Setup")
    print("No admin password set. Create one now.\n")
    pw = getpass.getpass("  New password: ")
    confirm = getpass.getpass("  Confirm: ")
    if pw != confirm:
        print("  Passwords do not match.")
        sys.exit(1)
    if len(pw) < 4:
        print("  Password too short (min 4 chars).")
        sys.exit(1)
    salt = os.urandom(16).hex()
    h = hashlib.sha256((salt + pw).encode()).hexdigest()
    _ADMIN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_ADMIN_FILE, 'w') as f:
        json.dump({"salt": salt, "hash": h}, f)
    print("  ✓ Admin password set.\n")


def _verify_password():
    """Prompt for password and verify against stored hash.

    If ``MKM_PORT_ADMIN_PASSWORD`` is set in the environment, that value
    is checked against the stored hash instead of prompting. A wrong env
    var still fails authentication — the gate is exercised, not skipped.
    """
    env_pw = os.environ.get("MKM_PORT_ADMIN_PASSWORD")
    if env_pw is not None:
        pw = env_pw
    else:
        print("\nMKM Portfolio Generator — Admin Authentication")
        pw = getpass.getpass("  Admin password: ")
    with open(_ADMIN_FILE) as f:
        stored = json.load(f)
    h = hashlib.sha256((stored['salt'] + pw).encode()).hexdigest()
    if h != stored['hash']:
        print("  ✗ Invalid password.")
        sys.exit(1)
    if env_pw is None:
        print("  ✓ Authenticated.\n")
