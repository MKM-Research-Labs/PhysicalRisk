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

"""Tests for _update_training_summary helper.

Covers:
  - _update_training_summary: create new, merge existing, recompute avg_auc
"""

import json
import time

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
# _update_training_summary
# ===========================================================================

class TestUpdateTrainingSummary:
    """Tests for the _update_training_summary helper."""

    def test_create_new_summary(self, trading_env):
        """Creates training_summary.json when it does not exist."""
        from routes.trading.stress.training import _update_training_summary

        classifiers_dir = trading_env['classifiers_dir']
        result = {
            "gauge_id": GAUGE_WESTMINSTER,
            "status": "trained",
            "metrics": {"auc_roc": 0.95, "accuracy": 0.90},
        }
        _update_training_summary(result)

        summary_path = classifiers_dir / "training_summary.json"
        assert summary_path.exists()
        summary = json.loads(summary_path.read_text())
        assert summary["num_gauges"] == 1
        assert summary["num_trained"] == 1
        assert summary["num_skipped"] == 0
        assert summary["avg_auc_roc"] == 0.95
        assert len(summary["gauges"]) == 1
        assert summary["gauges"][0]["gauge_id"] == GAUGE_WESTMINSTER

    def test_merge_into_existing_summary(self, trading_env):
        """Merges a new gauge result into an existing summary."""
        from routes.trading.stress.training import _update_training_summary

        classifiers_dir = trading_env['classifiers_dir']
        # Write initial summary with one gauge
        initial = {
            "num_gauges": 1,
            "num_trained": 1,
            "num_skipped": 0,
            "avg_auc_roc": 0.90,
            "gauges": [
                {
                    "gauge_id": "GAUGE-CHELSEA",
                    "status": "trained",
                    "metrics": {"auc_roc": 0.90},
                }
            ],
        }
        (classifiers_dir / "training_summary.json").write_text(json.dumps(initial))

        # Add a second gauge
        result = {
            "gauge_id": GAUGE_WESTMINSTER,
            "status": "trained",
            "metrics": {"auc_roc": 0.96},
        }
        _update_training_summary(result)

        summary = json.loads(
            (classifiers_dir / "training_summary.json").read_text()
        )
        assert summary["num_gauges"] == 2
        assert summary["num_trained"] == 2
        assert summary["num_skipped"] == 0
        # avg = (0.90 + 0.96) / 2 = 0.93
        assert summary["avg_auc_roc"] == 0.93

    def test_replace_existing_gauge_entry(self, trading_env):
        """Re-training a gauge replaces its entry, not duplicates it."""
        from routes.trading.stress.training import _update_training_summary

        classifiers_dir = trading_env['classifiers_dir']
        initial = {
            "num_gauges": 1,
            "num_trained": 1,
            "num_skipped": 0,
            "avg_auc_roc": 0.85,
            "gauges": [
                {
                    "gauge_id": GAUGE_WESTMINSTER,
                    "status": "trained",
                    "metrics": {"auc_roc": 0.85},
                }
            ],
        }
        (classifiers_dir / "training_summary.json").write_text(json.dumps(initial))

        # Re-train with improved AUC
        result = {
            "gauge_id": GAUGE_WESTMINSTER,
            "status": "trained",
            "metrics": {"auc_roc": 0.95},
        }
        _update_training_summary(result)

        summary = json.loads(
            (classifiers_dir / "training_summary.json").read_text()
        )
        assert summary["num_gauges"] == 1
        assert summary["num_trained"] == 1
        assert summary["avg_auc_roc"] == 0.95
        assert len(summary["gauges"]) == 1

    def test_skipped_gauge_not_counted_in_auc(self, trading_env):
        """A 'skipped' gauge does not contribute to avg_auc_roc."""
        from routes.trading.stress.training import _update_training_summary

        classifiers_dir = trading_env['classifiers_dir']
        initial = {
            "num_gauges": 1,
            "num_trained": 1,
            "num_skipped": 0,
            "avg_auc_roc": 0.92,
            "gauges": [
                {
                    "gauge_id": "GAUGE-CHELSEA",
                    "status": "trained",
                    "metrics": {"auc_roc": 0.92},
                }
            ],
        }
        (classifiers_dir / "training_summary.json").write_text(json.dumps(initial))

        # Add a skipped gauge
        result = {
            "gauge_id": GAUGE_WESTMINSTER,
            "status": "skipped",
            "metrics": {},
        }
        _update_training_summary(result)

        summary = json.loads(
            (classifiers_dir / "training_summary.json").read_text()
        )
        assert summary["num_gauges"] == 2
        assert summary["num_trained"] == 1
        assert summary["num_skipped"] == 1
        # avg_auc stays 0.92 (only trained gauges)
        assert summary["avg_auc_roc"] == 0.92

    def test_all_skipped_avg_auc_is_zero(self, trading_env):
        """When all gauges are skipped, avg_auc_roc is 0."""
        from routes.trading.stress.training import _update_training_summary

        result = {
            "gauge_id": GAUGE_WESTMINSTER,
            "status": "skipped",
            "metrics": {},
        }
        _update_training_summary(result)

        classifiers_dir = trading_env['classifiers_dir']
        summary = json.loads(
            (classifiers_dir / "training_summary.json").read_text()
        )
        assert summary["num_trained"] == 0
        assert summary["avg_auc_roc"] == 0.0
