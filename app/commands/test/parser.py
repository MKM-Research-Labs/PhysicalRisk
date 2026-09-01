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

"""Argument-parser registration for the ``test`` subcommand."""

import argparse

from .._catchment import add_catchment_flags
from .command import cmd_test


def register_parser(subparsers):
    """Register the 'test' subcommand."""
    sp_test = subparsers.add_parser(
        "test", help="Run tests and produce audit evidence package",
        formatter_class=_HelpFormatter)

    # Catchment selection (--thames / --halong / --catchment-id ...).
    # Pins MKM_CATCHMENT for the test subprocesses so suites run against
    # the chosen catchment instead of the 'thames' default.
    add_catchment_flags(sp_test)

    # Suite selectors — pick any combination
    suites = sp_test.add_argument_group("suite selectors (pick any combination)")
    suites.add_argument(
        "--unit", action="store_true",
        help="Unit/model tests with coverage (~7 000 tests)")
    suites.add_argument(
        "--e2e", action="store_true",
        help="Playwright E2E browser tests (~300 tests)")
    suites.add_argument(
        "--lineage", action="store_true",
        help="Data lineage consistency checks (BCBS 239)")
    suites.add_argument(
        "--all", action="store_true", dest="run_all",
        help="All three suites (default when no suite flag given)")

    # Output options
    outputs = sp_test.add_argument_group("output options")
    outputs.add_argument(
        "--audit", action="store_true",
        help="Generate audit reports (modularisation, duplication, hardcoding, full audit)")
    outputs.add_argument(
        "--pdf", action="store_true",
        help="Compile LaTeX reports to PDF")
    outputs.add_argument(
        "--check-deps", action="store_true",
        help="Verify required Python dependencies are installed")
    outputs.add_argument(
        "--model", nargs="+",
        help="Filter unit tests by model alias (e.g. MP GH TD)")

    # Hidden backward-compat aliases (deprecated)
    sp_test.add_argument("--test", action="store_true", dest="_compat_test",
                         help=argparse.SUPPRESS)
    sp_test.add_argument("--code", action="store_true", dest="_compat_code",
                         help=argparse.SUPPRESS)

    sp_test.set_defaults(func=cmd_test)


class _HelpFormatter(argparse.RawDescriptionHelpFormatter,
                     argparse.ArgumentDefaultsHelpFormatter):
    """Combined formatter for nicer help output."""
    pass
