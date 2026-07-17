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

"""Low-memory batch classifier training.

Trains a GBM flood classifier for every gauge that does not already have a
.joblib model file.  Shared read-only data (sequences, spatial model) is loaded
once; per-gauge temporaries (vectors, trainer, result) are explicitly freed and
``gc.collect()`` is called between gauges to keep the RSS footprint minimal.

Usage (CLI):
    python app.py port --train-classifiers

Usage (Python):
    from port.src.stressm.batch_train import batch_train_classifiers
    batch_train_classifiers(input_dir, output_dir)
"""

import gc
import logging
import time
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


def batch_train_classifiers(
    input_dir: Path,
    output_dir: Path,
    seed: int = 42,
    verbose: bool = False,
) -> dict:
    """Train classifiers for all untrained gauges, one at a time.

    Args:
        input_dir:   data/input/<catchment>/  (contains gauge.json, storm_sequences.json)
        output_dir:  data/input/<catchment>/   (classifiers/ subdir for .joblib files)
        seed:        Base random seed (each gauge gets seed + index).
        verbose:     Print per-gauge detail.

    Returns:
        Summary dict with counts and per-gauge status.
    """
    from .classifier import train_gauge_stressm_classifier, _print_classifier_result
    from .summary import load_gauge_training_context, update_training_summary
    from port.src.storm_multi.utils.serialization import load_sequences

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    stressm_dir = output_dir / "stressm"
    stressm_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Load gauge portfolio
    # ------------------------------------------------------------------
    all_gauges, all_gauge_ids, spatial_model = load_gauge_training_context()

    if not all_gauges:
        print("  No valid gauges found in gauge.json")
        return {"trained": 0, "skipped": 0, "failed": 0}

    # ------------------------------------------------------------------
    # 2. Identify untrained gauges
    # ------------------------------------------------------------------
    untrained = [
        g for g in all_gauges
        if not (stressm_dir / f"{g['gauge_id']}.joblib").exists()
    ]
    already_trained = len(all_gauges) - len(untrained)

    print(f"\n  Batch Classifier Training")
    print(f"  {'=' * 50}")
    print(f"  Total gauges       : {len(all_gauges)}")
    print(f"  Already trained    : {already_trained}")
    print(f"  To train           : {len(untrained)}")
    print(f"  {'=' * 50}\n")

    if not untrained:
        print("  All gauges already have classifiers. Nothing to do.")
        return {"trained": 0, "skipped": already_trained, "failed": 0}

    # ------------------------------------------------------------------
    # 3. Load shared data: sequences + spatial model
    # ------------------------------------------------------------------
    import database
    if not database.storm_sequences_exists(database.active_catchment()):
        raise FileNotFoundError(
            "storm_sequences not found. "
            "Run 'python app.py port --stressm' first."
        )

    print("  Loading storm sequences...", flush=True)
    sequences = load_sequences()
    print(f"  Loaded {len(sequences):,} sequences", flush=True)

    # ------------------------------------------------------------------
    # 4. Train each gauge sequentially with memory cleanup
    # ------------------------------------------------------------------
    t_start = time.time()
    n_trained = 0
    n_failed = 0
    clf_results = []

    for i, gauge in enumerate(untrained):
        gid = gauge["gauge_id"]
        target_idx = all_gauge_ids.index(gid)
        gauge_seed = seed + 1 + target_idx  # deterministic per-gauge seed

        elapsed = time.time() - t_start
        if n_trained > 0:
            avg_per_gauge = elapsed / n_trained
            remaining = (len(untrained) - i) * avg_per_gauge
            eta_str = f"  ETA {remaining / 60:.1f}m"
        else:
            eta_str = ""

        print(
            f"  [{i + 1}/{len(untrained)}] {gid}{eta_str}",
            flush=True,
        )

        try:
            rng = np.random.RandomState(gauge_seed)
            result = train_gauge_stressm_classifier(
                sequences=sequences,
                gauge=gauge,
                spatial_model=spatial_model,
                target_spatial_index=target_idx,
                output_dir=output_dir,
                rng=rng,
            )

            if verbose:
                _print_classifier_result(result)

            # Update summary incrementally (write after each gauge so
            # progress survives a crash)
            from .summary import update_training_summary
            update_training_summary(result, stressm_dir)
            clf_results.append({
                "gauge_id": gid,
                "status": result.get("status", "unknown"),
                "auc_roc": result.get("metrics", {}).get("auc_roc"),
            })
            n_trained += 1

        except Exception as exc:
            logger.error("Classifier failed for %s: %s", gid, exc, exc_info=True)
            print(f"    FAILED: {exc}", flush=True)
            clf_results.append({"gauge_id": gid, "status": "failed", "error": str(exc)})
            n_failed += 1

        # ----------------------------------------------------------
        # Memory cleanup: free per-gauge temporaries
        # ----------------------------------------------------------
        # The rng, result, and any large temporaries inside
        # train_gauge_stressm_classifier (vectors list, trainer) go
        # out of scope here.  Force a collection to reclaim them
        # before the next gauge.
        del rng
        gc.collect()

    # ------------------------------------------------------------------
    # 5. Final summary
    # ------------------------------------------------------------------
    elapsed_total = time.time() - t_start
    print(f"\n  {'=' * 50}")
    print(f"  Batch training complete")
    print(f"  Trained  : {n_trained}")
    print(f"  Failed   : {n_failed}")
    print(f"  Elapsed  : {elapsed_total / 60:.1f} min")
    if n_trained > 0:
        print(f"  Avg/gauge: {elapsed_total / n_trained:.1f}s")
    print(f"  {'=' * 50}\n")

    return {
        "trained": n_trained,
        "skipped": already_trained,
        "failed": n_failed,
        "elapsed_seconds": round(elapsed_total, 1),
        "gauges": clf_results,
    }


