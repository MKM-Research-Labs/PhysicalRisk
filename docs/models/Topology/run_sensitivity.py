#!/usr/bin/env python3

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

"""
Topology Model — Sensitivity Analysis Runner

Generates reproducible sensitivity results for the UMAP weather-to-flood
dimensionality reduction model (LaTeX tables, PNG figures, JSON audit log).
All random seeds are fixed for reproducibility.

Usage:
    python run_sensitivity.py

Implementation is split across sibling modules (_sensitivity_data,
_sensitivity_eval, _sensitivity_output); this file is the orchestrator.
"""

import json
import logging
import sys
import time
from datetime import datetime

import numpy as np
import umap

from _sensitivity_data import SEED, FIGURES_DIR, generate_weather_data
from _sensitivity_eval import (
    sweep_n_neighbors, sweep_min_dist, sweep_n_components, sweep_ensemble_size,
)
from _sensitivity_output import (
    write_table_neighbors, write_table_mindist, write_table_components,
    write_table_ensemble, plot_sweep, plot_ensemble, plot_comparison_table,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


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
