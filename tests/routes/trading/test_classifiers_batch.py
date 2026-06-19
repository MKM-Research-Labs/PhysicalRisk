# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for batch training, readiness, and clear-all endpoints."""

import json
import time
from unittest.mock import patch

import pytest

from ._data import (
    GAUGE_WESTMINSTER, GAUGE_CHELSEA, GAUGE_LAMBETH,
    ALL_TEST_GAUGE_IDS,
)


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
        import routes.trading.classifiers.batch_training as cl_mod
        cl_mod._batch_job = None

        resp = trading_client.get("/api/v1/trading/classifiers/train-all/status")
        data = resp.get_json()
        assert data["status"] == "idle"

    def test_train_all_status_fields(self, trading_client):
        """Status endpoint returns expected fields when batch is running."""
        import routes.trading.classifiers.batch_training as cl_mod
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
        import routes.trading.classifiers.batch_training as cl_mod
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
        import routes.trading.classifiers.batch_training as cl_mod
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
        import routes.trading.classifiers.batch_training as cl_mod
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
        import routes.trading.classifiers.batch_training as cl_mod
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
        import routes.trading.classifiers.batch_training as cl_mod
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
        import database
        monkeypatch.setattr(database, "list_classifier_ids",
                            lambda c: (_ for _ in ()).throw(RuntimeError("boom")))

        resp = trading_client.get("/api/v1/trading/classifiers/readiness")
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["status"] == "error"
        assert data["message"] == "Internal server error"


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
        import database
        monkeypatch.setattr(database, "list_classifier_ids",
                            lambda c: (_ for _ in ()).throw(RuntimeError("disk")))

        resp = trading_client.post("/api/v1/trading/classifiers/clear-all")
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["status"] == "error"
