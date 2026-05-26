# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Commercial asset schema composition.

Scope: office, retail, hotel, leisure, healthcare, multi-family, mixed-use.
Industrial / warehouse / manufacturing live in asset/industrial/ — kept out
of this composition.

Vocabulary is unified with asset/residential (FloodRiskType, PropertyPeriod,
RESILIENCE_LEVELS, etc.) so future cross-portfolio analytics work cleanly.
"""

from ..energy import ENERGY_PERFORMANCE_SCHEMA
from ..header import HEADER_SCHEMA as ASSET_HEADER_SCHEMA
from ..history import HISTORY_AND_INCIDENTS_SCHEMA, TRANSACTION_HISTORY_SCHEMA
from ..resilience import (
    HAZARD_PROFILE_SCHEMA,
    RATINGS_SCHEMA,
    RESILIENCE_MEASURES_SCHEMA,
    RISK_ASSESSMENT_SCHEMA,
)


# Default elevation when GroundLevelMeters is absent.
DEFAULT_ELEVATION: float = 12.0


# --- Commercial-only header extensions -------------------------------------

# Reuse the asset Header / Valuation / Construction / Location sub-sections,
# replace the residential-flavoured PropertyAttributes with commercial-only.

COMMERCIAL_TYPE_OPTIONS = ["Office", "Retail", "Hotel", "Leisure",
                           "Healthcare", "MultiFamily", "MixedUse", "Other"]

COMMERCIAL_ATTRIBUTES_SCHEMA = {
    "CommercialType": {
        "type": "menu",
        "options": COMMERCIAL_TYPE_OPTIONS,
        "description": "MSCI sector classification for the commercial asset"
    },
    "UseClassUKO": {
        "type": "string",
        "description": "UK Use Class Order code (e.g. 'E(g)(i)', 'C1', 'sui generis')"
    },
    "BusinessRatesCategory": {
        "type": "menu",
        "options": ["Shop and Premises", "Office", "Hotel", "Restaurant",
                    "Leisure", "Mixed", "Other"],
        "description": "VOA business rates category"
    },
    "OccupancyStatus": {
        "type": "menu",
        "options": ["Fully occupied", "Partially vacant", "Vacant"],
        "description": "Current occupancy status of the commercial asset"
    },
    "PropertyAreaSqm": {
        "type": "decimal",
        "description": "Gross internal area in square metres"
    },
    "NetInternalAreaSqm": {
        "type": "decimal",
        "description": "Net internal area (lettable) in square metres"
    },
    "NetLettableAreaSqm": {
        "type": "decimal",
        "description": "Net lettable area in square metres (= NIA for most assets)"
    },
    "NumberOfStoreys": {
        "type": "integer",
        "description": "Number of floors above ground"
    },
    "ConstructionYear": {
        "type": "integer",
        "description": "Year the building was constructed"
    },
    "PropertyPeriod": {
        "type": "menu",
        "options": ["Pre-1919", "1919-1944", "1945-1975", "1976-1999",
                    "2000-2008", "2009-Present"],
        "description": "Construction period classification"
    },
    "PropertyCondition": {
        "type": "menu",
        "options": ["Excellent", "Good", "Fair", "Poor", "Very poor"],
        "description": "Overall condition of property"
    },
    "TotalUnits": {
        "type": "integer",
        "description": "Number of lettable units (apartments / rooms / shops)"
    },
    "ParkingSpaces": {
        "type": "integer",
        "description": "On-site parking space count"
    },
    "LoadingBays": {
        "type": "integer",
        "description": "Service / loading bay count"
    },
    "PlantRoomLocation": {
        "type": "menu",
        "options": ["Basement", "Ground floor", "Roof", "External"],
        "description": "Primary plant room location"
    },
    "ServiceCore": {
        "type": "menu",
        "options": ["Central core", "Multiple cores", "External core", "None"],
        "description": "Service / circulation core configuration"
    },
    "LastMajorWorksDate": {
        "type": "date",
        "description": "Date of last significant refurbishment / works"
    },
}


ACCESSIBILITY_FEATURES_SCHEMA = {
    "DisabledAccess": {
        "type": "boolean",
        "description": "Compliant disabled access provision"
    },
    "GoodsLiftCount": {
        "type": "integer",
        "description": "Number of goods lifts"
    },
    "GoodsLiftCapacityKg": {
        "type": "decimal",
        "description": "Capacity of the largest goods lift in kg"
    },
    "EmergencyExits": {
        "type": "integer",
        "description": "Number of emergency exits"
    },
    "DeliveryBays": {
        "type": "integer",
        "description": "Number of delivery bays"
    },
}


TENANCY_SCHEMA = {
    "AnchorTenant": {
        "type": "string",
        "description": "Name of anchor tenant (single-tenant assets) or 'Multi-let'"
    },
    "WAULT": {
        "type": "decimal",
        "description": "Weighted Average Unexpired Lease Term in years"
    },
    "ServiceChargeGbpPerSqm": {
        "type": "decimal",
        "description": "Annual service charge in GBP per sqm of NIA"
    },
    "NetInitialYield": {
        "type": "decimal",
        "description": "Net initial yield (annual passing rent / capital value)"
    },
    "EquivalentYield": {
        "type": "decimal",
        "description": "Equivalent yield (uniform discount rate to reconcile DCF and term/reversion)"
    },
    "ReversionaryYield": {
        "type": "decimal",
        "description": "Reversionary yield (ERV / capital value)"
    },
    "CovenantStrength": {
        "type": "menu",
        "options": ["AAA", "AA", "A", "BBB", "BB", "B", "Unrated"],
        "description": "Aggregate tenant covenant strength"
    },
}


COMMERCIAL_HEADER_SCHEMA = {
    "Header": ASSET_HEADER_SCHEMA["Header"],
    "Valuation": ASSET_HEADER_SCHEMA["Valuation"],
    "CommercialAttributes": COMMERCIAL_ATTRIBUTES_SCHEMA,
    "AccessibilityFeatures": ACCESSIBILITY_FEATURES_SCHEMA,
    "Tenancy": TENANCY_SCHEMA,
    "Construction": ASSET_HEADER_SCHEMA["Construction"],
    "Location": ASSET_HEADER_SCHEMA["Location"],
    "RiskAssessment": RISK_ASSESSMENT_SCHEMA,
}


COMMERCIAL_SCHEMA = {
    "CommercialAsset": COMMERCIAL_HEADER_SCHEMA,
    "ProtectionMeasures": {
        "RiskAssessment": RATINGS_SCHEMA,
        "HazardProfile": HAZARD_PROFILE_SCHEMA,
        "ResilienceMeasures": RESILIENCE_MEASURES_SCHEMA,
    },
    "EnergyPerformance": ENERGY_PERFORMANCE_SCHEMA,
    "HistoryAndIncidents": HISTORY_AND_INCIDENTS_SCHEMA,
    "TransactionHistory": TRANSACTION_HISTORY_SCHEMA,
}
