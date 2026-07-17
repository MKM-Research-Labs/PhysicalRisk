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

"""
Configuration schema for the typhoon model.

Defines the *shape* of the calibration knobs the typhoon model expects:
parameter dataclasses for each transition block, the aggregate
CatchmentTyphoonConfig, and the regime / scenario-family enums.

Each catchment that wants typhoon simulation provides a tc.py under
data/catch/<id>/ that populates these dataclasses with concrete values.
The model layer (src/models/typhoon/) imports its runtime types from
here but never reads catchment-specific data.

All numeric defaults are *neutral placeholders*. Real values come from
the catchment's tc.py.
"""

from dataclasses import dataclass, field
from typing import Dict, List

from config.typhoon._enums import LandMask, RegimeClass, ScenarioFamily
from config.typhoon._transition import (
    GenesisPrior,
    IntensityParams,
    MotionParams,
    PeakWindParams,
    SizeParams,
)
from config.typhoon._field import (
    FilterParams,
    PlausibilityWeights,
    PropertyPoint,
    WindFieldParams,
)

__all__ = [
    "RegimeClass",
    "ScenarioFamily",
    "LandMask",
    "GenesisPrior",
    "PeakWindParams",
    "MotionParams",
    "IntensityParams",
    "SizeParams",
    "WindFieldParams",
    "PlausibilityWeights",
    "FilterParams",
    "PropertyPoint",
    "CatchmentTyphoonConfig",
]


@dataclass
class CatchmentTyphoonConfig:
    """All catchment-specific inputs the typhoon model needs for one run.

    The boundary adapter (added in Phase 1.7) reads raw values from the
    active catchment's tropical-cyclone config file (data/catch/<id>/tc.py)
    via the config package routing layer and assembles this object. The
    pipeline takes a single CatchmentTyphoonConfig — no other route in.

    Attributes:
        catchment_id: identifier of the active catchment
        genesis_prior: distribution over the initial state
        peak_wind: per-scenario-family peak-wind distribution params
        motion: motion transition parameters
        intensity: wind intensity transition parameters
        size: storm-size transition parameters
        wind_field: parametric wind-field parameters
        plausibility: simulation-mode plausibility weights
        filter: particle-filter algorithm parameters (ESS threshold, etc.)
        land_mask: callable (lon, lat) -> True if land at that point
        property_points: locations at which the wind-field is evaluated
        output_thresholds_ms: wind thresholds (m/s) for duration-above output
        horizon_hours: simulation horizon (typically 168h — one week)
    """
    catchment_id: str
    genesis_prior: GenesisPrior
    peak_wind: Dict[ScenarioFamily, PeakWindParams]
    motion: MotionParams
    intensity: IntensityParams
    size: SizeParams
    wind_field: WindFieldParams
    plausibility: PlausibilityWeights
    land_mask: LandMask
    filter: FilterParams = field(default_factory=FilterParams)
    property_points: List[PropertyPoint] = field(default_factory=list)
    output_thresholds_ms: List[float] = field(default_factory=lambda: [17.5, 25.0, 33.0, 42.0, 50.0])
    horizon_hours: float = 168.0
