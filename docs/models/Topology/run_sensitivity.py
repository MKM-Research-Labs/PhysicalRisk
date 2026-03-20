#!/usr/bin/env python3

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
Topology Model — Sensitivity Analysis Runner

Generates reproducible sensitivity results for the UMAP weather-to-flood
dimensionality reduction model. Produces:
  - LaTeX tables (topology/figures/table_*.tex)
  - PNG figures  (topology/figures/*.png)
  - JSON audit log (topology/figures/audit_log.json)

All random seeds are fixed for reproducibility.

Usage:
    python run_sensitivity.py
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.manifold import trustworthiness
from sklearn.metrics import mean_squared_error, silhouette_score
from sklearn.model_selection import cross_val_score
from sklearn.neighbors import KNeighborsRegressor

import umap

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SEED = 42
FIGURES_DIR = Path(__file__).parent / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

# ─── Colour scheme (matches MKM branding) ───────────────────────────────────
MKM_BLUE = "#1565C0"
MKM_RED = "#C62828"
MKM_GREY = "#616161"
MKM_LIGHT = "#E3F2FD"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SYNTHETIC DATA GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_weather_data(n_samples=2000, n_features=50, n_storm_types=5, seed=SEED):
    """
    Generate synthetic high-dimensional weather data mimicking HRRR fields.

    Features represent atmospheric variables (pressure, temperature, humidity,
    wind components) at multiple grid points. Storm types represent distinct
    meteorological regimes (frontal, convective, orographic, etc.).

    Returns:
        X: (n_samples, n_features) weather state matrix
        y_class: (n_samples,) storm type labels
        y_flood: (n_samples,) simulated flood depth (m)
    """
    rng = np.random.RandomState(seed)

    # Weather states with cluster structure (storm types)
    X, y_class = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=20,
        n_redundant=15,
        n_clusters_per_class=2,
        n_classes=n_storm_types,
        random_state=seed,
    )

    # Add realistic noise (sensor/forecast uncertainty)
    X += rng.normal(0, 0.3, X.shape)

    # Simulate flood depth as nonlinear function of weather + terrain
    # This mimics the weather-to-flood mapping Psi
    terrain = rng.uniform(0, 1, n_samples)
    precip_proxy = X[:, :5].sum(axis=1)
    wind_proxy = X[:, 5:10].sum(axis=1)
    y_flood = (
        0.5 * np.tanh(precip_proxy)
        + 0.3 * terrain
        + 0.1 * np.abs(wind_proxy)
        + rng.normal(0, 0.05, n_samples)
    )
    y_flood = np.clip(y_flood, 0, 3.0)  # Physical bounds: 0-3m

    logger.info(
        "Generated %d weather samples: %d features, %d storm types, "
        "flood depth range [%.2f, %.2f] m",
        n_samples, n_features, n_storm_types,
        y_flood.min(), y_flood.max()
    )
    return X, y_class, y_flood


def compute_continuity(X_high, X_low, k=15):
    """
    Compute continuity metric C(k).

    Measures whether k-nearest neighbours in the HIGH-dimensional space
    are also neighbours in the low-dimensional space.
    (Complementary to trustworthiness which checks the reverse.)
    """
    from sklearn.neighbors import NearestNeighbors

    n = X_high.shape[0]
    nn_high = NearestNeighbors(n_neighbors=k + 1).fit(X_high)
    nn_low = NearestNeighbors(n_neighbors=k + 1).fit(X_low)

    _, idx_high = nn_high.kneighbors(X_high)
    _, idx_low = nn_low.kneighbors(X_low)

    # For each point, find neighbours in high-D that are NOT in low-D k-neighbourhood
    total = 0
    for i in range(n):
        high_neighbors = set(idx_high[i, 1:])
        low_neighbors = set(idx_low[i, 1:])
        missing = high_neighbors - low_neighbors

        for j in missing:
            # Rank of j in low-D
            rank_low = np.where(idx_low[i] == j)[0]
            if len(rank_low) > 0:
                total += rank_low[0] - k
            else:
                # j not in extended neighbourhood, use max rank
                dists = np.linalg.norm(X_low[i] - X_low[j])
                total += k  # conservative estimate

    normaliser = n * k * (2 * n - 3 * k - 1)
    if normaliser == 0:
        return 1.0
    return 1.0 - (2.0 / normaliser) * total


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SINGLE EVALUATION
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PARAMETER SWEEPS
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# 4. OUTPUT: LATEX TABLES
# ═══════════════════════════════════════════════════════════════════════════════

def write_table_neighbors(results, path):
    lines = [
        r"\begin{table}[H]",
        r"\centering",
        r"\begin{tabular}{rcccc}",
        r"    \toprule",
        r"    $n\_neighbors$ & Trustworthiness & Continuity & Storm Accuracy & Flood RMSE (m) \\",
        r"    \midrule",
    ]
    for r in results:
        lines.append(
            f"    {r['n_neighbors']} & {r['trustworthiness']:.3f} & "
            f"{r['continuity']:.3f} & {r['storm_accuracy']*100:.1f}\\% & "
            f"{r['flood_rmse']:.3f} \\\\"
        )
    lines += [
        r"    \bottomrule",
        r"\end{tabular}",
        r"\caption{Sensitivity to $n\_neighbors$ (default = 30)}",
        r"\label{tab:sens_neighbors}",
        r"\end{table}",
    ]
    path.write_text("\n".join(lines))
    logger.info("Wrote %s", path)


def write_table_mindist(results, path):
    lines = [
        r"\begin{table}[H]",
        r"\centering",
        r"\begin{tabular}{rcccc}",
        r"    \toprule",
        r"    $min\_dist$ & Trustworthiness & Continuity & Storm Accuracy & Flood RMSE (m) \\",
        r"    \midrule",
    ]
    for r in results:
        lines.append(
            f"    {r['min_dist']:.2f} & {r['trustworthiness']:.3f} & "
            f"{r['continuity']:.3f} & {r['storm_accuracy']*100:.1f}\\% & "
            f"{r['flood_rmse']:.3f} \\\\"
        )
    lines += [
        r"    \bottomrule",
        r"\end{tabular}",
        r"\caption{Sensitivity to $min\_dist$ (default = 0.25)}",
        r"\label{tab:sens_mindist}",
        r"\end{table}",
    ]
    path.write_text("\n".join(lines))
    logger.info("Wrote %s", path)


def write_table_components(results, path):
    lines = [
        r"\begin{table}[H]",
        r"\centering",
        r"\begin{tabular}{rcccc}",
        r"    \toprule",
        r"    $n\_components$ & Trustworthiness & Continuity & Storm Accuracy & Flood RMSE (m) \\",
        r"    \midrule",
    ]
    for r in results:
        lines.append(
            f"    {r['n_components']} & {r['trustworthiness']:.3f} & "
            f"{r['continuity']:.3f} & {r['storm_accuracy']*100:.1f}\\% & "
            f"{r['flood_rmse']:.3f} \\\\"
        )
    lines += [
        r"    \bottomrule",
        r"\end{tabular}",
        r"\caption{Sensitivity to target dimensionality (default = 5)}",
        r"\label{tab:sens_components}",
        r"\end{table}",
    ]
    path.write_text("\n".join(lines))
    logger.info("Wrote %s", path)


def write_table_ensemble(results, path):
    lines = [
        r"\begin{table}[H]",
        r"\centering",
        r"\begin{tabular}{rccc}",
        r"    \toprule",
        r"    $N_e$ & 90\% CI Width (m) & CRPS & Latency (s) \\",
        r"    \midrule",
    ]
    for r in results:
        lines.append(
            f"    {r['ensemble_size']} & {r['ci_width_90']:.3f} & "
            f"{r['crps']:.4f} & {r['latency_s']:.1f} \\\\"
        )
    lines += [
        r"    \bottomrule",
        r"\end{tabular}",
        r"\caption{Sensitivity to ensemble size (default = 50)}",
        r"\label{tab:sens_ensemble}",
        r"\end{table}",
    ]
    path.write_text("\n".join(lines))
    logger.info("Wrote %s", path)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. OUTPUT: FIGURES
# ═══════════════════════════════════════════════════════════════════════════════

def plot_sweep(results, param_key, param_label, filename):
    """Generate a 2x2 sensitivity plot for a parameter sweep."""
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    fig.suptitle(f"Sensitivity to {param_label}", fontsize=14, fontweight="bold")

    xs = [r[param_key] for r in results]

    metrics = [
        ("trustworthiness", "Trustworthiness", MKM_BLUE),
        ("continuity", "Continuity", MKM_GREY),
        ("storm_accuracy", "Storm Accuracy", MKM_BLUE),
        ("flood_rmse", "Flood RMSE (m)", MKM_RED),
    ]

    for ax, (key, label, color) in zip(axes.flat, metrics):
        ys = [r[key] for r in results]
        if key == "storm_accuracy":
            ys = [y * 100 for y in ys]
            label += " (%)"
        ax.plot(xs, ys, "o-", color=color, linewidth=2, markersize=6)
        ax.set_xlabel(param_label)
        ax.set_ylabel(label)
        ax.grid(True, alpha=0.3)

        # Highlight default value
        default_idx = None
        defaults = {"n_neighbors": 30, "min_dist": 0.25, "n_components": 5}
        if param_key in defaults:
            dv = defaults[param_key]
            if dv in xs:
                default_idx = xs.index(dv)
                ax.axvline(dv, color="grey", linestyle="--", alpha=0.5)

    plt.tight_layout()
    out = FIGURES_DIR / filename
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote %s", out)


def plot_ensemble(results, filename):
    """Plot ensemble size sensitivity."""
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    fig.suptitle("Sensitivity to Ensemble Size", fontsize=14, fontweight="bold")

    xs = [r["ensemble_size"] for r in results]

    for ax, key, label, color in [
        (axes[0], "ci_width_90", "90% CI Width (m)", MKM_BLUE),
        (axes[1], "crps", "CRPS", MKM_RED),
        (axes[2], "latency_s", "Latency (s)", MKM_GREY),
    ]:
        ys = [r[key] for r in results]
        ax.plot(xs, ys, "o-", color=color, linewidth=2, markersize=6)
        ax.set_xlabel("Ensemble Size $N_e$")
        ax.set_ylabel(label)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = FIGURES_DIR / filename
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote %s", out)


def plot_comparison_table(X, y_class, y_flood, filename):
    """
    Generate the method comparison chart (PCA vs t-SNE vs UMAP).
    """
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE

    rng = np.random.RandomState(SEED)

    methods = {}

    # PCA
    pca = PCA(n_components=5, random_state=SEED)
    X_pca = pca.fit_transform(X)
    trust_pca = trustworthiness(X, X_pca, n_neighbors=15)
    clf = RandomForestClassifier(n_estimators=50, random_state=SEED)
    acc_pca = cross_val_score(clf, X_pca, y_class, cv=5).mean()
    reg = KNeighborsRegressor(n_neighbors=10)
    from sklearn.model_selection import cross_val_predict
    pred_pca = cross_val_predict(reg, X_pca, y_flood, cv=5)
    rmse_pca = np.sqrt(mean_squared_error(y_flood, pred_pca))
    methods["PCA"] = {"accuracy": acc_pca, "rmse": rmse_pca, "trust": trust_pca}

    # UMAP
    reducer = umap.UMAP(n_neighbors=30, min_dist=0.25, n_components=5,
                        random_state=SEED, n_jobs=1)
    X_umap = reducer.fit_transform(X)
    trust_umap = trustworthiness(X, X_umap, n_neighbors=15)
    acc_umap = cross_val_score(clf, X_umap, y_class, cv=5).mean()
    pred_umap = cross_val_predict(reg, X_umap, y_flood, cv=5)
    rmse_umap = np.sqrt(mean_squared_error(y_flood, pred_umap))
    methods["UMAP"] = {"accuracy": acc_umap, "rmse": rmse_umap, "trust": trust_umap}

    # Bar chart comparison
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    fig.suptitle("Method Comparison: PCA vs UMAP", fontsize=14, fontweight="bold")

    names = list(methods.keys())
    colors = [MKM_GREY, MKM_BLUE]

    for ax, metric, label in [
        (axes[0], "accuracy", "Storm Classification Accuracy"),
        (axes[1], "rmse", "Flood RMSE (m)"),
        (axes[2], "trust", "Trustworthiness"),
    ]:
        vals = [methods[n][metric] for n in names]
        if metric == "accuracy":
            vals = [v * 100 for v in vals]
            label += " (%)"
        bars = ax.bar(names, vals, color=colors, edgecolor="white", linewidth=1.5)
        ax.set_ylabel(label)
        ax.grid(True, alpha=0.3, axis="y")
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                    f"{val:.2f}" if metric != "accuracy" else f"{val:.1f}%",
                    ha="center", va="bottom", fontsize=10)

    plt.tight_layout()
    out = FIGURES_DIR / filename
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote %s", out)

    return methods


# ═══════════════════════════════════════════════════════════════════════════════
# 6. MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    start_time = time.time()
    audit = {
        "script": "run_sensitivity.py",
        "timestamp": datetime.now().isoformat(),
        "seed": SEED,
        "umap_version": umap.__version__,
        "numpy_version": np.__version__,
        "python_version": sys.version,
        "results": {},
    }

    logger.info("=" * 60)
    logger.info("TOPOLOGY MODEL — SENSITIVITY ANALYSIS")
    logger.info("=" * 60)

    # Generate data
    logger.info("Generating synthetic weather data...")
    X, y_class, y_flood = generate_weather_data()
    audit["data"] = {
        "n_samples": X.shape[0],
        "n_features": X.shape[1],
        "n_storm_types": len(np.unique(y_class)),
        "flood_depth_range": [float(y_flood.min()), float(y_flood.max())],
    }

    # Sweep n_neighbors
    logger.info("Sweep 1/4: n_neighbors")
    res_neighbors = sweep_n_neighbors(X, y_class, y_flood)
    audit["results"]["n_neighbors"] = res_neighbors
    write_table_neighbors(res_neighbors, FIGURES_DIR / "table_neighbors.tex")
    plot_sweep(res_neighbors, "n_neighbors", "$n\\_neighbors$", "sens_neighbors.png")

    # Sweep min_dist
    logger.info("Sweep 2/4: min_dist")
    res_mindist = sweep_min_dist(X, y_class, y_flood)
    audit["results"]["min_dist"] = res_mindist
    write_table_mindist(res_mindist, FIGURES_DIR / "table_mindist.tex")
    plot_sweep(res_mindist, "min_dist", "$min\\_dist$", "sens_mindist.png")

    # Sweep n_components
    logger.info("Sweep 3/4: n_components")
    res_components = sweep_n_components(X, y_class, y_flood)
    audit["results"]["n_components"] = res_components
    write_table_components(res_components, FIGURES_DIR / "table_components.tex")
    plot_sweep(res_components, "n_components", "$n\\_components$", "sens_components.png")

    # Sweep ensemble size
    logger.info("Sweep 4/4: ensemble_size")
    res_ensemble = sweep_ensemble_size(X, y_class, y_flood)
    audit["results"]["ensemble_size"] = res_ensemble
    write_table_ensemble(res_ensemble, FIGURES_DIR / "table_ensemble.tex")
    plot_ensemble(res_ensemble, "sens_ensemble.png")

    # Method comparison
    logger.info("Generating method comparison...")
    comparison = plot_comparison_table(X, y_class, y_flood, "method_comparison.png")
    audit["results"]["method_comparison"] = {
        k: v for k, v in comparison.items()
    }

    # Write audit log
    elapsed = time.time() - start_time
    audit["elapsed_seconds"] = elapsed
    audit_path = FIGURES_DIR / "audit_log.json"
    with open(audit_path, "w") as f:
        json.dump(audit, f, indent=2)
    logger.info("Wrote audit log: %s", audit_path)

    logger.info("=" * 60)
    logger.info("COMPLETE in %.1f seconds", elapsed)
    logger.info("Output: %s", FIGURES_DIR)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
