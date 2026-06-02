# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see auth.py for full license text)

"""cmd_port — top-level orchestrator for the port pipeline.

The heavy work lives in stage modules under ``stages/``; this file binds
``args`` to a :class:`StageContext`, resolves prerequisites, dispatches
each stage in order, then runs the summary + PDFs + lineage check.
"""

from config import config

from .._catchment import resolve_catchment
from .auth import _authenticate
from .context import StageContext
from .pdf_reports import run_lineage_chain_validation, run_pdf_reports
from .stages import hazardcurves, portfolios, storm, timeseries, trading, typhoon
from .summary import _print_port_summary


def _build_context(args) -> StageContext:
    """Lazy-import pipeline modules and lineage helpers, build StageContext."""
    output_dir = config.get_input_dir()
    input_dir = output_dir   # alias for lineage mappings

    from port.src import gauge, mortgage, hazard, counterparty
    from port.src import property as prop_gen
    from port.src import commercial as commercial_gen
    from port.src.commercial_loan import CommercialLoanPortfolioGenerator
    from port.src.gauge import gaugehd
    from port.src.property import propertyts, propertyhc

    try:
        from lineage.manifest import record_step, get_current_run_id, pre_hash_inputs
        from lineage.validation import (
            check_inputs_fresh, get_stale_downstream, resolve_prerequisites,
        )
    except ImportError:
        record_step = None
        get_current_run_id = None
        pre_hash_inputs = None
        check_inputs_fresh = None
        get_stale_downstream = None
        resolve_prerequisites = None

    run_id = None
    if get_current_run_id is not None:
        try:
            run_id = get_current_run_id()
        except Exception:
            pass

    # Determine which segments to run.
    segment_flags = [
        args.gauges, args.properties, args.mortgages, args.commercial,
        args.commercialts, args.commercialtsd, args.commercialtse,
        args.commercialhc, args.commercialshd, args.commercialshe,
        args.commercialtsb, args.commercialbri,
        args.gaugets, args.gaugehd, args.hazard,
        args.propertyts, args.propertytsd, args.propertytse,
        args.propertyhc, args.propertyshd, args.propertyshe,
        args.propertytsb, args.propertybri,
        args.counterparties, args.blotter, args.stressm,
        args.typhoon,
    ]
    run_all = args.all or not any(segment_flags)

    # Auto-prerequisite resolution (single-step mode only).
    if not run_all and not args.strict and resolve_prerequisites is not None:
        _step_flag = {
            "gauges": "gauges", "synthetic_gauges": "gauges",
            "properties": "properties",
            "mortgages": "mortgages", "gaugehd": "gaugehd",
            "stressm": "stressm", "hazard": "hazard",
            "propertyts": "propertyts", "propertyhc": "propertyhc",
            "propertytsd": "propertytsd", "propertytse": "propertytse",
            "propertyshd": "propertyshd", "propertyshe": "propertyshe",
            "propertytsb": "propertytsb", "propertybri": "propertybri",
            "counterparties": "counterparties", "blotter": "blotter",
        }
        requested = [
            name for name, attr in _step_flag.items()
            if getattr(args, attr, False)
                or (name == "stressm" and getattr(args, "gaugets", False))
        ]
        if requested:
            try:
                prereqs = resolve_prerequisites(requested, data_dir=output_dir)
                if prereqs:
                    arrow = ' → '
                    print(f"  Auto-running prerequisites: "
                          f"{arrow.join(prereqs)}\n")
                    for step in prereqs:
                        setattr(args, _step_flag[step], True)
            except Exception as e:
                print(f"  [lineage] Prerequisite check: {e}")

    return StageContext(
        args=args,
        catchment=config.catchment_id,
        output_dir=output_dir,
        input_dir=input_dir,
        run_id=run_id,
        run_all=run_all,
        gauge=gauge,
        mortgage=mortgage,
        hazard=hazard,
        counterparty=counterparty,
        prop_gen=prop_gen,
        commercial_gen=commercial_gen,
        commercial_loan_gen_cls=CommercialLoanPortfolioGenerator,
        gaugehd=gaugehd,
        propertyts=propertyts,
        propertyhc=propertyhc,
        record_step=record_step,
        pre_hash_inputs=pre_hash_inputs,
        get_stale_downstream=get_stale_downstream,
        check_inputs_fresh=check_inputs_fresh,
    )


def _backup_existing(output_dir):
    """Copy existing *.json files into a timestamped backup directory."""
    import shutil
    from datetime import datetime
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_dir = output_dir / '.backups' / ts
    backup_dir.mkdir(parents=True, exist_ok=True)
    backed = 0
    for f in output_dir.glob('*.json'):
        shutil.copy2(f, backup_dir / f.name)
        backed += 1
    print(f"  Backup: {backed} files → {backup_dir}")


def _repair_manifest(output_dir, catchment):
    """Standalone mode — re-hash all pipeline artifacts (no heavy imports)."""
    try:
        from lineage.manifest import repair_manifest
    except ImportError:
        print("ERROR: lineage package not available")
        return
    print(f"\nMKM Portfolio Generator — Manifest Repair")
    print(f"Catchment: {catchment}")
    print(f"Data dir:  {output_dir}\n")
    result = repair_manifest(data_dir=output_dir)
    for step in result["repaired"]:
        print(f"  ✓ {step}")
    for step in result["skipped"]:
        print(f"  ⚠ {step} (outputs missing — skipped)")
    print(f"\nRepaired {len(result['repaired'])} steps, "
          f"skipped {len(result['skipped'])}.")


def cmd_port(args):
    """Generate synthetic portfolio data.

    Catchment selection precedence (highest first):
      1. A per-catchment flag (``--thames`` / ``--halong`` / …) or the
         generic ``--catchment-id`` — both resolve to ``args.catchment_id``
      2. ``MKM_CATCHMENT`` env var
      3. Interactive prompt (only when (1) and (2) are both absent)

    The orchestrator pins ``config.catchment_id`` so every downstream
    consumer (random modules, params, data paths) resolves against the
    same catchment for the rest of the run.
    """
    catchment = resolve_catchment(args)
    if catchment is None:
        return  # user aborted the prompt
    config.catchment_id = catchment
    output_dir = config.get_input_dir()

    # --- Admin gate (skipped for read-only repair-manifest) ---------------
    if not getattr(args, 'repair_manifest', False):
        _authenticate()

    # --- Optional backup --------------------------------------------------
    if getattr(args, 'backup', False) and output_dir.exists():
        _backup_existing(output_dir)

    # --- Repair manifest (standalone, no heavy imports) ------------------
    if getattr(args, 'repair_manifest', False):
        _repair_manifest(output_dir, catchment)
        return

    ctx = _build_context(args)

    print(f"\nMKM Portfolio Generator")
    print(f"Catchment: {catchment}")
    print(f"Output: {output_dir}\n")

    # --- Pipeline stages --------------------------------------------------
    portfolios.run_all(ctx)
    storm.run_all(ctx)
    timeseries.run_all(ctx)
    hazardcurves.run_all(ctx)
    trading.run_all(ctx)
    typhoon.run_all(ctx)

    # --- Post-run reporting ----------------------------------------------
    if ctx.run_all:
        _print_port_summary(output_dir)

    run_pdf_reports(args, output_dir, ctx.run_all)
    run_lineage_chain_validation()

    print(f"Complete! Files in: {output_dir}")
