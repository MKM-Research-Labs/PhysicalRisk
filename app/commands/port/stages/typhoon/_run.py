# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Typhoon ensemble run — boundary adapter to the typhoon pipeline."""

import time
from pathlib import Path

import numpy as np

from config import config

from ...context import StageContext
from ._loaders import (
    _load_catchment_typhoon_config,
    _load_property_portfolio,
    _load_storm_event_drivers,
    _severity_quantiles,
)


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
            config.get_catch_dir(ctx.catchment) / "tc.py",
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
