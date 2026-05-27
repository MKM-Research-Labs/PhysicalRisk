# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see ../auth.py for full license text)

"""Typhoon stage — boundary adapter between the active catchment's
typhoon configuration and the catchment-agnostic typhoon model.

This stage is the only file in the codebase that knows both:
  - how to discover a catchment's tc.py (the production config path)
  - how to call the typhoon pipeline (the model entry point)

It deliberately does no math: the catchment file constructs the
CatchmentTyphoonConfig via its build_typhoon_config() function, and the
pipeline runs the SMC engine + wind-field model end-to-end.
"""

import importlib
import time
from pathlib import Path

import numpy as np

from config import config

from ..context import StageContext


def _load_catchment_typhoon_config(catchment_id: str):
    """Look up data/catch/<catchment_id>/tc.py and build a CatchmentTyphoonConfig.

    The catchment file is expected to expose a build_typhoon_config()
    function returning the assembled config. A catchment without typhoon
    coverage (e.g. Thames, extratropical) is rejected with a clear error
    so the user can pick a different flag or a different catchment.
    """
    try:
        module = importlib.import_module(f"catch.{catchment_id}.tc")
    except ModuleNotFoundError as exc:
        raise SystemExit(
            f"No typhoon configuration found for catchment '{catchment_id}'. "
            f"Expected file: data/catch/{catchment_id}/tc.py. "
            f"--typhoon is only valid for catchments with tropical-cyclone exposure."
        ) from exc

    builder = getattr(module, "build_typhoon_config", None)
    if builder is None:
        raise SystemExit(
            f"data/catch/{catchment_id}/tc.py must expose build_typhoon_config(). "
            f"See data/catch/halong/tc.py for the reference layout."
        )
    return builder(catchment_id=catchment_id)


def run_typhoon(ctx: StageContext):
    """Run the typhoon ensemble for the active catchment.

    Triggered by ``port --typhoon`` (or ``--ty``). Skipped under ``--all``
    by default because the typhoon model is opt-in per catchment.
    """
    args = ctx.args
    if not args.typhoon:
        return
    if ctx.strict_block("typhoon"):
        raise SystemExit
    print("Running Typhoon Wind Ensemble...")

    typhoon_cfg = _load_catchment_typhoon_config(ctx.catchment)

    typhoon_dir = Path(config.get_output_dir()) / "typhoon"
    output_path = typhoon_dir / "ensemble.json"
    events_dir = typhoon_dir / "events"
    inputs = {
        f"catch/{ctx.catchment}/tc.py":
            Path(__file__).resolve().parents[4] / "data" / "catch" / ctx.catchment / "tc.py",
    }
    pre = ctx.hash_inputs(inputs)

    # Local imports keep the start-up path light when --typhoon is unused.
    from models.typhoon.pipeline import simulate_typhoon_events, write_ensemble_json

    seed = args.typhoon_seed
    rng = np.random.default_rng(seed)

    t_step = time.time()
    ensemble = simulate_typhoon_events(
        config=typhoon_cfg,
        n_events=args.num_typhoon_events,
        n_particles=args.num_typhoon_particles,
        rng=rng,
        use_plausibility=not args.typhoon_no_plausibility,
        events_output_dir=events_dir,
    )
    elapsed = time.time() - t_step

    write_ensemble_json(ensemble, output_path)

    n_realizations = args.num_typhoon_events * args.num_typhoon_particles
    n_properties = len(typhoon_cfg.property_points)
    print(f"   {args.num_typhoon_events} events x {args.num_typhoon_particles} particles "
          f"= {n_realizations:,} realizations at {n_properties} property points")
    if ensemble.properties:
        peaks = [p.peak_sustained_p99 for p in ensemble.properties]
        peak_mean = sum(peaks) / len(peaks)
        print(f"   per-property p99 peak wind: mean across properties = {peak_mean:.1f} m/s")
    print(f"   wrote {output_path}")
    print(f"   per-event tracks in {events_dir}/")

    ctx.record(
        step_name="typhoon",
        generator="models.typhoon.pipeline.simulate_typhoon_events",
        inputs=inputs,
        outputs={
            "typhoon/ensemble.json": output_path,
            "typhoon/events/": events_dir,
        },
        parameters={
            "n_events": args.num_typhoon_events,
            "n_particles": args.num_typhoon_particles,
            "use_plausibility": not args.typhoon_no_plausibility,
            "seed": seed,
        },
        input_hashes=pre,
        elapsed_seconds=elapsed,
        stale_name="typhoon",
    )
    print()


def run_all(ctx: StageContext):
    run_typhoon(ctx)
