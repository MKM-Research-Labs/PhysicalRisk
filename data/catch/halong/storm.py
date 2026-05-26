# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Halong / Hanoi-specific storm calibration.

Per-catchment knobs for the storm simulation. **First-pass values
only** — needs proper recalibration against South China Sea typhoon
data (e.g. JMA RSMC Tokyo best-track archive) before any production
use.

Algorithm constants that don't vary by region (window length, sequence
probability curve, correlation factors, etc.) stay in ``config/port.py``.
"""

# Base precipitation (mm) at peak. Hanoi monsoon / typhoon-influenced;
# 24-hour rainfall totals of 100–300 mm are common during typhoon
# landfall. Placeholder anchored at the lower end pending calibration.
BASE_PRECIPITATION_MM: float = 100.0

# Synthetic storm track for spatial storms (lon, lat). Typhoons making
# landfall in northern Vietnam approach from the Gulf of Tonkin (east /
# south-east) and weaken westward over the Red River delta.
TRACK_START: tuple = (107.5, 21.03)   # Gulf of Tonkin
TRACK_END:   tuple = (104.5, 21.03)   # Lao border (storm dissipates inland)

# Probability weights for storm intensity category in batch generation.
# Tilted toward extreme / catastrophic relative to thames to reflect
# the typhoon regime; placeholder — recalibrate against actual return
# periods.
INTENSITY_WEIGHTS: dict = {
    "moderate":     0.25,
    "severe":       0.35,
    "extreme":      0.25,
    "catastrophic": 0.15,
}

__all__ = [
    "BASE_PRECIPITATION_MM",
    "TRACK_START",
    "TRACK_END",
    "INTENSITY_WEIGHTS",
]
