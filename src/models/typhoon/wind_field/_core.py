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
Parametric wind-field forward model.

Converts the latent storm state produced by the Bayesian progression
engine into a local wind speed at any (lon, lat). Architecture:

    geometry.py    radial distance r(x,t) and bearing theta(x,t)
    radial.py      symmetric profile V_sym(r) + outer-decay calibration
    asymmetry.py   motion-linked asymmetry correction
    surface.py     land/sea surface reduction at the evaluation point
    point.py       composes the above into evaluate_point()
    time_series.py iterates over a trajectory to produce WindFieldOutput

The package re-exports the user-facing surface here:

    evaluate_point(state, lon, lat, params, land_mask) -> float
    evaluate_point_with_geometry(...) -> PointWind(sustained, distance, azimuth)
    evaluate_time_series(traj, property, params, land_mask, thresholds)
        -> WindFieldOutput
    WindField(config) — convenience class binding the config once

Holland-style profile is reserved for a later phase; the symmetric
profile lives in radial.py and can be replaced without touching the
calling sites.
"""

from typing import Iterable, Optional

from config.typhoon import CatchmentTyphoonConfig, PropertyPoint
from models.typhoon.data_structures import TyphoonState, TyphoonTrajectory, WindFieldOutput
from models.typhoon.wind_field.asymmetry import (
    asymmetry_factor,
    compute_epsilon,
    compute_phi_deg,
)
from models.typhoon.wind_field.geometry import bearing_deg, haversine_distance_km
from models.typhoon.wind_field.point import (
    PointWind,
    evaluate_point,
    evaluate_point_with_geometry,
)
from models.typhoon.wind_field.radial import (
    calibrate_outer_decay_length,
    symmetric_profile,
)
from models.typhoon.wind_field.surface import surface_factor
from models.typhoon.wind_field.time_series import (
    duration_above_threshold,
    evaluate_time_series,
)


__all__ = [
    # geometry
    "haversine_distance_km",
    "bearing_deg",
    # radial profile
    "calibrate_outer_decay_length",
    "symmetric_profile",
    # asymmetry
    "asymmetry_factor",
    "compute_epsilon",
    "compute_phi_deg",
    # surface reduction
    "surface_factor",
    # point evaluation
    "PointWind",
    "evaluate_point",
    "evaluate_point_with_geometry",
    # trajectory evaluation
    "duration_above_threshold",
    "evaluate_time_series",
    # convenience class
    "WindField",
]


class WindField:
    """Convenience wrapper binding a CatchmentTyphoonConfig.

    Holds references to the wind-field parameters and the catchment's
    land mask so callers can repeatedly evaluate without re-passing the
    same arguments. The pipeline (Phase 1.7) constructs one of these
    per catchment and reuses it across all events and properties.
    """

    def __init__(self, config: CatchmentTyphoonConfig):
        self.config = config
        self.params = config.wind_field
        self.land_mask = config.land_mask
        self.thresholds_ms = config.output_thresholds_ms

    def evaluate(
        self,
        state: TyphoonState,
        longitude: float,
        latitude: float,
    ) -> float:
        return evaluate_point(state, longitude, latitude, self.params, self.land_mask)

    def evaluate_property(
        self,
        state: TyphoonState,
        property_point: PropertyPoint,
    ) -> float:
        return self.evaluate(state, property_point.longitude, property_point.latitude)

    def evaluate_trajectory(
        self,
        trajectory: TyphoonTrajectory,
        property_point: PropertyPoint,
        thresholds_ms: Optional[Iterable[float]] = None,
    ) -> WindFieldOutput:
        return evaluate_time_series(
            trajectory=trajectory,
            property_point=property_point,
            params=self.params,
            land_mask=self.land_mask,
            thresholds_ms=thresholds_ms if thresholds_ms is not None else self.thresholds_ms,
        )
