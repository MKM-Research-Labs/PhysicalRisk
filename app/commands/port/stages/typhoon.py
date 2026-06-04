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

    # If a property portfolio exists, evaluate the wind-field at the actual
    # property locations so the downstream damage step can match by id. The
    # catchment-defined showcase points remain the fallback when no portfolio
    # is present (typically: standalone --typhoon before --properties).
    properties = _load_property_portfolio(ctx)
    if properties:
        from dataclasses import replace as _dc_replace
        from config.typhoon import PropertyPoint
        from models.winddamage import extract_lon_lat, extract_property_id

        portfolio_points = []
        for record in properties:
            prop_id = extract_property_id(record)
            lon, lat = extract_lon_lat(record)
            if prop_id is None or lon is None or lat is None:
                continue
            portfolio_points.append(PropertyPoint(
                property_id=prop_id, longitude=lon, latitude=lat,
            ))
        if portfolio_points:
            typhoon_cfg = _dc_replace(typhoon_cfg, property_points=portfolio_points)

    # Outputs land under the per-catchment input dir (data/input/<catch>/typhoon)
    # alongside the other pipeline artefacts (gauge.json, gaugets/, etc.).
    typhoon_dir = ctx.input_dir / "typhoon"
    output_path = typhoon_dir / "ensemble.json"
    events_dir = typhoon_dir / "events"
    windts_dir = typhoon_dir / "windts"
    damage_dir = typhoon_dir / "damage"
    inputs = {
        f"catch/{ctx.catchment}/tc.py":
            Path(__file__).resolve().parents[4] / "data" / "catch" / ctx.catchment / "tc.py",
    }
    pre = ctx.hash_inputs(inputs)

    # Local imports keep the start-up path light when --typhoon is unused.
    from models.typhoon.pipeline import simulate_typhoon_events, write_ensemble_json

    seed = args.typhoon_seed
    rng = np.random.default_rng(seed)

    # Slave the typhoon count to the storm event set when one exists: one
    # typhoon per storm sequence, paired by the shared event_id (Stage 2
    # coupling). Falls back to the standalone --num-typhoon-events count when
    # storm_sequences.json is absent or pre-coupling (no event_id field).
    drivers = _load_storm_event_drivers(ctx)
    coupling_beta = getattr(args, "coupling_beta", None)
    if coupling_beta is None:
        from config.port import COUPLING_BETA
        coupling_beta = COUPLING_BETA
    if drivers:
        event_ids = [d["event_id"] for d in drivers]
        n_events = len(event_ids)
        # Stage 3: condition genesis on the paired storm severity. Convert each
        # event's severity latent z (base_intensity) into its empirical quantile
        # q_i = rank(z_i)/(N+1), then hand q + the per-event seed to the
        # pipeline so the §4 band-draw map fixes one coupled genesis Vmax per
        # event (coupling_spec.md §3-§4).
        event_severity_q = _severity_quantiles([d["base_intensity"] for d in drivers])
        event_seeds = [d["seed"] for d in drivers]
        print(f"   coupled mode: {n_events:,} typhoons slaved 1:1 to storm "
              f"sequences (paired by event_id, genesis conditioned on severity "
              f"z, beta={coupling_beta})")
    else:
        event_ids = None
        event_severity_q = None
        event_seeds = None
        n_events = args.num_typhoon_events
        print(f"   standalone mode: {n_events:,} typhoons "
              f"(no coupled storm set found)")

    t_step = time.time()
    ensemble = simulate_typhoon_events(
        config=typhoon_cfg,
        n_events=n_events,
        n_particles=args.num_typhoon_particles,
        rng=rng,
        use_plausibility=not args.typhoon_no_plausibility,
        events_output_dir=events_dir,
        windts_output_dir=windts_dir,
        event_ids=event_ids,
        event_severity_q=event_severity_q,
        event_seeds=event_seeds,
        coupling_beta=coupling_beta,
    )
    elapsed = time.time() - t_step

    write_ensemble_json(ensemble, output_path)

    n_realizations = n_events * args.num_typhoon_particles
    n_properties = len(typhoon_cfg.property_points)
    print(f"   {n_events} events x {args.num_typhoon_particles} particles "
          f"= {n_realizations:,} realizations at {n_properties} property points")
    if ensemble.properties:
        peaks = [p.peak_sustained_p99 for p in ensemble.properties]
        peak_mean = sum(peaks) / len(peaks)
        print(f"   per-property p99 peak wind: mean across properties = {peak_mean:.1f} m/s")
    # ------------------------------------------------------------------
    # Wind damage — per-event damage ratio per property
    # ------------------------------------------------------------------
    # `properties` was loaded above so the wind-field could be evaluated at
    # portfolio locations; reuse it directly.
    from models.winddamage import run_event_directory
    if properties:
        damage_files = run_event_directory(
            windts_dir=windts_dir,
            damage_dir=damage_dir,
            properties=properties,
        )
        n_damage_events = len(damage_files)
    else:
        n_damage_events = 0

    print(f"   wrote {output_path}")
    print(f"   per-event tracks in {events_dir}/")
    print(f"   per-property wind timeseries in {windts_dir}/")
    if n_damage_events:
        print(f"   per-event damage in {damage_dir}/  "
              f"({n_damage_events} events x {len(properties)} properties)")
    else:
        print("   (no property portfolio found — skipped damage step)")

    ctx.record(
        step_name="typhoon",
        generator="models.typhoon.pipeline.simulate_typhoon_events",
        inputs=inputs,
        outputs={
            "typhoon/ensemble.json": output_path,
            "typhoon/events/": events_dir,
            "typhoon/windts/": windts_dir,
            "typhoon/damage/": damage_dir,
        },
        parameters={
            "n_events": n_events,
            "n_particles": args.num_typhoon_particles,
            "coupled_to_storms": bool(drivers),
            "coupling_beta": coupling_beta if drivers else None,
            "use_plausibility": not args.typhoon_no_plausibility,
            "seed": seed,
        },
        input_hashes=pre,
        elapsed_seconds=elapsed,
        stale_name="typhoon",
    )
    print()


