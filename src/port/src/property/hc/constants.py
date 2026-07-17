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

"""Module-level constants for property hazard curve generation."""

from config.port import DEPTH_THRESHOLDS, MIN_EVENTS_FOR_GEV  # noqa: F401
from models.hazard.prs_analytical import (  # noqa: F401
    MIN_PRS_SPREAD_BPS,
    RECOVERY_RATES,
    compute_prs_spread,
)

# DEPTH_THRESHOLDS, MIN_EVENTS_FOR_GEV imported from config/port.py

# Tenors for term structure
TENORS = [1, 2, 3, 4, 5]

# Minimum annual probability derived from the 2bp spread floor (MIN_PRS_SPREAD_BPS).
# Previously derived from MAX_RETURN_PERIOD (a display parameter for gauge
# return period charts), which incorrectly imposed a 1% floor that capped
# all properties to 101bp and flattened the spread decomposition.
MIN_ANNUAL_PROBABILITY = MIN_PRS_SPREAD_BPS / 10_000  # 0.0002
