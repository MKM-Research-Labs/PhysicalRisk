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
Pure-math helpers for the spatial correlation model.

Module-level functions (not class methods) so the heavy ``numpy`` /
linear-algebra logic can live separately from the orchestrating class
in ``spatial_correlation.py``.
"""

import json
import logging
import math
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine great-circle distance in km."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return R * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def build_distance_matrix(gauge_locations: np.ndarray) -> np.ndarray:
    """Build symmetric N×N Haversine distance matrix (km) for the gauges."""
    n = len(gauge_locations)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_km(
                gauge_locations[i, 0], gauge_locations[i, 1],
                gauge_locations[j, 0], gauge_locations[j, 1],
            )
            D[i, j] = d
            D[j, i] = d
    return D


def correlation_matrix(
    dist_matrix: np.ndarray, range_km: float, nugget: float
) -> np.ndarray:
    """Build the N×N exponential correlation matrix.

    C[i,j] = (1 - nugget) * exp(-d[i,j] / range_km)   for i ≠ j
    C[i,i] = 1.0

    The nugget reduces off-diagonal values to ensure the matrix is
    strictly positive definite for Cholesky decomposition.
    """
    C = (1.0 - nugget) * np.exp(-dist_matrix / range_km)
    np.fill_diagonal(C, 1.0)
    return C


def cholesky_with_jitter(C: np.ndarray, range_km: float) -> np.ndarray:
    """Try Cholesky; on failure add small jitter and retry.

    Logs a warning when jitter is needed (numerical stability fallback).
    """
    try:
        return np.linalg.cholesky(C)
    except np.linalg.LinAlgError:
        logger.warning(
            "Cholesky failed at range %.1f km — adding jitter", range_km
        )
        n = C.shape[0]
        return np.linalg.cholesky(C + np.eye(n) * 1e-6)


def save_spatial_correlation_config(
    path: Path,
    params=None,
) -> None:
    """Write a spatial correlation config JSON file (for export / debugging).

    The canonical parameter values live in config.port (SPATIAL_CORR_*).
    This function serialises a SpatialCorrelationParams instance — or the
    config defaults when none is supplied — to JSON for inspection or hand-off.
    """
    # Local imports to avoid circular dependency at module load time
    from config.port import (
        SPATIAL_CORR_ENABLED,
        SPATIAL_CORR_MODEL_TYPE,
        SPATIAL_CORR_NUM_GAUGES,
    )
    from .spatial_correlation import SpatialCorrelationParams

    p = params or SpatialCorrelationParams()
    cfg = {
        "spatial_correlation": {
            "enabled": SPATIAL_CORR_ENABLED,
            "model_type": SPATIAL_CORR_MODEL_TYPE,
            "base_range_km": p.base_range_km,
            "nugget": p.nugget,
            "rho_intensity": p.rho_intensity,
            "sigma_lognormal": p.sigma_lognormal,
            "num_gauges": SPATIAL_CORR_NUM_GAUGES,
        }
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)
    logger.info("Saved spatial correlation config to %s", path)
