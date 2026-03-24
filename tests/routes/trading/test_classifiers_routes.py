# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Tests for the Classifiers tab backend endpoints."""

import json
import time
from unittest.mock import patch

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
        classifiers_dir = trading_env["classifiers_dir"]

        # Create a fake trained model + summary
        gid = GAUGE_WESTMINSTER
        (classifiers_dir / f"{gid}.joblib").write_bytes(b"fake_model")
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
                "model_path": str(classifiers_dir / f"{gid}.joblib"),
                "label_threshold": "severe_warning",
            }],
        }
        with open(classifiers_dir / "training_summary.json", "w") as f:
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
        classifiers_dir = trading_env["classifiers_dir"]
        gid = GAUGE_WESTMINSTER
        (classifiers_dir / f"{gid}.joblib").write_bytes(b"fake")
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
        with open(classifiers_dir / "training_summary.json", "w") as f:
            json.dump(summary, f)

        resp = trading_client.get("/api/v1/trading/classifiers/summary")
        data = resp.get_json()
        assert data["num_trained"] == 1
        assert data["avg_auc_roc"] == 0.95


class TestStaleMetricsSupressed:
    """Metrics must not leak through when .joblib is missing."""

    def test_no_model_hides_stale_metrics(self, trading_env, trading_client):
        """Gauge with summary entry but NO .joblib should show null metrics."""
        classifiers_dir = trading_env["classifiers_dir"]
        gid = GAUGE_CHELSEA

        # Write a training summary entry but NO .joblib file
        summary = {
            "gauges": [{
                "gauge_id": gid,
                "status": "trained",
                "metrics": {"auc_roc": 0.99, "accuracy": 0.98,
                             "brier_score": 0.01, "log_loss": 0.04},
                "flood_rate": 0.05,
                "n_samples": 5000,
            }],
        }
        with open(classifiers_dir / "training_summary.json", "w") as f:
            json.dump(summary, f)

        # Ensure no .joblib for this gauge
        joblib_path = classifiers_dir / f"{gid}.joblib"
        if joblib_path.exists():
            joblib_path.unlink()

        resp = trading_client.get("/api/v1/trading/classifiers/summary")
        data = resp.get_json()

        gauge = [g for g in data["gauges"] if g["gauge_id"] == gid][0]
        assert gauge["has_model"] is False
        assert gauge["status"] == "not_trained"
        assert gauge["auc_roc"] is None, "Stale AUC leaked through"
        assert gauge["accuracy"] is None, "Stale accuracy leaked through"
        assert gauge["flood_rate"] is None, "Stale flood_rate leaked through"
        assert gauge["n_samples"] is None, "Stale n_samples leaked through"

    def test_model_present_shows_metrics(self, trading_env, trading_client):
        """Gauge with both .joblib AND summary entry should show metrics."""
        classifiers_dir = trading_env["classifiers_dir"]
        gid = GAUGE_LAMBETH

        (classifiers_dir / f"{gid}.joblib").write_bytes(b"fake")
        summary = {
            "gauges": [{
                "gauge_id": gid,
                "status": "trained",
                "metrics": {"auc_roc": 0.91, "accuracy": 0.90,
                             "brier_score": 0.03, "log_loss": 0.08},
                "flood_rate": 0.12,
                "n_samples": 2000,
            }],
        }
        with open(classifiers_dir / "training_summary.json", "w") as f:
            json.dump(summary, f)

        resp = trading_client.get("/api/v1/trading/classifiers/summary")
        data = resp.get_json()

        gauge = [g for g in data["gauges"] if g["gauge_id"] == gid][0]
        assert gauge["has_model"] is True
        assert gauge["status"] == "trained"
        assert gauge["auc_roc"] == 0.91
        assert gauge["accuracy"] == 0.90

    def test_clear_all_removes_all_metrics(self, trading_env, trading_client):
        """After clear-all, every gauge should show null metrics."""
        classifiers_dir = trading_env["classifiers_dir"]

        # Create some trained gauges
        for gid in (GAUGE_WESTMINSTER, GAUGE_CHELSEA):
            (classifiers_dir / f"{gid}.joblib").write_bytes(b"fake")
        summary = {"gauges": [
            {"gauge_id": GAUGE_WESTMINSTER, "status": "trained",
             "metrics": {"auc_roc": 0.95}},
            {"gauge_id": GAUGE_CHELSEA, "status": "trained",
             "metrics": {"auc_roc": 0.93}},
        ]}
        with open(classifiers_dir / "training_summary.json", "w") as f:
            json.dump(summary, f)

        # Clear all
        resp = trading_client.post("/api/v1/trading/classifiers/clear-all")
        assert resp.get_json()["status"] == "success"

        # Now summary should show all null
        resp = trading_client.get("/api/v1/trading/classifiers/summary")
        data = resp.get_json()
        for g in data["gauges"]:
            assert g["has_model"] is False, f"{g['gauge_id']} still has model"
            assert g["auc_roc"] is None, f"{g['gauge_id']} has stale AUC"
            assert g["status"] == "not_trained", f"{g['gauge_id']} status not reset"


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

    def test_train_all_already_running(self, trading_client):
        """POST while batch is running returns current progress without starting new job."""
        import routes.trading.classifiers as cl_mod
        with cl_mod._batch_lock:
            cl_mod._batch_job = {
                "status": "running",
                "total": 5,
                "completed": 2,
                "current_gauge_id": "GAUGE-test",
                "results": [],
                "started": time.time() - 10,
                "avg_per_gauge": 5.0,
                "gauge_ids": [],
            }

        resp = trading_client.post("/api/v1/trading/classifiers/train-all")
        data = resp.get_json()
        assert data["status"] == "running"
        assert data["completed"] == 2
        assert data["total"] == 5

        cl_mod._batch_job = None

    def test_train_all_all_already_trained(self, trading_env, trading_client):
        """POST when every gauge has a .joblib returns 'complete'."""
        import routes.trading.classifiers as cl_mod
        cl_mod._batch_job = None

        classifiers_dir = trading_env["classifiers_dir"]
        for gid in ALL_TEST_GAUGE_IDS:
            (classifiers_dir / f"{gid}.joblib").write_bytes(b"fake")

        resp = trading_client.post("/api/v1/trading/classifiers/train-all")
        data = resp.get_json()
        assert data["status"] == "complete"
        assert data["message"] == "All gauges already trained"

        cl_mod._batch_job = None

    def test_status_eta_fallback_from_elapsed(self, trading_client):
        """ETA computed from elapsed/completed when avg_per_gauge is 0."""
        import routes.trading.classifiers as cl_mod
        with cl_mod._batch_lock:
            cl_mod._batch_job = {
                "status": "running",
                "total": 10,
                "completed": 5,
                "current_gauge_id": "G-X",
                "results": [],
                "started": time.time() - 50,
                "avg_per_gauge": 0,
                "gauge_ids": [],
            }

        resp = trading_client.get("/api/v1/trading/classifiers/train-all/status")
        data = resp.get_json()
        # remaining = (10-5) * (50/5) = 50
        assert data["eta_seconds"] is not None
        assert data["eta_seconds"] >= 40  # ~50s, allow for timing drift

        cl_mod._batch_job = None

    def test_status_eta_none_when_zero_completed(self, trading_client):
        """ETA is None when no gauges completed yet and no historical avg."""
        import routes.trading.classifiers as cl_mod
        with cl_mod._batch_lock:
            cl_mod._batch_job = {
                "status": "running",
                "total": 10,
                "completed": 0,
                "current_gauge_id": "G-X",
                "results": [],
                "started": time.time() - 5,
                "avg_per_gauge": 0,
                "gauge_ids": [],
            }

        resp = trading_client.get("/api/v1/trading/classifiers/train-all/status")
        data = resp.get_json()
        assert data["eta_seconds"] is None

        cl_mod._batch_job = None


