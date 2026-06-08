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
Model B — Ground Motion Intensity (MKM-SEIS-001).

Maps each instantiated earthquake's ``(M, R_JB)`` pair to a site peak ground
acceleration (PGA) via a Ground Motion Prediction Equation (GMPE) in lognormal
form:

    ln(PGA) = ln_PGA_mean(M, R_JB, V_S30) + sigma_total * epsilon,  epsilon ~ N(0, 1)

The seed GMPE is a single parametric Boore-Atkinson-style functional form per
tectonic regime (config/seismic_zones.json):

    ln(PGA_g) = c0 + c1 (M - mref) + c2 (M - mref)^2
                + c3 ln(sqrt(R_JB^2 + h^2)) + c4 ln(V_S30 / vref)

Soil amplification enters implicitly through V_S30. Additionally, when GS02
(seismic foundation design) is ABSENT and the site class is D or E, a soft-soil
amplification factor F_a multiplies the GMPE median before the residual is
sampled (Section 3.3 / Appendix C2).

The aleatory residual epsilon is the only random draw in Model B (one per
instantiated earthquake), taken from the single caller-owned generator so two
assets at the same (M, R_JB) receive different PGA realisations.
"""

import math
from typing import Tuple

import numpy as np

from config.seismic import GroundMotionConfig, OccurrenceConfig, SeismicModelConfig
from models.seismic.datastructures import (
    AssetSeismicFeatures,
    GroundMotionResult,
    GroundMotionSample,
    OccurrenceResult,
)
from models.seismic.occurrence import resolve_site_class

__all__ = [
    "regime_for_zone",
    "gmpe_for_regime",
    "effective_vs30",
    "gmpe_median_pga",
    "soil_amplification_factor",
    "sample_pga",
    "simulate_asset_ground_motion",
    "simulate_portfolio_ground_motion",
]


def regime_for_zone(
    zone: str, occ_cfg: OccurrenceConfig, gm_cfg: GroundMotionConfig,
) -> str:
    """The tectonic regime (and hence GMPE) for a hazard zone."""
    regime = occ_cfg.zones.get(zone, {}).get(
        "tectonic_regime", gm_cfg.default_regime)
    return regime if regime in gm_cfg.gmpe_by_regime else gm_cfg.default_regime


def gmpe_for_regime(regime: str, gm_cfg: GroundMotionConfig) -> dict:
    """The GMPE coefficient block for a regime (falling back to the default)."""
    return (gm_cfg.gmpe_by_regime.get(regime)
            or gm_cfg.gmpe_by_regime[gm_cfg.default_regime])


def effective_vs30(
    features: AssetSeismicFeatures, site_class: str, gm_cfg: GroundMotionConfig,
) -> float:
    """The V_S30 (m/s) to use: the asset's measured value, else the class proxy."""
    if features.soil_vs30_mps is not None:
        return features.soil_vs30_mps
    return gm_cfg.vs30_proxy_by_class.get(
        site_class, gm_cfg.vs30_proxy_by_class[gm_cfg.default_site_class])


def gmpe_median_pga(
    magnitude: float, r_jb_km: float, vs30: float, gmpe: dict,
) -> float:
    """Evaluate the parametric GMPE median PGA (g) — no residual, no F_a."""
    dm = magnitude - gmpe["mref"]
    r = math.sqrt(r_jb_km * r_jb_km + gmpe["h_km"] * gmpe["h_km"])
    ln_pga = (
        gmpe["c0"]
        + gmpe["c1"] * dm
        + gmpe["c2"] * dm * dm
        + gmpe["c3"] * math.log(r)
        + gmpe["c4"] * math.log(vs30 / gmpe["vref"])
    )
    return math.exp(ln_pga)


def soil_amplification_factor(
    features: AssetSeismicFeatures, site_class: str, gm_cfg: GroundMotionConfig,
) -> float:
    """Soft-soil amplification F_a applied to the GMPE median.

    F_a (default 1.30) applies only when the site class is in the gated set
    (D/E) and GS02 (seismic foundation design) is absent; otherwise 1.0.
    """
    amp = gm_cfg.soil_amplification
    if site_class in amp["applies_classes"] and not features.has(amp.get("gs02_code", "GS02")):
        return amp["fa"]
    return 1.0


def sample_pga(
    magnitude: float,
    r_jb_km: float,
    vs30: float,
    amplification_factor: float,
    gmpe: dict,
    sigma_total: float,
    rng: np.random.Generator,
) -> Tuple[float, float, float]:
    """Draw one site PGA (g) from the lognormal GMPE.

    Returns ``(pga_g, median_pga_g, epsilon)`` where ``median_pga_g`` already
    includes the soft-soil amplification factor.
    """
    median = gmpe_median_pga(magnitude, r_jb_km, vs30, gmpe) * amplification_factor
    epsilon = float(rng.standard_normal())
    pga = median * math.exp(sigma_total * epsilon)
    return pga, median, epsilon


def simulate_asset_ground_motion(
    occurrence: OccurrenceResult,
    features: AssetSeismicFeatures,
    config: SeismicModelConfig,
    rng: np.random.Generator,
) -> GroundMotionResult:
    """Sample a site PGA for every instantiated earthquake of one asset.

    Args:
        occurrence: the asset's Model A result (carries the events + site class).
        features: the asset's CDM-derived feature bundle (V_S30, GS02 gate).
        config: the hydrated seismic model config.
        rng: caller-owned random generator (one residual draw per event).

    Returns:
        A :class:`GroundMotionResult` whose samples align with the events.
    """
    gm_cfg = config.ground_motion
    regime = regime_for_zone(occurrence.zone, config.occurrence, gm_cfg)
    gmpe = gmpe_for_regime(regime, gm_cfg)
    sigma = gmpe.get("sigma_total", gm_cfg.default_sigma_total)
    site_class = occurrence.site_class
    vs30 = effective_vs30(features, site_class, gm_cfg)
    fa = soil_amplification_factor(features, site_class, gm_cfg)

    samples = []
    for ev in occurrence.events:
        pga, median, eps = sample_pga(
            ev.magnitude, ev.r_jb_km, vs30, fa, gmpe, sigma, rng)
        samples.append(GroundMotionSample(
            draw_index=ev.draw_index,
            pga_g=pga,
            median_pga_g=median,
            epsilon=eps,
        ))

    return GroundMotionResult(
        asset_id=occurrence.asset_id,
        regime=regime,
        vs30_mps=vs30,
        site_class=site_class,
        amplification_factor=fa,
        sigma_total=sigma,
        samples=samples,
    )


def simulate_portfolio_ground_motion(
    occurrences,
    features_by_id,
    config: SeismicModelConfig,
    rng: np.random.Generator,
):
    """Sample ground motion for every asset's occurrence result.

    Args:
        occurrences: list of per-asset :class:`OccurrenceResult`.
        features_by_id: mapping asset_id -> AssetSeismicFeatures.
        config: the hydrated seismic model config.
        rng: the single caller-owned generator.
    """
    return [
        simulate_asset_ground_motion(occ, features_by_id[occ.asset_id], config, rng)
        for occ in occurrences
    ]
