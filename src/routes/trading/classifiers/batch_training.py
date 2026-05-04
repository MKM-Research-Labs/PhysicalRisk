# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package root __init__.py for full license text)

"""Batch classifier training routes and background worker."""

import json
import logging
import threading
import time
from pathlib import Path

from flask import jsonify

from config import config
from routes.trading import trading_bp
from routes.trading._admin_auth import require_admin_password
from routes.trading._helpers import _load_gauge_locations

logger = logging.getLogger(__name__)

# ── batch training state ──────────────────────────────────────────────
_batch_job = None      # dict or None
_batch_lock = threading.Lock()

_TIMINGS_FILENAME = "classifier_timings.json"


def _load_timings(stressm_dir: Path) -> dict:
    """Load historical classifier training timings."""
    path = stressm_dir / _TIMINGS_FILENAME
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return {"runs": []}


def _save_timings(stressm_dir: Path, timings: dict) -> None:
    """Save classifier training timings (keep last 20 runs)."""
    timings["runs"] = timings["runs"][-20:]
    path = stressm_dir / _TIMINGS_FILENAME
    with open(path, "w") as f:
        json.dump(timings, f, indent=2)


def _avg_per_gauge_seconds(timings: dict) -> float:
    """Return average seconds per gauge from historical runs."""
    runs = timings.get("runs", [])
    if not runs:
        return 0.0
    total_time = sum(r.get("elapsed_seconds", 0) for r in runs)
    total_gauges = sum(r.get("num_gauges", 1) for r in runs)
    return total_time / max(total_gauges, 1)


