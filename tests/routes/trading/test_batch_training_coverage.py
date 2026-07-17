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

"""Tests for batch_training.py coverage:
- Line 79: SYNTH- gauge skipped in train-all
- Line 181: _batch_job["completed"] incremented in exception handler
- Line 194: return when _batch_job is None mid-training
"""

import json
import time
import threading
from unittest.mock import patch, MagicMock

import pytest

import routes.trading.classifiers.batch_training as cl_mod


class TestSynthGaugeSkipped:
    """Cover line 79: SYNTH- gauges are skipped when finding untrained gauges."""

    def test_synth_gauge_excluded_from_training(self, trading_env, trading_client):
        """POST train-all skips SYNTH- prefixed gauges."""
        cl_mod._batch_job = None

        # Patch _load_gauge_locations to include a SYNTH- gauge
        synth_locations = {"SYNTH-001": {"lat": 51.5, "lon": -0.1}}
        with patch("routes.trading.classifiers.batch_training._load_gauge_locations",
                    return_value=synth_locations):
            resp = trading_client.post("/api/v1/trading/classifiers/train-all")
            data = resp.get_json()

        # All gauges are synthetic, so all should be "already trained" (skipped)
        assert data["status"] == "complete"
        assert data["message"] == "All gauges already trained"

        cl_mod._batch_job = None

    def test_synth_gauge_excluded_real_gauge_trained(self, trading_env, trading_client):
        """SYNTH- gauges are skipped but real gauges are still queued for training."""
        cl_mod._batch_job = None

        locations = {
            "SYNTH-001": {"lat": 51.5, "lon": -0.1},
            "GAUGE-REAL": {"lat": 51.5, "lon": -0.1},
        }
        with patch("routes.trading.classifiers.batch_training._load_gauge_locations",
                    return_value=locations):
            resp = trading_client.post("/api/v1/trading/classifiers/train-all")
            data = resp.get_json()

        # GAUGE-REAL doesn't have a .joblib, so training should start
        assert data["status"] == "running"
        assert data["total"] == 1  # only GAUGE-REAL, not SYNTH-001

        # Wait briefly and cleanup
        time.sleep(0.2)
        cl_mod._batch_job = None


class TestBatchTrainingExceptionHandler:
    """Cover line 181: completed counter incremented when training fails."""

    def test_failed_gauge_increments_completed(self, trading_env):
        """When _train_single_gauge raises, completed is still incremented
        and the result records the failure."""
        cl_mod._batch_job = {
            "status": "running",
            "total": 1,
            "completed": 0,
            "current_gauge_id": None,
            "results": [],
            "started": time.time(),
            "avg_per_gauge": 0,
            "gauge_ids": ["GAUGE-FAIL"],
        }

        def mock_train(gid):
            raise RuntimeError("training exploded")

        with patch("routes.trading.stress.training._train_single_gauge", mock_train):
            cl_mod._run_batch_training(["GAUGE-FAIL"])

        # After running, completed should be 1 and result should show 'failed'
        assert cl_mod._batch_job is not None
        assert cl_mod._batch_job["completed"] == 1
        results = cl_mod._batch_job["results"]
        assert len(results) == 1
        assert results[0]["status"] == "failed"
        assert results[0]["gauge_id"] == "GAUGE-FAIL"
        assert "training exploded" in results[0]["error"]

        cl_mod._batch_job = None


class TestBatchJobNullMidTraining:
    """Cover line 194: return when _batch_job is None after completing all gauges."""

    def test_batch_job_none_after_loop(self, trading_env):
        """When _batch_job is set to None between the training loop and the
        post-loop code, _run_batch_training returns early."""
        # Set up a batch job that will succeed but get nulled after the loop
        cl_mod._batch_job = {
            "status": "running",
            "total": 1,
            "completed": 0,
            "current_gauge_id": None,
            "results": [],
            "started": time.time(),
            "avg_per_gauge": 0,
            "gauge_ids": ["GAUGE-TEST"],
        }

        call_count = 0

        def mock_train(gid):
            nonlocal call_count
            call_count += 1
            # After training, set _batch_job to None to simulate cancellation
            # This will be checked at line 193
            with cl_mod._batch_lock:
                cl_mod._batch_job["completed"] = 1
                cl_mod._batch_job["results"].append({
                    "gauge_id": gid, "status": "trained",
                    "elapsed_seconds": 0.1,
                })

        with patch("routes.trading.stress.training._train_single_gauge", mock_train):
            # After the loop completes, set _batch_job to None before _save_timings
            original_save = cl_mod._save_timings

            def intercept_save(stressm_dir, timings):
                # This is called after the loop; set _batch_job to None
                # to hit line 193-194
                pass  # Don't actually save

            with patch.object(cl_mod, "_save_timings", intercept_save):
                # Set _batch_job to None right after loop via a more targeted approach
                # We'll set it to None in _load_timings which runs after the loop
                original_load = cl_mod._load_timings

                def load_and_null(stressm_dir):
                    cl_mod._batch_job = None
                    return {"runs": []}

                with patch.object(cl_mod, "_load_timings", load_and_null):
                    cl_mod._run_batch_training(["GAUGE-TEST"])

        assert call_count == 1
        # _batch_job should be None (set by our load_and_null)
        assert cl_mod._batch_job is None

    def test_batch_job_none_at_loop_start(self, trading_env):
        """When _batch_job is None at the start of a loop iteration,
        _run_batch_training returns immediately (line 140-141)."""
        cl_mod._batch_job = None

        call_count = 0

        def mock_train(gid):
            nonlocal call_count
            call_count += 1

        with patch("routes.trading.stress.training._train_single_gauge", mock_train):
            cl_mod._run_batch_training(["GAUGE-001", "GAUGE-002"])

        # Should not have trained any gauges since _batch_job was None
        assert call_count == 0
        assert cl_mod._batch_job is None
