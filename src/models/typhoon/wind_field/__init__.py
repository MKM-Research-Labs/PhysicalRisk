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

The user-facing surface (re-exported below) is built in ``_core``; the
``WindField`` convenience class binds the config once.
"""

from ._core import (
    haversine_distance_km,
    bearing_deg,
    calibrate_outer_decay_length,
    symmetric_profile,
    asymmetry_factor,
    compute_epsilon,
    compute_phi_deg,
    surface_factor,
    PointWind,
    evaluate_point,
    evaluate_point_with_geometry,
    duration_above_threshold,
    evaluate_time_series,
    WindField,
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
