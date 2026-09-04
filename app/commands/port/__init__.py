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

"""Port command package — generates synthetic portfolio data.

Public surface (preserved for back-compat with the old port.py module):

    register_parser(subparsers)   — argparse plumbing
    cmd_port(args)                — top-level orchestrator
    _authenticate                 — admin gate (used by tests)
    _set_password                 — first-time password creation
    _verify_password              — env-var / prompt verification
    _admin_file_path              — locator for the .port_admin hash file
    _print_port_summary           — end-of-run report (used by tests)
"""

from .auth import (
    _admin_file_path,
    _authenticate,
    _set_password,
    _verify_password,
)
from .orchestrator import cmd_port
from .parser import register_parser
from .summary import _print_port_summary

__all__ = [
    "register_parser",
    "cmd_port",
    "_authenticate",
    "_set_password",
    "_verify_password",
    "_admin_file_path",
    "_print_port_summary",
]
