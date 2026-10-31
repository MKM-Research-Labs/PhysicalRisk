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

"""Per-property aggregation of WindFieldOutput realizations.

Each realization (one particle * one event) contributes a single
WindFieldOutput per property. aggregate_property_winds rolls a list of
those outputs into a PropertyPeakWindSummary with empirical statistics.
"""

from typing import Dict, Iterable, List

import numpy as np

from config.typhoon import PropertyPoint
from models.typhoon.data_structures import WindFieldOutput
from models.typhoon.pipeline.results import PropertyPeakWindSummary


__all__ = ["aggregate_property_winds", "summarise_property_winds"]


def aggregate_property_winds(
    property_point: PropertyPoint,
    realizations: List[WindFieldOutput],
    thresholds_ms: Iterable[float],
) -> PropertyPeakWindSummary:
    """Aggregate a list of WindFieldOutput into a single PropertyPeakWindSummary.

    Args:
        property_point: identifier and coords of the property
        realizations: one WindFieldOutput per (event, particle) pair
        thresholds_ms: wind thresholds (m/s) for exceedance and duration stats

    Returns:
        PropertyPeakWindSummary with empirical mean / p50 / p95 / p99 of peak
        sustained wind, threshold-exceedance probabilities, and mean duration
        above each threshold.
    """
    thresholds = [float(t) for t in thresholds_ms]
    return summarise_property_winds(
        property_point=property_point,
        peaks=np.array([r.peak_sustained_ms for r in realizations], dtype=float),
        durations={
            t: np.array([r.duration_above_ms.get(t, 0.0) for r in realizations], dtype=float)
            for t in thresholds
        },
    )


def summarise_property_winds(
    property_point: PropertyPoint,
    peaks: np.ndarray,
    durations: Dict[float, np.ndarray],
) -> PropertyPeakWindSummary:
    """Summarise per-realization peaks and durations for one property.

    Takes plain arrays so a long ensemble need not keep every realization's
    wind time series in memory (10,000 events x 100 particles would need
    hundreds of GB).

    Args:
        property_point: identifier and coords of the property
        peaks: peak sustained wind (m/s), one value per realization
        durations: {threshold_ms: hours above threshold, one per realization}

    Returns:
        PropertyPeakWindSummary, as described in aggregate_property_winds.
    """
    n = len(peaks)
    if n == 0:
        return PropertyPeakWindSummary(
            property_id=property_point.property_id,
            longitude=property_point.longitude,
            latitude=property_point.latitude,
            n_realizations=0,
            peak_sustained_samples=[],
            peak_sustained_mean=0.0,
            peak_sustained_p50=0.0,
            peak_sustained_p95=0.0,
            peak_sustained_p99=0.0,
            threshold_exceedance={t: 0.0 for t in durations},
            mean_duration_above_ms={t: 0.0 for t in durations},
        )

    # A realization exceeded a threshold iff its duration above it is > 0.
    threshold_exceedance = {t: int((d > 0.0).sum()) / n for t, d in durations.items()}
    # Mean hours above the threshold, averaged across realizations (zeros for
    # realizations that never breached).
    mean_duration_above_ms = {t: float(d.mean()) for t, d in durations.items()}

    return PropertyPeakWindSummary(
        property_id=property_point.property_id,
        longitude=property_point.longitude,
        latitude=property_point.latitude,
        n_realizations=n,
        peak_sustained_samples=[float(p) for p in peaks],
        peak_sustained_mean=float(peaks.mean()),
        peak_sustained_p50=float(np.quantile(peaks, 0.50)),
        peak_sustained_p95=float(np.quantile(peaks, 0.95)),
        peak_sustained_p99=float(np.quantile(peaks, 0.99)),
        threshold_exceedance=threshold_exceedance,
        mean_duration_above_ms=mean_duration_above_ms,
    )
