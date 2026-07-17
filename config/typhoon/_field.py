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

"""Wind-field, plausibility, filter, and property-point dataclasses."""

from dataclasses import dataclass


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
# Particle-filter algorithm parameters
# ===========================================================================


@dataclass
class FilterParams:
    """Hyperparameters for the Sequential Monte Carlo engine.

    Distinct from PlausibilityWeights (which tune the soft likelihood) —
    these are algorithm parameters of the particle filter itself.

    Attributes:
        ess_threshold_frac: resample when the effective sample size drops
            below ess_threshold_frac * N. Phase 1 default of 0.25 (loose)
            preserves trajectory breadth; calibration tightens it later.
    """
    ess_threshold_frac: float = 0.25


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
