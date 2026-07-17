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

"""Topology sensitivity — single UMAP evaluation + parameter sweeps."""

import logging
import time

import numpy as np
import umap
from sklearn.ensemble import RandomForestClassifier
from sklearn.manifold import trustworthiness
from sklearn.metrics import mean_squared_error, silhouette_score
from sklearn.model_selection import cross_val_score
from sklearn.neighbors import KNeighborsRegressor

from _sensitivity_data import SEED, compute_continuity

logger = logging.getLogger(__name__)

def evaluate_umap(X, y_class, y_flood, n_neighbors=30, min_dist=0.25,
                  n_components=5, seed=SEED):
    """
    Run UMAP with given params and evaluate all metrics.

    Returns dict with: trustworthiness, continuity, storm_accuracy,
    silhouette, flood_rmse
    """
    reducer = umap.UMAP(
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        n_components=n_components,
        random_state=seed,
        n_jobs=1,
    )
    X_embedded = reducer.fit_transform(X)

    # Trustworthiness (sklearn)
    trust = trustworthiness(X, X_embedded, n_neighbors=min(15, n_neighbors))

    # Continuity
    cont = compute_continuity(X, X_embedded, k=min(15, n_neighbors))

    # Storm classification accuracy (RF on embedded features)
    clf = RandomForestClassifier(n_estimators=50, random_state=seed)
    scores = cross_val_score(clf, X_embedded, y_class, cv=5, scoring="accuracy")
    storm_acc = scores.mean()

    # Silhouette score on embedded space
    sil = silhouette_score(X_embedded, y_class, sample_size=min(500, len(y_class)))

    # Flood RMSE (KNN regressor on embedded features)
    reg = KNeighborsRegressor(n_neighbors=10)
    from sklearn.model_selection import cross_val_predict
    y_pred = cross_val_predict(reg, X_embedded, y_flood, cv=5)
    flood_rmse = np.sqrt(mean_squared_error(y_flood, y_pred))

    return {
        "trustworthiness": float(trust),
        "continuity": float(cont),
        "storm_accuracy": float(storm_acc),
        "silhouette": float(sil),
        "flood_rmse": float(flood_rmse),
    }

def sweep_n_neighbors(X, y_class, y_flood):
    """Sweep n_neighbors parameter."""
    values = [10, 15, 20, 30, 40, 50]
    results = []
    for v in values:
        logger.info("  n_neighbors = %d", v)
        r = evaluate_umap(X, y_class, y_flood, n_neighbors=v)
        r["n_neighbors"] = v
        results.append(r)
    return results

def sweep_min_dist(X, y_class, y_flood):
    """Sweep min_dist parameter."""
    values = [0.05, 0.10, 0.25, 0.40, 0.50]
    results = []
    for v in values:
        logger.info("  min_dist = %.2f", v)
        r = evaluate_umap(X, y_class, y_flood, min_dist=v)
        r["min_dist"] = v
        results.append(r)
    return results

def sweep_n_components(X, y_class, y_flood):
    """Sweep n_components parameter."""
    values = [2, 3, 5, 7, 10]
    results = []
    for v in values:
        logger.info("  n_components = %d", v)
        r = evaluate_umap(X, y_class, y_flood, n_components=v)
        r["n_components"] = v
        results.append(r)
    return results

def sweep_ensemble_size(X, y_class, y_flood):
    """
    Sweep ensemble size by running multiple UMAP fits with different seeds
    and measuring prediction spread.
    """
    ensemble_sizes = [5, 10, 20, 50]
    results = []

    # Use subset for ensemble sweep (each fit is expensive)
    rng = np.random.RandomState(SEED)
    n_sub = min(500, len(y_flood))
    idx = rng.choice(len(y_flood), n_sub, replace=False)
    X_sub, y_flood_sub = X[idx], y_flood[idx]

    for ne in ensemble_sizes:
        logger.info("  ensemble_size = %d", ne)
        start = time.time()
        predictions = []

        for i in range(ne):
            reducer = umap.UMAP(
                n_neighbors=30, min_dist=0.25, n_components=5,
                random_state=SEED + i, n_jobs=1,
            )
            X_emb = reducer.fit_transform(X_sub)
            reg = KNeighborsRegressor(n_neighbors=10)
            reg.fit(X_emb, y_flood_sub)
            predictions.append(reg.predict(X_emb))

        elapsed = time.time() - start
        preds = np.array(predictions)
        mean_pred = preds.mean(axis=0)

        # 90% CI width per sample, then average
        ci_low = np.percentile(preds, 5, axis=0)
        ci_high = np.percentile(preds, 95, axis=0)
        ci_width = float(np.mean(ci_high - ci_low))

        # CRPS approximation (mean absolute error of ensemble mean)
        crps = float(np.mean(np.abs(mean_pred - y_flood_sub)))

        results.append({
            "ensemble_size": ne,
            "ci_width_90": ci_width,
            "crps": crps,
            "latency_s": float(elapsed),
        })

    return results
