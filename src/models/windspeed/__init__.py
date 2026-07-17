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
Wind-at-point query model — given a stored typhoon event, return the
sustained wind at any (hour, longitude, latitude).

Submodules:
    interpolation.py  linear state interpolation at arbitrary hour
    loader.py         EVT-*.json -> TyphoonTrajectory
    query.py          windspeed() function + WindSpeedModel class (with cache)
    timeseries.py     windspeed_series() — convenience for multi-hour queries

Catchment-agnostic — the model consumes WindFieldParams + a land mask
(typically pulled from CatchmentTyphoonConfig.wind_field / .land_mask).
"""

from models.windspeed.interpolation import interpolate_state_at_hour
from models.windspeed.loader import load_event
from models.windspeed.query import WindSpeedModel, windspeed
from models.windspeed.timeseries import windspeed_series


__all__ = [
    "interpolate_state_at_hour",
    "load_event",
    "windspeed",
    "WindSpeedModel",
    "windspeed_series",
]
