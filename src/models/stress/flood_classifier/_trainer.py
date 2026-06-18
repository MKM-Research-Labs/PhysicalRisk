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

"""Per-gauge flood-probability classifier training (Gradient Boosting)."""

import logging
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, roc_auc_score, brier_score_loss, log_loss
)

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
