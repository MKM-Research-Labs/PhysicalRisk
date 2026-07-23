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

"""The raw result of a peaks-over-threshold extraction (MKM-EF-001).

Separated from ``PotDiagnostics``: this is what the extractor produced, the
diagnostics are what gets reported. The peaks themselves are retained so that
Stage 2's severity cross-check can fit a distribution to their magnitudes
without re-running the extraction.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Peak:
    """One declustered flood peak.

    Attributes:
        date: the date of the peak, ISO ``YYYY-MM-DD``.
        value: the observed value at the peak.
    """

    date: str
    value: float


@dataclass(frozen=True)
class PotExtraction:
    """Everything a peaks-over-threshold pass produced from one record.

    Attributes:
        threshold: the level used to define an exceedance.
        peaks: the declustered peaks, in chronological order.
        annual_counts: peaks falling in each complete year-block of the record.
        record_start: first observation date, ISO ``YYYY-MM-DD``.
        record_end: last observation date, ISO ``YYYY-MM-DD``.
        record_years: length of the record in years, from the full span.
        achieved_rate_per_year: ``len(peaks) / record_years``.
        threshold_converged: whether the threshold search hit the configured
            target exceedance rate within tolerance.
    """

    threshold: float
    peaks: Tuple[Peak, ...]
    annual_counts: Tuple[int, ...]
    record_start: str
    record_end: str
    record_years: float
    achieved_rate_per_year: float
    threshold_converged: bool
