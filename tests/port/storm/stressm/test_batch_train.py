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

"""
Unit tests for batch_train.py — low-memory batch classifier training.

Uses mocks to avoid heavy GBM training while exercising all code paths
including error handling, incremental summary updates, and memory cleanup.
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import database
from db_helpers import tmp_catchment


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend (catchment "thames"). batch_train_classifiers now checks
    database.storm_sequences_exists() and reads sequences via the seam; _setup_dirs seeds
    them through database so the existence check passes."""
    with tmp_catchment(tmp_path, catchment="thames"):
        yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_gauge_json(n=3):
    """Build a minimal gauge.json dict with n gauges."""
    return {
        "flood_gauges": [
            {
                "FloodGauge": {
                    "Header": {"GaugeID": f"GAUGE-t{i:03d}", "CatchmentID": "thames"},
                    "Location": {
                        "GaugeLatitude": 51.4 + i * 0.01,
                        "GaugeLongitude": -0.3 + i * 0.01,
                    },
                    "FloodStages": {
                        "FloodAlert": 3.5 + i * 0.1,
                        "FloodWarning": 4.6 + i * 0.1,
                        "SevereFloodWarning": 5.5 + i * 0.1,
                    },
                }
            }
            for i in range(n)
        ],
    }


def _make_sequence_data():
    """Minimal storm sequences list."""
    return [
        MagicMock(sequence_start="2025-01-15T00:00:00"),
        MagicMock(sequence_start="2025-07-20T00:00:00"),
    ]


def _fake_train_result(gauge_id, status="trained", auc=0.95):
    """Build a classifier result dict."""
    return {
        "gauge_id": gauge_id,
        "status": status,
        "metrics": {"auc_roc": auc},
    }


# ---------------------------------------------------------------------------
# _update_training_summary
# ---------------------------------------------------------------------------

class TestUpdateTrainingSummary:
    """Incremental merge into training_summary.json."""

    def test_creates_new_summary(self, tmp_path):
        from port.src.stressm.summary import update_training_summary as _update_training_summary
        result = _fake_train_result("GAUGE-001")
        _update_training_summary(result, tmp_path)
        summary = json.loads((tmp_path / "training_summary.json").read_text())
        assert summary["num_gauges"] == 1
        assert summary["num_trained"] == 1
        assert summary["avg_auc_roc"] == 0.95

    def test_merges_into_existing(self, tmp_path):
        from port.src.stressm.summary import update_training_summary as _update_training_summary
        # First gauge
        _update_training_summary(_fake_train_result("GAUGE-001", auc=0.90), tmp_path)
        # Second gauge
        _update_training_summary(_fake_train_result("GAUGE-002", auc=1.0), tmp_path)
        summary = json.loads((tmp_path / "training_summary.json").read_text())
        assert summary["num_gauges"] == 2
        assert summary["num_trained"] == 2
        assert summary["avg_auc_roc"] == 0.95  # (0.90 + 1.0) / 2

    def test_replaces_existing_gauge(self, tmp_path):
        from port.src.stressm.summary import update_training_summary as _update_training_summary
        _update_training_summary(_fake_train_result("GAUGE-001", auc=0.80), tmp_path)
        _update_training_summary(_fake_train_result("GAUGE-001", auc=0.95), tmp_path)
        summary = json.loads((tmp_path / "training_summary.json").read_text())
        assert summary["num_gauges"] == 1
        assert summary["gauges"][0]["metrics"]["auc_roc"] == 0.95

    def test_skipped_gauge_not_counted_as_trained(self, tmp_path):
        from port.src.stressm.summary import update_training_summary as _update_training_summary
        result = {"gauge_id": "GAUGE-001", "status": "skipped"}
        _update_training_summary(result, tmp_path)
        summary = json.loads((tmp_path / "training_summary.json").read_text())
        assert summary["num_trained"] == 0
        assert summary["num_skipped"] == 1


# ---------------------------------------------------------------------------
# batch_train_classifiers
# ---------------------------------------------------------------------------

