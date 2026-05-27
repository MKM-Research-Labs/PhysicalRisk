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
Parameter dataclasses for the typhoon model.

These define the *shape* of the calibration knobs the model expects.
Each catchment provides concrete instances in its own config file under
data/catch/<id>/. The model imports nothing from data/catch/* — it only
sees these dataclasses.

CatchmentTyphoonConfig is the single object passed into the pipeline; it
aggregates every calibration input needed for a full simulation run.

All numeric defaults here are *neutral placeholders*. Real values are
provided by each catchment. The defaults exist so a parameter object can
be constructed in tests without supplying every field.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Tuple

from models.typhoon.data_structures import RegimeClass, ScenarioFamily


# A land mask is a callable taking (longitude, latitude) -> True if land.
# Catchments supply this; the model never embeds geometry.
LandMask = Callable[[float, float], bool]


# ===========================================================================
# Genesis prior — spec p.7-8
# ===========================================================================


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
    """
    r_max_intercept_log_km: float = 3.0
    r_max_v_coef: float = -0.1
    r_max_sigma_log: float = 0.1
    r_outer_intercept_log_km: float = 4.5
    r_outer_v_coef: float = 0.3
    r_outer_sigma_log: float = 0.08
    mean_reversion_rate: float = 0.2


# ===========================================================================
# Wind-field model — spec eqs. (22)-(29)
# ===========================================================================


@dataclass
class WindFieldParams:
    """Parametric radial wind-field parameters.

    Symmetric profile (spec eq. 23, piecewise):
        f_r(r) = alpha_eye + (1 - alpha_eye) * (r / R_max),          0 <= r < R_max
        f_r(r) = exp(-((r - R_max) / L)^p),                          r >= R_max

    L is determined by anchoring V_sym(R_outer) = v_outer_ref_ms (spec eq. 25).

    Asymmetry correction (spec eqs. 26-28):
        V(r, theta) = V_sym(r) * (1 + eps * cos(theta - phi))
        eps         = min(eps_max, c_eps * u / (V_max + eta))
        phi         = motion azimuth + asymmetry_phase_offset_deg

    Surface reduction (spec eq. 29):
        V_surf = rho_surf * V       where rho_surf depends on land/sea at the point.

    Attributes:
        alpha_eye: inner-core floor ratio — V at center equals alpha_eye * V_max
        outer_shape_p: exponent p of the outer decay envelope
        v_outer_ref_ms: anchor wind speed at R_outer used to calibrate L (typically gale-force)
        eps_max: cap on asymmetry strength
        c_eps: scaling coefficient relating translation speed to asymmetry
        eta_ms: stabilizing constant preventing division-by-zero at low V_max
        asymmetry_phase_offset_deg: azimuthal offset of peak asymmetry from motion direction
            (Northern Hemisphere convention: ~+90 deg places the peak to the right of motion)
        rho_surf_sea: surface reduction factor over sea (typically 1.0)
        rho_surf_land: surface reduction factor over land (typically < 1.0)
    """
    alpha_eye: float = 0.4
    outer_shape_p: float = 1.5
    v_outer_ref_ms: float = 17.5
    eps_max: float = 0.3
    c_eps: float = 0.6
    eta_ms: float = 1.0
    asymmetry_phase_offset_deg: float = 90.0
    rho_surf_sea: float = 1.0
    rho_surf_land: float = 0.8


# ===========================================================================
# Plausibility — spec p.6 (simulation-mode soft constraints)
# ===========================================================================


@dataclass
class PlausibilityWeights:
    """Soft-constraint weights for simulation-mode likelihood.

    Each component returns a multiplier in (0, 1]; the composite plausibility
    score is the product. Higher weights tighten the constraint. Phase 1
    defaults are deliberately loose so the posterior preserves breadth (which
    is the Phase 1 priority); calibration tightens them later.

    Attributes:
        heading_jump_weight: penalty strength on |delta psi|
        speed_jump_weight: penalty strength on |delta u|
        basin_boundary_weight: penalty strength on track leaving the basin bbox
        regime_consistency_weight: penalty strength on regime-incompatible behaviour
        heading_jump_sigma_deg: Gaussian scale for the heading-jump penalty (deg)
        speed_jump_sigma_kmh: Gaussian scale for the speed-jump penalty (km/h)
    """
    heading_jump_weight: float = 0.1
    speed_jump_weight: float = 0.1
    basin_boundary_weight: float = 0.1
    regime_consistency_weight: float = 0.1
    heading_jump_sigma_deg: float = 30.0
    speed_jump_sigma_kmh: float = 10.0


# ===========================================================================
# Property points — wind-field evaluation locations
# ===========================================================================


@dataclass
class PropertyPoint:
    """A location at which the wind-field is evaluated.

    Catchments supply these as the points where peak-wind distributions are
    reported.

    Attributes:
        property_id: stable identifier
        longitude: degrees east
        latitude: degrees north
    """
    property_id: str
    longitude: float
    latitude: float


# ===========================================================================
# Aggregate config — the single object passed into the pipeline
# ===========================================================================


@dataclass
class CatchmentTyphoonConfig:
    """All catchment-specific inputs the typhoon model needs for one run.

    The boundary adapter (added in Phase 1.7) reads raw values from the
    active catchment's tropical-cyclone config file via the config package
    and assembles this object. The pipeline takes a single
    CatchmentTyphoonConfig — no other route in.

    Attributes:
        catchment_id: identifier of the active catchment
        genesis_prior: distribution over the initial state
        peak_wind: per-scenario-family peak-wind distribution params
        motion: motion transition parameters
        intensity: wind intensity transition parameters
        size: storm-size transition parameters
        wind_field: parametric wind-field parameters
        plausibility: simulation-mode plausibility weights
        land_mask: callable (lon, lat) -> True if land at that point
        property_points: locations at which the wind-field is evaluated
        output_thresholds_ms: wind thresholds (m/s) for duration-above output
        horizon_hours: simulation horizon (typically 168h — one week)
    """
    catchment_id: str
    genesis_prior: GenesisPrior
    peak_wind: Dict[ScenarioFamily, PeakWindParams]
    motion: MotionParams
    intensity: IntensityParams
    size: SizeParams
    wind_field: WindFieldParams
    plausibility: PlausibilityWeights
    land_mask: LandMask
    property_points: List[PropertyPoint] = field(default_factory=list)
    output_thresholds_ms: List[float] = field(default_factory=lambda: [17.5, 25.0, 33.0, 42.0, 50.0])
    horizon_hours: float = 168.0
