# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see ../auth.py for full license text)

"""Seismic stage — boundary adapter between the active catchment's commercial
portfolio and the catchment-agnostic BRI seismic-resilience credit model.

This stage reads only ``commercial.json``, maps each commercial record into an
:class:`AssetSeismicFeatures` bundle via the CDM adapter, loads the catchment
fault trace (``data/catch/<id>/fault_trace.json``) for the source-to-site
spatial draw, runs the seismic model (Models A-D) for every asset, and writes
the per-asset resilience-credit aggregates to ``seismic/seismic.json``.

It deliberately does no seismic math: ``models.seismic.cdm_adapter`` owns the
CDM mapping and ``models.seismic.damage`` owns the simulation. The seismic model
is opt-in (``--seismic``) and is also run under ``--all``. When the catchment
has no fault trace the model still runs (occurrence only, R_JB = 0) and a
notice is printed.
"""

import json
import time
from pathlib import Path

import numpy as np

from ..context import StageContext


def _load_commercial_records(ctx: StageContext) -> list:
    """Read commercial.json for the active catchment, tolerating absence."""
    path = ctx.input_dir / "commercial.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("commercial_assets", "CommercialAssets",
                    "commercial", "Commercial"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def _catchment_dir(ctx: StageContext) -> Path:
    """The version-controlled catchment asset directory data/catch/<id>/."""
    return Path(__file__).resolve().parents[4] / "data" / "catch" / ctx.catchment


def run_seismic(ctx: StageContext):
    """Run the BRI seismic-resilience credit model over the commercial portfolio.

    Triggered by ``port --seismic`` (or ``--se``) and under ``--all``. Skips
    cleanly when no commercial.json is present.
    """
    args = ctx.args
    if not (ctx.run_all or args.seismic):
        return
    if ctx.strict_block("seismic"):
        raise SystemExit
    print("Running BRI Seismic-Resilience Credit Model...")

    records = _load_commercial_records(ctx)
    if not records:
        print("   (no commercial.json found — skipped seismic model)")
        print()
        return

    # Local imports keep the start-up path light when --seismic is unused.
    from config.seismic import SeismicRunConfig, load_seismic_config
    from models.seismic.cdm_adapter import commercial_portfolio_features
    from models.seismic.damage import simulate_portfolio_seismic
    from models.seismic.occurrence import fault_trace_path, load_fault_trace

    features = commercial_portfolio_features(records)
    if not features:
        print(f"   (none of {len(records)} commercial records are modellable "
              f"— skipped seismic model)")
        print()
        return

    fpath = fault_trace_path(_catchment_dir(ctx))
    fault = load_fault_trace(fpath) if fpath.exists() else None
    if fault is None:
        print(f"   (no fault_trace.json for '{ctx.catchment}' — occurrence only, "
              f"R_JB = 0; distance sensitivity disabled)")

    n_sim = args.num_sims
    config = load_seismic_config(run=SeismicRunConfig(n_sim=n_sim))
    rng = np.random.default_rng(args.seismic_seed)

    seismic_dir = ctx.input_dir / "seismic"
    output_path = seismic_dir / "seismic.json"
    inputs = {"commercial.json": ctx.input_dir / "commercial.json"}
    pre = ctx.hash_inputs(inputs)

    t_step = time.time()
    results = simulate_portfolio_seismic(features, config, fault, rng)
    elapsed = time.time() - t_step

    assets = [r.to_dict() for r in results]
    n_assets = len(assets)
    portfolio = {
        "n_assets": n_assets,
        "n_sim": n_sim,
        "total_events": sum(r.n_events for r in results),
        "total_collapse": sum(r.damage_state_counts.get(3, 0) for r in results),
        "mean_seismic_spread_bps":
            sum(r.seismic_spread_bps for r in results) / n_assets if n_assets else 0.0,
        "mean_loss_frequency":
            sum(r.loss_frequency for r in results) / n_assets if n_assets else 0.0,
        "mean_no_collapse_rate":
            sum(r.no_collapse_rate for r in results) / n_assets if n_assets else 0.0,
    }
    payload = {
        "metadata": {
            "catchment": ctx.catchment,
            "run_id": ctx.run_id,
            "model": "MKM-SEIS-001",
            "n_sim": n_sim,
            "seismic_seed": args.seismic_seed,
            "fault_trace": str(fpath) if fault is not None else None,
        },
        "portfolio": portfolio,
        "assets": assets,
    }

    seismic_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))

    print(f"   {n_assets} commercial assets x {n_sim:,} draws")
    print(f"   mean seismic spread = {portfolio['mean_seismic_spread_bps']:.2f} bps, "
          f"mean no-collapse rate = {portfolio['mean_no_collapse_rate']:.3f}")
    print(f"   wrote {output_path}")

    ctx.record(
        step_name="seismic",
        generator="models.seismic.damage.simulate_portfolio_seismic",
        inputs=inputs,
        outputs={"seismic/seismic.json": output_path},
        parameters={
            "n_sim": n_sim,
            "n_assets": n_assets,
            "seismic_seed": args.seismic_seed,
        },
        input_hashes=pre,
        elapsed_seconds=elapsed,
        stale_name="seismic",
    )
    print()


def run_all(ctx: StageContext):
    run_seismic(ctx)
