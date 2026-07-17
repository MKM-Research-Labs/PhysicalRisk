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

"""CDM-derived fire feature bundle."""

from dataclasses import dataclass
from typing import List, Optional


# ===========================================================================
# CDM-derived input features
# ===========================================================================


@dataclass
class AssetFireFeatures:
    """The CDM fields the fire model needs for one commercial asset.

    A boundary adapter extracts these from the commercial-asset CDM record
    (asset/commercial/schema.py) and the resilience/history sections. The model
    reads only this bundle, never the raw CDM, so the CDM schema can evolve
    independently.

    Each resilience-level field carries a value from the RESILIENCE_LEVELS
    vocabulary ("Not assessed" .. "Verified"), or None when unknown. They are
    named individually (not a flat list) because Model C (response
    effectiveness) reads detection, suppression and the passive/response fields
    separately.

    Attributes:
        asset_id: stable identifier for the asset.
        commercial_type: CommercialType option (e.g. "Office", "Hotel").
        construction_type: ConstructionType option (the structural frame, e.g.
            "Reinforced concrete", "Steel frame", "Timber frame"). Drives the
            combustibility of the structure — how readily it sustains a full
            conflagration — and the structural-fire-resistance fallback. None
            when unknown (treated as combustible by the model, cautiously).
        occupancy_status: OccupancyStatus option, or None if unknown.
        business_rates_category: BusinessRatesCategory option, or None.
        property_condition: PropertyCondition option, or None.
        automatic_detection_level: AutomaticDetectionInstalled resilience level.
        suppression_systems_level: SuppressionSystemsInstalled resilience level.
        emergency_procedures_level: EmergencyProceduresTested resilience level.
        structural_fire_resistance_level: StructuralFireResistanceAdequate level.
        compartments_level: CompartmentsProvided resilience level.
        fire_stopping_level: FireStoppingAtPenetrations resilience level.
        external_materials_level: ExternalMaterialsFireResistant level.
        access_route_level: AccessRouteResilient resilience level.
        business_continuity_level: BusinessContinuityPlanInPlace level.
        fire_damage_severity: FireDamageSeverity option, or None.
        years_since_last_fire: years since LastFireDate, or None if no prior fire.
        number_of_storeys: NumberOfStoreys (height proxy for the vertical penalty).
    """
    asset_id: str
    commercial_type: str
    construction_type: Optional[str] = None
    occupancy_status: Optional[str] = None
    business_rates_category: Optional[str] = None
    property_condition: Optional[str] = None
    # Detection / suppression / procedural levels (drive m_protection + Model C).
    automatic_detection_level: Optional[str] = None
    suppression_systems_level: Optional[str] = None
    emergency_procedures_level: Optional[str] = None
    # Passive (structural) defence levels.
    structural_fire_resistance_level: Optional[str] = None
    compartments_level: Optional[str] = None
    fire_stopping_level: Optional[str] = None
    external_materials_level: Optional[str] = None
    # Active response levels.
    access_route_level: Optional[str] = None
    business_continuity_level: Optional[str] = None
    # History & geometry.
    fire_damage_severity: Optional[str] = None
    years_since_last_fire: Optional[float] = None
    number_of_storeys: Optional[int] = None

    @property
    def protection_levels(self) -> List[str]:
        """The detection / suppression / procedural levels that drive
        m_protection (Model A), as a list with unknowns dropped."""
        return [
            lv for lv in (
                self.automatic_detection_level,
                self.suppression_systems_level,
                self.emergency_procedures_level,
            )
            if lv is not None
        ]
