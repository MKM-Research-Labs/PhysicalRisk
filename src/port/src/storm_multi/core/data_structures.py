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
Storm Sequence data structures for v2.0 multi-storm generator.

Defines SequenceStorm (individual storm within a sequence) and
StormSequence (container of 1-5 related storms forming one event).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class SequenceType(Enum):
    """Type of multi-storm sequence."""
    ISOLATED = "isolated"
    DOUBLET = "doublet"
    CLUSTER = "cluster"
    PERSISTENT = "persistent"


class GapType(Enum):
    """Inter-storm gap duration category."""
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


# Sequence type definitions from spec Table 1
SEQUENCE_TYPE_STORM_COUNTS = {
    SequenceType.ISOLATED: (1, 1),
    SequenceType.DOUBLET: (2, 2),
    SequenceType.CLUSTER: (3, 4),
    SequenceType.PERSISTENT: (4, 5),
}

# Which gap type each sequence type uses
SEQUENCE_GAP_TYPE = {
    SequenceType.DOUBLET: GapType.MEDIUM,
    SequenceType.CLUSTER: GapType.MEDIUM,
    SequenceType.PERSISTENT: GapType.SHORT,
}


@dataclass
class SequenceStorm:
    """A single precipitation event within a multi-storm sequence.

    This is distinct from the existing StormScenario class which represents
    an independent storm with track/spatial fields. SequenceStorm is a
    lighter record focused on temporal placement and intensity within a
    parent StormSequence.
    """
    storm_id: str
    scenario_id: str            # Parent StormSequence ID
    storm_index: int            # 0-based position within sequence
    start_time_hours: float     # Offset from sequence start (hours)
    duration_hours: float
    intensity_category: str     # minimal..catastrophic
    intensity_factor: float
    precipitation_mm: float
    peak_position: float        # 0-1, where peak occurs within storm
    generated_at: str = ""
    catchment_id: str = ""

    def to_dict(self) -> Dict:
        return {
            "storm_id": self.storm_id,
            "scenario_id": self.scenario_id,
            "storm_index": self.storm_index,
            "start_time_hours": self.start_time_hours,
            "duration_hours": self.duration_hours,
            "intensity_category": self.intensity_category,
            "intensity_factor": round(self.intensity_factor, 6),
            "precipitation_mm": round(self.precipitation_mm, 2),
            "peak_position": round(self.peak_position, 4),
            "generated_at": self.generated_at,
            "catchment_id": self.catchment_id,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "SequenceStorm":
        return cls(**{k: d[k] for k in cls.__dataclass_fields__ if k in d})


@dataclass
class StormSequence:
    """A sequence of 1-5 related storm events treated as one flood event.

    Implements the insurance industry 'hours clause' — the entire sequence
    fits within a 168-hour (7-day) event window, with all precipitation
    ending by hour 156 to allow final drainage observation.
    """
    # Identity
    sequence_id: str
    sequence_type: str          # isolated, doublet, cluster, persistent

    # Temporal structure
    sequence_start: str         # ISO format
    total_duration_hours: float # Sum of storm durations + gaps
    intensity_category: str = ""  # moderate, severe, extreme, catastrophic
    event_window_hours: int = 168
    drainage_window_hours: float = 12.0

    # Storm composition
    storms: List[SequenceStorm] = field(default_factory=list)
    num_storms: int = 1
    inter_storm_gaps_hours: List[float] = field(default_factory=list)

    # Aggregate statistics
    total_precipitation_mm: float = 0.0
    max_intensity_factor: float = 0.0
    avg_intensity_factor: float = 0.0
    cumulative_intensity_factor: float = 0.0

    # Storm<->typhoon coupling (Stage 2 — joint event driver).
    # See docs/models/storm_typhoon_coupling/coupling_spec.md.
    #   event_id       — shared 1:1 storm<->typhoon key, e.g. "EVT-00001".
    #   base_intensity — severity latent z (the upstream Normal(mean_cat,std_cat)
    #                    draw); drives both precipitation and, in Stage 3, wind.
    #   seed           — per-event seed so the paired typhoon genesis is
    #                    reproducible independently of batch draw order.
    event_id: str = ""
    base_intensity: float = 0.0
    seed: int = 0

    # Antecedent conditions
    antecedent_soil_moisture: Optional[str] = "normal"
    antecedent_groundwater: Optional[str] = "normal"

    # Spatial correlation metadata
    spatial_correlation_enabled: bool = False
    spatial_correlation_range_km: Optional[float] = None

    # Metadata
    generated_at: str = ""
    catchment_id: str = ""

    def to_dict(self) -> Dict:
        return {
            "sequence_id": self.sequence_id,
            "sequence_type": self.sequence_type,
            "intensity_category": self.intensity_category,
            "sequence_start": self.sequence_start,
            "total_duration_hours": round(self.total_duration_hours, 2),
            "event_window_hours": self.event_window_hours,
            "drainage_window_hours": round(self.drainage_window_hours, 2),
            "storms": [s.to_dict() for s in self.storms],
            "num_storms": self.num_storms,
            "inter_storm_gaps_hours": [round(g, 2) for g in self.inter_storm_gaps_hours],
            "total_precipitation_mm": round(self.total_precipitation_mm, 2),
            "max_intensity_factor": round(self.max_intensity_factor, 6),
            "avg_intensity_factor": round(self.avg_intensity_factor, 6),
            "cumulative_intensity_factor": round(self.cumulative_intensity_factor, 6),
            "event_id": self.event_id,
            "base_intensity": round(self.base_intensity, 6),
            "seed": self.seed,
            "antecedent_soil_moisture": self.antecedent_soil_moisture,
            "antecedent_groundwater": self.antecedent_groundwater,
            "spatial_correlation_enabled": self.spatial_correlation_enabled,
            "spatial_correlation_range_km": self.spatial_correlation_range_km,
            "generated_at": self.generated_at,
            "catchment_id": self.catchment_id,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "StormSequence":
        storms = [SequenceStorm.from_dict(s) for s in d.get("storms", [])]
        return cls(
            sequence_id=d["sequence_id"],
            sequence_type=d["sequence_type"],
            intensity_category=d.get("intensity_category", ""),
            sequence_start=d.get("sequence_start", ""),
            total_duration_hours=d.get("total_duration_hours", 0),
            event_window_hours=d.get("event_window_hours", 168),
            drainage_window_hours=d.get("drainage_window_hours", 12.0),
            storms=storms,
            num_storms=d.get("num_storms", len(storms)),
            inter_storm_gaps_hours=d.get("inter_storm_gaps_hours", []),
            total_precipitation_mm=d.get("total_precipitation_mm", 0.0),
            max_intensity_factor=d.get("max_intensity_factor", 0.0),
            avg_intensity_factor=d.get("avg_intensity_factor", 0.0),
            cumulative_intensity_factor=d.get("cumulative_intensity_factor", 0.0),
            event_id=d.get("event_id", ""),
            base_intensity=d.get("base_intensity", 0.0),
            seed=d.get("seed", 0),
            antecedent_soil_moisture=d.get("antecedent_soil_moisture", "normal"),
            antecedent_groundwater=d.get("antecedent_groundwater", "normal"),
            spatial_correlation_enabled=d.get("spatial_correlation_enabled", False),
            spatial_correlation_range_km=d.get("spatial_correlation_range_km"),
            generated_at=d.get("generated_at", ""),
            catchment_id=d.get("catchment_id", ""),
        )


def make_storm_id() -> str:
    """Generate a unique storm ID using the canonical STORM_ID_PREFIX from config.port."""
    from config.port import STORM_ID_PREFIX
    return f"{STORM_ID_PREFIX}-{uuid.uuid4().hex[:8]}"


def make_sequence_id() -> str:
    """Generate a unique sequence ID using the canonical SEQUENCE_ID_PREFIX from config.port."""
    from config.port import SEQUENCE_ID_PREFIX
    return f"{SEQUENCE_ID_PREFIX}-{uuid.uuid4().hex[:8]}"