class TestBatchTrainClassifiers:
    """End-to-end tests with mocked classifier training."""

    def _setup_dirs(self, tmp_path):
        """Create output dir; seed gauge portfolio + storm sequences via the seam."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        # gauge portfolio + storm sequences are read through the database seam now
        # (load_sequences is mocked in these tests, so the payload is just a presence marker).
        database.save_gauges(database.active_catchment(), _make_gauge_json(3))
        database.save_storm_sequences(database.active_catchment(), {"sequences": []})
        return input_dir, output_dir

    def test_missing_gauge_json(self, tmp_path):
        from port.src.stressm.batch_train import batch_train_classifiers
        input_dir = tmp_path / "empty_input"
        input_dir.mkdir()
        with pytest.raises(FileNotFoundError, match="gauge portfolio"):
            batch_train_classifiers(input_dir, tmp_path / "out")

    def test_no_valid_gauges(self, tmp_path):
        from port.src.stressm.batch_train import batch_train_classifiers
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        # gauge portfolio with no valid gauges (missing required fields)
        database.save_gauges(database.active_catchment(), {"flood_gauges": [{"bad": True}]})
        result = batch_train_classifiers(input_dir, tmp_path / "out")
        assert result["trained"] == 0

    def test_all_already_trained(self, tmp_path):
        from port.src.stressm.batch_train import batch_train_classifiers
        input_dir, output_dir = self._setup_dirs(tmp_path)
        # Pre-create joblib files for all gauges
        stressm_dir = output_dir / "stressm"
        stressm_dir.mkdir(parents=True)
        for i in range(3):
            (stressm_dir / f"GAUGE-t{i:03d}.joblib").write_bytes(b"fake")
        result = batch_train_classifiers(input_dir, output_dir)
        assert result["trained"] == 0
        assert result["skipped"] == 3

    def test_missing_sequences(self, tmp_path):
        from port.src.stressm.batch_train import batch_train_classifiers
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        database.save_gauges(database.active_catchment(), _make_gauge_json(2))
        # No storm_sequences seeded in the backend
        with pytest.raises(FileNotFoundError, match="storm_sequences"):
            batch_train_classifiers(input_dir, tmp_path / "out")

    @patch("port.src.stressm.classifier._print_classifier_result")
    @patch("port.src.storm_multi.models.spatial_correlation.SpatialCorrelationModel")
    @patch("port.src.storm_multi.utils.serialization.load_sequences")
    @patch("port.src.stressm.classifier.train_gauge_stressm_classifier")
    def test_successful_training(self, mock_train, mock_load_seq, mock_spatial, mock_print, tmp_path):
        from port.src.stressm.batch_train import batch_train_classifiers
        input_dir, output_dir = self._setup_dirs(tmp_path)

        mock_load_seq.return_value = _make_sequence_data()
        mock_spatial.return_value = MagicMock()

        def side_effect(**kwargs):
            gid = kwargs["gauge"]["gauge_id"]
            return _fake_train_result(gid)

        mock_train.side_effect = side_effect

        result = batch_train_classifiers(input_dir, output_dir, verbose=True)
        assert result["trained"] == 3
        assert result["failed"] == 0
        assert mock_train.call_count == 3
        assert "elapsed_seconds" in result

    @patch("port.src.storm_multi.models.spatial_correlation.SpatialCorrelationModel")
    @patch("port.src.storm_multi.utils.serialization.load_sequences")
    @patch("port.src.stressm.classifier.train_gauge_stressm_classifier")
    def test_training_failure_is_caught(self, mock_train, mock_load_seq, mock_spatial, tmp_path):
        from port.src.stressm.batch_train import batch_train_classifiers
        input_dir, output_dir = self._setup_dirs(tmp_path)

        mock_load_seq.return_value = _make_sequence_data()
        mock_spatial.return_value = MagicMock()
        mock_train.side_effect = RuntimeError("GBM diverged")

        result = batch_train_classifiers(input_dir, output_dir)
        assert result["trained"] == 0
        assert result["failed"] == 3
        assert all(g["status"] == "failed" for g in result["gauges"])

    @patch("port.src.storm_multi.models.spatial_correlation.SpatialCorrelationModel")
    @patch("port.src.storm_multi.utils.serialization.load_sequences")
    @patch("port.src.stressm.classifier.train_gauge_stressm_classifier")
    def test_partial_training(self, mock_train, mock_load_seq, mock_spatial, tmp_path):
        """One gauge already trained, one succeeds, one fails."""
        from port.src.stressm.batch_train import batch_train_classifiers
        input_dir, output_dir = self._setup_dirs(tmp_path)

        # Pre-train GAUGE-t000
        stressm_dir = output_dir / "stressm"
        stressm_dir.mkdir(parents=True)
        (stressm_dir / "GAUGE-t000.joblib").write_bytes(b"fake")

        mock_load_seq.return_value = _make_sequence_data()
        mock_spatial.return_value = MagicMock()

        call_count = [0]
        def side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return _fake_train_result(kwargs["gauge"]["gauge_id"])
            raise RuntimeError("Boom")

        mock_train.side_effect = side_effect

        result = batch_train_classifiers(input_dir, output_dir)
        assert result["trained"] == 1
        assert result["failed"] == 1
        assert result["skipped"] == 1

    @patch("port.src.storm_multi.models.spatial_correlation.SpatialCorrelationModel")
    @patch("port.src.storm_multi.utils.serialization.load_sequences")
    @patch("port.src.stressm.classifier.train_gauge_stressm_classifier")
    def test_eta_printed_after_first_gauge(self, mock_train, mock_load_seq, mock_spatial, tmp_path, capsys):
        """After the first gauge trains, ETA should appear in output."""
        from port.src.stressm.batch_train import batch_train_classifiers
        input_dir, output_dir = self._setup_dirs(tmp_path)

        mock_load_seq.return_value = _make_sequence_data()
        mock_spatial.return_value = MagicMock()
        mock_train.side_effect = lambda **kw: _fake_train_result(kw["gauge"]["gauge_id"])

        batch_train_classifiers(input_dir, output_dir)
        captured = capsys.readouterr().out
        assert "ETA" in captured
