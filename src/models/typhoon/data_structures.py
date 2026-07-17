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
Runtime data structures for the Bayesian typhoon progression model.

Defines the latent state, particles, trajectories, and wind-field output.
The regime and scenario-family enums are part of the configuration schema
and live in config/typhoon.py; this module imports them for use in the
state representation.

The state s_t corresponds to spec eq. (1):
    s_t = (lambda, phi, u, psi, V_max, R_max, R_outer, regime)

Units convention used throughout:
- longitude, latitude: degrees
- translation speed (u): km/h
- heading (psi): compass degrees from North, clockwise (0 = N, 90 = E, 180 = S, 270 = W)
- maximum sustained wind (V_max): m/s
- radii (R_max, R_outer): km
- time: hours since genesis (t = 0 at storm start)

Invariants like R_max < R_outer and V_max >= 0 are enforced by the transition
layer, not by the dataclass itself. Dataclasses are value objects.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.typhoon import RegimeClass, ScenarioFamily


# Re-export the enums for callers that prefer to import everything from
# this module. The canonical home is config.typhoon.
__all__ = [
    "RegimeClass",
    "ScenarioFamily",
    "TyphoonState",
    "TyphoonParticle",
    "TyphoonTrajectory",
    "WindFieldOutput",
]


# ===========================================================================
# Latent state — spec eq. (1)
# ===========================================================================


