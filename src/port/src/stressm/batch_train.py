# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

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
import json
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
    from port.src.storm_multi.models.spatial_correlation import SpatialCorrelationModel
    from port.src.storm_multi.utils.serialization import load_sequences

    from .classifier import _print_classifier_result, train_gauge_stressm_classifier
    from .gauge_parser import _extract_gauges, _load_gaugehd_baselines, _parse_gauge

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    stressm_dir = output_dir / "stressm"
    stressm_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Load gauge portfolio
    # ------------------------------------------------------------------
    gauge_path = input_dir / "gauge.json"
    if not gauge_path.exists():
        raise FileNotFoundError(f"gauge.json not found at {gauge_path}")

    with open(gauge_path) as f:
        gauge_json = json.load(f)

    baselines = _load_gaugehd_baselines(input_dir / "gaugehd")
    raw_gauges = _extract_gauges(gauge_json)
    all_gauges = [
        p for r in raw_gauges
        if (p := _parse_gauge(r, baselines)) is not None
    ]

    if not all_gauges:
        print("  No valid gauges found in gauge.json")
        return {"trained": 0, "skipped": 0, "failed": 0}

    # ------------------------------------------------------------------
    # 2. Identify untrained gauges
    # ------------------------------------------------------------------
    all_gauge_ids = [g["gauge_id"] for g in all_gauges]
    untrained = [
        g for g in all_gauges
        if not (stressm_dir / f"{g['gauge_id']}.joblib").exists()
    ]
    already_trained = len(all_gauges) - len(untrained)

    print("\n  Batch Classifier Training")
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
    seq_path = input_dir / "storm_sequences.json"
    if not seq_path.exists():
        raise FileNotFoundError(
            f"storm_sequences.json not found at {seq_path}. "
            f"Run 'python app.py port --stressm' first."
        )

    print("  Loading storm sequences...", flush=True)
    sequences = load_sequences(seq_path)
    print(f"  Loaded {len(sequences):,} sequences", flush=True)

    all_locations = [(g["lat"], g["lon"]) for g in all_gauges]
    spatial_model = SpatialCorrelationModel(all_locations)

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
            _update_training_summary(result, stressm_dir)
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
    print("  Batch training complete")
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


def _update_training_summary(result: dict, stressm_dir: Path):
    """Merge a single gauge result into training_summary.json (incremental save)."""
    summary_path = stressm_dir / "training_summary.json"

    if summary_path.exists():
        with open(summary_path) as f:
            summary = json.load(f)
    else:
        summary = {"num_gauges": 0, "num_trained": 0,
                   "num_skipped": 0, "avg_auc_roc": 0, "gauges": []}

    gauges = [g for g in summary.get("gauges", [])
              if g.get("gauge_id") != result.get("gauge_id")]
    gauges.append(result)

    trained = [g for g in gauges if g.get("status") == "trained"]
    avg_auc = (
        sum(g["metrics"]["auc_roc"] for g in trained) / len(trained)
        if trained else 0.0
    )
    summary["num_gauges"] = len(gauges)
    summary["num_trained"] = len(trained)
    summary["num_skipped"] = len(gauges) - len(trained)
    summary["avg_auc_roc"] = round(avg_auc, 4)
    summary["gauges"] = gauges

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
