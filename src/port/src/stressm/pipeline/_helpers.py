# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package root for full license text)

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
