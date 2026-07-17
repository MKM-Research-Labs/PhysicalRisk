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

"""Fire stage — boundary adapter between the active catchment's commercial
portfolio and the catchment-agnostic BRI fire-resilience credit model.

This stage reads only ``commercial.json`` (residential assets do not carry the
fire checklist and are out of scope), maps each commercial record into an
:class:`AssetFireFeatures` bundle via the CDM adapter, runs the fire model
(initiation + 15-min progression + containment) for every asset, and writes the
per-asset resilience-credit aggregates to ``fire/fire.json``.

It deliberately does no fire math: ``models.fire.cdm_adapter`` owns the CDM
mapping and ``models.fire.containment`` owns the simulation. The fire model is
opt-in (``--fire``) and is also run under ``--all``.
"""

import json
import time

import numpy as np

from ..context import StageContext


def _load_commercial_records(ctx: StageContext) -> list:
    """Read commercial.json for the active catchment, tolerating absence.

    Records are unwrapped from the ``commercial_assets`` wrapper (the shape the
    commercial generator writes). Returns an empty list when the file is missing
    or malformed so the stage can skip gracefully.
    """
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


def run_fire(ctx: StageContext):
    """Run the BRI fire-resilience credit model over the commercial portfolio.

    Triggered by ``port --fire`` (or ``--fi``) and under ``--all``. Skips
    cleanly when no commercial.json is present (e.g. a residential-only run).
    """
    args = ctx.args
    if not (ctx.run_all or args.fire):
        return
    if ctx.strict_block("fire"):
        raise SystemExit
    print("Running BRI Fire-Resilience Credit Model...")

    records = _load_commercial_records(ctx)
    if not records:
        print("   (no commercial.json found — skipped fire model)")
        print()
        return

    # Local imports keep the start-up path light when --fire is unused.
    from config.fire import FireRunConfig, load_fire_config
    from models.fire.cdm_adapter import commercial_portfolio_features
    from models.fire.containment import simulate_portfolio_fire

    features = commercial_portfolio_features(records)
    if not features:
        print(f"   (none of {len(records)} commercial records are modellable "
              f"— skipped fire model)")
        print()
        return

    n_sim = args.num_sims
    config = load_fire_config(run=FireRunConfig(n_sim=n_sim))
    rng = np.random.default_rng(args.fire_seed)

    fire_dir = ctx.input_dir / "fire"
    output_path = fire_dir / "fire.json"
    inputs = {"commercial.json": ctx.input_dir / "commercial.json"}
    pre = ctx.hash_inputs(inputs)

    t_step = time.time()
    results = simulate_portfolio_fire(features, config, rng)
    elapsed = time.time() - t_step

    assets = [r.to_dict() for r in results]
    n_assets = len(assets)
    portfolio = {
        "n_assets": n_assets,
        "n_sim": n_sim,
        "total_fires": sum(r.n_fires for r in results),
        "total_point_of_no_return": sum(r.n_point_of_no_return for r in results),
        "mean_loss_frequency":
            sum(r.loss_frequency for r in results) / n_assets if n_assets else 0.0,
        "mean_containment_rate":
            sum(r.containment_rate for r in results) / n_assets if n_assets else 0.0,
    }
    payload = {
        "metadata": {
            "catchment": ctx.catchment,
            "run_id": ctx.run_id,
            "model": "MKM-FIRE-001",
            "n_sim": n_sim,
            "fire_seed": args.fire_seed,
        },
        "portfolio": portfolio,
        "assets": assets,
    }

    fire_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))

    print(f"   {n_assets} commercial assets x {n_sim:,} draws")
    print(f"   mean loss frequency = {portfolio['mean_loss_frequency']:.4f}/yr, "
          f"mean containment rate = {portfolio['mean_containment_rate']:.3f}")
    print(f"   wrote {output_path}")

    ctx.record(
        step_name="fire",
        generator="models.fire.containment.simulate_portfolio_fire",
        inputs=inputs,
        outputs={"fire/fire.json": output_path},
        parameters={
            "n_sim": n_sim,
            "n_assets": n_assets,
            "fire_seed": args.fire_seed,
        },
        input_hashes=pre,
        elapsed_seconds=elapsed,
        stale_name="fire",
    )
    print()


def run_all(ctx: StageContext):
    run_fire(ctx)
