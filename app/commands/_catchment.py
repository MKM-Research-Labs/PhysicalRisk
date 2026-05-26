# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see auth.py for full license text)

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
