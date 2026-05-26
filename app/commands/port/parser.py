# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see auth.py for full license text)

"""argparse subparser for the port command."""

from .orchestrator import cmd_port


def _add_catchment_flags(sp):
    """Add one boolean flag per discovered catchment (e.g. --thames, --halong)
    plus a generic ``--catchment-id`` fallback. All mutually exclusive.

    Discovery is lazy so the help text reflects whatever's under
    ``data/catch/`` at parse time, no manual list maintenance.
    """
    from config import config
    group = sp.add_mutually_exclusive_group()
    try:
        catchments = config.list_catchments()
    except Exception:
        catchments = []
    for cname in catchments:
        group.add_argument(
            f"--{cname}",
            action="store_const", const=cname, dest="catchment_id",
            help=f"Generate against the {cname} catchment",
        )
    group.add_argument(
        "--catchment-id", "--catchment", type=str, default=None,
        help="Generic catchment selector (e.g. --catchment-id thames). "
             "Equivalent to --<catchment_id>.",
    )


def register_parser(subparsers):
    """Register the 'port' subcommand."""
    sp = subparsers.add_parser("port", help="Generate synthetic portfolio data")
    _add_catchment_flags(sp)

    # Per-step toggles ------------------------------------------------------
    sp.add_argument("--gauges", "--ga", action="store_true")
    sp.add_argument("--properties", "--pr", action="store_true")
    sp.add_argument("--mortgages", "--mo", action="store_true")
    sp.add_argument("--commercial", "--co", action="store_true",
                    help="Generate commercial portfolio (commercial.json + commercial_loan.json)")
    sp.add_argument("--commercialts", "--cts", action="store_true",
                    help="Commercial flood timeseries (commercialts/)")
    sp.add_argument("--commercialtsd", action="store_true",
                    help="Synthetic distance timeseries for commercial (zero elevation diff)")
    sp.add_argument("--commercialtse", action="store_true",
                    help="Synthetic elevation timeseries for commercial (zero distance)")
    sp.add_argument("--commercialhc", "--chc", action="store_true",
                    help="Commercial hazard curves + PRS pricing")
    sp.add_argument("--commercialshd", action="store_true",
                    help="Synthetic distance hazard curves for commercial")
    sp.add_argument("--commercialshe", action="store_true",
                    help="Synthetic elevation hazard curves for commercial")
    sp.add_argument("--gaugets", "--gt", action="store_true")
    sp.add_argument("--gaugehd", "--hd", action="store_true")
    sp.add_argument("--hazard", "--hz", action="store_true")
    sp.add_argument("--propertyts", "--pt", action="store_true")
    sp.add_argument("--propertytsd", action="store_true",
                    help="Synthetic distance timeseries (elevation diff = 0)")
    sp.add_argument("--propertytse", action="store_true",
                    help="Synthetic elevation timeseries (distance = 0)")
    sp.add_argument("--propertyhc", "--phc", action="store_true")
    sp.add_argument("--propertyshd", action="store_true",
                    help="Synthetic distance hazard curves (elevation diff = 0)")
    sp.add_argument("--propertyshe", action="store_true",
                    help="Synthetic elevation hazard curves (distance = 0)")
    sp.add_argument("--counterparties", "--ctpy", action="store_true")
    sp.add_argument("--blotter", "--bl", action="store_true")
    sp.add_argument("--stressm", action="store_true",
                    help="Multi-storm stress test (sequence-based, replaces --stress)")

    # Modifiers ------------------------------------------------------------
    sp.add_argument("--gauge-id", "--gid", type=str, default=None,
                    help="Restrict --stressm to a single gauge ID")
    sp.add_argument("--pdf", action="store_true",
                    help="Generate portfolio report PDF after generation")
    sp.add_argument("--all", "-a", action="store_true", help="Run all segments")
    sp.add_argument("--nostress", action="store_true",
                    help="Skip stress test generation when running --all (step 12)")
    sp.add_argument("--strict", action="store_true",
                    help="Refuse to run if upstream data is stale (BCBS 239 lineage guard)")
    sp.add_argument("--verbose", "-v", action="store_true")

    # Counts + tuning ------------------------------------------------------
    sp.add_argument("--num-properties", "-np", type=int, default=200)
    sp.add_argument("--num-commercial", "-nc", type=int, default=10,
                    help="Number of commercial assets to generate (--commercial)")
    sp.add_argument("--num-gauges", "-ng", type=int, default=52)
    sp.add_argument("--num-storms", "-ns", type=int, default=20000)
    sp.add_argument("--simulation-hours", type=int, default=168)
    sp.add_argument("--history-years", "-hy", type=int, default=50)
    sp.add_argument("--tail-weight", "-tw", type=float, default=2.0)
    sp.add_argument("--distribution", "-d", choices=["gev", "gumbel"], default="gev")

    # Maintenance ----------------------------------------------------------
    sp.add_argument("--repair-manifest", action="store_true",
                    help="Re-hash all pipeline artifacts and rebuild a consistent manifest")
    sp.add_argument("--backup", action="store_true",
                    help="Back up existing data files before overwriting")

    sp.set_defaults(func=cmd_port)
