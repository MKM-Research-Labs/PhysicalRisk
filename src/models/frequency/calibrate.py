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

"""Calibration orchestration for the Event Frequency Model (MKM-EF-001).

Composes threshold selection, declustering and rate estimation into a single
fitted rate, and decides when a record is too thin to speak for itself.

Calibration is a pure function of (observations, config) with one deliberate
exception: the ``fitted_at`` stamp. Pass it explicitly to make a run
byte-reproducible, as the golden-master regression does.

Family selection between Poisson and Negative Binomial is Stage 2. Stage 1
reports the dispersion index but does not act on it.
"""

import statistics
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence

from config.frequency import (
    MODEL_ID,
    MODEL_VERSION,
    PERIL_FLOOD,
    FrequencyConfig,
    config_hash,
)

from .datastructures import (
    CalibrationProvenance,
    FittedRate,
    PotDiagnostics,
    PotExtraction,
    ProvenanceClass,
)
from .pot import extract_pot


def summarise(extraction: PotExtraction) -> PotDiagnostics:
    """Summarise an extraction's annual count series.

    Args:
        extraction: the raw extraction result.

    Returns:
        A ``PotDiagnostics``. Variance is zero when fewer than two year blocks
        are available, and the dispersion index is zero when the mean is zero —
        in both cases there is nothing to test, and reporting zero is clearer
        than reporting a NaN that would propagate into the calibration report.
    """
    counts = extraction.annual_counts
    mean_count = statistics.fmean(counts) if counts else 0.0
    variance_count = statistics.variance(counts) if len(counts) > 1 else 0.0
    dispersion = variance_count / mean_count if mean_count > 0 else 0.0

    return PotDiagnostics(
        annual_counts=counts,
        mean_count=mean_count,
        variance_count=variance_count,
        dispersion_index=dispersion,
        threshold_converged=extraction.threshold_converged,
        achieved_rate_per_year=extraction.achieved_rate_per_year,
    )


def fallback_reason(
    extraction: PotExtraction,
    config: FrequencyConfig,
) -> str:
    """Return why the regional fallback rate applies, or an empty string.

    Args:
        extraction: the raw extraction result.
        config: the frequency configuration supplying the minima.

    Returns:
        A human-readable reason, or ``""`` when the record supports its own
        rate.
    """
    if extraction.record_years < config.rate.min_record_years:
        return (
            f"record of {extraction.record_years:.1f}y is shorter than the "
            f"{config.rate.min_record_years:.1f}y minimum"
        )
    if len(extraction.peaks) < config.rate.min_events_for_rate:
        return (
            f"{len(extraction.peaks)} declustered peaks is fewer than the "
            f"{config.rate.min_events_for_rate} required"
        )
    return ""


def calibrate_gauge_rate(
    gauge_id: str,
    observations: Sequence[Dict[str, Any]],
    value_key: str,
    config: FrequencyConfig,
    provenance_class: ProvenanceClass,
    source_dataset: str,
    source_version: str = "",
    peril: str = PERIL_FLOOD,
    fitted_at: Optional[str] = None,
) -> FittedRate:
    """Calibrate one gauge's annual event arrival rate.

    Args:
        gauge_id: the gauge being calibrated.
        observations: daily observation dicts with ``date`` and *value_key*.
        value_key: the observation field to read, e.g. ``level_meters``.
        config: the frequency configuration; its hash is recorded.
        provenance_class: what the source record is. Callers reading a
            synthetic series must pass ``GENERATOR_DERIVED`` — see
            ``docs/storm_freq/frequency_layer_definition_and_plan_v2.md`` §5.
            It is a required argument precisely so that it cannot be defaulted
            to ``OBSERVED`` by omission.
        source_dataset: identifier of the source dataset.
        source_version: version or revision of that dataset.
        peril: the peril whose arrivals are counted.
        fitted_at: ISO timestamp to stamp; defaults to the current UTC time.

    Returns:
        A ``FittedRate``. When the record is too short or too sparse the
        configured regional rate is used and the provenance class is
        overridden to ``REGIONAL_FALLBACK`` with the reason recorded.
    """
    extraction = extract_pot(observations, value_key, config.pot)
    reason = fallback_reason(extraction, config)

    if reason:
        lambda_per_year = config.rate.regional_fallback_lambda_per_year
        recorded_class = ProvenanceClass.REGIONAL_FALLBACK
    else:
        lambda_per_year = len(extraction.peaks) / extraction.record_years
        recorded_class = provenance_class

    provenance = CalibrationProvenance(
        provenance_class=recorded_class,
        source_dataset=source_dataset,
        source_version=source_version,
        record_start=extraction.record_start,
        record_end=extraction.record_end,
        value_key=value_key,
        declustering_window_days=config.pot.declustering_window_days,
        config_hash=config_hash(config),
        model_id=MODEL_ID,
        model_version=MODEL_VERSION,
        fitted_at=fitted_at or datetime.now(timezone.utc).isoformat(),
        note=reason,
    )

    return FittedRate(
        gauge_id=gauge_id,
        peril=peril,
        threshold=extraction.threshold,
        lambda_per_year=lambda_per_year,
        n_events=len(extraction.peaks),
        record_years=extraction.record_years,
        diagnostics=summarise(extraction),
        provenance=provenance,
    )
