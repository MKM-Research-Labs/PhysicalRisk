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

"""Tests for classifier summary endpoint — metrics, stale suppression."""

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
