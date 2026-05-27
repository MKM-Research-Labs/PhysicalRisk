# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

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
