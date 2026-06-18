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

"""Coverage expansion tests for classifiers.py — ImportError fallback,
train-all start error, batch cancellation before first gauge, metrics
readback from training_summary.json, post-loop cancellation, and
running average AUC/accuracy in status (lines 225, 307-309, 324,
338-344, 377, 434, 436)."""

import json
import time
from unittest.mock import patch, MagicMock

import pytest

from ._data import GAUGE_WESTMINSTER, GAUGE_CHELSEA, GAUGE_LAMBETH


class TestClearAllImportErrorFallback:
    """Line 225: ImportError in clear_all_classifiers."""

    def test_clear_all_succeeds_with_import_error(self, trading_env, trading_client,
                                                    monkeypatch):
        """clear-all still returns success when port_stress import fails."""
        classifiers_dir = trading_env["classifiers_dir"]
        (classifiers_dir / f"{GAUGE_WESTMINSTER}.joblib").write_bytes(b"fake")

        # Make the import raise ImportError
        import routes.trading.classifiers.batch_training as cl_mod
        import routes.trading.classifiers.summary as cl_summary
        original_clear = cl_summary.clear_all_classifiers

        def patched_import(*args, **kwargs):
            raise ImportError("no port_stress")

        # Patch at module level so the try/except triggers
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "routes.trading.port_stress" or (
                "port_stress" in str(name)):
                raise ImportError("no port_stress")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        resp = trading_client.post("/api/v1/trading/classifiers/clear-all")
        data = resp.get_json()
        assert data["status"] == "success"
        assert data["removed"] == 1


class TestTrainAllStartError:
    """Lines 307-309: except Exception in train_all_classifiers."""

    def test_train_all_returns_500_on_setup_error(self, trading_client, monkeypatch):
        """POST train-all returns 500 when config.get_classifiers_dir raises."""
        import routes.trading.classifiers.batch_training as cl_mod
        cl_mod._batch_job = None  # ensure not "already running"

        from config import config
        monkeypatch.setattr(
            config, "get_classifiers_dir",
            lambda: (_ for _ in ()).throw(RuntimeError("disk error")),
        )

        resp = trading_client.post("/api/v1/trading/classifiers/train-all")
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["status"] == "error"
        assert data["message"] == "Internal server error"


class TestBatchCancelledBeforeFirstGauge:
    """Line 324: return at top of loop when _batch_job is None."""

    def test_batch_returns_immediately_when_cancelled_before_start(self, trading_env):
        import routes.trading.classifiers.batch_training as cl_mod

        gauge_ids = [GAUGE_WESTMINSTER, GAUGE_CHELSEA]

        # Set batch_job then immediately clear it so the loop finds None
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

        # Cancel before first iteration
        cl_mod._batch_job = None

        call_count = 0

        def mock_train(gid):
            nonlocal call_count
            call_count += 1

        with patch("routes.trading.stress.training._train_single_gauge",
                   side_effect=mock_train):
            cl_mod._run_batch_training(gauge_ids)

        assert call_count == 0
        assert cl_mod._batch_job is None


class TestBatchReadsMetrics:
    """Lines 338-344: reading back metrics from training_summary.json."""

    def test_successful_batch_reads_metrics_from_summary(self, trading_env):
        import routes.trading.classifiers.batch_training as cl_mod

        classifiers_dir = trading_env["classifiers_dir"]
        gauge_ids = [GAUGE_WESTMINSTER]

        with cl_mod._batch_lock:
            cl_mod._batch_job = {
                "status": "running",
                "total": 1,
                "completed": 0,
                "current_gauge_id": None,
                "results": [],
                "started": time.time(),
                "avg_per_gauge": 0,
                "gauge_ids": gauge_ids,
            }

        def mock_train(gid):
            # Write training_summary.json with metrics
            summary = {"gauges": [{
                "gauge_id": gid,
                "status": "trained",
                "metrics": {"auc_roc": 0.95, "accuracy": 0.97},
            }]}
            with open(classifiers_dir / "training_summary.json", "w") as f:
                json.dump(summary, f)

        with patch("routes.trading.stress.training._train_single_gauge",
                   side_effect=mock_train):
            cl_mod._run_batch_training(gauge_ids)

        assert cl_mod._batch_job["status"] == "complete"
        result = cl_mod._batch_job["results"][0]
        assert result["auc_roc"] == 0.95
        assert result["accuracy"] == 0.97

        cl_mod._batch_job = None


class TestBatchCancelledAfterLoop:
    """Line 377: post-loop cancellation check."""

    def test_post_loop_cancellation_returns_early(self, trading_env):
        import routes.trading.classifiers.batch_training as cl_mod

        gauge_ids = [GAUGE_WESTMINSTER]

        with cl_mod._batch_lock:
            cl_mod._batch_job = {
                "status": "running",
                "total": 1,
                "completed": 0,
                "current_gauge_id": None,
                "results": [],
                "started": time.time(),
                "avg_per_gauge": 0,
                "gauge_ids": gauge_ids,
            }

        def mock_train(gid):
            # Cancel after training completes but before post-loop save
            pass

        with patch("routes.trading.stress.training._train_single_gauge",
                   side_effect=mock_train):
            # After mock_train runs, cancel the job so post-loop check hits
            original_save_timings = cl_mod._save_timings

            def cancel_then_save(stressm_dir, timings):
                cl_mod._batch_job = None

            with patch.object(cl_mod, "_save_timings", side_effect=cancel_then_save):
                cl_mod._run_batch_training(gauge_ids)

        # Job was cancelled during post-loop
        assert cl_mod._batch_job is None


class TestStatusRunningAverages:
    """Lines 434, 436: avg_auc and avg_accuracy computed from results."""

    def test_status_computes_avg_auc_and_accuracy(self, trading_client):
        import routes.trading.classifiers.batch_training as cl_mod

        with cl_mod._batch_lock:
            cl_mod._batch_job = {
                "status": "running",
                "total": 3,
                "completed": 2,
                "current_gauge_id": "GAUGE-X",
                "results": [
                    {"gauge_id": "G1", "status": "trained",
                     "auc_roc": 0.90, "accuracy": 0.92, "elapsed_seconds": 10},
                    {"gauge_id": "G2", "status": "trained",
                     "auc_roc": 0.80, "accuracy": 0.88, "elapsed_seconds": 12},
                ],
                "started": time.time() - 30,
                "avg_per_gauge": 10.0,
                "gauge_ids": [],
            }

        resp = trading_client.get("/api/v1/trading/classifiers/train-all/status")
        data = resp.get_json()

        assert data["avg_auc"] == 0.85
        assert data["avg_accuracy"] == 0.9

        cl_mod._batch_job = None

    def test_status_avg_none_when_no_metrics(self, trading_client):
        """avg_auc/avg_accuracy are None when results have no metrics."""
        import routes.trading.classifiers.batch_training as cl_mod

        with cl_mod._batch_lock:
            cl_mod._batch_job = {
                "status": "running",
                "total": 2,
                "completed": 1,
                "current_gauge_id": "GAUGE-Y",
                "results": [
                    {"gauge_id": "G1", "status": "trained",
                     "auc_roc": None, "accuracy": None, "elapsed_seconds": 10},
                ],
                "started": time.time() - 15,
                "avg_per_gauge": 10.0,
                "gauge_ids": [],
            }

        resp = trading_client.get("/api/v1/trading/classifiers/train-all/status")
        data = resp.get_json()

        assert data["avg_auc"] is None
        assert data["avg_accuracy"] is None

        cl_mod._batch_job = None
