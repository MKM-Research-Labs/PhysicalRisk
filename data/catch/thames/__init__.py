# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Thames catchment package — re-exports constants and class from config.py
so callers can do ``from catch.thames import ThamesCatchment, GAUGE_POINTS``
or load via ``importlib.import_module('catch.thames')``.
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
    MAXSLOPEPERCENT,
    MAXRANDOMELEVATION,
)

__all__ = [
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
    "MAXSLOPEPERCENT",
    "MAXRANDOMELEVATION",
]
