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

"""Flatten ProtectionMeasures.ResilienceMeasures (5 functional sub-sections)."""


def flatten_resilience(prop: dict) -> dict:
    """Return flat snake_case keys for every resilience sub-section."""
    rm = prop.get("ProtectionMeasures", {}).get("ResilienceMeasures", {})
    building = rm.get("BuildingAssessment", {})
    site = rm.get("SiteAndDrainage", {})
    flood = rm.get("FloodProtection", {})
    fire = rm.get("FireProtection", {})
    continuity = rm.get("ContinuityMeasures", {})

    return {
        # BuildingAssessment
        "site_exposure_assessed":             building.get("SiteExposureAssessed"),
        "orientation_mitigates_wind":         building.get("OrientationMitigatesWind"),
        "structure_designed_for_hazard_wind": building.get("StructureDesignedForHazardWind"),
        "continuous_load_path_provided":      building.get("ContinuousLoadPathProvided"),
        "lateral_bracing_adequate":           building.get("LateralBracingAdequate"),
        "roof_rated_for_design_wind":         building.get("RoofRatedForDesignWind"),
        "roof_edge_detail_wind_resistant":    building.get("RoofEdgeDetailWindResistant"),
        "cladding_rated_for_design_wind":     building.get("CladdingRatedForDesignWind"),
        "openings_wind_resistant":            building.get("OpeningsWindResistant"),
        "large_doors_reinforced":             building.get("LargeDoorsReinforced"),
        "rooftop_equipment_anchored":         building.get("RooftopEquipmentAnchored"),
        "facade_attachments_anchored":        building.get("FacadeAttachmentsAnchored"),
        "structural_fire_resistance_adequate": building.get("StructuralFireResistanceAdequate"),
        "compartments_provided":              building.get("CompartmentsProvided"),
        "fire_stopping_at_penetrations":      building.get("FireStoppingAtPenetrations"),
        "external_materials_fire_resistant":  building.get("ExternalMaterialsFireResistant"),
        "site_geotechnical_assessed":         building.get("SiteGeotechnicalAssessed"),
        "structure_meets_seismic_code":       building.get("StructureMeetsSeismicCode"),
        "seismic_detailing_to_standard":      building.get("SeismicDetailingToStandard"),
        "structural_regularity_adequate":     building.get("StructuralRegularityAdequate"),
        "foundation_suitable_for_hazard":     building.get("FoundationSuitableForHazard"),
        "nonstructural_components_anchored":  building.get("NonstructuralComponentsAnchored"),
        "heavy_equipment_anchored":           building.get("HeavyEquipmentAnchored"),

        # SiteAndDrainage
        "site_flood_hazard_assessed":          site.get("SiteFloodHazardAssessed"),
        "high_risk_zone_avoided_or_justified": site.get("HighRiskZoneAvoidedOrJustified"),
        "finished_floor_above_design_flood":   site.get("FinishedFloorAboveDesignFlood"),
        "occupied_levels_elevated":            site.get("OccupiedLevelsElevated"),
        "basement_flood_strategy":             site.get("BasementFloodStrategy"),
        "onsite_drainage_sized_for_design_storm": site.get("OnsiteDrainageSizedForDesignStorm"),
        "overland_flow_paths_maintained":      site.get("OverlandFlowPathsMaintained"),
        "permeable_or_retention_measures":     site.get("PermeableOrRetentionMeasures"),
        "wildfire_defensible_space":           site.get("WildfireDefensibleSpace"),
        "wildfire_non_combustible_perimeter":  site.get("WildfireNonCombustiblePerimeter"),
        "high_risk_ground_avoided_or_mitigated": site.get("HighRiskGroundAvoidedOrMitigated"),
        "liquefaction_mitigation_provided":    site.get("LiquefactionMitigationProvided"),

        # FloodProtection
        "permanent_flood_proofing_at_entries": flood.get("PermanentFloodProofingAtEntries"),
        "deployable_barriers_provided":        flood.get("DeployableBarriersProvided"),
        "backflow_prevention_installed":       flood.get("BackflowPreventionInstalled"),
        "electrical_systems_above_flood":      flood.get("ElectricalSystemsAboveFlood"),
        "mechanical_systems_above_flood":      flood.get("MechanicalSystemsAboveFlood"),
        "fuel_and_hazardous_stores_protected": flood.get("FuelAndHazardousStoresProtected"),
        "flood_gates":          flood.get("FloodGates"),
        "flood_barriers":       flood.get("FloodBarriers"),
        "sump_pump":            flood.get("SumpPump"),
        "flood_warning_system": flood.get("FloodWarningSystem"),

        # FireProtection
        "automatic_detection_installed":  fire.get("AutomaticDetectionInstalled"),
        "suppression_systems_installed":  fire.get("SuppressionSystemsInstalled"),

        # ContinuityMeasures
        "backup_power_installed":            continuity.get("BackupPowerInstalled"),
        "backup_power_protected_from_hazard": continuity.get("BackupPowerProtectedFromHazard"),
        "backup_water_supply_provided":      continuity.get("BackupWaterSupplyProvided"),
        "water_systems_protected_from_hazard": continuity.get("WaterSystemsProtectedFromHazard"),
        "telecom_redundancy_provided":       continuity.get("TelecomRedundancyProvided"),
        "critical_it_protected":             continuity.get("CriticalITProtected"),
        "access_route_resilient":            continuity.get("AccessRouteResilient"),
        "access_design_considers_hazards":   continuity.get("AccessDesignConsidersHazards"),
        "business_continuity_plan_in_place": continuity.get("BusinessContinuityPlanInPlace"),
        "emergency_procedures_tested":       continuity.get("EmergencyProceduresTested"),
    }
