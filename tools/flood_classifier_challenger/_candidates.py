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

"""Candidate models, each with ``fit(X, y, groups)`` and ``predict(X) -> P(flood)``.

Groups (storm ids) are passed to every fit so the calibrated Random Forest can
hold back whole storms for its isotonic fit.
"""

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from config.models import (
    CHALLENGER_CALIB_HOLDOUT,
    CHALLENGER_LOGIT_PARAMS,
    CHALLENGER_RF_PARAMS,
    flood_poly_coeffs,
    flood_poly_exp_clamp,
)
from models.stress.flood_classifier._trainer import GBM_PARAMS


class _Sklearn:
    """Wrap a scikit-learn classifier; ``single_class`` predicts the base rate."""

    def __init__(self, estimator):
        self.estimator = estimator
        self._const = None

    def fit(self, X, y, groups):
        if len(np.unique(y)) < 2:
            self._const = float(np.mean(y))
            return self
        self.estimator.fit(X, y)
        return self

    def predict(self, X):
        if self._const is not None:
            return np.full(len(X), self._const)
        return self.estimator.predict_proba(X)[:, 1]


class _IsotonicRF:
    """Random Forest recalibrated by isotonic regression on held-back storms."""

    def __init__(self, params, seed, n_jobs):
        self.params, self.seed, self.n_jobs = params, seed, n_jobs

    def fit(self, X, y, groups):
        split = GroupShuffleSplit(n_splits=1, test_size=CHALLENGER_CALIB_HOLDOUT,
                                  random_state=self.seed)
        fit_idx, cal_idx = next(split.split(X, y, groups))
        self.rf = _Sklearn(_make_rf(self.params, self.seed, self.n_jobs)).fit(
            X[fit_idx], y[fit_idx], groups[fit_idx])
        self.iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
        self.iso.fit(self.rf.predict(X[cal_idx]), y[cal_idx])
        return self

    def predict(self, X):
        return self.iso.predict(self.rf.predict(X))


class _FloodPolynomial:
    """The production fallback: P = σ(a·h + b·t + c·h·t + d·h² + e·t² + f).

    Its h and t are exactly the classifier features log_h_s and log_t_end.
    Fixed coefficients, so ``fit`` does nothing.
    """

    def fit(self, X, y, groups):
        return self

    def predict(self, X):
        a, b, c, d, e, f = flood_poly_coeffs
        h, t = X[:, 0], X[:, 1]
        z = np.clip(a * h + b * t + c * h * t + d * h**2 + e * t**2 + f,
                    -flood_poly_exp_clamp, flood_poly_exp_clamp)
        return 1.0 / (1.0 + np.exp(-z))


def _make_rf(params, seed, n_jobs):
    return RandomForestClassifier(**{**CHALLENGER_RF_PARAMS, **params},
                                  random_state=seed, n_jobs=n_jobs)


def make_model(name: str, params: dict, seed: int, n_jobs: int = 1):
    """Build candidate ``name`` with ``params`` overriding its defaults.

    ``n_jobs`` is the Random Forest's own thread count; the benchmark runs fits
    in parallel and keeps each fit single-threaded."""
    if name in ("gbm_prod", "gbm"):
        return _Sklearn(GradientBoostingClassifier(**{**GBM_PARAMS, **params},
                                                   random_state=seed))
    if name == "rf":
        return _Sklearn(_make_rf(params, seed, n_jobs))
    if name == "rf_cal":
        return _IsotonicRF(params, seed, n_jobs)
    if name == "logit":
        lr = LogisticRegression(**{**CHALLENGER_LOGIT_PARAMS, **params}, random_state=seed)
        return _Sklearn(make_pipeline(StandardScaler(), lr))
    if name == "poly":
        return _FloodPolynomial()
    raise ValueError(f"unknown candidate {name!r}")


# Order of the report.  ``tune`` names the search space (config) a model is tuned
# over; ``params_from`` reuses another model's tuned params in the same fold.
CANDIDATES = {
    "gbm_prod": {"label": "GBM (production)",       "tune": None,    "stochastic": True},
    "gbm":      {"label": "GBM (tuned)",            "tune": "gbm",   "stochastic": True},
    "rf":       {"label": "Random Forest",          "tune": "rf",    "stochastic": True},
    "rf_cal":   {"label": "Random Forest (calib.)", "tune": None,    "stochastic": True,
                 "params_from": "rf"},
    "logit":    {"label": "Logistic regression",    "tune": "logit", "stochastic": False},
    "poly":     {"label": "Flood polynomial",       "tune": None,    "stochastic": False,
                 "fixed": True},
}
