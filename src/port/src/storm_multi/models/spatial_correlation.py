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
Spatially correlated precipitation model for Storm Generator v2.0.

Generates per-gauge precipitation multipliers using an exponential
correlation kernel calibrated to the Thames catchment (spec: Storm Generator
Spatial Correlation Spec, Section 5).

Algorithm:
    1. Build N×N Haversine distance matrix once at construction.
    2. Build correlation matrix:
           C[i,j] = (1 - nugget) * exp(-d[i,j] / range_km)  for i ≠ j
           C[i,i] = 1.0
    3. Intensity-conditioned range:
           range_km = base_range * (1 + rho_intensity * (intensity_factor - 1))
    4. Cholesky decomposition: L  s.t.  L @ L.T = C  (cached by range).
    5. Per active precipitation hour:
           z       = L @ N(0, 1)^n_gauges       (correlated standard normals)
           M       = exp(sigma * z - sigma² / 2) (mean-1 lognormal)
           M_norm  = M / mean(M)                 (preserve catchment mean)
           precip_gauge[i] = catchment_precip * M_norm[i]

Default parameters (Thames-calibrated, spec Table 2):
    base_range_km   = 40.0   half of Thames corridor length
    nugget          = 0.05   5% micro-scale variability
    rho_intensity   = 0.40   range scaling per unit intensity_factor above 1
    sigma_lognormal = 0.40   40% spatial coefficient of variation
