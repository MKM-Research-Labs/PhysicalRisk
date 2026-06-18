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

"""Genesis prior and per-block transition parameter dataclasses."""

from dataclasses import dataclass, field
from typing import Dict, Tuple

from config.typhoon._enums import RegimeClass, ScenarioFamily


@dataclass
class GenesisPrior:
    """Prior distribution over the initial (genesis) state.

    Sampled once per event at t = 0. The genesis state is propagated forward
    by the transition model.

    Attributes:
        bbox: spatial bbox for genesis location (lon_min, lat_min, lon_max, lat_max)
        heading_mean_deg: von Mises mean for initial heading (compass degrees)
        heading_kappa: von Mises concentration (higher = tighter around the mean)
        speed_shape: Gamma shape parameter for initial translation speed (km/h)
        speed_scale: Gamma scale parameter for initial translation speed (km/h)
        regime_weights: categorical weights over RegimeClass (must sum to 1)
        scenario_mix: categorical weights over ScenarioFamily (must sum to 1)
    """
    bbox: Tuple[float, float, float, float]
    heading_mean_deg: float
    heading_kappa: float
    speed_shape: float
    speed_scale: float
    regime_weights: Dict[RegimeClass, float] = field(default_factory=dict)
    scenario_mix: Dict[ScenarioFamily, float] = field(default_factory=dict)


# ===========================================================================
# Peak-wind distribution — spec eq. (14)
# ===========================================================================


@dataclass
class PeakWindParams:
    """Hybrid truncated-normal + Pareto tail for initial peak wind sampling.

    Reproduces spec eq. (14):
        P(V > v) = 1 - Phi((v - mu) / sigma),          v <= v_T
        P(V > v) = P(V > v_T) * (v_T / v)^alpha,       v > v_T

    A separate PeakWindParams instance is supplied per ScenarioFamily so the
    upper tail is controlled independently from the body.

    Attributes:
        mu_ms: baseline mean peak wind (m/s)
        sigma_ms: baseline standard deviation (m/s)
        v_threshold_ms: tail threshold v_T (m/s); above this the Pareto tail dominates
        alpha: Pareto tail index — lower = fatter tail
        v_min_ms: floor (samples below are clamped or rejected)
        v_max_ms: cap (samples above are clamped or rejected)
    """
    mu_ms: float
    sigma_ms: float
    v_threshold_ms: float
    alpha: float
    v_min_ms: float = 10.0
    v_max_ms: float = 100.0


# ===========================================================================
# Motion transition — spec eq. (5)
# ===========================================================================


@dataclass
class MotionParams:
    """Regime-conditioned motion transition parameters.

    The motion update is:
        u_t   ~ N(mu_u(s_{t-1}, k),   sigma_u^2(k))
        psi_t ~ N(mu_psi(s_{t-1}, k), sigma_psi^2(k))

    For Phase 1 we use simple persistence-plus-regime-target means:
        mu_u   = speed_persistence  * u_{t-1}   + (1 - speed_persistence)  * mean_speed[k]
        mu_psi = heading_persistence * psi_{t-1} + (1 - heading_persistence) * mean_heading[k]

    Above the recurvature latitude, NW_RECURVER and SHARP_RECURVE regimes apply
    an additive northward bias (recurvature_bias_deg_per_step) to mu_psi.

    Attributes:
        mean_speed_kmh: per-regime climatological mean translation speed (km/h)
        sigma_speed_kmh: per-regime stddev of one-step speed update (km/h)
        mean_heading_deg: per-regime climatological mean heading (compass deg)
        sigma_heading_deg: per-regime stddev of one-step heading update (deg)
        speed_persistence: weight on previous speed in the conditional mean (0..1)
        heading_persistence: weight on previous heading in the conditional mean (0..1)
        recurvature_latitude: latitude (deg) above which recurvature bias activates
        recurvature_bias_deg_per_step: additive northward bias above the threshold
    """
    mean_speed_kmh: Dict[RegimeClass, float] = field(default_factory=dict)
    sigma_speed_kmh: Dict[RegimeClass, float] = field(default_factory=dict)
    mean_heading_deg: Dict[RegimeClass, float] = field(default_factory=dict)
    sigma_heading_deg: Dict[RegimeClass, float] = field(default_factory=dict)
    speed_persistence: float = 0.7
    heading_persistence: float = 0.7
    recurvature_latitude: float = 20.0
    recurvature_bias_deg_per_step: float = 5.0


# ===========================================================================
# Intensity transition — spec eqs. (8) and (9)
# ===========================================================================


@dataclass
class IntensityParams:
    """Wind intensity transition parameters.

    Over water (spec eq. 8): V_t ~ N(V_{t-1} + drift * dt, sigma^2 * dt)
    Over land (spec eq. 9):  V_t = V_{t-1} * exp(-k_land * dt)

    Attributes:
        drift_ms_per_hour: mean change in V_max per hour over water (m/s/h)
        sigma_ms_per_hour: stddev of the over-water innovation (m/s/sqrt(h))
        k_land_per_hour: exponential land-decay rate (1/h)
    """
    drift_ms_per_hour: float = 0.0
    sigma_ms_per_hour: float = 1.0
    k_land_per_hour: float = 0.15


# ===========================================================================
# Size transition — spec eq. (10)
# ===========================================================================


@dataclass
class SizeParams:
    """Storm size transition — R_max and R_outer evolve coupled to V_max.

    R_max and R_outer are modelled in log-space with mean reversion toward a
    V-conditional climatological mean:
        log(R_max_target)   = r_max_intercept   + r_max_v_coef   * log(V_max)
        log(R_outer_target) = r_outer_intercept + r_outer_v_coef * log(V_max)
        log(R_t) <- log(R_{t-1}) + rate * (log(R_target) - log(R_{t-1})) + N(0, sigma^2)

    The transition layer enforces the invariant R_max < R_outer.

    Attributes:
        r_max_intercept_log_km: intercept of log(R_max) regression on log(V_max)
        r_max_v_coef: slope of log(R_max) on log(V_max) (typically slightly negative)
        r_max_sigma_log: multiplicative noise stddev in log-space
        r_outer_intercept_log_km: intercept of log(R_outer) on log(V_max)
        r_outer_v_coef: slope of log(R_outer) on log(V_max) (typically positive)
        r_outer_sigma_log: multiplicative noise stddev in log-space
        mean_reversion_rate: per-hour pull toward the V-conditional mean (0..1)
        r_outer_invariant_buffer: when a noisy draw violates R_max < R_outer,
            R_outer is widened to r_outer_invariant_buffer * R_max. Buffer
            > 1.0 keeps the geometry distinct without compressing the tail.
    """
    r_max_intercept_log_km: float = 3.0
    r_max_v_coef: float = -0.1
    r_max_sigma_log: float = 0.1
    r_outer_intercept_log_km: float = 4.5
    r_outer_v_coef: float = 0.3
    r_outer_sigma_log: float = 0.08
    mean_reversion_rate: float = 0.2
    r_outer_invariant_buffer: float = 1.5
