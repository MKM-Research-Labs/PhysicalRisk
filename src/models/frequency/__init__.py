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

"""Event Frequency Model — MKM-EF-001.

Supplies the time dimension the flood chain is missing. The platform simulates
storms and asks whether each one floods a gauge; that conditional says nothing
about how often such an event arrives, so two gauges with equal conditional
probability price identically however differently exposed they are.

The unit that carries the rate is the **event**, not the storm. A storm
sequence of one to five storms inside the 168-hour insurance hours clause is a
single event, so the nesting is:

    storm  ->  event (hours clause)  ->  year  ->  tenor

This package estimates the arrival rate of events per year. The annualisation
that multiplies it into the hazard curve is Stage 3, and the multi-year leg
then follows from the Poisson compounding already in
``models.hazard.gev.compute_term_structure``.

Stage 1 scope: peaks-over-threshold extraction with declustering, arrival-rate
estimation, and provenance. Distribution families and their selection are
Stage 2; nothing here is consumed for pricing yet.

Per rule R4 this module contains no function definitions — only re-exports.
"""

from .annualise import (
    annual_exceedance_probability,
    annual_exceedance_rate,
    return_period_years,
)
from .calibrate import calibrate_gauge_rate, fallback_reason, summarise
from .datastructures import (
    CalibrationProvenance,
    EventCatalogue,
    EventFrame,
    FittedRate,
    Peak,
    PotDiagnostics,
    PotExtraction,
    ProvenanceClass,
    rate_from_dict,
    rate_to_dict,
)
from .events import build_catalogue, build_event_frame
from .families import FamilySelection, dispersion_test, select_family
from .persist import calibrate_and_save, calibrate_catchment
from .pot import ExceedanceRate, exceedance_rate

__all__ = [
    "annual_exceedance_probability",
    "annual_exceedance_rate",
    "return_period_years",
    "calibrate_catchment",
    "calibrate_and_save",
    "exceedance_rate",
    "ExceedanceRate",
    "select_family",
    "dispersion_test",
    "FamilySelection",
    "build_catalogue",
    "build_event_frame",
    "EventCatalogue",
    "EventFrame",
    "calibrate_gauge_rate",
    "summarise",
    "fallback_reason",
    "FittedRate",
    "PotDiagnostics",
    "PotExtraction",
    "Peak",
    "CalibrationProvenance",
    "ProvenanceClass",
    "rate_to_dict",
    "rate_from_dict",
]
