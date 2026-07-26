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

"""Exporting an event loss table in a comparable shape (MKM-EF-001, Stage 6).

The ELT is the interchange format a catastrophe desk compares models in, so the
export carries the model identity and calibration alongside the rows: a table of
rates and losses with no provenance is not comparable, it is unattributable. The
document is plain JSON-serialisable primitives — no numpy scalars — so it crosses
the ``database`` seam and a third-party tool without special handling.
"""

from typing import Optional

from config.frequency import MODEL_ID, MODEL_VERSION

from ..datastructures import EventLossTable


def elt_document(
    table: EventLossTable,
    catchment: str,
    provenance_class: str,
    config_hash: Optional[str] = None,
) -> dict:
    """Return the event loss table as an attributed, serialisable document.

    Args:
        table: the assembled event loss table.
        catchment: the catchment the losses are for.
        provenance_class: how the underlying rate was obtained — the same
            ``ProvenanceClass`` value the fitted rate carries, passed as its
            string so a generator-derived table can never read as observed.
        config_hash: the frequency-config hash the losses were produced under,
            recorded so the table ties back to an exact calibration.

    Returns:
        A dict with a ``metadata`` block and an ``events`` list of ELT rows.
    """
    return {
        "metadata": {
            "model_id": MODEL_ID,
            "model_version": MODEL_VERSION,
            "catchment": catchment,
            "subject_id": table.subject_id,
            "provenance_class": provenance_class,
            "config_hash": config_hash,
            "lambda_effective": table.lambda_effective,
            "num_events": table.n_events,
            "average_annual_loss": table.average_annual_loss(),
        },
        "events": table.rows(),
    }
