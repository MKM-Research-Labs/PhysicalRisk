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
Data structures for the storm gauge forward model.

Enums for intensity profiles and decay kernels, plus dataclasses
for storm tracks, gauge configuration, and gauge responses.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class IntensityProfile(Enum):
    """Storm intensity profile shapes."""
    TRIANGULAR = "triangular"       # Linear ramp up, linear ramp down
    BETA = "beta"                   # Beta distribution shape (smoother)
    GAUSSIAN = "gaussian"           # Gaussian envelope


class DecayKernel(Enum):
    """Spatial decay kernels for storm footprint."""
    GAUSSIAN = "gaussian"           # exp(-d²/2σ²)
    EXPONENTIAL = "exponential"     # exp(-d/λ)
    LINEAR = "linear"               # max(0, 1 - d/r)


@dataclass
class TrackPoint:
    """A point along the storm track."""
    longitude: float
    latitude: float
    time_hours: float              # Hours since storm start
    intensity: float               # 0-100 intensity at this point


@dataclass
class Storm:
    """
    Storm event with full parameterisation.

    Attributes:
        storm_id: Unique identifier
        name: Human-readable name
        start_time: Storm start datetime
        duration_hours: Total storm duration
        track: List of track points with timing and intensity
        peak_intensity: Maximum intensity (0-100 scale)
        footprint_km: Characteristic width of precipitation field
        decay_kernel: How intensity falls off with distance
        decay_parameter: Kernel-specific parameter (e.g., std dev for gaussian)
        intensity_profile: Shape of intensity along track
        speed_kmh: Average storm speed
        metadata: Additional metadata
    """
    storm_id: str
    name: str
    start_time: datetime
    duration_hours: float
    track: List[TrackPoint]
    peak_intensity: float
    footprint_km: float
    decay_kernel: DecayKernel = DecayKernel.GAUSSIAN
    decay_parameter: float = 0.5    # Normalised: 1.0 = footprint_km
    intensity_profile: IntensityProfile = IntensityProfile.TRIANGULAR
    speed_kmh: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialisation."""
        return {
            "storm_id": self.storm_id,
            "name": self.name,
            "start_time": self.start_time.isoformat(),
            "duration_hours": self.duration_hours,
            "track": [
                {
                    "longitude": p.longitude,
                    "latitude": p.latitude,
                    "time_hours": p.time_hours,
                    "intensity": p.intensity,
                }
                for p in self.track
            ],
            "peak_intensity": self.peak_intensity,
            "footprint_km": self.footprint_km,
            "decay_kernel": self.decay_kernel.value,
            "decay_parameter": self.decay_parameter,
            "intensity_profile": self.intensity_profile.value,
            "speed_kmh": self.speed_kmh,
            "metadata": self.metadata,
        }


@dataclass
class GaugeConfig:
    """
    Gauge configuration for model.

    Attributes:
        gauge_id: Unique identifier
        gauge_name: Human-readable name
        latitude: Gauge latitude
        longitude: Gauge longitude
        base_level: Normal water level (meters)
        flood_alert: FloodAlert threshold (meters)
        flood_warning: FloodWarning threshold (meters)
        severe_warning: SevereFloodWarning threshold (meters)
        historical_high: Historical maximum level (meters)
        sensitivity: Gauge-specific response multiplier (default 1.0)
    """
    gauge_id: str
    gauge_name: str
    latitude: float
    longitude: float
    base_level: float
    flood_alert: float
    flood_warning: float
    severe_warning: float
    historical_high: Optional[float] = None
    sensitivity: float = 1.0

    @classmethod
    def from_gauge_portfolio(cls, gauge_data: Dict[str, Any]) -> "GaugeConfig":
        """Create GaugeConfig from gauge portfolio entry."""
        fg = gauge_data.get("FloodGauge", gauge_data)
        header = fg.get("Header", {})
        location = fg.get("Location", {})
        stages = fg.get("FloodStages", {})

        flood_alert = stages.get("FloodAlert", 4.0)
        base_level = flood_alert * 0.35

        return cls(
            gauge_id=header.get("GaugeID", "UNKNOWN"),
            gauge_name=header.get("GaugeName", ""),
            latitude=location.get("GaugeLatitude", 0),
            longitude=location.get("GaugeLongitude", 0),
            base_level=base_level,
            flood_alert=flood_alert,
            flood_warning=stages.get("FloodWarning", flood_alert * 1.33),
            severe_warning=stages.get("SevereFloodWarning", flood_alert * 1.58),
            historical_high=stages.get("HistoricalHighLevel"),
        )


@dataclass
class GaugeResponse:
    """
    Gauge response to a storm event.

    Attributes:
        gauge_id: Gauge identifier
        storm_id: Storm identifier
        flooded: Whether gauge exceeded flood alert
        peak_level: Maximum water level during event (meters)
        peak_exceedance: Maximum level above flood alert (meters, can be negative)
        peak_time_hours: Time of peak relative to storm start
        peak_intensity: Maximum storm intensity experienced at this gauge (0-100)
        peak_intensity_time_hours: Time of peak intensity
        duration_above_alert: Hours above flood alert threshold
        duration_above_warning: Hours above flood warning threshold
        duration_above_severe: Hours above severe warning threshold
        accumulation: Integral of exceedance over time (meter-hours)
        intensity_timeseries: Storm intensity at gauge over time
        level_timeseries: Water level at gauge over time
    """
    gauge_id: str
    storm_id: str
    flooded: bool
    peak_level: float
    peak_exceedance: float
    peak_time_hours: float
    peak_intensity: float
    peak_intensity_time_hours: float
    duration_above_alert: float
    duration_above_warning: float
    duration_above_severe: float
    accumulation: float
    intensity_timeseries: List[Dict[str, float]] = field(default_factory=list)
    level_timeseries: List[Dict[str, float]] = field(default_factory=list)

    def to_dict(self, include_timeseries: bool = True) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialisation."""
        d = {
            "gauge_id": self.gauge_id,
            "storm_id": self.storm_id,
            "flooded": self.flooded,
            "peak_level": round(self.peak_level, 3),
            "peak_exceedance": round(self.peak_exceedance, 3),
            "peak_time_hours": round(self.peak_time_hours, 2),
            "peak_intensity": round(self.peak_intensity, 2),
            "peak_intensity_time_hours": round(self.peak_intensity_time_hours, 2),
            "duration_above_alert": round(self.duration_above_alert, 2),
            "duration_above_warning": round(self.duration_above_warning, 2),
            "duration_above_severe": round(self.duration_above_severe, 2),
            "accumulation": round(self.accumulation, 3),
        }
        if include_timeseries:
            d["intensity_timeseries"] = [
                {"time_hours": round(p["time_hours"], 2), "intensity": round(p["intensity"], 2)}
                for p in self.intensity_timeseries
            ]
            d["level_timeseries"] = [
                {"time_hours": round(p["time_hours"], 2), "level": round(p["level"], 3)}
                for p in self.level_timeseries
            ]
        return d