def _severity_quantiles(z_values: list) -> list:
    """Map per-event severity latents z to empirical quantiles q_i.

    ``q_i = rank(z_i) / (N+1)`` using average ranks for ties (coupling_spec.md
    §3). The (N+1) denominator keeps every q strictly inside (0, 1) so the §4
    inverse-survival map ``Vmax = S_cat⁻¹(1−ρ_w)`` never hits the degenerate
    endpoints. Returns a list aligned 1:1 with the input order.
    """
    from scipy.stats import rankdata

    if not z_values:
        return []
    n = len(z_values)
    ranks = rankdata(z_values, method="average")
    return [float(r / (n + 1)) for r in ranks]


def _load_storm_event_drivers(ctx: StageContext) -> list:
    """Read storm_sequences.json and return the per-event coupling drivers.

    Each driver is ``{"event_id", "base_intensity", "seed"}`` in file order —
    the 1:1 storm<->typhoon pairing produced by the storm stage (Stage 2).
    ``base_intensity`` is the severity latent ``z`` that Stage 3 will use to
    condition typhoon genesis; ``seed`` makes that genesis reproducible per
    event.

    Returns an empty list when storm_sequences.json is missing or carries no
    coupling fields (a pre-Stage-2 file). The caller then falls back to the
    standalone ``--num-typhoon-events`` count.
    """
    import json

    seq_path = ctx.input_dir / "storm_sequences.json"
    if not seq_path.exists():
        return []
    try:
        data = json.loads(seq_path.read_text())
    except (OSError, json.JSONDecodeError):
        return []

    drivers = []
    for seq in data.get("sequences", []):
        event_id = seq.get("event_id")
        if not event_id:
            # Pre-coupling file (no event_id) — cannot pair; bail out so the
            # caller uses the standalone count rather than a partial pairing.
            return []
        drivers.append({
            "event_id": event_id,
            "base_intensity": float(seq.get("base_intensity", 0.0)),
            "seed": int(seq.get("seed", 0)),
        })
    return drivers


def _load_property_portfolio(ctx: StageContext) -> list:
    """Read property.json + commercial.json (when present) for the active catchment.

    Returns a list of property records. Commercial records are appended after
    residential. Missing files are tolerated — the damage step skips when the
    portfolio is empty.
    """
    import json

    portfolio: list = []

    for fname in ("property.json", "commercial.json"):
        path = ctx.input_dir / fname
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, list):
            portfolio.extend(data)
        elif isinstance(data, dict):
            # Common wrappers: {"properties": [...]} or {"Properties": [...]}
            for key in ("properties", "Properties", "commercial", "Commercial"):
                if isinstance(data.get(key), list):
                    portfolio.extend(data[key])
                    break
    return portfolio


def run_all(ctx: StageContext):
    run_typhoon(ctx)
