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

"""Accuracy and calibration metrics on held-out storms."""

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from config.models import CHALLENGER_ECE_BINS, CHALLENGER_PROB_CLIP


def _clip(p):
    return np.clip(p, CHALLENGER_PROB_CLIP, 1 - CHALLENGER_PROB_CLIP)


def brier(y, p):
    return float(np.mean((p - y) ** 2))


def log_loss(y, p):
    p = _clip(p)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def auc(y, p):
    return float(roc_auc_score(y, p)) if 0 < y.sum() < len(y) else None


def reliability(y, p, bins=CHALLENGER_ECE_BINS):
    """Equal-width reliability bins: (mean predicted, observed rate, count)."""
    idx = np.minimum((p * bins).astype(int), bins - 1)
    rows = []
    for b in range(bins):
        m = idx == b
        n = int(m.sum())
        rows.append((float(p[m].mean()) if n else None,
                     float(y[m].mean()) if n else None, n))
    return rows


def ece(y, p, bins=CHALLENGER_ECE_BINS):
    """Expected calibration error over equal-width bins."""
    return float(sum(n * abs(mp - obs) for mp, obs, n in reliability(y, p, bins) if n)
                 / len(y))


def calibration_slope_intercept(y, p):
    """Logistic recalibration y ~ σ(α + β·logit p); perfect calibration is (0, 1)."""
    if not 0 < y.sum() < len(y):
        return None, None
    q = _clip(p)
    logit = np.log(q / (1 - q)).reshape(-1, 1)
    fit = LogisticRegression(penalty=None, max_iter=1000).fit(logit, y)
    return float(fit.coef_[0, 0]), float(fit.intercept_[0])


def score(y, p) -> dict:
    """All held-out metrics for one model.

    ``cash_mae`` is the mean |p − realised outcome| per unit notional: the error
    in the stress cash price N·p·d against the knock-out the storm delivered.
    """
    slope, intercept = calibration_slope_intercept(y, p)
    return {
        "brier": brier(y, p),
        "log_loss": log_loss(y, p),
        "auc": auc(y, p),
        "ece": ece(y, p),
        "cal_slope": slope,
        "cal_intercept": intercept,
        "cash_mae": float(np.mean(np.abs(p - y))),
        "n": int(len(y)),
    }
