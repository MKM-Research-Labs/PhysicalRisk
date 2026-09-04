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

"""Mekong / Phnom Penh-specific storm calibration.

Per-catchment knobs for the storm simulation. **First-pass values only** —
the lower Mekong flood regime is dominated by the SW monsoon flood pulse and
the seasonal Tonlé Sap reversal, with weaker (remnant) tropical-cyclone
influence than coastal Vietnam. Recalibrate against MRC / MOWRAM gauge records
before any production use.

Algorithm constants that don't vary by region (window length, sequence
probability curve, correlation factors, etc.) stay in ``config/port.py``.

Tropical-cyclone-specific configuration lives in the sibling ``tc.py``.
"""

# Base precipitation (mm) at peak. Lower-Mekong monsoon; 24-hour totals of
# 80-200 mm occur during active monsoon surges. Placeholder anchored low.
BASE_PRECIPITATION_MM: float = 90.0

# Synthetic storm track for spatial storms (lon, lat). Systems reaching the
# lower Mekong approach from the south-east (Mekong delta / Gulf of Thailand
# side) and track north-west, weakening inland toward the Tonlé Sap.
TRACK_START: tuple = (106.0, 10.80)   # SE, lower Mekong delta
TRACK_END:   tuple = (104.2, 12.00)   # NW, inland toward Tonlé Sap

# Probability weights for storm intensity category in batch generation.
# Tilted toward moderate / severe — Cambodia generally sees weakened remnant
# systems rather than full-strength landfalls; placeholder, recalibrate.
INTENSITY_WEIGHTS: dict = {
    "moderate":     0.40,
    "severe":       0.35,
    "extreme":      0.18,
    "catastrophic": 0.07,
}

__all__ = [
    "BASE_PRECIPITATION_MM",
    "TRACK_START",
    "TRACK_END",
    "INTENSITY_WEIGHTS",
]
