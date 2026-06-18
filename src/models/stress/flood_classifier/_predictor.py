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

"""Load trained per-gauge models and predict flood probability."""

import json
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier

from config.port import LOG_END

# Log-transform constants — LOG_END defined in config/port.py
LOG_EPS = 1e-8    # floor for h/s to avoid ln(0) or ln(negative)

logger = logging.getLogger(__name__)


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
