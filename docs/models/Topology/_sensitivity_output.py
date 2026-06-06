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


"""Topology sensitivity — LaTeX tables and matplotlib figures."""

import logging

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import umap
from sklearn.ensemble import RandomForestClassifier
from sklearn.manifold import trustworthiness
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import cross_val_score
from sklearn.neighbors import KNeighborsRegressor

from _sensitivity_data import FIGURES_DIR, MKM_BLUE, MKM_GREY, MKM_RED, SEED

logger = logging.getLogger(__name__)

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
