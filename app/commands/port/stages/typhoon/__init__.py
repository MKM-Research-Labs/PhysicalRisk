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
