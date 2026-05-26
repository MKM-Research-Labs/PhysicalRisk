# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Asset resilience schema — hazard exposure, hazard profile, resilience checklist, ratings.

Holds four schema dicts as separate module-level names so the legacy
composition in property/schema/__init__.py continues to resolve to the
same PROPERTY_SCHEMA shape:

    RISK_ASSESSMENT_SCHEMA      raw hazard exposure facts
    HAZARD_PROFILE_SCHEMA       normalised hazard classes
    RATINGS_SCHEMA              insurance + governing-body (BRI) ratings
    RESILIENCE_MEASURES_SCHEMA  5 sub-section resilience checklist

The 5-level RESILIENCE_LEVELS vocabulary is exported for downstream BRI
scoring code that needs to compare option lists against the canonical set.
"""

# --- Raw hazard exposure facts ----------------------------------------------

RISK_ASSESSMENT_SCHEMA = {
    "EAFloodZone": {
        "type": "menu",
        "options": ["Zone 1", "Zone 2", "Zone 3a", "Zone 3b"],
        "description": "Environment Agency flood zone"
    },
    "OverallFloodRisk": {
        "type": "menu",
        "options": ["Very low", "Low", "Medium", "High", "Very high"],
        "description": "Overall flood risk assessment"
    },
    "FloodRiskType": {
        "type": "menu",
        "options": ["Fluvial", "Pluvial", "GroundWater", "Coastal", "Multiple"],
        "description": "Primary type of flood risk (drives flood-resilience regime)"
    },
    "GroundLevelMeters": {
        "type": "decimal",
        "description": "Height above sea level in meters"
    },
    "RiverDistanceMeters": {
        "type": "decimal",
        "description": "Distance to nearest river in meters"
    },
    "LastFloodDate": {
        "type": "date",
        "description": "Date of most recent flood event at this property"
    },
    "SoilType": {
        "type": "menu",
        "options": [
            "Clay", "Sandy", "Loamy", "Chalk", "Peat", "Rocky", "Mixed",
            "Saltpans", "Unknown",
        ],
        "description": "Predominant soil composition"
    },
    "LakeDistanceMeters": {
        "type": "decimal",
        "description": "Distance to nearest lake in meters"
    },
    "CoastalDistanceMeters": {
        "type": "decimal",
        "description": "Distance to coastline in meters"
    },
    "CanalDistanceMeters": {
        "type": "decimal",
        "description": "Distance to nearest canal in meters"
    },
    "GovernmentalDefenceScheme": {
        "type": "boolean",
        "description": "Covered by government flood defence scheme"
    },
    "BaseFloodElevationMeters": {
        "type": "decimal",
        "description": "Design flood level in metres (same vertical datum as GroundLevelMeters)"
    },
    "VerticalDatum": {
        "type": "menu",
        "options": ["AOD", "ODN", "WGS84", "Other"],
        "description": "Vertical reference datum used for all elevation fields"
    },
    "SoilVs30Mps": {
        "type": "decimal",
        "description": "Shear wave velocity Vs30 in m/s (OED SoilValue); enables seismic site class"
    },
    "FloodDebrisPresent": {
        "type": "boolean",
        "description": "Significant debris or sediment load expected in catchment floodwater"
    },
}


# --- Normalised hazard classes ----------------------------------------------

_HAZARD_CLASS_OPTIONS = ["None", "Low", "Medium", "High", "Extreme"]

HAZARD_PROFILE_SCHEMA = {
    "FloodHazardClass": {
        "type": "menu",
        "options": _HAZARD_CLASS_OPTIONS,
        "description": "Normalised flood hazard class for the site"
    },
    "WindHazardClass": {
        "type": "menu",
        "options": _HAZARD_CLASS_OPTIONS,
        "description": "Normalised wind/storm hazard class for the site"
    },
    "SeismicHazardClass": {
        "type": "menu",
        "options": _HAZARD_CLASS_OPTIONS,
        "description": "Normalised seismic hazard class for the site"
    },
    "FireHazardClass": {
        "type": "menu",
        "options": _HAZARD_CLASS_OPTIONS,
        "description": "Normalised fire/wildfire hazard class for the site"
    },
    "DesignWindSpeedKmh": {
        "type": "decimal",
        "description": "Site design wind speed in km/h corresponding to WindHazardClass"
    },
    "DesignFloodReturnYr": {
        "type": "integer",
        "description": "Design flood return period in years (e.g. 100 = 1-in-100yr)"
    },
    "DesignSeismicPGA": {
        "type": "decimal",
        "description": "Peak ground acceleration in g for mapped seismic hazard class"
    },
}


# --- Insurance + governing-body ratings -------------------------------------

RATINGS_SCHEMA = {
    "InsuranceBodyRatings": {
        "InsuranceRating": {
            "type": "string",
            "description": "Risk rating assigned by the local insurance market, insurer or underwriting body"
        },
        "InsuranceDate": {
            "type": "date",
            "description": "Date the insurance rating was issued"
        },
        "InsuranceRatingVersion": {
            "type": "string",
            "description": "Version identifier of the insurance rating scheme"
        },
        "InsuranceRatingBody": {
            "type": "string",
            "description": "Name of insurer, broker, pool or local insurance authority that assigned the rating"
        }
    },
    "GoverningBodyRatings": {
        "BRIRating": {
            "type": "menu",
            "options": ["AA", "AA+", "A", "A+", "B", "B+", "NR"],
            "description": "Overall BRI letter grade (weakest-of applicable hazard sub-ratings; '+' suffix indicates operational continuity measures also met)"
        },
        "BRIScore": {
            "type": "decimal",
            "description": "Overall BRI weighted score (0.0-1.0); diagnostic value alongside BRIRating"
        },
        "BRIFloodRating": {
            "type": "menu",
            "options": ["AA", "A", "B", "NR", "N/A"],
            "description": "BRI sub-rating for flood resilience (N/A when FloodHazardClass is None)"
        },
        "BRIFloodScore": {
            "type": "decimal",
            "description": "BRI sub-score for flood resilience (0.0-1.0); null when FloodHazardClass is None"
        },
        "BRIWindRating": {
            "type": "menu",
            "options": ["AA", "A", "B", "NR", "N/A"],
            "description": "BRI sub-rating for wind resilience (N/A when WindHazardClass is None)"
        },
        "BRIWindScore": {
            "type": "decimal",
            "description": "BRI sub-score for wind resilience (0.0-1.0); null when WindHazardClass is None"
        },
        "BRIFireRating": {
            "type": "menu",
            "options": ["AA", "A", "B", "NR", "N/A"],
            "description": "BRI sub-rating for fire resilience (N/A when FireHazardClass is None)"
        },
        "BRIFireScore": {
            "type": "decimal",
            "description": "BRI sub-score for fire resilience (0.0-1.0); null when FireHazardClass is None"
        },
        "BRISeismicRating": {
            "type": "menu",
            "options": ["AA", "A", "B", "NR", "N/A"],
            "description": "BRI sub-rating for seismic resilience (N/A when SeismicHazardClass is None)"
        },
        "BRISeismicScore": {
            "type": "decimal",
            "description": "BRI sub-score for seismic resilience (0.0-1.0); null when SeismicHazardClass is None"
        },
        "BRIDate": {
            "type": "date",
            "description": "Date the BRI rating was issued"
        },
        "BRIRatingVersion": {
            "type": "string",
            "description": "Version identifier of the BRI methodology applied (e.g., 'BRI v1.6')"
        },
        "BRIRatingAgent": {
            "type": "string",
            "description": "Verifier or certifier that performed the BRI assessment (e.g., Bureau Veritas)"
        }
    }
}


# --- Resilience checklist ---------------------------------------------------

RESILIENCE_LEVELS = ["Not assessed", "Partial", "Meets minimum", "Enhanced", "Verified"]


def _level(description: str) -> dict:
    """Build a 5-level menu field definition using RESILIENCE_LEVELS."""
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
