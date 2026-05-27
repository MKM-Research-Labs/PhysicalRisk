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

"""Output data structures for the typhoon ensemble pipeline.

PropertyPeakWindSummary       — per-property aggregated statistics
TyphoonEventEnsemble          — top-level pipeline result

Both serialize to / deserialize from plain dicts so the pipeline output
can be written as JSON for the regulatory inventory and downstream
risk consumers.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


__all__ = [
    "PropertyPeakWindSummary",
    "TyphoonEventEnsemble",
]


@dataclass
class PropertyPeakWindSummary:
    """Aggregated peak-wind statistics at a single property point.

    Each realization (one per particle per event) contributes one peak
    sustained wind value, used to build the empirical posterior.

    Attributes:
        property_id: identifier matching the catchment's PropertyPoint
        longitude: degrees east
        latitude: degrees north
        n_realizations: total count (n_events * n_particles)
        peak_sustained_samples: every realization's peak sustained wind (m/s)
        peak_sustained_mean: empirical mean of peak_sustained_samples
        peak_sustained_p50: empirical median
        peak_sustained_p95: empirical 95th percentile
        peak_sustained_p99: empirical 99th percentile
        threshold_exceedance: {threshold_ms: probability of any realization
            exceeding the threshold during the simulation}
        mean_duration_above_ms: {threshold_ms: mean hours above threshold,
            averaged across all realizations}
    """
    property_id: str
    longitude: float
    latitude: float
    n_realizations: int
    peak_sustained_samples: List[float]
    peak_sustained_mean: float
    peak_sustained_p50: float
    peak_sustained_p95: float
    peak_sustained_p99: float
    threshold_exceedance: Dict[float, float] = field(default_factory=dict)
    mean_duration_above_ms: Dict[float, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "property_id": self.property_id,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "n_realizations": self.n_realizations,
            "peak_sustained_samples": list(self.peak_sustained_samples),
            "peak_sustained_mean": self.peak_sustained_mean,
            "peak_sustained_p50": self.peak_sustained_p50,
            "peak_sustained_p95": self.peak_sustained_p95,
            "peak_sustained_p99": self.peak_sustained_p99,
            # JSON object keys must be strings.
            "threshold_exceedance": {str(k): v for k, v in self.threshold_exceedance.items()},
            "mean_duration_above_ms": {str(k): v for k, v in self.mean_duration_above_ms.items()},
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PropertyPeakWindSummary":
        return cls(
            property_id=d["property_id"],
            longitude=d["longitude"],
            latitude=d["latitude"],
            n_realizations=d["n_realizations"],
            peak_sustained_samples=list(d["peak_sustained_samples"]),
            peak_sustained_mean=d["peak_sustained_mean"],
            peak_sustained_p50=d["peak_sustained_p50"],
            peak_sustained_p95=d["peak_sustained_p95"],
            peak_sustained_p99=d["peak_sustained_p99"],
            threshold_exceedance={float(k): v for k, v in d.get("threshold_exceedance", {}).items()},
            mean_duration_above_ms={float(k): v for k, v in d.get("mean_duration_above_ms", {}).items()},
        )


@dataclass
class TyphoonEventEnsemble:
    """Top-level result of simulate_typhoon_events().

    Attributes:
        catchment_id: identifier of the active catchment
        n_events: number of events simulated
        n_particles: particles per event
        horizon_hours: simulation horizon
        dt_hours: step length
        properties: per-property summaries, one entry per catchment property point
        metadata: free-form auxiliary metadata (timings, seeds, etc.)
    """
    catchment_id: str
    n_events: int
    n_particles: int
    horizon_hours: float
    dt_hours: float
    properties: List[PropertyPeakWindSummary]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "catchment_id": self.catchment_id,
            "n_events": self.n_events,
            "n_particles": self.n_particles,
            "horizon_hours": self.horizon_hours,
            "dt_hours": self.dt_hours,
            "properties": [p.to_dict() for p in self.properties],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TyphoonEventEnsemble":
        return cls(
            catchment_id=d["catchment_id"],
            n_events=d["n_events"],
            n_particles=d["n_particles"],
            horizon_hours=d["horizon_hours"],
            dt_hours=d["dt_hours"],
            properties=[PropertyPeakWindSummary.from_dict(p) for p in d.get("properties", [])],
            metadata=dict(d.get("metadata", {})),
        )
