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

"""Calibrate every gauge in a catchment and persist the result (MKM-EF-001).

Reads the gauge daily records through the ``database`` seam, extracts a
declustered arrival rate per gauge, and writes the fitted rates back through
the same seam. No file path appears anywhere in this module (rule R6).

The provenance class is **not** a parameter with a default. On a synthetic
catchment the gauge record is generated from an assumed flood frequency, so a
rate extracted from it recovers the generator's own input and carries no
observational content. Defaulting that to ``observed`` would launder an
assumption into evidence, so the caller has to say which it is.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from config.frequency import (
    MODEL_ID,
    MODEL_VERSION,
    SOURCE_DATASET_GAUGE_DAILY,
    FrequencyConfig,
    config_hash,
    load_frequency_config,
)

from .calibrate import calibrate_gauge_rate
from .datastructures import ProvenanceClass, rate_to_dict

# Key under which the daily observations sit in a gauge history record.
OBSERVATIONS_KEY = "daily_observations"

# Observation field carrying the water level.
LEVEL_KEY = "level_meters"


def calibrate_catchment(
    catchment: str,
    provenance_class: ProvenanceClass,
    config: Optional[FrequencyConfig] = None,
    source_version: str = "",
    fitted_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Calibrate every gauge in *catchment* and return the rate document.

    Args:
        catchment: catchment identifier.
        provenance_class: what the gauge records are. Synthetic catchments must
            pass ``GENERATOR_DERIVED``; see the module docstring.
        config: frequency configuration; defaults to the catchment's own.
        source_version: version or revision of the gauge dataset.
        fitted_at: ISO timestamp to stamp; defaults to the current UTC time.

    Returns:
        A document of ``{"metadata": {...}, "rates": {gauge_id: {...}}}``.
        Gauges whose record cannot be read are skipped and counted in the
        metadata rather than aborting the run.
    """
    import database

    settings = config if config is not None else load_frequency_config(catchment)
    stamp = fitted_at or datetime.now(timezone.utc).isoformat()

    rates: Dict[str, Any] = {}
    skipped = []
    for gauge_id in database.iter_gauge_history_ids(catchment):
        try:
            history = database.get_gauge_history(catchment, gauge_id)
            observations = (history or {}).get(OBSERVATIONS_KEY) or []
        except (OSError, ValueError, KeyError):
            skipped.append(gauge_id)
            continue
        if not observations:
            skipped.append(gauge_id)
            continue

        rate = calibrate_gauge_rate(
            gauge_id=gauge_id,
            observations=observations,
            value_key=LEVEL_KEY,
            config=settings,
            provenance_class=provenance_class,
            source_dataset=SOURCE_DATASET_GAUGE_DAILY,
            source_version=source_version,
            fitted_at=stamp,
        )
        rates[gauge_id] = rate_to_dict(rate)

    return {
        "metadata": {
            "catchment_id": catchment,
            "model_id": MODEL_ID,
            "model_version": MODEL_VERSION,
            "config_hash": config_hash(settings),
            "provenance_class": provenance_class.value,
            "generated_at": stamp,
            "num_gauges": len(rates),
            "num_skipped": len(skipped),
            "skipped_gauges": skipped,
        },
        "rates": rates,
    }


def calibrate_and_save(
    catchment: str,
    provenance_class: ProvenanceClass,
    config: Optional[FrequencyConfig] = None,
    source_version: str = "",
    fitted_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Calibrate a catchment and persist the result through the seam.

    Args:
        catchment: catchment identifier.
        provenance_class: what the gauge records are.
        config: frequency configuration; defaults to the catchment's own.
        source_version: version or revision of the gauge dataset.
        fitted_at: ISO timestamp to stamp; defaults to the current UTC time.

    Returns:
        The document that was written.
    """
    import database

    document = calibrate_catchment(
        catchment, provenance_class, config, source_version, fitted_at)
    database.save_frequency_rates(catchment, document)
    return document
