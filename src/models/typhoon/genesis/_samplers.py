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

"""Initial-state samplers for the typhoon genesis prior."""

import math
from typing import Dict, Tuple

import numpy as np

from config.typhoon import GenesisPrior, RegimeClass, ScenarioFamily, SizeParams


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
