# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Thames catchment package.

Re-exports location/geometry constants from ``config.py`` and storm
calibration constants from ``storm.py`` so callers can do either:

    from catch.thames import ThamesCatchment, GAUGE_POINTS
    from catch.thames import BASE_PRECIPITATION_MM, TRACK_START

or load the package via ``importlib.import_module('catch.thames')``.
"""

from .config import (
    ThamesCatchment,
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
    "ThamesCatchment",
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