class TestClassifiersReadiness:
    """GET /trading/classifiers/readiness."""

    def test_readiness_no_models(self, trading_client):
        """No .joblib files → ready=False."""
        resp = trading_client.get("/api/v1/trading/classifiers/readiness")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert data["ready"] is False
        assert data["trained"] == 0
        assert data["total"] == len(ALL_TEST_GAUGE_IDS)
        assert data["missing"] == len(ALL_TEST_GAUGE_IDS)

    def test_readiness_partial(self, trading_env, trading_client):
        """Some gauges trained → ready=False, correct counts."""
        classifiers_dir = trading_env["classifiers_dir"]
        (classifiers_dir / f"{GAUGE_WESTMINSTER}.joblib").write_bytes(b"fake")
        (classifiers_dir / f"{GAUGE_CHELSEA}.joblib").write_bytes(b"fake")

        resp = trading_client.get("/api/v1/trading/classifiers/readiness")
        data = resp.get_json()
        assert data["ready"] is False
        assert data["trained"] == 2
        assert data["missing"] == data["total"] - 2

    def test_readiness_all_trained(self, trading_env, trading_client):
        """All gauges have .joblib → ready=True."""
        classifiers_dir = trading_env["classifiers_dir"]
        for gid in ALL_TEST_GAUGE_IDS:
            (classifiers_dir / f"{gid}.joblib").write_bytes(b"fake")

        resp = trading_client.get("/api/v1/trading/classifiers/readiness")
        data = resp.get_json()
        assert data["ready"] is True
        assert data["trained"] == data["total"]
        assert data["missing"] == 0

    def test_readiness_error(self, trading_client, monkeypatch):
        """Internal error → 500 with error status."""
        from config import config
        monkeypatch.setattr(config, "get_classifiers_dir",
                            lambda: (_ for _ in ()).throw(RuntimeError("boom")))

        resp = trading_client.get("/api/v1/trading/classifiers/readiness")
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["status"] == "error"
        assert "boom" in data["message"]


