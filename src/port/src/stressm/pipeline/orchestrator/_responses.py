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

"""Per-sequence spatial compound gauge-response computation."""

import time

import numpy as np

from .._helpers import _extract_pulse_peaks


def compute_sequence_records(sequences, count, verbose, n_gauges, target_indices,
                             spatial_model, rng, alert_arr, warning_arr, severe_arr,
                             make_seasonal_params, make_precip_series,
                             compute_sequence_gauge_response):
    """Compute compound gauge responses for every sequence.

    Returns ``(sequence_records, alert_count, warning_count, severe_count)``.
    The seasonal-params builder and the storm_multi callables are passed in so
    this module avoids the heavy (lazy) storm_multi imports.
    """
    sequence_records = []
    alert_count = warning_count = severe_count = 0
    t2 = time.time()

    for i, seq in enumerate(sequences):
        if verbose and (i % 100 == 0) and i > 0:
            elapsed = time.time() - t2
            rate = i / elapsed
            eta = (count - i) / rate
            print(f"    [{i:,}/{count:,}]  {rate:.0f}/s  ETA {eta:.0f}s", flush=True)
        elif not verbose and (i % 2000 == 0) and i > 0:
            elapsed = time.time() - t2
            rate = i / elapsed
            eta = (count - i) / rate
            print(f"    [{i:,}/{count:,}]  ETA {eta / 60:.1f}m", flush=True)

        # Seasonal base levels: winter storms start from higher baseline
        seq_gauge_params = make_seasonal_params(seq)

        catchment_precip = make_precip_series(seq)
        gauge_precip_all = spatial_model.apply_to_sequence(seq, catchment_precip, rng=rng)

        peaks = np.empty(n_gauges)
        peak_hours = np.empty(n_gauges, dtype=int)
        pulse_peaks_per_gauge = []  # v2.2: per-pulse peaks per gauge

        for local_i, (gp, spatial_i) in enumerate(zip(seq_gauge_params, target_indices)):
            levels = compute_sequence_gauge_response(
                seq, gp, precip_series=gauge_precip_all[spatial_i]
            )
            pk_idx = int(np.argmax(levels))
            peaks[local_i] = levels[pk_idx]
            peak_hours[local_i] = pk_idx

            # v2.2: extract per-pulse peaks from the 168h hydrograph
            pp = _extract_pulse_peaks(levels, seq, lag=gp.response_lag_hours)
            pulse_peaks_per_gauge.append(pp)

        is_alert   = peaks >= alert_arr
        is_warning = peaks >= warning_arr
        is_severe  = peaks >= severe_arr

        if is_alert.any():
            alert_count += 1
        if is_warning.any():
            warning_count += 1
        if is_severe.any():
            severe_count += 1

        sequence_records.append({
            "sequence_id":        seq.sequence_id,
            "sequence_type":      seq.sequence_type,
            "intensity_category": seq.intensity_category,
            "num_storms":         len(seq.storms),
            "total_precip_mm":    round(seq.total_precipitation_mm, 1),
            "peaks_m":            [round(float(p), 3) for p in peaks],
            "peak_hours":         [int(h) for h in peak_hours],
            "alert":              [bool(v) for v in is_alert],
            "warning":            [bool(v) for v in is_warning],
            "severe":             [bool(v) for v in is_severe],
            "pulse_peaks":        pulse_peaks_per_gauge,
        })

    t3 = time.time()
    print(f"  Gauge responses computed in {(t3 - t2) / 60:.1f} min", flush=True)
    return sequence_records, alert_count, warning_count, severe_count