@trading_bp.route("/trading/classifiers/train-all", methods=["POST"])
@require_admin_password
def train_all_classifiers():
    """Start batch training for all untrained gauges."""
    global _batch_job

    with _batch_lock:
        if _batch_job and _batch_job["status"] == "running":
            return jsonify({
                "status": "running",
                "message": "Batch training already in progress",
                "completed": _batch_job["completed"],
                "total": _batch_job["total"],
            })

    try:
        stressm_dir = config.get_classifiers_dir()
        gauge_locations = _load_gauge_locations()

        # Find untrained gauges (skip synthetic — background-only for PRS)
        untrained = []
        for gid in gauge_locations:
            if gid.startswith('SYNTH-'):
                continue
            if not (stressm_dir / f"{gid}.joblib").exists():
                untrained.append(gid)

        if not untrained:
            return jsonify({
                "status": "complete",
                "message": "All gauges already trained",
                "completed": 0,
                "total": 0,
            })

        # Load historical timings for ETA
        timings = _load_timings(stressm_dir)
        avg_per_gauge = _avg_per_gauge_seconds(timings)

        with _batch_lock:
            _batch_job = {
                "status": "running",
                "total": len(untrained),
                "completed": 0,
                "current_gauge_id": None,
                "results": [],
                "started": time.time(),
                "avg_per_gauge": avg_per_gauge,
                "gauge_ids": untrained,
            }

        thread = threading.Thread(
            target=_run_batch_training,
            args=(untrained,),
            daemon=True,
        )
        thread.start()

        eta = round(avg_per_gauge * len(untrained)) if avg_per_gauge > 0 else None

        return jsonify({
            "status": "running",
            "total": len(untrained),
            "completed": 0,
            "eta_seconds": eta,
            "message": f"Training {len(untrained)} classifiers...",
        })

    except Exception as e:
        logger.error("Train-all start error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


def _run_batch_training(gauge_ids: list):
    """Run classifier training for multiple gauges sequentially."""
    global _batch_job

    from routes.trading.stress.training import _train_single_gauge

    stressm_dir = config.get_classifiers_dir()
    t_start = time.time()

    for i, gid in enumerate(gauge_ids):
        with _batch_lock:
            if _batch_job is None:
                return  # cancelled or reset
            _batch_job["current_gauge_id"] = gid

        try:
            # Use the existing single-gauge training function
            t_gauge = time.time()
            _train_single_gauge(gid)
            gauge_elapsed = time.time() - t_gauge

            # Read back metrics from training_summary.json
            gauge_metrics = {}
            try:
                summary_path = stressm_dir / "training_summary.json"
                if summary_path.exists():
                    with open(summary_path) as _f:
                        _summary = json.load(_f)
                    for _g in _summary.get("gauges", []):
                        if _g.get("gauge_id") == gid:
                            gauge_metrics = _g.get("metrics", {})
                            break
            except Exception:
                pass

            with _batch_lock:
                if _batch_job is None:
                    return
                _batch_job["completed"] = i + 1
                _batch_job["results"].append({
                    "gauge_id": gid,
                    "status": "trained",
                    "elapsed_seconds": round(gauge_elapsed, 1),
                    "auc_roc": gauge_metrics.get("auc_roc"),
                    "accuracy": gauge_metrics.get("accuracy"),
                })

        except Exception as exc:
            logger.error("Batch training failed for %s: %s", gid, exc)
            gauge_elapsed = time.time() - t_gauge
            with _batch_lock:
                if _batch_job is None:
                    return
                _batch_job["completed"] = i + 1
                _batch_job["results"].append({
                    "gauge_id": gid,
                    "status": "failed",
                    "elapsed_seconds": round(gauge_elapsed, 1),
                    "error": str(exc),
                })

    elapsed = time.time() - t_start

    with _batch_lock:
        if _batch_job is None:
            return
        results = list(_batch_job.get("results", []))

    # Save timing for future ETA estimates
    timings = _load_timings(stressm_dir)
    num_trained = sum(1 for r in results if r["status"] == "trained")
    timings["runs"].append({
        "num_gauges": len(gauge_ids),
        "num_trained": num_trained,
        "elapsed_seconds": round(elapsed, 2),
        "avg_per_gauge_seconds": round(elapsed / max(len(gauge_ids), 1), 2),
    })
    _save_timings(stressm_dir, timings)

    with _batch_lock:
        if _batch_job is not None:
            _batch_job["status"] = "complete"
            _batch_job["current_gauge_id"] = None

    logger.info("Batch training complete: %d/%d trained (%.1fs)",
                num_trained, len(gauge_ids), elapsed)


@trading_bp.route("/trading/classifiers/train-all/status", methods=["GET"])
def train_all_status():
    """Return batch training progress."""
    with _batch_lock:
        if _batch_job is None:
            return jsonify({"status": "idle", "message": "No batch training in progress"})

        completed = _batch_job["completed"]
        total = _batch_job["total"]
        status = _batch_job["status"]
        current = _batch_job.get("current_gauge_id")
        avg_pg = _batch_job.get("avg_per_gauge", 0)
        elapsed = time.time() - _batch_job["started"]

        # Compute ETA
        if avg_pg > 0:
            remaining = (total - completed) * avg_pg
        elif completed > 0:
            remaining = (total - completed) * (elapsed / completed)
        else:
            remaining = None

        results = list(_batch_job.get("results", []))

        # Running averages from trained gauges
        trained_results = [r for r in results if r.get("status") == "trained"]
        avg_auc = None
        avg_accuracy = None
        if trained_results:
            aucs = [r["auc_roc"] for r in trained_results if r.get("auc_roc") is not None]
            accs = [r["accuracy"] for r in trained_results if r.get("accuracy") is not None]
            if aucs:
                avg_auc = round(sum(aucs) / len(aucs), 4)
            if accs:
                avg_accuracy = round(sum(accs) / len(accs), 4)

        num_failed = sum(1 for r in results if r.get("status") == "failed")
        num_skipped = sum(1 for r in results if r.get("status") == "skipped")

        resp = {
            "status": status,
            "total": total,
            "completed": completed,
            "current_gauge_id": current,
            "pct": round(completed / max(total, 1) * 100, 1),
            "elapsed_seconds": round(elapsed),
            "eta_seconds": round(remaining) if remaining is not None else None,
            "results": results,
            "avg_auc": avg_auc,
            "avg_accuracy": avg_accuracy,
            "num_trained": len(trained_results),
            "num_failed": num_failed,
            "num_skipped": num_skipped,
        }

        return jsonify(resp)
