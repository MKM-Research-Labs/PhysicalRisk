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
password is set on first run and stored as a salted SHA-256 hash beside the
portfolio it guards, at ``<data root>/.port_admin``. Both the setup and the
verification branch accept ``MKM_PORT_ADMIN_PASSWORD`` from the environment,
so unattended runs never stall on a prompt — a wrong value still fails, so
the gate is exercised rather than skipped.
"""

import getpass
import hashlib
import json
import os
import sys
from pathlib import Path

from config import config


def _admin_file_path() -> Path:
    """Locate the admin credential file.

    ``MKM_ADMIN_FILE_PATH`` wins when set — the same override the web-side
    locator in ``routes.trading._admin_auth`` honours, so one variable
    redirects both halves of the gate.

    Otherwise the path follows the data root. Anchoring it there rather than
    to the repo means a throwaway portfolio under ``MKM_DATA_ROOT`` carries
    its own credential: it takes the first-run setup branch below instead of
    resolving to ``data/.port_admin``, which is a dangling symlink whenever
    the shared volume is detached.
    """
    override = os.environ.get("MKM_ADMIN_FILE_PATH")
    if override:
        return Path(override)
    return config.get_admin_credential_path()


def _authenticate():
    """Require admin password before port generation."""
    if not _admin_file_path().exists():
        _set_password()
        return
    _verify_password()


def _set_password():
    """First-time password creation.

    Reads ``MKM_PORT_ADMIN_PASSWORD`` when set, for the same reason
    ``_verify_password`` does. A freshly generated portfolio has no
    credential yet, so without this there is no non-interactive route to
    creating one and an unattended run blocks on ``getpass`` forever.
    The length check still applies, so the env var cannot install a
    weaker credential than a human could.
    """
    admin_file = _admin_file_path()
    print("\nMKM Portfolio Generator — Admin Setup")
    print("No admin password set. Create one now.\n")
    env_pw = os.environ.get("MKM_PORT_ADMIN_PASSWORD")
    if env_pw is not None:
        pw = confirm = env_pw
    else:
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
    admin_file.parent.mkdir(parents=True, exist_ok=True)
    with open(admin_file, 'w') as f:
        json.dump({"salt": salt, "hash": h}, f)
    print("  \u2713 Admin password set.\n")


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
    with open(_admin_file_path()) as f:
        stored = json.load(f)
    h = hashlib.sha256((stored['salt'] + pw).encode()).hexdigest()
    if h != stored['hash']:
        print("  \u2717 Invalid password.")
        sys.exit(1)
    if env_pw is None:
        print("  \u2713 Authenticated.\n")
