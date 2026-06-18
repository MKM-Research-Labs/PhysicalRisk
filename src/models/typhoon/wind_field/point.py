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

"""Single-point wind-field evaluation.

Composes the four blocks (geometry, radial profile, asymmetry, surface
reduction) into a single function evaluate_point() that returns the
sustained wind speed at a (lon, lat) for a given typhoon state.

The convenience tuple result evaluate_point_with_geometry() also returns
r and theta so callers (e.g. the time-series evaluator) can record
distance and azimuth at peak without recomputing.
"""

from typing import NamedTuple

from config.typhoon import LandMask, WindFieldParams
from models.typhoon.data_structures import TyphoonState
from models.typhoon.wind_field.asymmetry import (
    asymmetry_factor,
    compute_epsilon,
    compute_phi_deg,
)
from models.typhoon.wind_field.geometry import bearing_deg, haversine_distance_km
from models.typhoon.wind_field.radial import (
    calibrate_outer_decay_length,
    symmetric_profile,
)
from models.typhoon.wind_field.surface import surface_factor


__all__ = [
    "PointWind",
    "evaluate_point",
    "evaluate_point_with_geometry",
]


class PointWind(NamedTuple):
    """Wind-field evaluation result at a single point and time."""
    sustained_ms: float
    distance_km: float
    azimuth_deg: float


def evaluate_point_with_geometry(
    state: TyphoonState,
    point_lon: float,
    point_lat: float,
    params: WindFieldParams,
    land_mask: LandMask,
) -> PointWind:
    """Return sustained wind plus geometry (r, theta) at the point.

    Computation order matches the spec layer architecture:
        1. r = haversine(center, x)         (geometry)
        2. theta = bearing(center -> x)     (geometry)
        3. L = calibrate_outer_decay_length (radial calibration)
        4. V_sym = symmetric_profile(r)     (radial profile)
        5. eps, phi -> asymmetry factor      (asymmetry)
        6. rho = surface_factor(point)      (surface reduction)
        7. V_final = V_sym * asym * rho
    """
    r_km = haversine_distance_km(state.longitude, state.latitude, point_lon, point_lat)
    # Bearing is undefined at r=0; use 0 as a placeholder. Asymmetry at the
    # center contributes nothing anyway because cos(0) * V_sym(0) is just
    # alpha_eye * V_max scaled by (1 + eps * cos(...)), which collapses
    # cleanly under the cosine rule for any theta.
    theta_deg = bearing_deg(state.longitude, state.latitude, point_lon, point_lat) if r_km > 1e-9 else 0.0

    decay_length = calibrate_outer_decay_length(
        v_max_ms=state.v_max_ms,
        r_max_km=state.r_max_km,
        r_outer_km=state.r_outer_km,
        v_outer_ref_ms=params.v_outer_ref_ms,
        outer_shape_p=params.outer_shape_p,
    )
    v_sym = symmetric_profile(
        r_km=r_km,
        r_max_km=state.r_max_km,
        v_max_ms=state.v_max_ms,
        alpha_eye=params.alpha_eye,
        outer_decay_length_km=decay_length,
        outer_shape_p=params.outer_shape_p,
    )

    eps = compute_epsilon(
        translation_speed_kmh=state.translation_speed_kmh,
        v_max_ms=state.v_max_ms,
        eps_max=params.eps_max,
        c_eps=params.c_eps,
        eta_ms=params.eta_ms,
    )
    phi = compute_phi_deg(state.heading_deg, params.asymmetry_phase_offset_deg)
    asym = asymmetry_factor(theta_deg, phi, eps)

    rho = surface_factor(
        is_land=bool(land_mask(point_lon, point_lat)),
        rho_surf_sea=params.rho_surf_sea,
        rho_surf_land=params.rho_surf_land,
    )

    v_final = max(0.0, v_sym * asym * rho)
    return PointWind(sustained_ms=v_final, distance_km=r_km, azimuth_deg=theta_deg)


def evaluate_point(
    state: TyphoonState,
    point_lon: float,
    point_lat: float,
    params: WindFieldParams,
    land_mask: LandMask,
) -> float:
    """Return only the sustained wind (m/s); discards geometry."""
    return evaluate_point_with_geometry(state, point_lon, point_lat, params, land_mask).sustained_ms
