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

"""Shared catchment selection helpers for CLI subcommands.

Provides a single source of truth for both the argparse flag wiring and
the runtime resolution rule (CLI flag → ``MKM_CATCHMENT`` env var →
interactive prompt), so the ``port`` and ``server`` commands stay in
sync.
"""

import os

from config import config


def add_catchment_flags(sp) -> None:
    """Attach per-catchment boolean flags + a generic ``--catchment-id``.

    Each available catchment under ``data/catch/`` gets its own
    ``--<name>`` flag; all are mutually exclusive. Discovery is lazy so
    the help text reflects the on-disk state.
    """
    group = sp.add_mutually_exclusive_group()
    try:
        catchments = config.list_catchments()
    except Exception:
        catchments = []
    for cname in catchments:
        group.add_argument(
            f"--{cname}",
            action="store_const", const=cname, dest="catchment_id",
            help=f"Use the {cname} catchment",
        )
    group.add_argument(
        "--catchment-id", "--catchment", type=str, default=None,
        help="Generic catchment selector (e.g. --catchment-id thames). "
             "Equivalent to --<catchment_id>.",
    )


def resolve_catchment(args) -> str | None:
    """Resolve the catchment to run against.

    Precedence: CLI flag → ``MKM_CATCHMENT`` env var → interactive prompt.
    Returns ``None`` if the user aborts the prompt or supplies an invalid
    explicit choice.
    """
    chosen = getattr(args, 'catchment_id', None)
    if not chosen:
        chosen = os.environ.get('MKM_CATCHMENT')
    if chosen:
        available = config.list_catchments()
        if available and chosen not in available:
            print(f"\n  ✗ Unknown catchment '{chosen}'.")
            print(f"  Available: {', '.join(available)}")
            return None
        return chosen

    available = config.list_catchments()
    if not available:
        print("\n  ✗ No catchments configured under data/catch/.")
        return None
    if len(available) == 1:
        return available[0]
    print("\nMKM — Catchment Selection")
    print(f"Available catchments: {', '.join(available)}")
    while True:
        chosen = input("  Catchment: ").strip().lower()
        if chosen in available:
            return chosen
        if not chosen:
            print("  ✗ No catchment selected — aborting.")
            return None
        print(f"  ✗ '{chosen}' not available. Try one of: {', '.join(available)}")