class TestClearAllClassifiers:
    """POST /trading/classifiers/clear-all."""

    def test_clear_empty(self, trading_env, trading_client):
        """No models to clear → removed=0."""
        resp = trading_client.post("/api/v1/trading/classifiers/clear-all")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert data["removed"] == 0

    def test_clear_removes_models(self, trading_env, trading_client):
        """Clears .joblib files and training_summary.json."""
        classifiers_dir = trading_env["classifiers_dir"]
        for gid in [GAUGE_WESTMINSTER, GAUGE_CHELSEA, GAUGE_LAMBETH]:
            (classifiers_dir / f"{gid}.joblib").write_bytes(b"fake")
        (classifiers_dir / "training_summary.json").write_text("{}")
        (classifiers_dir / "classifier_timings.json").write_text("{}")

        resp = trading_client.post("/api/v1/trading/classifiers/clear-all")
        data = resp.get_json()
        assert data["status"] == "success"
        assert data["removed"] == 3

        # Verify files are gone
        assert not list(classifiers_dir.glob("*.joblib"))
        assert not (classifiers_dir / "training_summary.json").exists()
        assert not (classifiers_dir / "classifier_timings.json").exists()

    def test_clear_error(self, trading_client, monkeypatch):
        """Internal error → 500."""
        from config import config
        monkeypatch.setattr(config, "get_classifiers_dir",
                            lambda: (_ for _ in ()).throw(RuntimeError("disk")))

        resp = trading_client.post("/api/v1/trading/classifiers/clear-all")
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["status"] == "error"


class TestTimingsHelpers:
    """Unit tests for _load_timings, _save_timings, _avg_per_gauge_seconds."""

    def test_load_timings_missing_file(self, tmp_path):
        from routes.trading.classifiers import _load_timings
        result = _load_timings(tmp_path)
        assert result == {"runs": []}

    def test_load_timings_valid(self, tmp_path):
        from routes.trading.classifiers import _load_timings
        data = {"runs": [{"num_gauges": 5, "elapsed_seconds": 100}]}
        (tmp_path / "classifier_timings.json").write_text(json.dumps(data))

        result = _load_timings(tmp_path)
        assert len(result["runs"]) == 1
        assert result["runs"][0]["num_gauges"] == 5

    def test_load_timings_corrupt_json(self, tmp_path):
        from routes.trading.classifiers import _load_timings
        (tmp_path / "classifier_timings.json").write_text("not json{{{")

        result = _load_timings(tmp_path)
        assert result == {"runs": []}

    def test_save_timings_truncates_to_20(self, tmp_path):
        from routes.trading.classifiers import _save_timings
        timings = {"runs": [{"i": i} for i in range(30)]}
        _save_timings(tmp_path, timings)

        with open(tmp_path / "classifier_timings.json") as f:
            saved = json.load(f)
        assert len(saved["runs"]) == 20
        # Keeps the last 20 (indices 10-29)
        assert saved["runs"][0]["i"] == 10

    def test_avg_per_gauge_seconds_empty(self):
        from routes.trading.classifiers import _avg_per_gauge_seconds
        assert _avg_per_gauge_seconds({"runs": []}) == 0.0

    def test_avg_per_gauge_seconds(self):
        from routes.trading.classifiers import _avg_per_gauge_seconds
        timings = {"runs": [
            {"elapsed_seconds": 100, "num_gauges": 10},
            {"elapsed_seconds": 60, "num_gauges": 5},
        ]}
        # total_time=160, total_gauges=15 → 160/15 ≈ 10.667
        result = _avg_per_gauge_seconds(timings)
        assert abs(result - 160 / 15) < 0.001


