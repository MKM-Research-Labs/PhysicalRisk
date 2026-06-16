# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see auth.py for full license text)

"""argparse subparser for the port command."""

from .._catchment import add_catchment_flags
from .orchestrator import cmd_port


def register_parser(subparsers):
    """Register the 'port' subcommand."""
    sp = subparsers.add_parser("port", help="Generate synthetic portfolio data")
    add_catchment_flags(sp)

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
    sp.add_argument("--commercialtsb", action="store_true",
                    help="BRI-adjusted floor timeseries for commercial (commercialtsb/)")
    sp.add_argument("--commercialbri", action="store_true",
                    help="BRI-adjusted floor hazard curves for commercial (commercialbri.json)")
    # Wind-coupled peril scenarios for commercial (require --typhoon damage)
    sp.add_argument("--commercialtsw", action="store_true",
                    help="Wind-only peril timeseries for commercial (commercialtsw/)")
    sp.add_argument("--commercialtsfaw", action="store_true",
                    help="Flood-AND-wind peril timeseries for commercial (commercialtsfaw/)")
    sp.add_argument("--commercialtsfow", action="store_true",
                    help="Flood-OR-wind peril timeseries for commercial (commercialtsfow/)")
    sp.add_argument("--commercialwin", action="store_true",
                    help="Wind-only hazard curves for commercial (commercialwin.json)")
    sp.add_argument("--commercialfaw", action="store_true",
                    help="Flood-AND-wind hazard curves for commercial (commercialfaw.json)")
    sp.add_argument("--commercialfow", action="store_true",
                    help="Flood-OR-wind hazard curves for commercial (commercialfow.json)")
    sp.add_argument("--commercialtsbow", action="store_true",
                    help="BRI-OR-wind peril timeseries for commercial (commercialtsbow/)")
    sp.add_argument("--commercialtsbaw", action="store_true",
                    help="BRI-AND-wind peril timeseries for commercial (commercialtsbaw/)")
    sp.add_argument("--commercialbow", action="store_true",
                    help="BRI-OR-wind hazard curves for commercial (commercialbow.json)")
    sp.add_argument("--commercialbaw", action="store_true",
                    help="BRI-AND-wind hazard curves for commercial (commercialbaw.json)")
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
    sp.add_argument("--propertytsb", action="store_true",
                    help="BRI-adjusted floor timeseries (floor = BRIAdjustedFloorLevelMeters)")
    sp.add_argument("--propertybri", action="store_true",
                    help="BRI-adjusted floor hazard curves (propertybri.json)")
    # Wind-coupled peril scenarios (require --typhoon damage)
    sp.add_argument("--propertytsw", action="store_true",
                    help="Wind-only peril timeseries (propertytsw/)")
    sp.add_argument("--propertytsfaw", action="store_true",
                    help="Flood-AND-wind peril timeseries (propertytsfaw/)")
    sp.add_argument("--propertytsfow", action="store_true",
                    help="Flood-OR-wind peril timeseries (propertytsfow/)")
    sp.add_argument("--propertywin", action="store_true",
                    help="Wind-only hazard curves (propertywin.json)")
    sp.add_argument("--propertyfaw", action="store_true",
                    help="Flood-AND-wind hazard curves (propertyfaw.json)")
    sp.add_argument("--propertyfow", action="store_true",
                    help="Flood-OR-wind hazard curves (propertyfow.json)")
    sp.add_argument("--propertytsbow", action="store_true",
                    help="BRI-OR-wind peril timeseries (propertytsbow/)")
    sp.add_argument("--propertytsbaw", action="store_true",
                    help="BRI-AND-wind peril timeseries (propertytsbaw/)")
    sp.add_argument("--propertybow", action="store_true",
                    help="BRI-OR-wind hazard curves (propertybow.json)")
    sp.add_argument("--propertybaw", action="store_true",
                    help="BRI-AND-wind hazard curves (propertybaw.json)")
    sp.add_argument("--counterparties", "--ctpy", action="store_true")
    sp.add_argument("--blotter", "--bl", action="store_true")
    sp.add_argument("--stressm", action="store_true",
                    help="Multi-storm stress test (sequence-based, replaces --stress)")
    sp.add_argument("--typhoon", "--ty", action="store_true",
                    help="Run typhoon (tropical cyclone) wind ensemble for the active catchment")
    sp.add_argument("--fire", "--fi", action="store_true",
                    help="Run the BRI fire-resilience credit model over the commercial portfolio")
    sp.add_argument("--seismic", "--se", action="store_true",
                    help="Run the BRI seismic-resilience credit model over the commercial portfolio")

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
    sp.add_argument("--num-sims", "-ns", type=int, default=10000,
                    help="Monte Carlo draws shared by the storm, fire and "
                         "seismic models (default 10000)")
    sp.add_argument("--simulation-hours", type=int, default=168)
    sp.add_argument("--history-years", "-hy", type=int, default=50)
    sp.add_argument("--tail-weight", "-tw", type=float, default=2.0)
    sp.add_argument("--distribution", "-d", choices=["gev", "gumbel"], default="gev")

    # Typhoon ensemble (--typhoon) -----------------------------------------
    sp.add_argument("--num-typhoon-events", type=int, default=50,
                    help="Number of typhoon events to simulate (default 50)")
    sp.add_argument("--num-typhoon-particles", type=int, default=100,
                    help="Particles per event in the SMC engine (default 100)")
    sp.add_argument("--typhoon-seed", type=int, default=None,
                    help="RNG seed for typhoon simulation; None = nondeterministic")
    sp.add_argument("--typhoon-no-plausibility", action="store_true",
                    help="Disable simulation-mode plausibility weighting (pure Monte Carlo)")
    sp.add_argument("--coupling-beta", type=float, default=None,
                    help="Storm->wind coupling strength beta (coupling_spec.md §4): "
                         "0=pure ceiling, 1=comonotone, ~0.5 expert default. "
                         "None = config.port.COUPLING_BETA. Only used in coupled mode.")

    # Fire model (--fire) --------------------------------------------------
    # Draw count is the shared --num-sims; only the seed is fire-specific.
    sp.add_argument("--fire-seed", type=int, default=None,
                    help="RNG seed for the fire model; None = nondeterministic")

    # Seismic model (--seismic) --------------------------------------------
    # Draw count is the shared --num-sims; only the seed is seismic-specific.
    sp.add_argument("--seismic-seed", type=int, default=None,
                    help="RNG seed for the seismic model; None = nondeterministic")

    # Maintenance ----------------------------------------------------------
    sp.add_argument("--repair-manifest", action="store_true",
                    help="Re-hash all pipeline artifacts and rebuild a consistent manifest")
    sp.add_argument("--backup", action="store_true",
                    help="Back up existing data files before overwriting")

    sp.set_defaults(func=cmd_port)
