# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Tests for classifier timing helpers and summary edge cases."""

import json
import time
from unittest.mock import patch

import pytest

from ._data import (
    GAUGE_WESTMINSTER, GAUGE_CHELSEA, GAUGE_LAMBETH,
    ALL_TEST_GAUGE_IDS,
)


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
