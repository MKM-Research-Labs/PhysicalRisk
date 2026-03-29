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

"""Tests for train_gauge_stressm_classifier and portfolio-level classifier training."""

import numpy as np
import pytest

from port.src.stressm import (
    generate_stressm,
    train_gauge_stressm_classifier,
)
from port.src.storm_multi.generators.batch_generator import generate_event_set
from port.src.storm_multi.models.spatial_correlation import SpatialCorrelationModel


# ---------------------------------------------------------------------------
# Lines 557-671: train_gauge_stressm_classifier
# ---------------------------------------------------------------------------

class TestTrainGaugeStressmClassifier:

    @pytest.fixture(scope="class")
    def sequences_20(self):
        return generate_event_set(count=20, seed=99)

    @pytest.fixture(scope="class")
    def spatial_model_3g(self):
        locs = [(51.46, -0.30), (51.47, -0.20), (51.48, -0.10)]
        return SpatialCorrelationModel(locs)

    @pytest.fixture(scope="class")
    def gauge_dict(self):
        return {
            "gauge_id":      "GAUGE-clf001",
            "base_level":    1.2,
            "flood_alert":   3.5,
            "flood_warning": 4.6,
            "severe_warning": 5.5,
        }

    def test_returns_result_dict(self, sequences_20, spatial_model_3g,
                                 gauge_dict, tmp_path):
        result = train_gauge_stressm_classifier(
            sequences=sequences_20,
            gauge=gauge_dict,
            spatial_model=spatial_model_3g,
            target_spatial_index=0,
            output_dir=tmp_path,
            rng=np.random.RandomState(7),
        )
        assert isinstance(result, dict)

    def test_result_has_gauge_id(self, sequences_20, spatial_model_3g,
                                  gauge_dict, tmp_path):
        result = train_gauge_stressm_classifier(
            sequences=sequences_20,
            gauge=gauge_dict,
            spatial_model=spatial_model_3g,
            target_spatial_index=0,
            output_dir=tmp_path,
            rng=np.random.RandomState(8),
        )
        assert result.get("gauge_id") == "GAUGE-clf001"

    def test_result_has_label_threshold(self, sequences_20, spatial_model_3g,
                                         gauge_dict, tmp_path):
        result = train_gauge_stressm_classifier(
            sequences=sequences_20,
            gauge=gauge_dict,
            spatial_model=spatial_model_3g,
            target_spatial_index=0,
            output_dir=tmp_path,
            rng=np.random.RandomState(9),
        )
        assert "label_threshold" in result
        assert result["label_threshold"] in ("severe_warning", "flood_alert")

    def test_model_file_written(self, sequences_20, spatial_model_3g,
                                 gauge_dict, tmp_path):
        train_gauge_stressm_classifier(
            sequences=sequences_20,
            gauge=gauge_dict,
            spatial_model=spatial_model_3g,
            target_spatial_index=0,
            output_dir=tmp_path,
            rng=np.random.RandomState(10),
        )
        stressm_dir = tmp_path / "stressm"
        assert stressm_dir.exists()

    def test_fallback_to_alert_when_no_severe_events(self, sequences_20,
                                                       spatial_model_3g,
                                                       tmp_path):
        """severe_warning=100m ensures no events breach it -> fallback to alert."""
        extreme_gauge = {
            "gauge_id":      "GAUGE-extreme",
            "base_level":    1.0,
            "flood_alert":   3.5,
            "flood_warning": 4.6,
            "severe_warning": 100.0,   # unreachable -> triggers fallback
        }
        result = train_gauge_stressm_classifier(
            sequences=sequences_20,
            gauge=extreme_gauge,
            spatial_model=spatial_model_3g,
            target_spatial_index=0,
            output_dir=tmp_path,
            rng=np.random.RandomState(11),
        )
        # Fallback should set label to flood_alert
        assert result["label_threshold"] == "flood_alert"

    def test_severe_zero_branch(self, sequences_20, spatial_model_3g, tmp_path):
        """severe_warning=0 exercises the else branch in log_hs computation."""
        zero_gauge = {
            "gauge_id":      "GAUGE-zero-severe",
            "base_level":    0.1,
            "flood_alert":   0.5,
            "flood_warning": 1.0,
            "severe_warning": 0.0,   # triggers else branch: log(max(lv, _LOG_EPS))
        }
        result = train_gauge_stressm_classifier(
            sequences=sequences_20,
            gauge=zero_gauge,
            spatial_model=spatial_model_3g,
            target_spatial_index=0,
            output_dir=tmp_path,
            rng=np.random.RandomState(12),
        )
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Lines 364-384: full-portfolio train_classifier=True
# ---------------------------------------------------------------------------

class TestPortfolioClassifier:

    def test_portfolio_classifier_trains_all_gauges(self, gauge_dir, tmp_path):
        """train_classifier=True without gauge_id covers lines 364-384."""
        result = generate_stressm(
            input_dir=gauge_dir,
            output_dir=tmp_path,
            count=20,
            catchment_id="thames",
            seed=42,
            train_classifier=True,
        )
        assert result["num_gauges"] == 3
        stressm_dir = tmp_path / "stressm"
        assert stressm_dir.exists()
        # At least some .joblib files should have been written
        joblibs = list(stressm_dir.glob("*.joblib"))
        assert len(joblibs) > 0

    def test_portfolio_classifier_summary_unchanged(self, gauge_dir, tmp_path):
        """Return value still has the correct structure after classifier training."""
        result = generate_stressm(
            input_dir=gauge_dir,
            output_dir=tmp_path,
            count=20,
            catchment_id="thames",
            seed=1,
            train_classifier=True,
        )
        assert result["num_sequences"] == 20
        assert "type_counts" in result
