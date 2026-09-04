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

"""Thames-specific storm calibration.

Per-catchment knobs for the storm simulation: where storms originate
and end (synthetic track), how intense they are at peak (base
precipitation), and the relative frequency of each intensity category
within a batch.

Algorithm constants that don't vary by region (window length, sequence
probability curve, correlation factors, etc.) stay in ``config/port.py``.
"""

# Base precipitation (mm) at peak — scales storm intensity. Thames
# floodplain is calibrated against ~35 mm baseline rainfall.
BASE_PRECIPITATION_MM: float = 35.0

# Synthetic storm track for spatial storms (lon, lat). Thames storms
# track west-to-east across southern England, roughly along the 51.4°N
# parallel.
TRACK_START: tuple = (-2.6, 51.45)   # west of London (Wiltshire area)
TRACK_END:   tuple = (1.4,  51.38)   # Thames estuary / North Sea coast

# Probability weights for storm intensity category in batch generation.
# Thames-calibrated to Flood Re pricing (20–60 bps): heavy-tailed but
# centred on moderate/severe events, catastrophic rare.
INTENSITY_WEIGHTS: dict = {
    "moderate":     0.40,
    "severe":       0.35,
    "extreme":      0.20,
    "catastrophic": 0.05,
}

__all__ = [
    "BASE_PRECIPITATION_MM",
    "TRACK_START",
    "TRACK_END",
    "INTENSITY_WEIGHTS",
]
