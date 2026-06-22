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

"""Tests for _train_single_gauge — part 2.

Integration-level tests with mocked heavy dependencies.
"""

import json
import time
from unittest.mock import patch, MagicMock

import pytest

from ._data import GAUGE_WESTMINSTER, SAMPLE_GAUGE_JSON


@pytest.fixture(autouse=True)
def clear_training_jobs():
    """Reset module-level _training_jobs dict before and after each test."""
    import routes.trading.stress.training as training_mod
    training_mod._training_jobs.clear()
    yield
    training_mod._training_jobs.clear()


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
        ):
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
