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

"""
JSON serialization for Storm Generator v2.0 event sets.

Saves and loads StormSequence lists to/from disk.
Schema version: 2.0-multi-storm (spec Section 7.3).

Output files:
  storm_sequences.json  — full event set (~10-12 MB for 10K sequences)
  sequences_summary.json  — metadata only (~200 KB for 10K sequences)
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

import database
from ..core.data_structures import StormSequence

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "2.0-multi-storm"
SEQUENCES_FILENAME = "storm_sequences.json"
SUMMARY_FILENAME = "sequences_summary.json"


def save_sequences(sequences: List[StormSequence], catchment: Optional[str] = None) -> None:
    """Persist a list of StormSequence objects through the database seam.

    Args:
        sequences: List of StormSequence objects to save.
        catchment: Catchment to store under (defaults to ``database.active_catchment()``).
    """
    catchment = catchment or database.active_catchment()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "num_sequences": len(sequences),
        "sequences": [s.to_dict() for s in sequences],
    }

    database.save_storm_sequences(catchment, payload)
    logger.info("Saved %d sequences for catchment %s", len(sequences), catchment)


def load_sequences(catchment: Optional[str] = None) -> List[StormSequence]:
    """Load a list of StormSequence objects through the database seam.

    Args:
        catchment: Catchment to read from (defaults to ``database.active_catchment()``).

    Returns:
        List of reconstructed StormSequence objects.

    Raises:
        FileNotFoundError: If no storm-sequences document exists.
        ValueError: If the schema_version is unrecognised.
    """
    catchment = catchment or database.active_catchment()
    payload = database.get_storm_sequences(catchment)
    if payload is None:
        raise FileNotFoundError(f"Storm sequences not found for catchment {catchment}")

    version = payload.get("schema_version", "")
    if version != SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported schema_version '{version}'. "
            f"Expected '{SCHEMA_VERSION}'."
        )

    sequences = [StormSequence.from_dict(d) for d in payload.get("sequences", [])]
    logger.info("Loaded %d sequences for catchment %s", len(sequences), catchment)
    return sequences


def save_summary(sequences: List[StormSequence], catchment: Optional[str] = None) -> None:
    """Persist a lightweight summary (metadata only, no per-storm detail).

    Contains counts and aggregate statistics per sequence type and intensity
    category. Suitable for quick inspection without loading the full sequence set.

    Args:
        sequences: List of StormSequence objects.
        catchment: Catchment to store under (defaults to ``database.active_catchment()``).
    """
    catchment = catchment or database.active_catchment()

    # Aggregate by sequence type
    type_counts: dict = {}
    category_counts: dict = {}
    storm_count_dist: dict = {}

    for seq in sequences:
        stype = seq.sequence_type
        type_counts[stype] = type_counts.get(stype, 0) + 1
        storm_count_dist[seq.num_storms] = storm_count_dist.get(seq.num_storms, 0) + 1
        for storm in seq.storms:
            cat = storm.intensity_category
            category_counts[cat] = category_counts.get(cat, 0) + 1

    total = len(sequences)
    total_precip = [s.total_precipitation_mm for s in sequences]
    durations = [s.total_duration_hours for s in sequences]

    summary = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "num_sequences": total,
        "sequence_type_counts": type_counts,
        "sequence_type_fractions": {
            k: round(v / total, 4) for k, v in type_counts.items()
        },
        "storm_count_distribution": {
            str(k): v for k, v in sorted(storm_count_dist.items())
        },
        "intensity_category_counts": category_counts,
        "precipitation_mm": {
            "min": round(min(total_precip), 2) if total_precip else 0,
            "max": round(max(total_precip), 2) if total_precip else 0,
            "mean": round(sum(total_precip) / total, 2) if total else 0,
        },
        "duration_hours": {
            "min": round(min(durations), 2) if durations else 0,
            "max": round(max(durations), 2) if durations else 0,
            "mean": round(sum(durations) / total, 2) if total else 0,
        },
    }

    database.save_sequence_summary(catchment, summary)
    logger.info("Saved summary for %d sequences for catchment %s", total, catchment)
