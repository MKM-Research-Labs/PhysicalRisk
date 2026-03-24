# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for /trading/stress/train and _train_single_gauge.

Covers:
  - train_classifier: already trained, in progress, gauge not found, missing files, success
  - _train_single_gauge: success and failure paths with mocked dependencies
"""

import json
import time
from unittest.mock import patch

import pytest

from ._data import GAUGE_WESTMINSTER, SAMPLE_GAUGE_JSON


# Gauge JSON in the Header.GaugeID format that training.py's parser expects.
_TRAINING_GAUGE_JSON = {
    "flood_gauges": [
        {"FloodGauge": {"Header": {"GaugeID": GAUGE_WESTMINSTER}}},
        {"FloodGauge": {"Header": {"GaugeID": "GAUGE-002"}}},
    ]
}


# ---------------------------------------------------------------------------
# Fixture: clear _training_jobs between tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_training_jobs():
    """Reset module-level _training_jobs dict before and after each test."""
    import routes.trading.stress.training as training_mod
    training_mod._training_jobs.clear()
    yield
    training_mod._training_jobs.clear()


@pytest.fixture
def training_env(trading_env):
    """Trading env with gauge.json in Header.GaugeID format for training route."""
    input_dir = trading_env['input_dir']
    with open(input_dir / 'gauge.json', 'w') as f:
        json.dump(_TRAINING_GAUGE_JSON, f)
    return trading_env


@pytest.fixture
def training_client(training_env):
    """Flask test client with training-compatible gauge.json."""
    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()


# ===========================================================================
# POST /trading/stress/train/<gauge_id>
# ===========================================================================

class TestTrainClassifier:
    """Tests for the train endpoint."""

    def test_train_already_trained_returns_ready(self, trading_env, trading_client):
        """If joblib already exists, POST returns ready immediately."""
        classifiers_dir = trading_env['classifiers_dir']
        (classifiers_dir / f"{GAUGE_WESTMINSTER}.joblib").write_bytes(b"model")

        resp = trading_client.post(
            f"/api/v1/trading/stress/train/{GAUGE_WESTMINSTER}"
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ready"
        assert data["gauge_id"] == GAUGE_WESTMINSTER

    def test_train_already_in_progress(self, trading_env, trading_client):
        """If training is already in progress, return training status."""
        import routes.trading.stress.training as training_mod
        training_mod._training_jobs[GAUGE_WESTMINSTER] = {
            "status": "training",
            "started": time.time() - 5,
            "error": None,
        }

        resp = trading_client.post(
            f"/api/v1/trading/stress/train/{GAUGE_WESTMINSTER}"
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "training"
        assert "elapsed_seconds" in data

    def test_train_gauge_not_found_404(self, training_env, training_client):
        """Gauge not in gauge.json => 404."""
        input_dir = training_env['input_dir']
        (input_dir / "storm_sequences.json").write_text("[]")

        resp = training_client.post(
            "/api/v1/trading/stress/train/GAUGE-NONEXISTENT"
        )
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["status"] == "error"
        assert "not found" in data["message"]

    def test_train_no_gauge_json_404(self, training_env, training_client):
        """Missing gauge.json => 404."""
        import os
        os.remove(training_env['input_dir'] / 'gauge.json')

        resp = training_client.post(
            f"/api/v1/trading/stress/train/{GAUGE_WESTMINSTER}"
        )
        assert resp.status_code == 404
        data = resp.get_json()
        assert "gauge.json not found" in data["message"]

    def test_train_no_storm_sequences_404(self, training_env, training_client):
        """Missing storm_sequences.json => 404."""
        resp = training_client.post(
            f"/api/v1/trading/stress/train/{GAUGE_WESTMINSTER}"
        )
        assert resp.status_code == 404
        data = resp.get_json()
        assert "storm_sequences.json not found" in data["message"]

    def test_train_starts_background_thread(self, training_env, training_client):
        """Successful POST starts training and returns training status."""
        input_dir = training_env['input_dir']
        (input_dir / "storm_sequences.json").write_text("[]")

        with patch(
            "routes.trading.stress.training._train_single_gauge"
        ) as mock_train:
            resp = training_client.post(
                f"/api/v1/trading/stress/train/{GAUGE_WESTMINSTER}"
            )

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "training"
        assert data["gauge_id"] == GAUGE_WESTMINSTER
        assert "Poll" in data["message"]

        # Verify training job was registered
        import routes.trading.stress.training as training_mod
        assert GAUGE_WESTMINSTER in training_mod._training_jobs
        assert training_mod._training_jobs[GAUGE_WESTMINSTER]["status"] == "training"

    def test_train_corrupt_gauge_json_500(self, training_env, training_client):
        """Corrupt gauge.json => 500."""
        input_dir = training_env['input_dir']
        (input_dir / "gauge.json").write_text("{invalid json")
        (input_dir / "storm_sequences.json").write_text("[]")

        resp = training_client.post(
            f"/api/v1/trading/stress/train/{GAUGE_WESTMINSTER}"
        )
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["status"] == "error"
        assert "Error reading gauge.json" in data["message"]

    def test_train_previously_failed_can_restart(self, training_env, training_client):
        """A previously failed job can be restarted."""
        import routes.trading.stress.training as training_mod
        training_mod._training_jobs[GAUGE_WESTMINSTER] = {
            "status": "failed",
            "started": time.time() - 60,
            "error": "Timeout",
        }

        input_dir = training_env['input_dir']
        (input_dir / "storm_sequences.json").write_text("[]")

        with patch(
            "routes.trading.stress.training._train_single_gauge"
        ):
            resp = training_client.post(
                f"/api/v1/trading/stress/train/{GAUGE_WESTMINSTER}"
            )

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "training"


# ===========================================================================
# _train_single_gauge (integration-level, mocked heavy deps)
# ===========================================================================

class TestTrainSingleGauge:
    """Tests for the background training function with mocked dependencies."""

    def test_train_success_updates_job_to_ready(self, trading_env):
        """Successful training sets job status to 'ready'."""
        import routes.trading.stress.training as training_mod

        training_mod._training_jobs[GAUGE_WESTMINSTER] = {
            "status": "training",
            "started": time.time(),
            "error": None,
        }

        fake_result = {
            "gauge_id": GAUGE_WESTMINSTER,
            "status": "trained",
            "metrics": {"auc_roc": 0.94, "accuracy": 0.91},
        }

        with patch(
            "routes.trading.stress.training.json"
        ) as mock_json, patch(
            "routes.trading.stress.training._update_training_summary"
        ) as mock_summary, patch(
            "routes.trading.stress.training._train_single_gauge"
        ) as mock_impl:
            # Instead of mocking the function itself, call it and simulate
            # the success path by directly manipulating the job dict
            pass

        # Test the actual logic by mocking the heavy imports
        mock_imports = {
            "numpy": __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock(),
        }

        with patch.dict("sys.modules", {
            "numpy": mock_imports["numpy"],
            "port.src.stressm.classifier": __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock(),
            "port.src.stressm.gauge_parser": __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock(),
            "port.src.storm_multi.models.spatial_correlation": __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock(),
            "port.src.storm_multi.utils.serialization": __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock(),
        }), patch(
            "routes.trading.stress.training._update_training_summary"
        ), patch(
            "routes.trading.stress._helpers._invalidate_predictor_cache"
        ):
            from unittest.mock import MagicMock

            # Mock the imports inside _train_single_gauge
            mock_train_func = MagicMock(return_value=fake_result)
            mock_extract = MagicMock(return_value=[
                {"FloodGauge": {"Header": {"GaugeID": GAUGE_WESTMINSTER}}}
            ])
            mock_parse = MagicMock(return_value={
                "gauge_id": GAUGE_WESTMINSTER,
                "lat": 51.5, "lon": -0.12,
            })
            mock_baselines = MagicMock(return_value={})
            mock_spatial = MagicMock()
            mock_load_seq = MagicMock(return_value=[])

            # Write required files
            input_dir = trading_env['input_dir']
            with open(input_dir / "gauge.json", "w") as f:
                json.dump(SAMPLE_GAUGE_JSON, f)
            (input_dir / "storm_sequences.json").write_text("[]")

            with patch(
                "port.src.stressm.classifier.train_gauge_stressm_classifier",
                mock_train_func,
            ), patch(
                "port.src.stressm.gauge_parser._extract_gauges",
                mock_extract,
            ), patch(
                "port.src.stressm.gauge_parser._parse_gauge",
                mock_parse,
            ), patch(
                "port.src.stressm.gauge_parser._load_gaugehd_baselines",
                mock_baselines,
            ), patch(
                "port.src.storm_multi.models.spatial_correlation.SpatialCorrelationModel",
                mock_spatial,
            ), patch(
                "port.src.storm_multi.utils.serialization.load_sequences",
                mock_load_seq,
            ):
                training_mod._train_single_gauge(GAUGE_WESTMINSTER)

            job = training_mod._training_jobs[GAUGE_WESTMINSTER]
            assert job["status"] == "ready"
            assert job["error"] is None

    def test_train_failure_updates_job_to_failed(self, trading_env):
        """Exception during training sets job status to 'failed'."""
        import routes.trading.stress.training as training_mod

        training_mod._training_jobs[GAUGE_WESTMINSTER] = {
            "status": "training",
            "started": time.time(),
            "error": None,
        }

        # Force an exception by making the gauge.json unreadable
        input_dir = trading_env['input_dir']
        (input_dir / "gauge.json").write_text("{corrupt")

        # The function catches all exceptions
        training_mod._train_single_gauge(GAUGE_WESTMINSTER)

        job = training_mod._training_jobs[GAUGE_WESTMINSTER]
        assert job["status"] == "failed"
        assert job["error"] is not None
        assert len(job["error"]) > 0
