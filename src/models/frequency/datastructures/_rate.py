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

"""The fitted arrival rate produced by the Event Frequency Model (MKM-EF-001).

A ``FittedRate`` is the whole output of Stage 1: an annual event arrival rate
for one gauge and peril, the extraction that produced it, and the provenance
that says what it is based on.

Nothing in Stage 1 consumes it for pricing. The annualisation seam that will
multiply it into the hazard curve is Stage 3.
"""

from dataclasses import dataclass

from ._diagnostics import PotDiagnostics
from ._provenance import CalibrationProvenance


@dataclass(frozen=True)
class FittedRate:
    """An annual event arrival rate for one gauge and peril.

    Attributes:
        gauge_id: the gauge the rate belongs to.
        peril: the peril the rate counts arrivals for. The layer is generic;
            only ``flood`` is calibrated in this phase.
        threshold: the level above which an observation counts as an
            exceedance, in the units of the source observation field.
        lambda_per_year: the annual arrival rate of declustered events.
        n_events: declustered peaks found in the record.
        record_years: length of the record in years.
        diagnostics: the annual count series and its summary statistics.
        provenance: what this rate is based on and how it was produced.
    """

    gauge_id: str
    peril: str
    threshold: float
    lambda_per_year: float
    n_events: int
    record_years: float
    diagnostics: PotDiagnostics
    provenance: CalibrationProvenance

    def annual_rate(self) -> float:
        """Return the annual arrival rate.

        Named to match the interface the Stage 2 frequency families implement,
        so callers can treat a Stage 1 rate and a Stage 2 fitted family alike.

        Returns:
            Events per year.
        """
        return self.lambda_per_year
