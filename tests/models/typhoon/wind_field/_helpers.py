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

"""Shared helpers for the wind_field test package.

Geography is deliberately neutral — coordinates around (5, 5) lie inside
the test bbox in tests/models/typhoon/conftest.py. The leading underscore
tells the pytest collection hook to skip this file as a test module.
"""

from datetime import datetime
from typing import List

from config.typhoon import ScenarioFamily
from models.typhoon.data_structures import (
    RegimeClass,
    TyphoonState,
    TyphoonTrajectory,
)


# Canonical test geography — coordinates are inside the neutral test bbox
# (0, 0, 10, 10) defined in tests/models/typhoon/conftest.py.
DEFAULT_LON = 5.0
DEFAULT_LAT = 5.0


def make_state(
    lon: float = DEFAULT_LON,
    lat: float = DEFAULT_LAT,
    speed: float = 18.0,
    heading: float = 270.0,
    v: float = 40.0,
    r_max: float = 35.0,
    r_outer: float = 150.0,
    regime: RegimeClass = RegimeClass.STRAIGHT_WESTWARD,
    land: bool = False,
    t: float = 0.0,
) -> TyphoonState:
    """Build a TyphoonState with sensible defaults for wind-field tests."""
    return TyphoonState(
        longitude=lon,
        latitude=lat,
        translation_speed_kmh=speed,
        heading_deg=heading,
        v_max_ms=v,
        r_max_km=r_max,
        r_outer_km=r_outer,
        regime=regime,
        land_flag=land,
        time_hours=t,
    )


def synthetic_track(
    start_lon: float,
    start_lat: float,
    n_steps: int,
    dt_hours: float = 1.0,
    speed_kmh: float = 30.0,
    heading_deg: float = 90.0,
    v_max: float = 50.0,
    r_max_km: float = 30.0,
    r_outer_km: float = 150.0,
) -> TyphoonTrajectory:
    """Build a TyphoonTrajectory with a deterministic linear track.

    Bypasses the transition layer so the wind-field acceptance tests can
    work against a clean, predictable geometry. Position is advanced by
    `transitions.position.update_position` so the trajectory uses the same
    advection model the real simulator uses.
    """
    from models.typhoon.transitions.position import update_position

    states: List[TyphoonState] = []
    lon, lat = start_lon, start_lat
    states.append(make_state(
        lon=lon, lat=lat,
        speed=speed_kmh, heading=heading_deg,
        v=v_max, r_max=r_max_km, r_outer=r_outer_km,
        t=0.0,
    ))
    for i in range(1, n_steps + 1):
        prev = states[-1]
        new_lon, new_lat = update_position(prev, speed_kmh, heading_deg, dt_hours)
        states.append(make_state(
            lon=new_lon, lat=new_lat,
            speed=speed_kmh, heading=heading_deg,
            v=v_max, r_max=r_max_km, r_outer=r_outer_km,
            t=i * dt_hours,
        ))
    return TyphoonTrajectory(
        event_id="EVT-SYN",
        particle_id=0,
        scenario_family=ScenarioFamily.BASELINE,
        genesis_time=datetime(2026, 1, 1),
        states=states,
    )
