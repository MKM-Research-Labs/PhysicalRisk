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
Tests for models.stress.flood_classifier — FloodClassifierTrainer and FloodPredictor.

Covers: train_gauge (normal, single-class skip), predict,
predict_series, predict_surface, available_gauges.
"""

import json
from pathlib import Path

import numpy as np
import pytest


# ===========================================================================
# Helpers
# ===========================================================================

def _make_vectors(n_pos=60, n_neg=140) -> dict:
    """Create synthetic stress vectors for one gauge with balanced classes.

    Vector format (v1.3 log-transformed):
      [log_h_s, log_t_end, delta_log_h, delta2_log_h, flood_flag]
    where severe_level=5.0, so log_h_s = ln(w/5.0).
    """
    rng = np.random.default_rng(42)
    # Positive: water above severe (log_h_s > 0), rising log velocity
    pos = [[rng.uniform(0.1, 1.2),    # log_h_s > 0  (w > severe)
            rng.uniform(-4.0, 0.0),   # log_t_end
            rng.uniform(0.01, 0.08),  # delta_log_h  (rising)
            rng.uniform(-0.02, 0.02), # delta2_log_h
            1]
           for _ in range(n_pos)]
    # Negative: water below severe (log_h_s < 0), stable/falling
    neg = [[rng.uniform(-2.0, -0.2),  # log_h_s < 0  (w < severe)
            rng.uniform(-5.0, 0.0),   # log_t_end
            rng.uniform(-0.05, 0.05), # delta_log_h  (stable)
            rng.uniform(-0.02, 0.02), # delta2_log_h
            0]
           for _ in range(n_neg)]
    return {
        "gauges": {
            "GAUGE-001": {
                "alert_level": 4.0,
                "severe_level": 5.0,
                "vector": pos + neg,
            }
        }
    }


def _make_single_class_vectors() -> dict:
    """Create vectors with all-negative labels (single class).

    Vector format (v1.3 log-transformed): [log_h_s, log_t, dlh, d2lh, flood_flag]
    """
    data = [[-1.5, -2.0, 0.0, 0.0, 0] for _ in range(50)]
    return {
        "gauges": {
            "GAUGE-BAD": {
                "alert_level": 4.0,
                "severe_level": 5.0,
                "vector": data,
            }
        }
    }


@pytest.fixture
def vectors_file(tmp_path) -> Path:
    p = tmp_path / "stress_vectors.json"
    p.write_text(json.dumps(_make_vectors()))
    return p


@pytest.fixture
def trained_model_dir(tmp_path, vectors_file) -> Path:
    from models.stress.flood_classifier import FloodClassifierTrainer
    model_dir = tmp_path / "models"
    trainer = FloodClassifierTrainer(vectors_file, model_dir)
    data = json.loads(vectors_file.read_text())
    for gid, gdata in data["gauges"].items():
        trainer.train_gauge(gid, gdata)
    return model_dir


# ===========================================================================
# FloodClassifierTrainer
# ===========================================================================

class TestFloodClassifierTrainer:

    def test_train_gauge_returns_dict(self, tmp_path, vectors_file):
        from models.stress.flood_classifier import FloodClassifierTrainer
        trainer = FloodClassifierTrainer(vectors_file, tmp_path / "models")
        data = json.loads(vectors_file.read_text())
        gauge_data = data["gauges"]["GAUGE-001"]
        result = trainer.train_gauge("GAUGE-001", gauge_data)
        assert isinstance(result, dict)

    def test_train_gauge_status_trained(self, tmp_path, vectors_file):
        from models.stress.flood_classifier import FloodClassifierTrainer
        trainer = FloodClassifierTrainer(vectors_file, tmp_path / "models")
        data = json.loads(vectors_file.read_text())
        result = trainer.train_gauge("GAUGE-001", data["gauges"]["GAUGE-001"])
        assert result["status"] == "trained"

    def test_train_gauge_has_metrics(self, tmp_path, vectors_file):
        from models.stress.flood_classifier import FloodClassifierTrainer
        trainer = FloodClassifierTrainer(vectors_file, tmp_path / "models")
        data = json.loads(vectors_file.read_text())
        result = trainer.train_gauge("GAUGE-001", data["gauges"]["GAUGE-001"])
        assert "metrics" in result
        assert "auc_roc" in result["metrics"]
        assert "accuracy" in result["metrics"]

    def test_train_gauge_creates_joblib_file(self, tmp_path, vectors_file):
        from models.stress.flood_classifier import FloodClassifierTrainer
        model_dir = tmp_path / "models"
        trainer = FloodClassifierTrainer(vectors_file, model_dir)
        data = json.loads(vectors_file.read_text())
        trainer.train_gauge("GAUGE-001", data["gauges"]["GAUGE-001"])
        assert (model_dir / "GAUGE-001.joblib").exists()

    def test_train_gauge_single_class_skipped(self, tmp_path):
        from models.stress.flood_classifier import FloodClassifierTrainer
        vectors_path = tmp_path / "single.json"
        vectors_path.write_text(json.dumps(_make_single_class_vectors()))
        trainer = FloodClassifierTrainer(vectors_path, tmp_path / "models")
        data = json.loads(vectors_path.read_text())
        result = trainer.train_gauge("GAUGE-BAD", data["gauges"]["GAUGE-BAD"])
        assert result["status"] == "skipped"
        assert result["reason"] == "single_class"



# ===========================================================================
# FloodPredictor
# ===========================================================================

class TestFloodPredictor:

    def test_predict_returns_float(self, trained_model_dir):
        from models.stress.flood_classifier import FloodPredictor
        predictor = FloodPredictor(trained_model_dir)
        prob = predictor.predict("GAUGE-001", water_level=4.5, hour=40)
        assert isinstance(prob, float)

    def test_predict_in_range(self, trained_model_dir):
        from models.stress.flood_classifier import FloodPredictor
        predictor = FloodPredictor(trained_model_dir)
        prob = predictor.predict("GAUGE-001", water_level=4.5, hour=40,
                                 delta_w=0.2, delta2_w=0.0)
        assert 0.0 <= prob <= 1.0

    def test_predict_high_level_higher_probability(self, trained_model_dir):
        from models.stress.flood_classifier import FloodPredictor
        predictor = FloodPredictor(trained_model_dir)
        # severe_level=5.0 → below severe (2m) vs above severe (6m)
        p_low = predictor.predict("GAUGE-001", water_level=2.0, hour=40)
        p_high = predictor.predict("GAUGE-001", water_level=6.0, hour=40)
        assert p_high > p_low

    def test_predict_missing_model_raises(self, trained_model_dir):
        from models.stress.flood_classifier import FloodPredictor
        predictor = FloodPredictor(trained_model_dir)
        with pytest.raises(FileNotFoundError):
            predictor.predict("GAUGE-NONEXISTENT", water_level=4.5)

    def test_predict_caches_model(self, trained_model_dir):
        from models.stress.flood_classifier import FloodPredictor
        predictor = FloodPredictor(trained_model_dir)
        predictor.predict("GAUGE-001", water_level=4.0, hour=10)
        predictor.predict("GAUGE-001", water_level=4.5, hour=20)
        assert "GAUGE-001" in predictor._models

    def test_predict_series_returns_list(self, trained_model_dir):
        from models.stress.flood_classifier import FloodPredictor
        predictor = FloodPredictor(trained_model_dir)
        levels = [3.5, 4.0, 4.5, 5.0]
        result = predictor.predict_series("GAUGE-001", levels)
        assert isinstance(result, list)
        assert len(result) == 4

    def test_predict_series_all_in_range(self, trained_model_dir):
        from models.stress.flood_classifier import FloodPredictor
        predictor = FloodPredictor(trained_model_dir)
        levels = [2.0, 3.0, 4.0, 5.0, 6.0]
        result = predictor.predict_series("GAUGE-001", levels)
        assert all(0.0 <= p <= 1.0 for p in result)

    def test_predict_series_with_derivatives(self, trained_model_dir):
        from models.stress.flood_classifier import FloodPredictor
        predictor = FloodPredictor(trained_model_dir)
        levels = [4.0, 4.2, 4.5]
        hours = [30, 31, 32]
        delta_ws = [0.1, 0.2, 0.3]
        delta2_ws = [0.0, 0.05, 0.0]
        result = predictor.predict_series("GAUGE-001", levels, hours,
                                          delta_ws, delta2_ws)
        assert len(result) == 3

    def test_predict_series_default_derivatives(self, trained_model_dir):
        from models.stress.flood_classifier import FloodPredictor
        predictor = FloodPredictor(trained_model_dir)
        result = predictor.predict_series("GAUGE-001", [3.0, 4.0])
        assert len(result) == 2

    def test_available_gauges(self, trained_model_dir):
        from models.stress.flood_classifier import FloodPredictor
        predictor = FloodPredictor(trained_model_dir)
        gauges = predictor.available_gauges()
        assert "GAUGE-001" in gauges

    def test_available_gauges_empty_dir(self, tmp_path):
        from models.stress.flood_classifier import FloodPredictor
        predictor = FloodPredictor(tmp_path)
        assert predictor.available_gauges() == []

    def test_load_summary(self, trained_model_dir):
        """Lines 188-192: _load_summary() loads training_summary.json."""
        from models.stress.flood_classifier import FloodPredictor
        predictor = FloodPredictor(trained_model_dir)
        summary = predictor._load_summary()
        assert 'num_gauges' in summary
        assert 'num_trained' in summary

    def test_load_summary_cached(self, trained_model_dir):
        """_load_summary caches on second call."""
        from models.stress.flood_classifier import FloodPredictor
        predictor = FloodPredictor(trained_model_dir)
        s1 = predictor._load_summary()
        s2 = predictor._load_summary()
        assert s1 is s2  # same object (cached)

    def test_predict_surface_returns_grid(self, trained_model_dir):
        """predict_surface returns a 2D probability grid (hours × levels)."""
        from models.stress.flood_classifier import FloodPredictor
        predictor = FloodPredictor(trained_model_dir)
        result = predictor.predict_surface(
            'GAUGE-001',
            level_min=2.0, level_max=6.0,
            level_steps=5, hour_max=4,
        )
        assert 'water_levels' in result
        assert 'hours' in result
        assert 'probabilities' in result
        assert len(result['probabilities']) == 4      # hour_max rows
        assert len(result['probabilities'][0]) == 5  # level_steps cols
