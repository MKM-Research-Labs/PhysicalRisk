# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package root __init__.py for full license text)

"""Classifier summary, readiness, and clear-all routes."""

import hashlib
import json
import logging
from pathlib import Path

from flask import jsonify

from config import config
from routes.trading import trading_bp
from routes.trading._helpers import _load_gauge_locations

logger = logging.getLogger(__name__)


def _compute_data_version(stressm_dir: Path) -> str:
    """Compute a short hash reflecting current classifier state on disk."""
    parts = sorted(p.name for p in stressm_dir.glob("GAUGE-*.joblib"))
    summary_path = stressm_dir / "training_summary.json"
    mtime = str(summary_path.stat().st_mtime) if summary_path.exists() else "0"
    raw = "|".join(parts) + "|" + mtime
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


@trading_bp.route("/trading/classifiers/summary", methods=["GET"])
def classifiers_summary():
    """Return all gauges with classifier status, metrics, sorted west->east."""
    try:
        stressm_dir = config.get_classifiers_dir()
        gauge_locations = _load_gauge_locations()

        # Load training summary
        summary_path = stressm_dir / "training_summary.json"
        trained_map = {}
        if summary_path.exists():
            with open(summary_path) as f:
                summary = json.load(f)
            for g in summary.get("gauges", []):
                trained_map[g["gauge_id"]] = g

        # Build response for all gauges (from gauge_locations)
        # Skip synthetic gauges — background-only for PRS pricing
        gauges = []
        for gid, loc in gauge_locations.items():
            if gid.startswith('SYNTH-'):
                continue
            has_model = (stressm_dir / f"{gid}.joblib").exists()
            info = trained_map.get(gid, {})
            metrics = info.get("metrics", {})

            # Only show metrics if the .joblib model actually exists on disk.
            # Prevents stale metrics appearing after Clear All or port re-run.
            if has_model:
                status = info.get("status", "trained")
                auc_roc = metrics.get("auc_roc")
                accuracy = metrics.get("accuracy")
                brier_score = metrics.get("brier_score")
                log_loss = metrics.get("log_loss")
                flood_rate = info.get("flood_rate")
                n_samples = info.get("n_samples")
                feature_importance = info.get("feature_importance")
                label_threshold = info.get("label_threshold")
                severe_level = info.get("severe_level")
                alert_level = info.get("alert_level")
            else:
                status = "not_trained"
                auc_roc = accuracy = brier_score = log_loss = None
                flood_rate = n_samples = None
                feature_importance = None
                label_threshold = severe_level = alert_level = None

            gauges.append({
                "gauge_id": gid,
                "gauge_name": loc.get("name", gid),
                "lat": loc.get("lat", 0),
                "lon": loc.get("lon", 0),
                "has_model": has_model,
                "status": status,
                "auc_roc": auc_roc,
                "accuracy": accuracy,
                "brier_score": brier_score,
                "log_loss": log_loss,
                "flood_rate": flood_rate,
                "n_samples": n_samples,
                "feature_importance": feature_importance,
                "label_threshold": label_threshold,
                "severe_level": severe_level,
                "alert_level": alert_level,
            })

        # Sort west->east by longitude
        gauges.sort(key=lambda g: g["lon"])

        trained = [g for g in gauges if g["has_model"]]
        avg_auc = (
            sum(g["auc_roc"] for g in trained if g["auc_roc"] is not None)
            / max(len([g for g in trained if g["auc_roc"] is not None]), 1)
        )

        return jsonify({
            "status": "success",
            "gauges": gauges,
            "num_total": len(gauges),
            "num_trained": len(trained),
            "avg_auc_roc": round(avg_auc, 4) if trained else None,
            "data_version": _compute_data_version(stressm_dir),
        })

    except Exception as e:
        logger.error("Classifiers summary error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@trading_bp.route("/trading/classifiers/readiness", methods=["GET"])
def classifiers_readiness():
    """Check whether all gauges have trained classifiers."""
    try:
        stressm_dir = config.get_classifiers_dir()
        gauge_locations = _load_gauge_locations()

        # Exclude synthetic gauges from readiness check
        real_gauges = {
            gid: loc for gid, loc in gauge_locations.items()
            if not gid.startswith('SYNTH-')
        }

        total = len(real_gauges)
        trained = sum(
            1 for gid in real_gauges
            if (stressm_dir / f"{gid}.joblib").exists()
        )
        missing = [
            gid for gid in real_gauges
            if not (stressm_dir / f"{gid}.joblib").exists()
        ]

        return jsonify({
            "status": "success",
            "ready": trained == total and total > 0,
            "total": total,
            "trained": trained,
            "missing": len(missing),
        })

    except Exception as e:
        logger.error("Classifiers readiness error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@trading_bp.route("/trading/classifiers/clear-all", methods=["POST"])
def clear_all_classifiers():
    """Delete all trained classifier models and training summary."""
    try:
        stressm_dir = config.get_classifiers_dir()
        removed = 0

        # Remove all .joblib model files
        for p in stressm_dir.glob("*.joblib"):
            p.unlink()
            removed += 1

        # Remove training summary
        summary_path = stressm_dir / "training_summary.json"
        if summary_path.exists():
            summary_path.unlink()

        # Remove timings
        from .batch_training import _TIMINGS_FILENAME
        timings_path = stressm_dir / _TIMINGS_FILENAME
        if timings_path.exists():
            timings_path.unlink()

        logger.info("Cleared %d classifier models from %s", removed, stressm_dir)
        return jsonify({
            "status": "success",
            "removed": removed,
            "message": f"Cleared {removed} classifier(s)",
        })

    except Exception as e:
        logger.error("Clear classifiers error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500