class TestSummaryEdgeCases:
    """Edge cases for classifiers_summary."""

    def test_avg_auc_null_when_no_trained(self, trading_client):
        """avg_auc_roc is None when no gauges are trained."""
        resp = trading_client.get("/api/v1/trading/classifiers/summary")
        data = resp.get_json()
        assert data["avg_auc_roc"] is None

    def test_trained_without_auc(self, trading_env, trading_client):
        """Gauge with .joblib but no auc_roc in summary still counted as trained."""
        classifiers_dir = trading_env["classifiers_dir"]
        gid = GAUGE_WESTMINSTER
        (classifiers_dir / f"{gid}.joblib").write_bytes(b"fake")
        summary = {"gauges": [{
            "gauge_id": gid,
            "status": "trained",
            "metrics": {},
        }]}
        with open(classifiers_dir / "training_summary.json", "w") as f:
            json.dump(summary, f)

        resp = trading_client.get("/api/v1/trading/classifiers/summary")
        data = resp.get_json()
        assert data["num_trained"] == 1
        # avg_auc_roc = 0/1 = 0.0 (only trained gauge has no auc)
        assert data["avg_auc_roc"] == 0.0

    def test_summary_error(self, trading_client, monkeypatch):
        """Internal error → 500."""
        from config import config
        monkeypatch.setattr(config, "get_classifiers_dir",
                            lambda: (_ for _ in ()).throw(RuntimeError("oops")))

        resp = trading_client.get("/api/v1/trading/classifiers/summary")
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["status"] == "error"

    def test_multiple_trained_avg_auc(self, trading_env, trading_client):
        """avg_auc_roc averages correctly over multiple trained gauges."""
        classifiers_dir = trading_env["classifiers_dir"]
        gauges_data = []
        for gid, auc in [(GAUGE_WESTMINSTER, 0.90), (GAUGE_CHELSEA, 0.80)]:
            (classifiers_dir / f"{gid}.joblib").write_bytes(b"fake")
            gauges_data.append({
                "gauge_id": gid,
                "status": "trained",
                "metrics": {"auc_roc": auc, "accuracy": 0.9,
                             "brier_score": 0.02, "log_loss": 0.05},
            })
        with open(classifiers_dir / "training_summary.json", "w") as f:
            json.dump({"gauges": gauges_data}, f)

        resp = trading_client.get("/api/v1/trading/classifiers/summary")
        data = resp.get_json()
        assert data["num_trained"] == 2
        assert data["avg_auc_roc"] == 0.85

    def test_gauge_all_fields_present(self, trading_env, trading_client):
        """Verify all expected gauge fields are in the response."""
        classifiers_dir = trading_env["classifiers_dir"]
        gid = GAUGE_WESTMINSTER
        (classifiers_dir / f"{gid}.joblib").write_bytes(b"fake")
        summary = {"gauges": [{
            "gauge_id": gid,
            "status": "trained",
            "metrics": {"auc_roc": 0.95, "accuracy": 0.96,
                         "brier_score": 0.01, "log_loss": 0.04},
            "flood_rate": 0.09,
            "n_samples": 1000,
            "feature_importance": {"log_h_s": 0.8},
            "label_threshold": "severe_warning",
            "severe_level": 5.0,
            "alert_level": 3.0,
        }]}
        with open(classifiers_dir / "training_summary.json", "w") as f:
            json.dump(summary, f)

        resp = trading_client.get("/api/v1/trading/classifiers/summary")
        g = next(g for g in resp.get_json()["gauges"] if g["gauge_id"] == gid)
        expected_fields = [
            "gauge_id", "gauge_name", "lat", "lon", "has_model", "status",
            "auc_roc", "accuracy", "brier_score", "log_loss",
            "flood_rate", "n_samples", "feature_importance",
            "label_threshold", "severe_level", "alert_level",
        ]
        for field in expected_fields:
            assert field in g, f"Missing field: {field}"


