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
Flood probability classifier — F(ln(w/s), ln(t/T), Δln(w/s), Δ²ln(w/s)) → P(flood).

Trains a Gradient Boosting classifier per gauge using stress test vectors.
Features are log-transformed relative to the severe flood threshold (s) and
the storm horizon (T=168h):

  log_h_s   = ln(w / s)         — water level relative to severe threshold
  log_t_end = ln((t+1) / 168)   — log storm time (negative early, ~0 at end)
  delta_log_h   = Δln(w/s)      — log velocity (≈ relative rate of rise)
  delta2_log_h  = Δ²ln(w/s)     — log acceleration

The log transform normalises water levels across gauges with different severe
thresholds and introduces natural monotonicity: ln(w/s)=0 exactly when water
equals severe level, negative below, positive above.

Usage:
    trainer = FloodClassifierTrainer(output_dir)
    result = trainer.train_gauge('GAUGE-abc123', gauge_data)

    predictor = FloodPredictor(output_dir)
    prob = predictor.predict('GAUGE-abc123', water_level=4.2, hour=36,
                             delta_w=0.3, delta2_w=-0.05)
"""

import json
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, roc_auc_score, brier_score_loss, log_loss
)

from config.port import LOG_END

# Log-transform constants — LOG_END defined in config/port.py
LOG_EPS = 1e-8    # floor for h/s to avoid ln(0) or ln(negative)

logger = logging.getLogger(__name__)


class FloodClassifierTrainer:
    """Train per-gauge flood probability classifiers."""

    def __init__(self, vectors_path: Path, output_dir: Path):
        self.vectors_path = Path(vectors_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def train_gauge(self, gauge_id: str, gauge_data: dict,
                    test_size: float = 0.2) -> dict:
        """Train a GBM classifier for one gauge.

        Returns dict with model path, metrics, and metadata.
        """
        vector = gauge_data['vector']
        alert_level = gauge_data['alert_level']
        severe_level = gauge_data.get('severe_level', 0)

        # Features (v1.3 log-transformed, 4 features):
        #   [log_h_s, log_t_end, delta_log_h, delta2_log_h, flood_flag]
        X = np.array([[v[0], v[1], v[2], v[3]] for v in vector])
        y = np.array([v[4] for v in vector])  # flood_flag

        # Check for degenerate cases
        n_pos = int(y.sum())
        n_neg = len(y) - n_pos
        if n_pos == 0 or n_neg == 0:
            logger.warning("%s: single-class data (pos=%d, neg=%d), skipping",
                           gauge_id, n_pos, n_neg)
            return {
                'gauge_id': gauge_id,
                'status': 'skipped',
                'reason': 'single_class',
                'n_positive': n_pos,
                'n_negative': n_neg,
            }

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y)

        model = GradientBoostingClassifier(
            n_estimators=300,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            min_samples_leaf=50,
            random_state=42,
        )
        model.fit(X_train, y_train)

        # Predictions
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        # Metrics
        acc = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_prob)
        brier = brier_score_loss(y_test, y_prob)
        logloss = log_loss(y_test, y_prob)

        # Feature importance
        fi = model.feature_importances_
        feature_names = ['log_h_s', 'log_t_end', 'delta_log_h', 'delta2_log_h']
        importance = {fn: round(float(fi[i]), 4)
                      for i, fn in enumerate(feature_names)}

        # Save model — strip random_state to avoid numpy BitGenerator
        # pickle incompatibilities across scikit-learn / numpy versions.
        model.random_state = 42
        model_path = self.output_dir / f"{gauge_id}.joblib"
        joblib.dump(model, model_path)

        return {
            'gauge_id': gauge_id,
            'status': 'trained',
            'alert_level': alert_level,
            'severe_level': severe_level,
            'n_samples': len(y),
            'n_positive': n_pos,
            'n_negative': n_neg,
            'flood_rate': round(n_pos / len(y), 4),
            'test_size': len(y_test),
            'metrics': {
                'accuracy': round(acc, 4),
                'auc_roc': round(auc, 4),
                'brier_score': round(brier, 4),
                'log_loss': round(logloss, 4),
            },
            'feature_importance': importance,
            'model_path': str(model_path),
        }



class FloodPredictor:
    """Load trained models and predict flood probability.

    Inputs are raw (water_level in metres, hour index, raw deltas).
    The predictor transforms them to log-space internally using the
    severe_level stored in training_summary.json.
    """

    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self._models: Dict[str, GradientBoostingClassifier] = {}
        self._summary: Optional[dict] = None
        self._severe_map: Optional[Dict[str, float]] = None

    def _load_model(self, gauge_id: str) -> GradientBoostingClassifier:
        if gauge_id not in self._models:
            path = self.model_dir / f"{gauge_id}.joblib"
            if not path.exists():
                raise FileNotFoundError(
                    f"No trained model for {gauge_id}")
            try:
                self._models[gauge_id] = joblib.load(path)
            except (ValueError, ModuleNotFoundError) as exc:
                raise RuntimeError(
                    f"Cannot load classifier for {gauge_id}: {exc}. "
                    f"The model was saved with a different scikit-learn/numpy "
                    f"version. Delete {path.name} and retrain the gauge."
                ) from exc
        return self._models[gauge_id]

    def _load_summary(self) -> dict:
        if self._summary is None:
            path = self.model_dir / 'training_summary.json'
            if not path.exists():
                # Classifiers trained by the stressm pipeline before
                # training_summary.json was introduced.  Predictions still
                # work — _get_severe_level() falls back to 1.0 per gauge.
                logger.warning(
                    "training_summary.json not found in %s — "
                    "severe_level will fall back to 1.0 for all gauges; "
                    "re-run 'port --stressm --classifier' to regenerate",
                    self.model_dir,
                )
                self._summary = {'gauges': []}
            else:
                with open(path) as f:
                    self._summary = json.load(f)
        return self._summary

    def _get_severe_level(self, gauge_id: str) -> float:
        """Return the severe flood threshold for a gauge (used for log transform)."""
        if self._severe_map is None:
            summary = self._load_summary()
            self._severe_map = {
                g['gauge_id']: g.get('severe_level', 0)
                for g in summary.get('gauges', [])
                if g.get('status') == 'trained'
            }
        s = self._severe_map.get(gauge_id, 0)
        return s if s > 0 else 1.0  # fallback to 1.0 to avoid div-by-zero

    def _transform(self, water_level: float, hour: int,
                   delta_w: float, delta2_w: float,
                   severe_level: float) -> np.ndarray:
        """Convert raw (w, t, dw, d²w) to log-space feature vector.

        log_h_s      = ln(w / s)
        log_t_end    = ln((t+1) / 168)
        delta_log_h  = log_h_s(t) - log_h_s(t-1)  [reconstructed from delta_w]
        delta2_log_h = delta_log_h(t) - delta_log_h(t-1)  [from delta2_w]
        """
        log_h = math.log(max(water_level / severe_level, LOG_EPS))
        log_t = math.log((hour + 1) / LOG_END)

        # Reconstruct log deltas from raw deltas
        prev_level = water_level - delta_w
        log_h_prev = math.log(max(prev_level / severe_level, LOG_EPS))
        delta_log_h = log_h - log_h_prev

        prev_delta_w = delta_w - delta2_w          # delta at hour t-1
        prev_prev_level = prev_level - prev_delta_w
        log_h_prev2 = math.log(max(prev_prev_level / severe_level, LOG_EPS))
        prev_delta_log_h = log_h_prev - log_h_prev2
        delta2_log_h = delta_log_h - prev_delta_log_h

        return np.array([[log_h, log_t, delta_log_h, delta2_log_h]])

    def predict(self, gauge_id: str,
                water_level: float,
                hour: int = 0,
                delta_w: float = 0.0, delta2_w: float = 0.0) -> float:
        """Predict P(flood) for a single observation.

        Args:
            gauge_id: Gauge identifier
            water_level: Current water level in metres AOD
            hour: Storm hour index (0 = start of storm, 167 = end)
            delta_w: Raw velocity — change in water level from previous hour
            delta2_w: Raw acceleration — change in velocity from previous hour

        Returns:
            Probability between 0 and 1
        """
        model = self._load_model(gauge_id)
        severe = self._get_severe_level(gauge_id)
        X = self._transform(water_level, hour, delta_w, delta2_w, severe)
        return float(model.predict_proba(X)[0, 1])

    def predict_series(self, gauge_id: str,
                       water_levels: List[float],
                       hours: Optional[List[int]] = None,
                       delta_ws: Optional[List[float]] = None,
                       delta2_ws: Optional[List[float]] = None) -> List[float]:
        """Predict P(flood) for a time series of observations."""
        n = len(water_levels)
        if hours is None:
            hours = list(range(n))
        if delta_ws is None:
            delta_ws = [0.0] * n
        if delta2_ws is None:
            delta2_ws = [0.0] * n
        model = self._load_model(gauge_id)
        severe = self._get_severe_level(gauge_id)
        rows = [
            self._transform(wl, hr, dw, d2w, severe)[0]
            for wl, hr, dw, d2w in zip(water_levels, hours, delta_ws, delta2_ws)
        ]
        X = np.array(rows)
        return model.predict_proba(X)[:, 1].tolist()

    def predict_surface(self, gauge_id: str,
                        level_min: float, level_max: float,
                        level_steps: int = 50,
                        hour_max: int = 60,
                        delta_w: float = 0.0,
                        delta2_w: float = 0.0) -> dict:
        """Generate a probability surface F(w, t) over a grid.

        Uses constant delta_w=0 and delta2_w=0 across the grid (steady-state).
        Both water level and hour vary, producing a proper 2D surface.

        Returns dict with water_levels, hours, and probabilities matrix.
        """
        model = self._load_model(gauge_id)
        severe = self._get_severe_level(gauge_id)
        levels = np.linspace(level_min, level_max, level_steps)
        hours = list(range(hour_max))

        rows = []
        for h in hours:
            for lv in levels:
                rows.append(
                    self._transform(float(lv), h, delta_w, delta2_w, severe)[0]
                )
        X = np.array(rows)
        probs = model.predict_proba(X)[:, 1]
        prob_matrix = probs.reshape(hour_max, level_steps)

        return {
            'water_levels': levels.tolist(),
            'hours': hours,
            'probabilities': prob_matrix.tolist(),
        }

    def available_gauges(self) -> List[str]:
        """List gauge IDs with trained models."""
        return sorted(
            p.stem for p in self.model_dir.glob('GAUGE-*.joblib'))
