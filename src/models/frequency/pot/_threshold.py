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

"""Threshold selection for peaks-over-threshold extraction (MKM-EF-001).

The threshold is chosen to deliver a target mean number of independent peaks
per year rather than being fixed at a level. A rate target is what makes the
extraction comparable across gauges whose levels are on different datums.

The search is a linear scan over candidate quantiles. The achieved rate is not
strictly monotone in the threshold once declustering is applied — raising the
threshold can split one long cluster into two shorter ones — so a bisection
would not be safe, and the scan is cheap at daily resolution.
"""

from typing import List, Sequence, Tuple

from config.frequency import PotConfig

from ..datastructures import Peak
from ._decluster import decluster


def quantile(sorted_values: Sequence[float], fraction: float) -> float:
    """Return the value at *fraction* through *sorted_values*.

    Uses nearest-rank rather than interpolation: the result is always an
    observed value, which keeps candidate thresholds on the empirical support
    of the record.

    Args:
        sorted_values: values in ascending order; must not be empty.
        fraction: position in ``[0, 1]``.

    Returns:
        The value at that position.
    """
    index = int(fraction * (len(sorted_values) - 1))
    return sorted_values[max(0, min(index, len(sorted_values) - 1))]


def candidate_thresholds(values: Sequence[float], config: PotConfig) -> List[float]:
    """Build the list of candidate thresholds to search.

    Args:
        values: every observation in the record.
        config: extraction knobs supplying the quantile bounds and step count.

    Returns:
        Ascending, de-duplicated candidate thresholds. Empty if *values* is
        empty.
    """
    if not values:
        return []

    ordered = sorted(values)
    span = config.search_quantile_hi - config.search_quantile_lo
    steps = max(1, config.search_steps)

    seen = []
    for step in range(steps + 1):
        fraction = config.search_quantile_lo + span * step / steps
        candidate = quantile(ordered, fraction)
        if not seen or candidate > seen[-1]:
            seen.append(candidate)
    return seen


def rate_at_threshold(
    observations: Sequence[Peak],
    threshold: float,
    record_years: float,
    window_days: int,
) -> Tuple[float, int]:
    """Compute the declustered exceedance rate at one candidate threshold.

    Args:
        observations: the whole record, in chronological order.
        threshold: the candidate threshold.
        record_years: length of the record in years; must be positive.
        window_days: declustering separation.

    Returns:
        ``(peaks_per_year, n_peaks)``.
    """
    exceedances = [o for o in observations if o.value >= threshold]
    n_peaks = len(decluster(exceedances, window_days))
    return n_peaks / record_years, n_peaks


def select_threshold(
    observations: Sequence[Peak],
    record_years: float,
    config: PotConfig,
) -> Tuple[float, float, bool]:
    """Choose the threshold whose declustered rate is closest to the target.

    Args:
        observations: the whole record, in chronological order.
        record_years: length of the record in years; must be positive.
        config: extraction knobs supplying the target rate and tolerance.

    Returns:
        ``(threshold, achieved_rate_per_year, converged)``. ``converged`` is
        True when the achieved rate is within the configured tolerance of the
        target. For an empty record the threshold is ``0.0``, the rate ``0.0``
        and ``converged`` False.
    """
    candidates = candidate_thresholds([o.value for o in observations], config)
    if not candidates:
        return 0.0, 0.0, False

    best_threshold = candidates[0]
    best_rate = 0.0
    best_error = None

    for candidate in candidates:
        rate, _ = rate_at_threshold(
            observations, candidate, record_years, config.declustering_window_days)
        error = abs(rate - config.target_exceedance_rate_per_year)
        if best_error is None or error < best_error:
            best_threshold, best_rate, best_error = candidate, rate, error

    converged = best_error <= config.target_rate_tolerance
    return best_threshold, best_rate, converged
