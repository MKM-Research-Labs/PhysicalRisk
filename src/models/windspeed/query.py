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

"""Wind-at-point query — the core (event, hour, lon, lat) -> V_max function
and the WindSpeedModel class that caches loaded events for repeated queries.
"""

from pathlib import Path
from typing import Dict, Optional, Union

from config.typhoon import CatchmentTyphoonConfig, LandMask, WindFieldParams
from models.typhoon.data_structures import TyphoonTrajectory
from models.typhoon.wind_field import evaluate_point
from models.windspeed.interpolation import interpolate_state_at_hour
from models.windspeed.loader import load_event


__all__ = ["windspeed", "WindSpeedModel"]


def windspeed(
    event: Union[Path, str, TyphoonTrajectory],
    hour: float,
    lon: float,
    lat: float,
    *,
    wind_field_params: WindFieldParams,
    land_mask: LandMask,
) -> float:
    """Return sustained wind speed (m/s) at the given point and hour.

    Args:
        event: a path to an EVT-*.json file, or an already-loaded trajectory
        hour: hour since the event's genesis; clamped to the trajectory range
        lon: longitude of the query point (degrees east)
        lat: latitude of the query point (degrees north)
        wind_field_params: wind-field calibration (from CatchmentTyphoonConfig)
        land_mask: callable (lon, lat) -> True if land at that point

    Returns:
        sustained wind speed at the point, m/s
    """
    trajectory = load_event(event)
    state = interpolate_state_at_hour(trajectory.states, hour)
    return evaluate_point(state, lon, lat, wind_field_params, land_mask)


class WindSpeedModel:
    """Reusable wind-at-point query model.

    Binds a CatchmentTyphoonConfig once and exposes a query interface that
    caches loaded events so repeated lookups against the same event don't
    re-parse JSON.

    Typical use:
        ws = WindSpeedModel(config)
        v = ws.query("data/halong/typhoon/events/EVT-0001.json",
                     hour=24.0, lon=105.85, lat=21.03)
    """

    def __init__(self, config: CatchmentTyphoonConfig):
        self.config = config
        self.wind_field_params: WindFieldParams = config.wind_field
        self.land_mask: LandMask = config.land_mask
        self._cache: Dict[str, TyphoonTrajectory] = {}

    def _resolve(self, event: Union[Path, str, TyphoonTrajectory]) -> TyphoonTrajectory:
        """Load and cache the event by its source key (path string or id)."""
        if isinstance(event, TyphoonTrajectory):
            return event
        key = str(event)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        trajectory = load_event(event)
        self._cache[key] = trajectory
        return trajectory

    def query(
        self,
        event: Union[Path, str, TyphoonTrajectory],
        hour: float,
        lon: float,
        lat: float,
    ) -> float:
        trajectory = self._resolve(event)
        state = interpolate_state_at_hour(trajectory.states, hour)
        return evaluate_point(state, lon, lat, self.wind_field_params, self.land_mask)

    def __call__(
        self,
        event: Union[Path, str, TyphoonTrajectory],
        hour: float,
        lon: float,
        lat: float,
    ) -> float:
        return self.query(event, hour, lon, lat)

    def clear_cache(self) -> None:
        """Drop all cached events."""
        self._cache.clear()

    @property
    def cached_event_keys(self) -> tuple:
        """Inspect what's currently cached (debugging / introspection)."""
        return tuple(self._cache.keys())
