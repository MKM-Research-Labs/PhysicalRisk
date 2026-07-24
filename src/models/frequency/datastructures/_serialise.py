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

"""Serialisation for fitted rates (MKM-EF-001).

A fitted rate is only useful to an auditor if it survives a round trip intact —
provenance included. These functions are the boundary between the typed objects
and the plain dictionaries the ``database`` seam persists.

The round trip is exact: ``from_dict(to_dict(rate)) == rate``. That is asserted
in the tests, because a provenance record that silently loses its class or its
config hash on the way to storage is worse than no provenance at all.
"""

from typing import Any, Dict

from ._diagnostics import PotDiagnostics
from ._provenance import CalibrationProvenance, ProvenanceClass
from ._rate import FittedRate


def rate_to_dict(rate: FittedRate) -> Dict[str, Any]:
    """Convert a fitted rate to a plain dictionary for persistence.

    Args:
        rate: the fitted rate.

    Returns:
        A JSON-serialisable dictionary.
    """
    return {
        "gauge_id": rate.gauge_id,
        "peril": rate.peril,
        "threshold": rate.threshold,
        "lambda_per_year": rate.lambda_per_year,
        "n_events": rate.n_events,
        "record_years": rate.record_years,
        "diagnostics": {
            "annual_counts": list(rate.diagnostics.annual_counts),
            "mean_count": rate.diagnostics.mean_count,
            "variance_count": rate.diagnostics.variance_count,
            "dispersion_index": rate.diagnostics.dispersion_index,
            "threshold_converged": rate.diagnostics.threshold_converged,
            "achieved_rate_per_year": rate.diagnostics.achieved_rate_per_year,
        },
        "provenance": {
            "provenance_class": rate.provenance.provenance_class.value,
            "source_dataset": rate.provenance.source_dataset,
            "source_version": rate.provenance.source_version,
            "record_start": rate.provenance.record_start,
            "record_end": rate.provenance.record_end,
            "value_key": rate.provenance.value_key,
            "declustering_window_days": rate.provenance.declustering_window_days,
            "config_hash": rate.provenance.config_hash,
            "model_id": rate.provenance.model_id,
            "model_version": rate.provenance.model_version,
            "fitted_at": rate.provenance.fitted_at,
            "note": rate.provenance.note,
        },
    }


def rate_from_dict(payload: Dict[str, Any]) -> FittedRate:
    """Rebuild a fitted rate from its persisted form.

    Args:
        payload: a dictionary produced by :func:`rate_to_dict`.

    Returns:
        The reconstructed ``FittedRate``.

    Raises:
        KeyError: if a required field is absent. Persisted provenance that
            cannot be read back in full is not provenance, so a partial record
            fails rather than being silently completed with defaults.
    """
    d = payload["diagnostics"]
    p = payload["provenance"]
    return FittedRate(
        gauge_id=payload["gauge_id"],
        peril=payload["peril"],
        threshold=payload["threshold"],
        lambda_per_year=payload["lambda_per_year"],
        n_events=payload["n_events"],
        record_years=payload["record_years"],
        diagnostics=PotDiagnostics(
            annual_counts=tuple(d["annual_counts"]),
            mean_count=d["mean_count"],
            variance_count=d["variance_count"],
            dispersion_index=d["dispersion_index"],
            threshold_converged=d["threshold_converged"],
            achieved_rate_per_year=d["achieved_rate_per_year"],
        ),
        provenance=CalibrationProvenance(
            provenance_class=ProvenanceClass(p["provenance_class"]),
            source_dataset=p["source_dataset"],
            source_version=p["source_version"],
            record_start=p["record_start"],
            record_end=p["record_end"],
            value_key=p["value_key"],
            declustering_window_days=p["declustering_window_days"],
            config_hash=p["config_hash"],
            model_id=p["model_id"],
            model_version=p["model_version"],
            fitted_at=p["fitted_at"],
            note=p.get("note", ""),
        ),
    )
