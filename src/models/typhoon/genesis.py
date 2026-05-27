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
Genesis prior sampling for the typhoon model.

Implements the t=0 sampler that produces a TyphoonState from a
CatchmentTyphoonConfig. Each genesis sample consists of:

- Position uniform in the basin bbox
- Initial heading from a von Mises around the climatological mean
- Initial translation speed from a Gamma(shape, scale)
- Initial peak wind V_max from a hybrid truncated-normal + Pareto tail
  (spec eq. 14, per ScenarioFamily)
- Initial size (R_max, R_outer) from log-space regression on V_max
- Regime drawn from the categorical regime mixture
- Land flag evaluated via the catchment-supplied land_mask

The Pareto tail is the principal mechanism for generating rare extreme
storms; the scenario family controls how fat that tail is. Phase 1 of the
typhoon model prioritises *breadth* of the peak-wind distribution, so all
samplers route through this module.

All randomness flows through a single numpy.random.Generator passed in by
the caller. Callers that need reproducibility seed their own Generator.
"""

import math
from typing import Dict, List, Tuple

import numpy as np
from scipy.special import ndtri

from config.typhoon import (
    CatchmentTyphoonConfig,
    GenesisPrior,
    PeakWindParams,
    RegimeClass,
    ScenarioFamily,
    SizeParams,
)
from models.typhoon.data_structures import TyphoonState


__all__ = [
    "peak_wind_exceedance",
    "peak_wind_inverse_exceedance",
    "sample_peak_wind",
    "sample_genesis_location",
    "sample_initial_heading",
    "sample_initial_speed",
    "sample_initial_size",
    "sample_regime",
    "sample_scenario_family",
    "sample_genesis",
    "sample_genesis_ensemble",
]


# ===========================================================================
# Peak-wind hybrid distribution — spec eq. (14)
# ===========================================================================
#
#   P(V > v) = 1 - Phi((v - mu) / sigma),          v <= v_T   (body)
#   P(V > v) = P(V > v_T) * (v_T / v)^alpha,       v > v_T    (Pareto tail)
#
# Sampling is by inverse exceedance: draw U ~ Uniform(0, 1), compute
# v = F^{-1}(1 - U). U is interpreted as the exceedance probability p.


def _normal_cdf(z: float) -> float:
    """Standard normal CDF using math.erf (no scipy import needed)."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def peak_wind_exceedance(v_ms: float, params: PeakWindParams) -> float:
    """Survival function P(V > v) under the hybrid distribution.

    Args:
        v_ms: peak wind speed (m/s)
        params: distribution parameters (mu, sigma, v_T, alpha)

    Returns:
        P(V > v_ms) in [0, 1].
    """
    z = (v_ms - params.mu_ms) / params.sigma_ms
    body = 1.0 - _normal_cdf(z)
    if v_ms <= params.v_threshold_ms:
        return body
    z_t = (params.v_threshold_ms - params.mu_ms) / params.sigma_ms
    p_t = 1.0 - _normal_cdf(z_t)
    return p_t * (params.v_threshold_ms / v_ms) ** params.alpha


def peak_wind_inverse_exceedance(p: float, params: PeakWindParams) -> float:
    """Inverse survival function — solve P(V > v) = p for v.

    Args:
        p: exceedance probability in (0, 1)
        params: distribution parameters

    Returns:
        v such that P(V > v) = p, clamped to [v_min_ms, v_max_ms].
    """
    if p <= 0.0:
        return params.v_max_ms
    if p >= 1.0:
        return params.v_min_ms

    z_t = (params.v_threshold_ms - params.mu_ms) / params.sigma_ms
    p_t = 1.0 - _normal_cdf(z_t)

    if p >= p_t:
        # Body region: 1 - Phi((v - mu)/sigma) = p
        # => v = mu + sigma * Phi^{-1}(1 - p)
        v = params.mu_ms + params.sigma_ms * float(ndtri(1.0 - p))
    else:
        # Tail region: p_t * (v_t / v)^alpha = p
        # => v = v_t * (p_t / p)^(1 / alpha)
        v = params.v_threshold_ms * (p_t / p) ** (1.0 / params.alpha)

    return max(params.v_min_ms, min(params.v_max_ms, v))


def sample_peak_wind(params: PeakWindParams, rng: np.random.Generator) -> float:
    """Draw a single peak-wind sample under the hybrid distribution."""
    u = float(rng.uniform())
    return peak_wind_inverse_exceedance(u, params)


# ===========================================================================
# Initial-state samplers
# ===========================================================================


def sample_genesis_location(prior: GenesisPrior, rng: np.random.Generator) -> Tuple[float, float]:
    """Sample (longitude, latitude) uniformly inside the basin bbox."""
    lon_min, lat_min, lon_max, lat_max = prior.bbox
    lon = float(rng.uniform(lon_min, lon_max))
    lat = float(rng.uniform(lat_min, lat_max))
    return lon, lat


