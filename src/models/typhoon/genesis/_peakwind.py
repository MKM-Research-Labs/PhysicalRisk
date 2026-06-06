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


"""Peak-wind hybrid distribution and storm->wind coupling for the typhoon genesis prior."""

import math
from typing import Dict, Tuple

import numpy as np
from scipy.special import ndtri

from config.typhoon import PeakWindParams, ScenarioFamily


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
# Storm -> wind coupling — coupling_spec.md §3.3, §4
# ===========================================================================
#
# Under the coupled event set the per-event genesis peak wind is no longer an
# independent draw from a single scenario family. Instead the paired storm's
# severity quantile q drives a band-limited draw against the catchment's
# scenario-mix-weighted exceedance curve S_cat (re-roled as the attainable
# CEILING curve, not a realised marginal):
#
#     ceiling(q) = q
#     floor(q)   = 1 - (1 - q)^beta
#     rho_w      = floor(q) + B * (ceiling(q) - floor(q)),   B ~ Uniform[0,1]
#     u          = 1 - rho_w
#     Vmax       = S_cat^{-1}(u)
#
# This forbids low-rain/high-wind (rho_w <= q) while pulling wind up in the
# storm tail via the rising floor. beta is the single coupling-strength knob.


def coupling_floor(q: float, beta: float) -> float:
    """Rising wind floor f(q) = 1 - (1 - q)^beta  (coupling_spec.md §4.1).

    Monotone increasing in q, with f(q) <= q for all q in [0,1] (the band
    never inverts) and f(0) = 0. beta -> 0 collapses the floor to 0 (pure
    ceiling); beta = 1 gives f(q) = q (deterministic comonotone).
    """
    q = min(max(q, 0.0), 1.0)
    beta = max(beta, 0.0)
    return 1.0 - (1.0 - q) ** beta


def mixture_peak_wind_exceedance(
    v_ms: float,
    peak_wind: Dict[ScenarioFamily, PeakWindParams],
    scenario_mix: Dict[ScenarioFamily, float],
) -> float:
    """S_cat(v): scenario-mix-weighted survival function (coupling_spec.md §3.3).

        S_cat(v) = sum_family  w[family] * P(V > v | family)

    Weights are renormalised over the families that have both a positive mix
    weight and a PeakWindParams entry, so a partial config still yields a
    proper survival curve.
    """
    total = 0.0
    wsum = 0.0
    for family, weight in scenario_mix.items():
        params = peak_wind.get(family)
        if params is None or weight <= 0.0:
            continue
        total += weight * peak_wind_exceedance(v_ms, params)
        wsum += weight
    return total / wsum if wsum > 0.0 else 0.0


def mixture_peak_wind_inverse(
    u: float,
    peak_wind: Dict[ScenarioFamily, PeakWindParams],
    scenario_mix: Dict[ScenarioFamily, float],
    tol: float = 1e-4,
    max_iter: int = 100,
) -> float:
    """S_cat^{-1}(u): invert the mixture survival by bisection.

    S_cat is monotone decreasing in v, so a standard bisection on
    [min v_min_ms, max v_max_ms] across the active families converges. u is
    the exceedance probability (small u -> large Vmax). Out-of-range u clamps
    to the curve's endpoints.
    """
    families = [
        f for f, w in scenario_mix.items()
        if w > 0.0 and f in peak_wind
    ] or list(peak_wind.keys())

    v_lo = min(peak_wind[f].v_min_ms for f in families)
    v_hi = max(peak_wind[f].v_max_ms for f in families)

    u = min(max(u, 0.0), 1.0)

    def S(v: float) -> float:
        return mixture_peak_wind_exceedance(v, peak_wind, scenario_mix)

    # Endpoints: S(v_lo) is the largest attainable exceedance, S(v_hi) the
    # smallest. Targets outside that range clamp to the nearest endpoint.
    if u >= S(v_lo):
        return v_lo
    if u <= S(v_hi):
        return v_hi

    for _ in range(max_iter):
        mid = 0.5 * (v_lo + v_hi)
        if S(mid) > u:
            # Exceedance still above target -> need a higher wind speed.
            v_lo = mid
        else:
            v_hi = mid
        if v_hi - v_lo < tol:
            break
    return 0.5 * (v_lo + v_hi)


def derive_scenario_family(
    v_max_ms: float,
    peak_wind: Dict[ScenarioFamily, PeakWindParams],
    scenario_mix: Dict[ScenarioFamily, float],
) -> ScenarioFamily:
    """Label a coupled Vmax with the nearest scenario family (by body mean mu).

    Under coupling the scenario family is no longer sampled — it is a derived
    tag for downstream display/grouping. Families are intensity-ordered by
    mu_ms, so nearest-mu gives an intuitive label (a super-typhoon Vmax tags
    EXTREME; a mild Vmax tags HISTORICAL).
    """
    families = [
        f for f, w in scenario_mix.items()
        if w > 0.0 and f in peak_wind
    ] or list(peak_wind.keys())
    return min(families, key=lambda f: abs(v_max_ms - peak_wind[f].mu_ms))


def coupled_genesis_wind(
    q: float,
    beta: float,
    peak_wind: Dict[ScenarioFamily, PeakWindParams],
    scenario_mix: Dict[ScenarioFamily, float],
    rng: np.random.Generator,
) -> Tuple[float, ScenarioFamily]:
    """Draw a coupled genesis (Vmax, scenario_family) for one event.

    Implements the coupling_spec.md §4 band draw: given the paired storm's
    severity quantile q and the coupling strength beta, draw the wind
    strength-percentile rho_w uniformly in [floor(q), q], map to the
    exceedance probability u = 1 - rho_w, and invert S_cat to a peak wind.

    Args:
        q: storm severity quantile in [0,1] (1 = most severe storm).
        beta: coupling strength (>0). See coupling_floor.
        peak_wind: per-family PeakWindParams (the ceiling curve).
        scenario_mix: per-family mix weights.
        rng: random generator (the within-band B ~ Uniform[0,1] draw).

    Returns:
        (v_max_ms, scenario_family) — the genesis peak wind and its derived
        family label.
    """
    ceiling = min(max(q, 0.0), 1.0)
    floor = coupling_floor(q, beta)
    b = float(rng.uniform())
    rho_w = floor + b * (ceiling - floor)
    u = 1.0 - rho_w
    v_max_ms = mixture_peak_wind_inverse(u, peak_wind, scenario_mix)
    scenario = derive_scenario_family(v_max_ms, peak_wind, scenario_mix)
    return v_max_ms, scenario