@dataclass
class TyphoonState:
    """Latent typhoon state at a single time step.

    Corresponds to s_t = (lambda, phi, u, psi, V_max, R_max, R_outer, regime)
    from the Bayesian progression spec, eq. (1).

    Attributes:
        longitude: lambda_t — degrees east
        latitude: phi_t — degrees north
        translation_speed_kmh: u_t — forward speed in km/h
        heading_deg: psi_t — compass bearing of motion, degrees from North, clockwise
        v_max_ms: V_t — maximum sustained wind at storm center, m/s
        r_max_km: R_max — radius of maximum wind, km
        r_outer_km: R_outer — outer wind radius (e.g. gale-force radius), km
        regime: k_t — discrete regime class
        land_flag: True if storm center is over land at this step
        time_hours: t — hours since genesis (genesis is t = 0)
    """
    longitude: float
    latitude: float
    translation_speed_kmh: float
    heading_deg: float
    v_max_ms: float
    r_max_km: float
    r_outer_km: float
    regime: RegimeClass
    land_flag: bool
    time_hours: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialisation."""
        return {
            "longitude": self.longitude,
            "latitude": self.latitude,
            "translation_speed_kmh": self.translation_speed_kmh,
            "heading_deg": self.heading_deg,
            "v_max_ms": self.v_max_ms,
            "r_max_km": self.r_max_km,
            "r_outer_km": self.r_outer_km,
            "regime": self.regime.value,
            "land_flag": self.land_flag,
            "time_hours": self.time_hours,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TyphoonState":
        """Construct from a dictionary (inverse of to_dict)."""
        return cls(
            longitude=d["longitude"],
            latitude=d["latitude"],
            translation_speed_kmh=d["translation_speed_kmh"],
            heading_deg=d["heading_deg"],
            v_max_ms=d["v_max_ms"],
            r_max_km=d["r_max_km"],
            r_outer_km=d["r_outer_km"],
            regime=RegimeClass(d["regime"]),
            land_flag=d["land_flag"],
            time_hours=d["time_hours"],
        )


# ===========================================================================
# Particles and trajectories — spec eq. (13)
# ===========================================================================


@dataclass
class TyphoonParticle:
    """One particle in the Sequential Monte Carlo posterior approximation.

    Corresponds to (s_t^(i), w_t^(i)) in spec eq. (13). The particle_id is
    stable across resampling so trajectories can be reconstructed by chaining
    parent_id pointers.

    Attributes:
        state: current latent state
        weight: normalised particle weight in [0, 1]
        particle_id: stable identifier across resampling
        parent_id: index of parent in previous step (None for genesis particles)
    """
    state: TyphoonState
    weight: float
    particle_id: int
    parent_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.to_dict(),
            "weight": self.weight,
            "particle_id": self.particle_id,
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TyphoonParticle":
        return cls(
            state=TyphoonState.from_dict(d["state"]),
            weight=d["weight"],
            particle_id=d["particle_id"],
            parent_id=d.get("parent_id"),
        )


@dataclass
class TyphoonTrajectory:
    """Time-ordered sequence of states for a single particle / event.

    Attributes:
        event_id: identifier shared across particles in the same simulated event
        particle_id: identifier of the particle this trajectory belongs to
        scenario_family: scenario family used for genesis prior of this event
        genesis_time: absolute calendar time corresponding to t = 0
        states: list of TyphoonState ordered by time_hours ascending
    """
    event_id: str
    particle_id: int
    scenario_family: ScenarioFamily
    genesis_time: datetime
    states: List[TyphoonState] = field(default_factory=list)

    @property
    def horizon_hours(self) -> float:
        """Time of the final state, or 0.0 if empty."""
        return self.states[-1].time_hours if self.states else 0.0

    @property
    def n_steps(self) -> int:
        return len(self.states)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "particle_id": self.particle_id,
            "scenario_family": self.scenario_family.value,
            "genesis_time": self.genesis_time.isoformat(),
            "states": [s.to_dict() for s in self.states],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TyphoonTrajectory":
        return cls(
            event_id=d["event_id"],
            particle_id=d["particle_id"],
            scenario_family=ScenarioFamily(d["scenario_family"]),
            genesis_time=datetime.fromisoformat(d["genesis_time"]),
            states=[TyphoonState.from_dict(s) for s in d["states"]],
        )


# ===========================================================================
# Wind-field output — spec p.13
# ===========================================================================


@dataclass
class WindFieldOutput:
    """Point-location wind-field summary over a trajectory.

    Captures the point outputs required by the wind-field spec (p.13):
    sustained wind time series, peak sustained wind, time of peak,
    threshold-exceedance durations, and distance/azimuth from center at peak.

    Gust outputs are not populated in Phase 1; the fields exist so a later
    phase can add them without changing the type.

    Attributes:
        point_id: stable identifier (typically property_id)
        longitude: point longitude
        latitude: point latitude
        time_hours: monotonically increasing sample times
        sustained_ms: sustained wind in m/s at each sample time
        gust_ms: gust wind in m/s at each sample time (Phase 1: empty)
        peak_sustained_ms: max of sustained_ms over the trajectory
        time_of_peak_hours: time_hours value at the peak
        distance_at_peak_km: storm-center distance at moment of peak
        azimuth_at_peak_deg: bearing from center to point at moment of peak
        duration_above_ms: {threshold_ms: hours above threshold}
    """
    point_id: str
    longitude: float
    latitude: float
    time_hours: List[float]
    sustained_ms: List[float]
    peak_sustained_ms: float
    time_of_peak_hours: float
    distance_at_peak_km: float
    azimuth_at_peak_deg: float
    duration_above_ms: Dict[float, float] = field(default_factory=dict)
    gust_ms: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "point_id": self.point_id,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "time_hours": list(self.time_hours),
            "sustained_ms": list(self.sustained_ms),
            "gust_ms": list(self.gust_ms),
            "peak_sustained_ms": self.peak_sustained_ms,
            "time_of_peak_hours": self.time_of_peak_hours,
            "distance_at_peak_km": self.distance_at_peak_km,
            "azimuth_at_peak_deg": self.azimuth_at_peak_deg,
            # JSON object keys must be strings — encode thresholds as strings
            "duration_above_ms": {str(k): v for k, v in self.duration_above_ms.items()},
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "WindFieldOutput":
        return cls(
            point_id=d["point_id"],
            longitude=d["longitude"],
            latitude=d["latitude"],
            time_hours=list(d["time_hours"]),
            sustained_ms=list(d["sustained_ms"]),
            gust_ms=list(d.get("gust_ms", [])),
            peak_sustained_ms=d["peak_sustained_ms"],
            time_of_peak_hours=d["time_of_peak_hours"],
            distance_at_peak_km=d["distance_at_peak_km"],
            azimuth_at_peak_deg=d["azimuth_at_peak_deg"],
            duration_above_ms={float(k): v for k, v in d.get("duration_above_ms", {}).items()},
        )