class TestRunBatchTraining:
    """Tests for _run_batch_training helper."""

    def test_successful_batch(self, trading_env):
        """Batch trains gauges and records timings."""
        import routes.trading.classifiers as cl_mod

        classifiers_dir = trading_env["classifiers_dir"]
        gauge_ids = [GAUGE_WESTMINSTER, GAUGE_CHELSEA]

        with cl_mod._batch_lock:
            cl_mod._batch_job = {
                "status": "running",
                "total": 2,
                "completed": 0,
                "current_gauge_id": None,
                "results": [],
                "started": time.time(),
                "avg_per_gauge": 0,
                "gauge_ids": gauge_ids,
            }

        with patch("routes.trading.stress.training._train_single_gauge"):
            cl_mod._run_batch_training(gauge_ids)

        assert cl_mod._batch_job["status"] == "complete"
        assert cl_mod._batch_job["completed"] == 2
        assert len(cl_mod._batch_job["results"]) == 2
        assert all(r["status"] == "trained" for r in cl_mod._batch_job["results"])

        # Check timings were saved
        timings_path = classifiers_dir / "classifier_timings.json"
        assert timings_path.exists()
        with open(timings_path) as f:
            timings = json.load(f)
        assert len(timings["runs"]) == 1
        assert timings["runs"][0]["num_gauges"] == 2

        cl_mod._batch_job = None

    def test_batch_with_failure(self, trading_env):
        """Failed gauge training is recorded as 'failed' in results."""
        import routes.trading.classifiers as cl_mod

        gauge_ids = [GAUGE_WESTMINSTER, GAUGE_CHELSEA]

        with cl_mod._batch_lock:
            cl_mod._batch_job = {
                "status": "running",
                "total": 2,
                "completed": 0,
                "current_gauge_id": None,
                "results": [],
                "started": time.time(),
                "avg_per_gauge": 0,
                "gauge_ids": gauge_ids,
            }

        def side_effect(gid):
            if gid == GAUGE_CHELSEA:
                raise RuntimeError("training failed")

        with patch("routes.trading.stress.training._train_single_gauge",
                    side_effect=side_effect):
            cl_mod._run_batch_training(gauge_ids)

        assert cl_mod._batch_job["status"] == "complete"
        results = cl_mod._batch_job["results"]
        assert results[0]["status"] == "trained"
        assert results[1]["status"] == "failed"
        assert "training failed" in results[1]["error"]

        cl_mod._batch_job = None

    def test_batch_cancelled_mid_run(self, trading_env):
        """Setting _batch_job to None mid-run stops processing."""
        import routes.trading.classifiers as cl_mod

        gauge_ids = [GAUGE_WESTMINSTER, GAUGE_CHELSEA, GAUGE_LAMBETH]

        with cl_mod._batch_lock:
            cl_mod._batch_job = {
                "status": "running",
                "total": 3,
                "completed": 0,
                "current_gauge_id": None,
                "results": [],
                "started": time.time(),
                "avg_per_gauge": 0,
                "gauge_ids": gauge_ids,
            }

        call_count = 0

        def side_effect(gid):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                with cl_mod._batch_lock:
                    cl_mod._batch_job = None

        with patch("routes.trading.stress.training._train_single_gauge",
                    side_effect=side_effect):
            cl_mod._run_batch_training(gauge_ids)

        # Only first gauge was trained before cancellation caused early return
        assert call_count == 1
        assert cl_mod._batch_job is None
