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

"""Position advection — spec eqs. (6) and (7).

Equirectangular forward step on the surface of the Earth. Adequate for
tropical / sub-tropical hourly steps; the great-circle correction is
small at low latitudes and short distances. A future phase may swap in a
full geodesic destination formula if higher-latitude or longer-step use
cases arise.
"""

import math
from typing import Tuple

from models.typhoon.data_structures import TyphoonState


__all__ = [
    "EARTH_RADIUS_KM",
    "haversine_step",
    "update_position",
]


# Mean Earth radius used by the equirectangular advection step.
EARTH_RADIUS_KM: float = 6371.0


def haversine_step(
    longitude: float,
    latitude: float,
    east_km: float,
    north_km: float,
) -> Tuple[float, float]:
    """Advance (longitude, latitude) by (east_km, north_km) in equirectangular
    approximation.

    Longitude is wrapped to (-180, 180]. Latitude is clamped to [-90, 90]
    (a defensive guard — at typhoon-relevant latitudes the storm will never
    approach the poles, but Phase 1 trajectories must remain valid even
    under noisy regimes).
    """
    lat_rad = math.radians(latitude)
    # Avoid division by zero exactly at the pole; clamp the cosine floor.
    cos_lat = max(math.cos(lat_rad), 1e-6)

    d_lat_deg = math.degrees(north_km / EARTH_RADIUS_KM)
    d_lon_deg = math.degrees(east_km / (EARTH_RADIUS_KM * cos_lat))

    new_lat = max(-90.0, min(90.0, latitude + d_lat_deg))
    new_lon = longitude + d_lon_deg
    # Wrap longitude into (-180, 180].
    new_lon = ((new_lon + 180.0) % 360.0) - 180.0
    return new_lon, new_lat


def update_position(
    state: TyphoonState,
    speed_kmh: float,
    heading_deg: float,
    dt_hours: float = 1.0,
) -> Tuple[float, float]:
    """Advance position by (speed * dt) in the heading direction.

    Compass heading is converted to mathematical angle (East = 0, CCW positive)
    so that dx = u * dt * cos and dy = u * dt * sin describe (East, North)
    displacement in kilometres.
    """
    # Compass to math: math_angle = 90 - compass.
    math_rad = math.radians(90.0 - heading_deg)
    distance_km = speed_kmh * dt_hours
    east_km = distance_km * math.cos(math_rad)
    north_km = distance_km * math.sin(math_rad)
    return haversine_step(state.longitude, state.latitude, east_km, north_km)
