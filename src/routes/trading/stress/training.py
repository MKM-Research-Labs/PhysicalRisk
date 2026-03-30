# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""On-demand classifier training endpoints.

Provides:
  GET  /trading/stress/classifier-status/<gauge_id>  — check if classifier exists
  POST /trading/stress/train/<gauge_id>              — kick off background training

When a gauge has no trained classifier, the frontend can request training via
the POST endpoint.  Training runs in a background daemon thread; the frontend
polls the status endpoint every few seconds until the classifier is ready.
"""

import json
import logging
import threading
import time
from pathlib import Path

from flask import jsonify

from config import config
from .. import trading_bp

logger = logging.getLogger(__name__)

# Module-level dict to track training jobs.
# gauge_id -> {"status": "training"|"ready"|"failed", "started": float, "error": str|None}
_training_jobs: dict = {}
_training_lock = threading.Lock()


@trading_bp.route("/trading/stress/classifier-status/<gauge_id>", methods=["GET"])
def classifier_status(gauge_id):
    """Check whether a trained classifier exists for a gauge."""
    stressm_dir = config.get_classifiers_dir()
    joblib_path = stressm_dir / f"{gauge_id}.joblib"

    if joblib_path.exists():
        return jsonify({"status": "ready", "gauge_id": gauge_id})

    with _training_lock:
        job = _training_jobs.get(gauge_id)

    if job:
        if job["status"] == "training":
            elapsed = time.time() - job["started"]
            return jsonify({
                "status": "training",
                "gauge_id": gauge_id,
                "elapsed_seconds": round(elapsed),
                "message": f"Training classifier for {gauge_id}... ({round(elapsed)}s)",
            })
        if job["status"] == "ready":
            return jsonify({"status": "ready", "gauge_id": gauge_id})
        if job["status"] == "failed":
            return jsonify({
                "status": "failed",
                "gauge_id": gauge_id,
                "error": job.get("error", "Unknown error"),
            })

    return jsonify({"status": "not_trained", "gauge_id": gauge_id})


@trading_bp.route("/trading/stress/train/<gauge_id>", methods=["POST"])
def train_classifier(gauge_id):
    """Start background training for a single gauge classifier."""
    stressm_dir = config.get_classifiers_dir()

    # Already trained?
    if (stressm_dir / f"{gauge_id}.joblib").exists():
        return jsonify({"status": "ready", "gauge_id": gauge_id})

    # Already in progress?
    with _training_lock:
        job = _training_jobs.get(gauge_id)
        if job and job["status"] == "training":
            elapsed = time.time() - job["started"]
            return jsonify({
                "status": "training",
                "gauge_id": gauge_id,
                "elapsed_seconds": round(elapsed),
            })

    # Validate gauge exists in gauge.json
    gauge_path = config.get_input_dir() / "gauge.json"
    if not gauge_path.exists():
        return jsonify({
            "status": "error",
            "message": "gauge.json not found",
        }), 404

    try:
        with open(gauge_path) as f:
            gauge_json = json.load(f)
        raw_gauges = gauge_json.get("flood_gauges", [])
        if isinstance(raw_gauges, dict):
            raw_gauges = list(raw_gauges.values())
        gauge_ids = []
        for rec in raw_gauges:
            fg = rec.get("FloodGauge", rec)
            gid = fg.get("Header", {}).get("GaugeID") or fg.get("gauge_id")
            if gid:
                gauge_ids.append(gid)
        if gauge_id not in gauge_ids:
            return jsonify({
                "status": "error",
                "message": f"Gauge {gauge_id} not found in gauge.json",
            }), 404
    except Exception as exc:
        return jsonify({
            "status": "error",
            "message": f"Error reading gauge.json: {exc}",
        }), 500

    # Check storm_sequences.json exists (required for training)
    seq_path = config.get_input_dir() / "storm_sequences.json"
    if not seq_path.exists():
        return jsonify({
            "status": "error",
            "message": "storm_sequences.json not found. Run 'app.py port --stressm' first.",
        }), 404

    # Start background training
    with _training_lock:
        _training_jobs[gauge_id] = {
            "status": "training",
            "started": time.time(),
            "error": None,
        }

    thread = threading.Thread(
        target=_train_single_gauge,
        args=(gauge_id,),
        daemon=True,
    )
    thread.start()

    return jsonify({
        "status": "training",
        "gauge_id": gauge_id,
        "message": (
            f"Training started for {gauge_id}. "
            f"Poll /trading/stress/classifier-status/{gauge_id} for progress."
        ),
    })


def _train_single_gauge(gauge_id: str):
    """Train a single gauge classifier in a background thread."""
    try:
        import numpy as np
        from port.src.stressm.classifier import train_gauge_stressm_classifier
        from port.src.stressm.summary import load_gauge_training_context
        from port.src.storm_multi.utils.serialization import load_sequences

        input_dir = config.get_input_dir()
        output_dir = config.get_output_dir()

        # Load gauge data and spatial model
        all_gauges, all_gauge_ids, spatial_model = load_gauge_training_context(input_dir)

        # Find target gauge
        target = [g for g in all_gauges if g["gauge_id"] == gauge_id]
        if not target:
            with _training_lock:
                _training_jobs[gauge_id] = {
                    "status": "failed",
                    "started": _training_jobs[gauge_id]["started"],
                    "error": f"Gauge {gauge_id} not found after parsing",
                }
            return

        target_idx = all_gauge_ids.index(gauge_id)

        # Load sequences
        seq_path = input_dir / "storm_sequences.json"
        sequences = load_sequences(seq_path)

        # Train — write classifier to classifiers/ dir (not output/stressm/)
        result = train_gauge_stressm_classifier(
            sequences=sequences,
            gauge=target[0],
            spatial_model=spatial_model,
            target_spatial_index=target_idx,
            output_dir=output_dir,
            rng=np.random.RandomState(42),
            classifiers_dir=config.get_classifiers_dir(),
        )

        # Update training_summary.json (merge with existing)
        from port.src.stressm.summary import update_training_summary
        update_training_summary(result, config.get_classifiers_dir())

        with _training_lock:
            _training_jobs[gauge_id] = {
                "status": "ready",
                "started": _training_jobs[gauge_id]["started"],
                "error": None,
            }
        logger.info("Classifier training complete for %s", gauge_id)

    except Exception as exc:
        logger.error("Classifier training failed for %s: %s",
                     gauge_id, exc, exc_info=True)
        with _training_lock:
            _training_jobs[gauge_id] = {
                "status": "failed",
                "started": _training_jobs.get(gauge_id, {}).get("started", 0),
                "error": str(exc),
            }


