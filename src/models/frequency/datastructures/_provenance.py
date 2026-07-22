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

"""Calibration provenance for the Event Frequency Model (MKM-EF-001).

Every fitted rate carries one of these. It answers, for an auditor, the
question a rate on its own cannot: *what is this number actually based on?*

The ``ProvenanceClass`` distinction is the point of the record. A rate
extracted from an observed gauge series and a rate recovered from a synthetic
series that was itself generated from an assumed frequency are both floats, and
they are not the same kind of evidence. See
``docs/storm_freq/frequency_layer_definition_and_plan_v2.md`` §5.
"""

from dataclasses import dataclass
from enum import Enum


class ProvenanceClass(str, Enum):
    """What a fitted rate is based on.

    Attributes:
        OBSERVED: extracted from a real measured gauge record.
        GENERATOR_DERIVED: extracted from a synthetic record whose flood
            frequency was itself an input to the generator. The extraction is
            sound; the number carries no observational content.
        REGIONAL_FALLBACK: the gauge record was too short or too sparse to
            support its own estimate, so the configured regional rate was used.
    """

    OBSERVED = "observed"
    GENERATOR_DERIVED = "generator-derived"
    REGIONAL_FALLBACK = "regional-fallback"


@dataclass(frozen=True)
class CalibrationProvenance:
    """The recipe that produced a fitted rate.

    Attributes:
        provenance_class: what the rate is based on.
        source_dataset: identifier of the dataset the record came from.
        source_version: version or revision of that dataset.
        record_start: first date in the record, ISO ``YYYY-MM-DD``.
        record_end: last date in the record, ISO ``YYYY-MM-DD``.
        value_key: the observation field the record was read from.
        declustering_window_days: the independence rule applied.
        config_hash: content hash of the ``FrequencyConfig`` used.
        model_id: the model that produced the rate.
        model_version: that model's version.
        fitted_at: ISO-8601 timestamp of the calibration run.
        note: free-text qualifier, used to record why a fallback was taken.
    """

    provenance_class: ProvenanceClass
    source_dataset: str
    source_version: str
    record_start: str
    record_end: str
    value_key: str
    declustering_window_days: int
    config_hash: str
    model_id: str
    model_version: str
    fitted_at: str
    note: str = ""