def sample_initial_heading(prior: GenesisPrior, rng: np.random.Generator) -> float:
    """Sample initial heading from a von Mises around the climatological mean.

    Returns a compass bearing in [0, 360).
    """
    # Convert compass degrees -> radians for the von Mises mode parameter.
    mu_rad = math.radians(prior.heading_mean_deg)
    sample_rad = float(rng.vonmises(mu_rad, prior.heading_kappa))
    # Numpy returns samples on (-pi, pi]; convert back to compass deg [0, 360).
    sample_deg = math.degrees(sample_rad)
    return sample_deg % 360.0


def sample_initial_speed(prior: GenesisPrior, rng: np.random.Generator) -> float:
    """Sample initial translation speed (km/h) from a Gamma(shape, scale)."""
    return float(rng.gamma(prior.speed_shape, prior.speed_scale))


def sample_initial_size(
    v_max_ms: float,
    params: SizeParams,
    rng: np.random.Generator,
) -> Tuple[float, float]:
    """Sample (R_max, R_outer) in km conditioned on V_max.

    Each radius is drawn from a lognormal whose mean (in log space) is a
    linear function of log(V_max). The invariant R_max < R_outer is
    enforced post-sampling by widening R_outer when collisions occur.
    """
    log_v = math.log(max(v_max_ms, 1.0))   # guard against V near zero
    log_rmax_mean = params.r_max_intercept_log_km + params.r_max_v_coef * log_v
    log_router_mean = params.r_outer_intercept_log_km + params.r_outer_v_coef * log_v

    log_rmax = float(rng.normal(log_rmax_mean, params.r_max_sigma_log))
    log_router = float(rng.normal(log_router_mean, params.r_outer_sigma_log))

    r_max = math.exp(log_rmax)
    r_outer = math.exp(log_router)

    # Invariant: R_max < R_outer. If a noisy draw violates it, widen R_outer
    # via the catchment-configured buffer factor (SizeParams.r_outer_invariant_buffer).
    if r_outer <= r_max:
        r_outer = r_max * params.r_outer_invariant_buffer

    return r_max, r_outer


def _categorical(weights: Dict, rng: np.random.Generator):
    """Draw a key from a non-empty {key: probability} mapping.

    Probabilities are renormalised defensively (so that small calibration
    drift in a catchment's weights does not error out at sample time).
    """
    if not weights:
        raise ValueError("Cannot sample from empty categorical weights")
    keys = list(weights.keys())
    probs = np.array([float(weights[k]) for k in keys], dtype=float)
    total = probs.sum()
    if total <= 0.0:
        raise ValueError("Categorical weights must sum to a positive value")
    probs = probs / total
    idx = int(rng.choice(len(keys), p=probs))
    return keys[idx]


def sample_regime(
    weights: Dict[RegimeClass, float],
    rng: np.random.Generator,
) -> RegimeClass:
    """Draw a regime class from the categorical regime mixture."""
    return _categorical(weights, rng)


def sample_scenario_family(
    mix: Dict[ScenarioFamily, float],
    rng: np.random.Generator,
) -> ScenarioFamily:
    """Draw a scenario family from the categorical scenario-family mixture."""
    return _categorical(mix, rng)


# ===========================================================================
# Top-level genesis samplers
# ===========================================================================


def sample_genesis(
    config: CatchmentTyphoonConfig,
    scenario: ScenarioFamily,
    rng: np.random.Generator,
) -> TyphoonState:
    """Sample one genesis state under the given scenario family.

    Args:
        config: catchment configuration
        scenario: scenario family selecting the peak-wind distribution
        rng: random generator (caller-owned for reproducibility)

    Returns:
        TyphoonState at t = 0.
    """
    prior = config.genesis_prior

    lon, lat = sample_genesis_location(prior, rng)
    heading_deg = sample_initial_heading(prior, rng)
    speed_kmh = sample_initial_speed(prior, rng)
    v_max_ms = sample_peak_wind(config.peak_wind[scenario], rng)
    r_max_km, r_outer_km = sample_initial_size(v_max_ms, config.size, rng)
    regime = sample_regime(prior.regime_weights, rng)
    land_flag = bool(config.land_mask(lon, lat))

    return TyphoonState(
        longitude=lon,
        latitude=lat,
        translation_speed_kmh=speed_kmh,
        heading_deg=heading_deg,
        v_max_ms=v_max_ms,
        r_max_km=r_max_km,
        r_outer_km=r_outer_km,
        regime=regime,
        land_flag=land_flag,
        time_hours=0.0,
    )


def sample_genesis_ensemble(
    config: CatchmentTyphoonConfig,
    n: int,
    rng: np.random.Generator,
) -> List[TyphoonState]:
    """Sample n genesis states with scenarios drawn from the prior mix.

    Args:
        config: catchment configuration
        n: number of genesis states to draw
        rng: random generator

    Returns:
        List of n TyphoonState instances at t = 0.
    """
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")
    mix = config.genesis_prior.scenario_mix
    states: List[TyphoonState] = []
    for _ in range(n):
        scenario = sample_scenario_family(mix, rng)
        states.append(sample_genesis(config, scenario, rng))
    return states
