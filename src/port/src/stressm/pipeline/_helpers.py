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

"""Pipeline helper utilities."""

import numpy as np


def _extract_pulse_peaks(levels: np.ndarray, seq, lag: int = 2) -> list:
    """Extract per-pulse peak levels from a 168h gauge hydrograph.

    For each storm in the sequence, finds the maximum level within the
    storm's active window (start -> start + duration + lag + 6h buffer).

    Returns a list of dicts, one per pulse, with keys:
        storm_index, peak_m, start_hour, duration_hours, precip_mm
    """
    n = len(levels)
    result = []
    for storm in seq.storms:
        start_h = max(0, int(round(storm.start_time_hours)))
        end_h = min(n, start_h + int(round(storm.duration_hours)) + lag + 6)
        if start_h >= end_h:
            continue
        window = levels[start_h:end_h]
        peak_m = float(np.max(window))
        result.append({
            "storm_index": storm.storm_index,
            "peak_m": round(peak_m, 3),
            "start_hour": round(storm.start_time_hours, 1),
            "duration_hours": round(storm.duration_hours, 1),
            "precip_mm": round(storm.precipitation_mm, 1),
        })
    return result