"""

import json
import math
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from ..core.data_structures import StormSequence
from config.port import (
    SPATIAL_CORR_BASE_RANGE_KM,
    SPATIAL_CORR_NUGGET,
    SPATIAL_CORR_RHO_INTENSITY,
    SPATIAL_CORR_SIGMA_LOGNORMAL,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class SpatialCorrelationParams:
    """Parameters for the exponential spatial correlation model.

    Defaults are sourced from config.port (SPATIAL_CORR_*) so that a single
    edit to config/port.py propagates everywhere without touching this file.
    """
    base_range_km: float = SPATIAL_CORR_BASE_RANGE_KM    # Correlation range at intensity_factor = 1
    nugget: float = SPATIAL_CORR_NUGGET                   # Micro-scale variability (diagonal regularisation)
    rho_intensity: float = SPATIAL_CORR_RHO_INTENSITY     # Range increase per unit intensity_factor above 1
    sigma_lognormal: float = SPATIAL_CORR_SIGMA_LOGNORMAL # Log-space standard deviation of spatial field

    @classmethod
    def from_dict(cls, d: dict) -> "SpatialCorrelationParams":
        sc = d.get("spatial_correlation", d)
        return cls(
            base_range_km=sc.get("base_range_km", SPATIAL_CORR_BASE_RANGE_KM),
            nugget=sc.get("nugget", SPATIAL_CORR_NUGGET),
            rho_intensity=sc.get("rho_intensity", SPATIAL_CORR_RHO_INTENSITY),
            sigma_lognormal=sc.get("sigma_lognormal", SPATIAL_CORR_SIGMA_LOGNORMAL),
        )

    @classmethod
    def load(cls, path: Path) -> "SpatialCorrelationParams":
        with open(path) as f:
            return cls.from_dict(json.load(f))


# ---------------------------------------------------------------------------
# Main model
# ---------------------------------------------------------------------------

class SpatialCorrelationModel:
    """Spatially correlated precipitation field generator.

    Constructs the distance matrix and caches Cholesky factors at first use
    for each distinct effective range. Sampling is therefore fast after the
    first call at a given intensity level.

    Args:
        gauge_locations: Sequence of (latitude, longitude) pairs in degrees.
        params: Correlation model parameters. Defaults to Thames calibration.
    """

    def __init__(
        self,
        gauge_locations: Sequence[Tuple[float, float]],
        params: Optional[SpatialCorrelationParams] = None,
    ):
        self.params = params or SpatialCorrelationParams()
        self.gauge_locations = np.array(gauge_locations, dtype=float)  # (n, 2): [lat, lon]
        self.n_gauges = len(self.gauge_locations)
        self.dist_matrix = self._build_distance_matrix()
        self._cholesky_cache: Dict[float, np.ndarray] = {}

    # ------------------------------------------------------------------
    # Distance matrix
    # ------------------------------------------------------------------

    @staticmethod
    def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine great-circle distance in km."""
        R = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
        return R * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    def _build_distance_matrix(self) -> np.ndarray:
        """Build symmetric N×N Haversine distance matrix (km)."""
        n = self.n_gauges
        D = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                d = self.haversine_km(
                    self.gauge_locations[i, 0], self.gauge_locations[i, 1],
                    self.gauge_locations[j, 0], self.gauge_locations[j, 1],
                )
                D[i, j] = d
                D[j, i] = d
        return D

    # ------------------------------------------------------------------
    # Correlation matrix
    # ------------------------------------------------------------------

    def effective_range_km(self, intensity_factor: float) -> float:
        """Intensity-conditioned correlation range.

        Higher-intensity storms have broader spatial footprint → longer
        effective range → stronger spatial coherence across gauges.

        Args:
            intensity_factor: Storm intensity multiplier (e.g. 1.0 = moderate,
                              1.8 = severe, 3.0 = extreme).

        Returns:
            Effective correlation range in km.
        """
        return self.params.base_range_km * (
            1.0 + self.params.rho_intensity * max(0.0, intensity_factor - 1.0)
        )

    def correlation_matrix(self, range_km: float) -> np.ndarray:
        """Build N×N exponential correlation matrix.

        C[i,j] = (1 - nugget) * exp(-d[i,j] / range_km)   for i ≠ j
        C[i,i] = 1.0

        The nugget reduces off-diagonal values to ensure the matrix is
        strictly positive definite for Cholesky decomposition.

        Args:
            range_km: Effective correlation range.

        Returns:
            Symmetric (n_gauges, n_gauges) correlation matrix.
        """
        C = (1.0 - self.params.nugget) * np.exp(-self.dist_matrix / range_km)
        np.fill_diagonal(C, 1.0)
        return C

    # ------------------------------------------------------------------
    # Cholesky (cached)
    # ------------------------------------------------------------------

    def _get_cholesky(self, range_km: float) -> np.ndarray:
        """Return (and cache) Cholesky factor for a given range.

        The cache key is range rounded to 1 decimal place so that ranges
        that are effectively identical reuse the same factor.
        """
        key = round(range_km, 1)
        if key not in self._cholesky_cache:
            C = self.correlation_matrix(range_km)
            try:
                L = np.linalg.cholesky(C)
            except np.linalg.LinAlgError:
                # Fallback: add small jitter if numerical issues arise
                logger.warning(
                    "Cholesky failed at range %.1f km — adding jitter", range_km
                )
                C += np.eye(self.n_gauges) * 1e-6
                L = np.linalg.cholesky(C)
            self._cholesky_cache[key] = L
            logger.debug("Cached Cholesky for range=%.1f km", range_km)
        return self._cholesky_cache[key]

    # ------------------------------------------------------------------
    # Sampling
    # ------------------------------------------------------------------

    def sample_multipliers(
        self,
        intensity_factor: float,
        rng: Optional[np.random.RandomState] = None,
    ) -> np.ndarray:
        """Sample one set of per-gauge precipitation multipliers.

        The returned multipliers preserve the catchment mean: mean(M_norm) = 1.
        Applying them to catchment-average precipitation gives spatially
        varying gauge-level precipitation that sums to the same total.

        Args:
            intensity_factor: Determines the effective correlation range.
            rng: Random state for reproducibility.

        Returns:
            np.ndarray of shape (n_gauges,) with positive multipliers
            whose mean is exactly 1.0.
        """
        range_km = self.effective_range_km(intensity_factor)
        L = self._get_cholesky(range_km)

        if rng is not None:
            z = rng.randn(self.n_gauges)
        else:
            z = np.random.randn(self.n_gauges)

        correlated_z = L @ z
        sigma = self.params.sigma_lognormal
        M = np.exp(sigma * correlated_z - 0.5 * sigma ** 2)
        return M / M.mean()

    def apply_to_sequence(
        self,
        sequence: StormSequence,
        catchment_precip: np.ndarray,
        rng: Optional[np.random.RandomState] = None,
    ) -> np.ndarray:
        """Apply spatial correlation to a sequence's catchment precipitation.

        For each hour with non-zero precipitation, sample spatially correlated
        multipliers and distribute the catchment total across gauges. Hours
        with zero precipitation remain zero at all gauges.

        Args:
            sequence: The StormSequence providing the intensity_factor.
            catchment_precip: Hourly catchment precipitation (mm/h), shape (168,).
            rng: Random state for reproducibility.

        Returns:
            np.ndarray of shape (n_gauges, 168) containing per-gauge hourly
            precipitation (mm/h). Each column preserves catchment mean.
        """
        n_hours = len(catchment_precip)
        gauge_precip = np.zeros((self.n_gauges, n_hours))
        intensity = sequence.max_intensity_factor

        for h in range(n_hours):
            cp = catchment_precip[h]
            if cp > 0.0:
                M = self.sample_multipliers(intensity, rng=rng)
                gauge_precip[:, h] = cp * M

        return gauge_precip

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_gauge_portfolio(
        cls,
        portfolio: dict,
        params: Optional[SpatialCorrelationParams] = None,
    ) -> "SpatialCorrelationModel":
        """Construct from a gauge portfolio dict (as loaded from gauge.json).

        Args:
            portfolio: Dict with key 'flood_gauges' → list of gauge dicts.
            params: Correlation parameters. Defaults to Thames calibration.
        """
        locations = []
        for entry in portfolio.get("flood_gauges", []):
            fg = entry.get("FloodGauge", entry)
            loc = fg.get("Location", {})
            lat = loc.get("GaugeLatitude", 0.0)
            lon = loc.get("GaugeLongitude", 0.0)
            locations.append((lat, lon))
        return cls(gauge_locations=locations, params=params)

    @classmethod
    def from_gauge_portfolio_file(
        cls,
        path: Path,
        params: Optional[SpatialCorrelationParams] = None,
    ) -> "SpatialCorrelationModel":
        """Construct from a gauge portfolio JSON file."""
        with open(path) as f:
            portfolio = json.load(f)
        return cls.from_gauge_portfolio(portfolio, params=params)


# ---------------------------------------------------------------------------
# Config file I/O
# ---------------------------------------------------------------------------

def save_spatial_correlation_config(
    path: Path,
    params: Optional[SpatialCorrelationParams] = None,
) -> None:
    """Write a spatial correlation config JSON file (for export / debugging).

    The canonical parameter values live in config.port (SPATIAL_CORR_*).
    This function serialises a SpatialCorrelationParams instance — or the
    config defaults when none is supplied — to JSON for inspection or hand-off.
    """
    from config.port import (
        SPATIAL_CORR_ENABLED,
        SPATIAL_CORR_MODEL_TYPE,
        SPATIAL_CORR_NUM_GAUGES,
    )
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
