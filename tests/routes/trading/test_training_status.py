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

"""Tests for /trading/stress/classifier-status and edge cases.

Covers:
  - classifier_status: ready (joblib exists), not_trained, training in progress, failed
  - Edge cases: gauge isolation, race conditions, dict-format gauge.json
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
    from fixtures_admin import AuthenticatedTestClient
    app = create_app()
    app.config['TESTING'] = True
    app.test_client_class = AuthenticatedTestClient
    return app.test_client()


# ===========================================================================
# GET /trading/stress/classifier-status/<gauge_id>
# ===========================================================================

class TestClassifierStatus:
    """Tests for the classifier-status endpoint."""

    def test_status_ready_when_joblib_exists(self, trading_env, trading_client):
        """If a .joblib file exists for the gauge, status is 'ready'."""
        classifiers_dir = trading_env['classifiers_dir']
        (classifiers_dir / f"{GAUGE_WESTMINSTER}.joblib").write_bytes(b"fake")

        resp = trading_client.get(
            f"/api/v1/trading/stress/classifier-status/{GAUGE_WESTMINSTER}"
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ready"
        assert data["gauge_id"] == GAUGE_WESTMINSTER

    def test_status_not_trained_when_no_joblib_no_job(self, trading_env, trading_client):
        """No joblib file and no training job => not_trained."""
        resp = trading_client.get(
            f"/api/v1/trading/stress/classifier-status/{GAUGE_WESTMINSTER}"
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "not_trained"
        assert data["gauge_id"] == GAUGE_WESTMINSTER

    def test_status_training_in_progress(self, trading_env, trading_client):
        """When a training job is in progress, status is 'training' with elapsed."""
        import routes.trading.stress.training as training_mod
        training_mod._training_jobs[GAUGE_WESTMINSTER] = {
            "status": "training",
            "started": time.time() - 10,
            "error": None,
        }

        resp = trading_client.get(
            f"/api/v1/trading/stress/classifier-status/{GAUGE_WESTMINSTER}"
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "training"
        assert data["gauge_id"] == GAUGE_WESTMINSTER
        assert "elapsed_seconds" in data
        assert data["elapsed_seconds"] >= 10
        assert "message" in data

    def test_status_ready_from_job_dict(self, trading_env, trading_client):
        """Job dict says 'ready' (joblib might not exist yet) => status ready."""
        import routes.trading.stress.training as training_mod
        training_mod._training_jobs[GAUGE_WESTMINSTER] = {
            "status": "ready",
            "started": time.time() - 5,
            "error": None,
        }

        resp = trading_client.get(
            f"/api/v1/trading/stress/classifier-status/{GAUGE_WESTMINSTER}"
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ready"

    def test_status_failed_from_job_dict(self, trading_env, trading_client):
        """Job dict says 'failed' => status failed with error message."""
        import routes.trading.stress.training as training_mod
        training_mod._training_jobs[GAUGE_WESTMINSTER] = {
            "status": "failed",
            "started": time.time() - 20,
            "error": "Out of memory",
        }

        resp = trading_client.get(
            f"/api/v1/trading/stress/classifier-status/{GAUGE_WESTMINSTER}"
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "failed"
        assert data["gauge_id"] == GAUGE_WESTMINSTER
        assert data["error"] == "Out of memory"

    def test_status_failed_no_error_key(self, trading_env, trading_client):
        """Failed job with no 'error' key falls back to 'Unknown error'."""
        import routes.trading.stress.training as training_mod
        training_mod._training_jobs[GAUGE_WESTMINSTER] = {
            "status": "failed",
            "started": time.time(),
        }

        resp = trading_client.get(
            f"/api/v1/trading/stress/classifier-status/{GAUGE_WESTMINSTER}"
        )
        data = resp.get_json()
        assert data["status"] == "failed"
        assert data["error"] == "Unknown error"

    def test_status_unknown_gauge_not_trained(self, trading_env, trading_client):
        """Unknown gauge with no joblib and no job => not_trained."""
        resp = trading_client.get(
            "/api/v1/trading/stress/classifier-status/GAUGE-NONEXISTENT"
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "not_trained"

    def test_status_joblib_takes_precedence_over_job_dict(
        self, trading_env, trading_client
    ):
        """If joblib exists on disk, status is 'ready' even if job dict says 'training'."""
        import routes.trading.stress.training as training_mod
        training_mod._training_jobs[GAUGE_WESTMINSTER] = {
            "status": "training",
            "started": time.time(),
            "error": None,
        }
        classifiers_dir = trading_env['classifiers_dir']
        (classifiers_dir / f"{GAUGE_WESTMINSTER}.joblib").write_bytes(b"model")

        resp = trading_client.get(
            f"/api/v1/trading/stress/classifier-status/{GAUGE_WESTMINSTER}"
        )
        data = resp.get_json()
        assert data["status"] == "ready"


# ===========================================================================
# Edge cases / concurrency
# ===========================================================================

class TestEdgeCases:
    """Edge case and isolation tests."""

    def test_training_jobs_isolated_between_gauges(
        self, trading_env, trading_client
    ):
        """Training status of one gauge does not affect another."""
        import routes.trading.stress.training as training_mod
        training_mod._training_jobs[GAUGE_WESTMINSTER] = {
            "status": "training",
            "started": time.time(),
            "error": None,
        }

        resp = trading_client.get(
            "/api/v1/trading/stress/classifier-status/GAUGE-CHELSEA"
        )
        data = resp.get_json()
        assert data["status"] == "not_trained"

    def test_train_does_not_start_if_joblib_created_between_check_and_post(
        self, trading_env, trading_client
    ):
        """If joblib appears between status check and train call, returns ready."""
        classifiers_dir = trading_env['classifiers_dir']
        (classifiers_dir / f"{GAUGE_WESTMINSTER}.joblib").write_bytes(b"model")

        resp = trading_client.post(
            f"/api/v1/trading/stress/train/{GAUGE_WESTMINSTER}"
        )
        data = resp.get_json()
        assert data["status"] == "ready"

    def test_gauge_json_dict_format(self, training_env, training_client):
        """gauge.json with dict-format flood_gauges is handled."""
        input_dir = training_env['input_dir']
        dict_gauge_json = {
            "flood_gauges": {
                "0": {
                    "FloodGauge": {
                        "Header": {"GaugeID": GAUGE_WESTMINSTER},
                    }
                }
            }
        }
        with open(input_dir / "gauge.json", "w") as f:
            json.dump(dict_gauge_json, f)
        (input_dir / "storm_sequences.json").write_text("[]")

        with patch("routes.trading.stress.training._train_single_gauge"):
            resp = training_client.post(
                f"/api/v1/trading/stress/train/{GAUGE_WESTMINSTER}"
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "training"
