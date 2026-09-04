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

"""Mekong catchment package — Phnom Penh, Cambodia (lower Mekong).

Re-exports location/geometry constants from ``config.py`` and storm
calibration constants from ``storm.py`` so callers can do either:

    from catch.mekong import MekongCatchment, GAUGE_POINTS
    from catch.mekong import BASE_PRECIPITATION_MM, TRACK_START

or load the package via ``importlib.import_module('catch.mekong')``.
Tropical-cyclone configuration lives in the sibling ``tc.py``.
"""

from .config import (
    MekongCatchment,
    GAUGE_POINTS,
    GAUGE_NAMES,
    AREAS,
    STREETS,
    AREA_VALUE_FACTORS,
    FLOOD_DECISION_BODIES,
    GAUGE_OWNERS,
    DATA_CURATORS,
    MORTGAGE_LENDERS,
    BOUNDS,
    CENTER_LAT,
    CENTER_LON,
    BASE_PROPERTY_VALUE,
    CURRENCY,
    MAXSLOPEPERCENT,
    MAXRANDOMELEVATION,
)
from .storm import (
    BASE_PRECIPITATION_MM,
    TRACK_START,
    TRACK_END,
    INTENSITY_WEIGHTS,
)

__all__ = [
    # config.py
    "MekongCatchment",
    "GAUGE_POINTS",
    "GAUGE_NAMES",
    "AREAS",
    "STREETS",
    "AREA_VALUE_FACTORS",
    "FLOOD_DECISION_BODIES",
    "GAUGE_OWNERS",
    "DATA_CURATORS",
    "MORTGAGE_LENDERS",
    "BOUNDS",
    "CENTER_LAT",
    "CENTER_LON",
    "BASE_PROPERTY_VALUE",
    "CURRENCY",
    "MAXSLOPEPERCENT",
    "MAXRANDOMELEVATION",
    # storm.py
    "BASE_PRECIPITATION_MM",
    "TRACK_START",
    "TRACK_END",
    "INTENSITY_WEIGHTS",
]
