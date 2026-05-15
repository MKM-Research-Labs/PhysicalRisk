# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
ProtectionMeasures.ResilienceMeasures — resilience checks grouped by function.

Covers §2.3 of the revised Property CDM. Five sub-sections, grouped by what the
check is about (building fabric, site/drainage, flood protection, fire
protection, continuity), not by which downstream framework consumes them.

Every checklist item is a 5-level menu using ``RESILIENCE_LEVELS`` as its
controlled vocabulary, per the revised CDM review §4.3:

    Not assessed   — the measure has not been evaluated for this asset.
    Partial        — present but does not meet the minimum requirement.
    Meets minimum  — meets the minimum requirement.
    Enhanced       — exceeds the minimum requirement.
    Verified       — verified by an independent third party (highest level).

``BasementFloodStrategy`` keeps its own vocabulary because it describes a
strategy choice (No basement / Flood-resistant / etc.) rather than an
assessment level.
"""

RESILIENCE_LEVELS = ["Not assessed", "Partial", "Meets minimum", "Enhanced", "Verified"]


def _level(description: str) -> dict:
    """Helper — build a menu field def with the standard resilience levels."""
    return {
        "type": "menu",
        "options": RESILIENCE_LEVELS,
        "description": description,
    }


BUILDING_ASSESSMENT_SCHEMA = {
    "SiteExposureAssessed":             _level("Site wind exposure (terrain/topography) has been explicitly assessed"),
    "OrientationMitigatesWind":         _level("Building orientation/massing selected to reduce wind pressure where practicable"),
    "StructureDesignedForHazardWind":   _level("Primary structure designed to required wind speed for mapped hazard class"),
    "ContinuousLoadPathProvided":       _level("Continuous load path from roof to foundation for wind loads"),
    "LateralBracingAdequate":           _level("Lateral bracing / shear systems appropriate for design wind loads"),
    "RoofRatedForDesignWind":           _level("Roof system (covering, fixings, edges) rated for design wind speed"),
    "RoofEdgeDetailWindResistant":      _level("Roof edges, parapets and eaves detailed to resist wind uplift"),
    "CladdingRatedForDesignWind":       _level("External cladding rated/anchored for design wind pressures"),
    "OpeningsWindResistant":            _level("External doors and windows in wind-exposed façades rated or protected"),
    "LargeDoorsReinforced":             _level("Large doors (garages, loading bays) reinforced or braced for wind"),
    "RooftopEquipmentAnchored":         _level("Rooftop mechanical/electrical equipment anchored for design wind speeds"),
    "FacadeAttachmentsAnchored":        _level("Façade-mounted elements (signage, louvers, awnings) anchored for design wind loads"),
    "StructuralFireResistanceAdequate": _level("Primary structural frame has fire-resistance ratings appropriate to building type and code"),
    "CompartmentsProvided":             _level("Fire-rated walls, floors and doors form effective compartments"),
    "FireStoppingAtPenetrations":       _level("Penetrations in fire-rated elements properly sealed with fire-stopping systems"),
    "ExternalMaterialsFireResistant":   _level("External cladding and roof materials non-combustible or fire-resistant in high fire-risk contexts"),
    "SiteGeotechnicalAssessed":         _level("Site geotechnical and seismic conditions formally investigated"),
    "StructureMeetsSeismicCode":        _level("Structural system designed to at least the mapped seismic hazard level for the site"),
    "SeismicDetailingToStandard":       _level("Seismic detailing (ductility, confinement, reinforcement) follows a recognised seismic code"),
    "StructuralRegularityAdequate":     _level("Structural configuration avoids severe irregularities (soft storey, torsional eccentricity)"),
    "FoundationSuitableForHazard":      _level("Foundation type selected and detailed for expected seismic and ground-movement conditions"),
    "NonstructuralComponentsAnchored":  _level("Suspended ceilings, partitions and heavy fittings braced/anchored against seismic movement"),
    "HeavyEquipmentAnchored":           _level("Heavy equipment and building services (tanks, chillers, switchgear) anchored and braced"),
}

SITE_AND_DRAINAGE_SCHEMA = {
    "SiteFloodHazardAssessed":          _level("Site flood hazard explicitly assessed across all relevant perils"),
    "HighRiskZoneAvoidedOrJustified":   _level("High flood-risk locations avoided where feasible, or formally justified and mitigated"),
    "FinishedFloorAboveDesignFlood":    _level("Finished floor of occupied spaces above design flood level for the site"),
    "OccupiedLevelsElevated":           _level("Primary occupied levels elevated (stilts, raised plinth) in high flood-risk areas"),
    "BasementFloodStrategy": {
        "type": "menu",
        "options": ["None", "No basement", "Flood-resistant basement", "Deliberately floodable with protection"],
        "description": "Strategy applied to basements for flood resistance"
    },
    "OnsiteDrainageSizedForDesignStorm":  _level("On-site surface drainage designed for at least the design storm (capacity, slopes, outlets)"),
    "OverlandFlowPathsMaintained":        _level("Site layout maintains positive overland flow paths away from buildings"),
    "PermeableOrRetentionMeasures":       _level("Permeable surfaces or retention features (swales, detention basins) used for runoff"),
    "WildfireDefensibleSpace":            _level("Defensible space (managed vegetation, reduced fuel load) provided around the building"),
    "WildfireNonCombustiblePerimeter":    _level("Non-combustible zone maintained directly adjacent to external walls and roofs"),
    "HighRiskGroundAvoidedOrMitigated":   _level("Known landslide-prone slopes, unstable ground or subsidence areas avoided or mitigated"),
    "LiquefactionMitigationProvided":     _level("Ground improvement or foundation design implemented where liquefaction is a risk"),
}

FLOOD_PROTECTION_SCHEMA = {
    "PermanentFloodProofingAtEntries": _level("Permanent flood-resistant construction at typical entry points (walls, doors, thresholds)"),
    "DeployableBarriersProvided":      _level("Deployable flood barriers/gates provided at all flood-exposed openings below design flood level"),
    "BackflowPreventionInstalled":     _level("Backflow prevention devices installed on sewer/drainage connections"),
    "ElectricalSystemsAboveFlood":     _level("Main electrical switchboards and critical electrical equipment above design flood level or protected"),
    "MechanicalSystemsAboveFlood":     _level("Main mechanical plant (pumps, boilers, chillers) above design flood level or protected"),
    "FuelAndHazardousStoresProtected": _level("Fuel tanks and hazardous material stores elevated or secured to prevent flotation and leakage"),
    "FloodGates":                      _level("Flood gates installed at vulnerable openings"),
    "FloodBarriers":                   _level("Permanent or removable flood barriers in place"),
    "SumpPump":                        _level("Sump pump system installed for basement / low-point dewatering"),
    "FloodWarningSystem":              _level("Flood warning / monitoring system in place"),
}

FIRE_PROTECTION_SCHEMA = {
    "AutomaticDetectionInstalled":  _level("Automatic fire detection and alarm systems installed and covering required areas"),
    "SuppressionSystemsInstalled":  _level("Fire suppression systems (sprinklers, hydrants, hose reels) installed per code and functional"),
}

CONTINUITY_MEASURES_SCHEMA = {
    "BackupPowerInstalled":              _level("Backup power system (generator or equivalent) installed with capacity to maintain critical functions"),
    "BackupPowerProtectedFromHazard":    _level("Backup power equipment and fuel storage protected from site-specific hazards"),
    "BackupWaterSupplyProvided":         _level("Backup water storage or alternative water supply exists for essential uses"),
    "WaterSystemsProtectedFromHazard":   _level("Critical pumps and water/sanitation treatment equipment protected from relevant hazards"),
    "TelecomRedundancyProvided":         _level("At least one backup or redundant telecommunications pathway provided"),
    "CriticalITProtected":               _level("Critical IT and data infrastructure protected (elevated, fire-protected, with power conditioning)"),
    "AccessRouteResilient":              _level("At least one access/egress route expected to remain usable or be restored quickly under hazards"),
    "AccessDesignConsidersHazards":      _level("Site access points designed with hazard impacts in mind"),
    "BusinessContinuityPlanInPlace":     _level("Written business/operations continuity plan exists addressing local hazard scenarios"),
    "EmergencyProceduresTested":         _level("Emergency response procedures documented and periodically exercised (drills or tests)"),
}

RESILIENCE_MEASURES_SCHEMA = {
    "BuildingAssessment": BUILDING_ASSESSMENT_SCHEMA,
    "SiteAndDrainage": SITE_AND_DRAINAGE_SCHEMA,
    "FloodProtection": FLOOD_PROTECTION_SCHEMA,
    "FireProtection": FIRE_PROTECTION_SCHEMA,
    "ContinuityMeasures": CONTINUITY_MEASURES_SCHEMA,
}
