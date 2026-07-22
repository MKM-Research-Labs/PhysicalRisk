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

"""Extraction diagnostics for the Event Frequency Model (MKM-EF-001).

Carries the annual count series and the summary statistics computed from it.
The dispersion index is reported here but *not acted on* — family selection
between Poisson and Negative Binomial is Stage 2. Reporting it now means the
Stage 2 selector has nothing to recompute and the Stage 1 calibration report
can already show where overdispersion lives.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class PotDiagnostics:
    """Summary of the declustered annual count series.

    Attributes:
        annual_counts: declustered peak count for each whole year of record,
            in chronological order.
        mean_count: arithmetic mean of ``annual_counts``.
        variance_count: sample variance of ``annual_counts`` (zero when fewer
            than two years are available).
        dispersion_index: ``variance_count / mean_count``; approximately one
            supports a Poisson arrival process, materially above one indicates
            overdispersion. Zero when the mean is zero.
        threshold_converged: whether the threshold search reached the target
            exceedance rate within the configured tolerance.
        achieved_rate_per_year: the exceedance rate the selected threshold
            actually produced.
    """

    annual_counts: Tuple[int, ...]
    mean_count: float
    variance_count: float
    dispersion_index: float
    threshold_converged: bool
    achieved_rate_per_year: float
