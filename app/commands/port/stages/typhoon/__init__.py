# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see ../auth.py for full license text)

"""Typhoon stage — boundary adapter between the active catchment's
typhoon configuration and the catchment-agnostic typhoon model.

This stage is the only file in the codebase that knows both:
  - how to discover a catchment's tc.py (the production config path)
  - how to call the typhoon pipeline (the model entry point)

It deliberately does no math: the catchment file constructs the
CatchmentTyphoonConfig via its build_typhoon_config() function, and the
pipeline runs the SMC engine + wind-field model end-to-end.
"""

from ._loaders import (
    _load_catchment_typhoon_config,
    _load_storm_event_drivers,
    _load_property_portfolio,
    _severity_quantiles,
)
from ._run import run_typhoon
from ._run_all import run_all

__all__ = [
    "run_all",
    "run_typhoon",
    "_load_catchment_typhoon_config",
    "_load_storm_event_drivers",
    "_load_property_portfolio",
    "_severity_quantiles",
]
