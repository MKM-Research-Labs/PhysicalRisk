# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Tests for the Classifiers tab backend endpoints."""

import json

import pytest

from ._data import (
    GAUGE_WESTMINSTER, GAUGE_CHELSEA, GAUGE_LAMBETH,
    ALL_TEST_GAUGE_IDS,
)


class TestClassifiersSummary:
    """GET /trading/classifiers/summary."""

    def test_returns_success(self, trading_client):
        resp = trading_client.get("/api/v1/trading/classifiers/summary")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"

    def test_returns_all_gauges(self, trading_client):
        resp = trading_client.get("/api/v1/trading/classifiers/summary")
        data = resp.get_json()
        assert "gauges" in data
        assert data["num_total"] > 0

    def test_gauge_fields(self, trading_client):
        resp = trading_client.get("/api/v1/trading/classifiers/summary")
        data = resp.get_json()
        gauges = data["gauges"]
        if gauges:
            g = gauges[0]
            assert "gauge_id" in g
            assert "gauge_name" in g
            assert "has_model" in g
            assert "status" in g
            assert "auc_roc" in g
            assert "feature_importance" in g

    def test_no_models_initially(self, trading_client):
        """No .joblib files → all gauges show has_model=False."""
        resp = trading_client.get("/api/v1/trading/classifiers/summary")
        data = resp.get_json()
        assert data["num_trained"] == 0
        for g in data["gauges"]:
            assert g["has_model"] is False

    def test_trained_gauge_shows_metrics(self, trading_env, trading_client):
        """When training_summary.json + .joblib exist, metrics appear."""
        stressm_dir = trading_env["stressm_dir"]

        # Create a fake trained model + summary
        gid = GAUGE_WESTMINSTER
        (stressm_dir / f"{gid}.joblib").write_bytes(b"fake_model")
        summary = {
            "num_gauges": 1,
            "num_trained": 1,
            "num_skipped": 0,
            "avg_auc_roc": 0.9925,
            "gauges": [{
                "gauge_id": gid,
                "status": "trained",
                "alert_level": 3.18,
                "severe_level": 5.04,
                "n_samples": 3393600,
                "n_positive": 306064,
                "n_negative": 3087536,
                "flood_rate": 0.0902,
                "test_size": 678720,
                "metrics": {
                    "accuracy": 0.9768,
                    "auc_roc": 0.9925,
                    "brier_score": 0.0174,
                    "log_loss": 0.0607,
                },
                "feature_importance": {
                    "log_h_s": 0.7655,
                    "log_t_end": 0.1652,
                    "delta_log_h": 0.066,
                    "delta2_log_h": 0.0034,
                },
                "model_path": str(stressm_dir / f"{gid}.joblib"),
                "label_threshold": "severe_warning",
            }],
        }
        with open(stressm_dir / "training_summary.json", "w") as f:
            json.dump(summary, f)

        resp = trading_client.get("/api/v1/trading/classifiers/summary")
        data = resp.get_json()

        trained = [g for g in data["gauges"] if g["gauge_id"] == gid]
        assert len(trained) == 1
        g = trained[0]
        assert g["has_model"] is True
        assert g["auc_roc"] == 0.9925
        assert g["accuracy"] == 0.9768
        assert g["flood_rate"] == 0.0902
        assert g["feature_importance"]["log_h_s"] == 0.7655

    def test_gauges_sorted_by_longitude(self, trading_client):
        resp = trading_client.get("/api/v1/trading/classifiers/summary")
        data = resp.get_json()
        lons = [g["lon"] for g in data["gauges"]]
        assert lons == sorted(lons)

    def test_avg_auc_computed(self, trading_env, trading_client):
        stressm_dir = trading_env["stressm_dir"]
        gid = GAUGE_WESTMINSTER
        (stressm_dir / f"{gid}.joblib").write_bytes(b"fake")
        summary = {
            "gauges": [{
                "gauge_id": gid,
                "status": "trained",
                "metrics": {"auc_roc": 0.95, "accuracy": 0.95,
                             "brier_score": 0.02, "log_loss": 0.05},
                "flood_rate": 0.1,
                "n_samples": 1000,
            }],
        }
        with open(stressm_dir / "training_summary.json", "w") as f:
            json.dump(summary, f)

        resp = trading_client.get("/api/v1/trading/classifiers/summary")
        data = resp.get_json()
        assert data["num_trained"] == 1
        assert data["avg_auc_roc"] == 0.95


class TestBatchTraining:
    """POST /trading/classifiers/train-all + GET status."""

    def test_train_all_starts(self, trading_client):
        """POST returns running or complete."""
        resp = trading_client.post("/api/v1/trading/classifiers/train-all")
        data = resp.get_json()
        # Either 'running' (gauges found to train) or 'complete' (all already trained)
        # or 'error' (missing storm_sequences.json etc.)
        assert data["status"] in ("running", "complete", "error")

    def test_train_all_status_idle(self, trading_client):
        """Status endpoint returns idle when no batch is running."""
        # Reset batch job state
        import routes.trading.classifiers as cl_mod
        cl_mod._batch_job = None

        resp = trading_client.get("/api/v1/trading/classifiers/train-all/status")
        data = resp.get_json()
        assert data["status"] == "idle"

    def test_train_all_status_fields(self, trading_client):
        """Status endpoint returns expected fields when batch is running."""
        import routes.trading.classifiers as cl_mod
        import time
        with cl_mod._batch_lock:
            cl_mod._batch_job = {
                "status": "running",
                "total": 10,
                "completed": 3,
                "current_gauge_id": "GAUGE-test",
                "results": [],
                "started": time.time() - 30,
                "avg_per_gauge": 10.0,
                "gauge_ids": [],
            }

        resp = trading_client.get("/api/v1/trading/classifiers/train-all/status")
        data = resp.get_json()
        assert data["status"] == "running"
        assert data["total"] == 10
        assert data["completed"] == 3
        assert data["current_gauge_id"] == "GAUGE-test"
        assert data["pct"] == 30.0
        assert data["eta_seconds"] is not None

        # Cleanup
        cl_mod._batch_job = None

    def test_train_all_complete_includes_results(self, trading_client):
        """Complete status includes results list."""
        import routes.trading.classifiers as cl_mod
        import time
        with cl_mod._batch_lock:
            cl_mod._batch_job = {
                "status": "complete",
                "total": 2,
                "completed": 2,
                "current_gauge_id": None,
                "results": [
                    {"gauge_id": "G1", "status": "trained"},
                    {"gauge_id": "G2", "status": "trained"},
                ],
                "started": time.time() - 60,
                "avg_per_gauge": 30.0,
                "gauge_ids": [],
            }

        resp = trading_client.get("/api/v1/trading/classifiers/train-all/status")
        data = resp.get_json()
        assert data["status"] == "complete"
        assert len(data["results"]) == 2

        cl_mod._batch_job = None
