# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use is prohibited
# unless separately authorized in writing by MKM Research Labs.

"""Model A occurrence output types."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class EarthquakeEvent:
    """One instantiated earthquake for one Monte Carlo draw (Model A).

    Produced only for draws whose Poisson count is >= 1. Carries the sampled
    magnitude, the rupture centroid drawn along the fault trace, the
    Wells-Coppersmith surface rupture length, and the Joyner-Boore
    source-to-site distance R_JB consumed by Model B.

    Attributes:
        draw_index: index of the Monte Carlo draw that instantiated the event.
        magnitude: sampled moment magnitude M (truncated Gutenberg-Richter).
        rupture_centroid_lat: latitude of the rupture centroid (degrees).
        rupture_centroid_lon: longitude of the rupture centroid (degrees).
        rupture_length_km: along-fault surface rupture length L_r (km).
        r_jb_km: Joyner-Boore distance from the asset to the rupture (km).
    """
    draw_index: int
    magnitude: float
    rupture_centroid_lat: float
    rupture_centroid_lon: float
    rupture_length_km: float
    r_jb_km: float


@dataclass
class OccurrenceResult:
    """Per-asset summary of Model A occurrence over n_sim draws.

    Attributes:
        asset_id: stable identifier for the asset.
        zone: resolved seismic hazard zone label (e.g. "Moderate").
        site_class: resolved Eurocode 8 site class (A-E).
        fault_distance_km: static asset-to-fault distance (km), or None when
            the asset carries no coordinates / no fault trace is supplied.
        lambda_annual: per-asset annual occurrence rate lambda_i.
        lambda_effective: lambda_annual * horizon_years (the Poisson mean).
        n_sim: number of Monte Carlo draws.
        n_events: number of draws that instantiated an earthquake (N >= 1).
        events: the instantiated EarthquakeEvent records.
    """
    asset_id: str
    zone: str
    site_class: str
    fault_distance_km: Optional[float]
    lambda_annual: float
    lambda_effective: float
    n_sim: int
    n_events: int
    events: List[EarthquakeEvent] = field(default_factory=list)

    @property
    def event_rate(self) -> float:
        """Fraction of draws that instantiated an earthquake."""
        return self.n_events / self.n_sim if self.n_sim else 0.0
