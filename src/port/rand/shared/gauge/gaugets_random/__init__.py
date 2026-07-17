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
Thames-specific gauge time series random value generators.

Random value generation logic for Thames catchment flood gauge time series
simulations: water-level simulation (_levels) + reading/series generation
(_readings).
"""

from ._levels import DEFAULT_PARAMS, calculate_water_level, determine_alert_status
from ._readings import (
    generate_gauge_reading,
    generate_timestep_readings,
    generate_flood_simulation,
    generate_time_series,
)

__all__ = [
    "DEFAULT_PARAMS",
    "calculate_water_level",
    "determine_alert_status",
    "generate_gauge_reading",
    "generate_timestep_readings",
    "generate_flood_simulation",
    "generate_time_series",
]
