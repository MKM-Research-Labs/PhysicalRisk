# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see auth.py for full license text)

"""Port command package — generates synthetic portfolio data.

Public surface (preserved for back-compat with the old port.py module):

    register_parser(subparsers)   — argparse plumbing
    cmd_port(args)                — top-level orchestrator
    _authenticate                 — admin gate (used by tests)
    _set_password                 — first-time password creation
    _verify_password              — env-var / prompt verification
    _ADMIN_FILE                   — Path to the .port_admin hash file
    _print_port_summary           — end-of-run report (used by tests)
"""

from .auth import _ADMIN_FILE, _authenticate, _set_password, _verify_password
from .orchestrator import cmd_port
from .parser import register_parser
from .summary import _print_port_summary

__all__ = [
    "register_parser",
    "cmd_port",
    "_authenticate",
    "_set_password",
    "_verify_password",
    "_ADMIN_FILE",
    "_print_port_summary",
]
