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

"""Raw hazard exposure facts and normalised hazard-class schemas."""

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
    "WindThresholdMajorMps": {
        "type": "decimal",
        "description": "Operational peak sustained wind (m/s) the property can withstand "
                       "with Grade-A wind protection; consumed as the 50%-damage threshold "
                       "(v_50) by the wind damage model. SE-Asia commercial Grade-A ~ 69.4 m/s "
                       "(250 km/h). Replaces the legacy WindThresholdKph (still readable as a "
                       "deprecated alias = MajorMps x 3.6)."
    },
    "WindThresholdMinorMps": {
        "type": "decimal",
        "description": "Operational peak sustained wind (m/s) the property can withstand "
                       "with Grade-B wind protection. SE-Asia commercial Grade-B ~ 55.6 m/s "
                       "(200 km/h). Used as the lower bound of the wind-damage curve."
    },
    "WaterThresholdMajorM": {
        "type": "decimal",
        "description": "Water (tsunami/storm-surge) overtopping height the property can "
                       "withstand with Grade-A protection, in metres above the local gauge "
                       "SevereFloodWarning level. SE-Asia commercial Grade-A = 10 m."
    },
    "WaterThresholdMinorM": {
        "type": "decimal",
        "description": "Water (tsunami/storm-surge) overtopping height the property can "
                       "withstand with Grade-B protection, in metres above the local gauge "
                       "SevereFloodWarning level. SE-Asia commercial Grade-B = 5 m."
    },
    "FlashThresholdMajorM": {
        "type": "decimal",
        "description": "Flash-flood / fluvial overtopping height the property can withstand "
                       "with Grade-A protection, in metres above the local gauge "
                       "SevereFloodWarning level. SE-Asia commercial Grade-A = 5 m."
    },
    "FlashThresholdMinorM": {
        "type": "decimal",
        "description": "Flash-flood / fluvial overtopping height the property can withstand "
                       "with Grade-B protection, in metres above the local gauge "
                       "SevereFloodWarning level. SE-Asia commercial Grade-B = 3 m."
    },
    "WindThresholdKph": {
        "type": "decimal",
        "description": "DEPRECATED: legacy single-grade wind threshold in km/h. Retained "
                       "as a read-only alias = WindThresholdMajorMps x 3.6 so existing "
                       "fixtures and the wind damage model continue to resolve. New writers "
                       "MUST populate WindThresholdMajorMps / WindThresholdMinorMps instead."
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
