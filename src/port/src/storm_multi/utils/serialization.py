# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from ..core.data_structures import StormSequence

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "2.0-multi-storm"
SEQUENCES_FILENAME = "storm_sequences.json"
SUMMARY_FILENAME = "sequences_summary.json"


def save_sequences(sequences: List[StormSequence], path: Path) -> None:
    """Serialise a list of StormSequence objects to JSON.

    Args:
        sequences: List of StormSequence objects to save.
        path: Output file path (e.g. .../storm_sequences.json).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "num_sequences": len(sequences),
        "sequences": [s.to_dict() for s in sequences],
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    logger.info("Saved %d sequences to %s", len(sequences), path)


def load_sequences(path: Path) -> List[StormSequence]:
    """Load a list of StormSequence objects from JSON.

    Args:
        path: Path to a file produced by save_sequences().

    Returns:
        List of reconstructed StormSequence objects.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the schema_version is unrecognised.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Sequences file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    version = payload.get("schema_version", "")
    if version != SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported schema_version '{version}'. "
            f"Expected '{SCHEMA_VERSION}'."
        )

    sequences = [StormSequence.from_dict(d) for d in payload.get("sequences", [])]
    logger.info("Loaded %d sequences from %s", len(sequences), path)
    return sequences


def save_summary(sequences: List[StormSequence], path: Path) -> None:
    """Save a lightweight summary JSON (metadata only, no per-storm detail).

    Contains counts and aggregate statistics per sequence type and intensity
    category. Suitable for quick inspection without loading the full file.

    Args:
        sequences: List of StormSequence objects.
        path: Output file path (e.g. .../sequences_summary.json).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

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

    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info("Saved summary for %d sequences to %s", total, path)
