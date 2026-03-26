# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Tests for _run_batch_training helper function."""

import json
import time
from unittest.mock import patch

import pytest

from ._data import (
    GAUGE_WESTMINSTER, GAUGE_CHELSEA, GAUGE_LAMBETH,
    ALL_TEST_GAUGE_IDS,
)


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
