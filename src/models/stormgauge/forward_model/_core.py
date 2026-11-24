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
Storm gauge forward model.

Computes gauge water level responses given storm parameters by mapping storm
characteristics (track, intensity, footprint) to a water-level timeseries at
each gauge location. Geometry/intensity and response simulation live in mixins.
"""

from config.models import (
    stormgauge_decay_hours,
    stormgauge_lag_hours,
    stormgauge_rise_hours,
    stormgauge_time_resolution_hours,
)

from ._intensity import _IntensityMixin
from ._response import _ResponseMixin


class StormGaugeModel(_IntensityMixin, _ResponseMixin):
    """
    Forward model: Storm parameters -> Gauge water level responses.

    The model computes water level at each gauge based on:
    1. The storm's position along its track at each step, and its distance from the gauge
    2. Storm intensity at that position
    3. Spatial decay based on distance and footprint
    4. Gauge-specific transfer function (intensity -> water level), lagged and smoothed

    Parameters (defaults from ``config.models``, Table 3 of the model document):
        time_resolution_hours: Time step for simulation
        response_lag_hours: Lag between storm passage and the gauge's target level
        response_rise_hours: Time constant of the rise towards a higher target
        response_decay_hours: Time constant of the fall towards a lower target
    """

    def __init__(
        self,
        time_resolution_hours: float = stormgauge_time_resolution_hours,
        response_lag_hours: float = stormgauge_lag_hours,
        response_rise_hours: float = stormgauge_rise_hours,
        response_decay_hours: float = stormgauge_decay_hours,
    ):
        self.time_resolution_hours = time_resolution_hours
        self.response_lag_hours = response_lag_hours
        self.response_rise_hours = response_rise_hours
        self.response_decay_hours = response_decay_hours
