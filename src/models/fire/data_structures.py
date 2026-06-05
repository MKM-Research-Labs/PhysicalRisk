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
Runtime data structures for the fire model.

AssetFireFeatures is the CDM-derived feature bundle the initiation stage reads
(the small subset of commercial-asset + resilience fields that drive lambda_i
and the initiation-class prior). IgnitionDraw and AssetInitiationResult capture
the Stage-1 output: per-draw fire/no-fire decisions and per-asset summaries.

Dataclasses are value objects; sampling logic lives in initiation.py.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from config.fire import InitiationClass

__all__ = [
    "AssetFireFeatures",
    "IgnitionDraw",
    "AssetInitiationResult",
]


# ===========================================================================
# CDM-derived input features
# ===========================================================================


@dataclass
class AssetFireFeatures:
    """The CDM fields the initiation stage needs for one commercial asset.

    A boundary adapter extracts these from the commercial-asset CDM record
    (asset/commercial/schema.py) and the resilience/history sections. The model
    reads only this bundle, never the raw CDM, so the CDM schema can evolve
    independently.

    Attributes:
        asset_id: stable identifier for the asset.
        commercial_type: CommercialType option (e.g. "Office", "Hotel").
        occupancy_status: OccupancyStatus option, or None if unknown.
        business_rates_category: BusinessRatesCategory option, or None.
        property_condition: PropertyCondition option, or None.
        protection_levels: resilience-level strings for the protection fields
            (AutomaticDetectionInstalled, SuppressionSystemsInstalled,
            EmergencyProceduresTested). Their mean level index drives m_protection.
        fire_damage_severity: FireDamageSeverity option, or None.
        years_since_last_fire: years since LastFireDate, or None if no prior fire.
        number_of_storeys: NumberOfStoreys (height proxy for later stages).
    """
    asset_id: str
    commercial_type: str
    occupancy_status: Optional[str] = None
    business_rates_category: Optional[str] = None
    property_condition: Optional[str] = None
    protection_levels: List[str] = field(default_factory=list)
    fire_damage_severity: Optional[str] = None
    years_since_last_fire: Optional[float] = None
    number_of_storeys: Optional[int] = None


# ===========================================================================
# Stage-1 outputs
# ===========================================================================


@dataclass
class IgnitionDraw:
    """One Poisson draw for one asset.

    Attributes:
        draw_index: index of the draw within the asset's n_sim ensemble.
        count: Poisson count N_i for this draw.
        fire: True when count >= 1 (a fire instantiates).
        initiation_class: assigned entry-point class when fire is True, else None.
    """
    draw_index: int
    count: int
    fire: bool
    initiation_class: Optional[InitiationClass] = None


@dataclass
class AssetInitiationResult:
    """Per-asset summary of the Stage-1 initiation simulation.

    Attributes:
        asset_id: the asset this result is for.
        lambda_annual: effective annual ignition rate lambda_i.
        lambda_effective: rate scaled to the run horizon (lambda_i * horizon_years).
        n_sim: number of draws taken.
        n_fires: number of draws with a fire (count >= 1).
        fire_probability: n_fires / n_sim — empirical P(at least one ignition).
        class_counts: count of instantiated fires by InitiationClass.
        draws: the per-draw IgnitionDraw records.
    """
    asset_id: str
    lambda_annual: float
    lambda_effective: float
    n_sim: int
    n_fires: int
    fire_probability: float
    class_counts: Dict[InitiationClass, int] = field(default_factory=dict)
    draws: List[IgnitionDraw] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serialisable summary (omits per-draw detail)."""
        return {
            "asset_id": self.asset_id,
            "lambda_annual": self.lambda_annual,
            "lambda_effective": self.lambda_effective,
            "n_sim": self.n_sim,
            "n_fires": self.n_fires,
            "fire_probability": self.fire_probability,
            "class_counts": {k.value: v for k, v in self.class_counts.items()},
        }
