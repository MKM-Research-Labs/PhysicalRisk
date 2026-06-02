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
CDM-to-OED Location exporter.

Converts a list of property CDM records (as produced by property.json) into an
OED v5.0.0 Location CSV file that can be fed directly into OASIS LMF.

Public API:
    cdm_to_oed_rows(properties)  — list[dict], one per property
    export_oed_csv(properties, path)  — write Location CSV to file

OED spec reference: OasisLMF/ODS_OpenExposureData v5.0.0 (2024-11).
Field mapping document: docs/oasis/cdm_oed_mapping.md (forthcoming).
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

# ---------------------------------------------------------------------------
# Lookup tables  (CDM value → OED integer code)
# ---------------------------------------------------------------------------

# OED OccupancyCode — OED v5 Chapter 3 Appendix A
# CDM OccupancyType / PropertyResi → OED 4-digit code
_OCCUPANCY_CODE: Dict[str, int] = {
    # Residential
    "Residential owner-occupied":     1000,
    "Residential rented":             1000,
    "Residential social":             1000,
    "Detached house":                 1050,
    "Semi-detached house":            1050,
    "Terraced house":                 1050,
    "Bungalow":                       1050,
    "Flat":                           1100,
    "Maisonette":                     1100,
    "Apartment":                      1100,
    "Studio":                         1100,
    # Commercial
    "Commercial":                     1150,
    "Office":                         1160,
    "Retail":                         1170,
    "Restaurant":                     1180,
    "Hotel":                          1190,
    # Industrial
    "Industrial":                     1200,
    "Warehouse":                      1210,
    "Factory":                        1210,
    "Mixed Use":                      1300,
}

# OED ConstructionCode — Chapter 3 Appendix B
# CDM ConstructionType → OED code
_CONSTRUCTION_CODE: Dict[str, int] = {
    "Brick":                     5000,
    "Stone":                     5010,
    "Concrete":                  5050,
    "Reinforced Concrete":       5055,
    "Timber frame":              5100,
    "Steel frame":               5150,
    "Steel":                     5150,
    "Masonry":                   5010,
    "Mixed":                     5999,
    "Other":                     5999,
}

# OED FoundationType — Chapter 3 Appendix C
# CDM FoundationType → OED code
_FOUNDATION_CODE: Dict[str, int] = {
    "Strip foundations":         1,
    "Pad foundations":           2,
    "Raft foundations":          3,
    "Pile foundations":          4,
    "Deep foundations":          4,
    "Basement":                  5,
    "Slab on grade":             6,
    "Unknown":                   99,
    "Other":                     99,
}

# OED BuildingCondition — CDM PropertyCondition → OED code
# OED: 1=Good, 2=Average, 3=Poor
_BUILDING_CONDITION: Dict[str, int] = {
    "Excellent":   1,
    "Good":        1,
    "Average":     2,
    "Fair":        2,
    "Poor":        3,
    "Very poor":   3,
}

# OED TerrainRoughness — CDM UrbanRuralClassification → OED
# OED: 1=Open, 2=Rural, 3=Suburban, 4=Urban, 5=Dense urban
_TERRAIN_ROUGHNESS: Dict[str, int] = {
    "Rural":         2,
    "Semi-rural":    2,
    "Suburban":      3,
    "Urban":         4,
    "Dense urban":   5,
}

# OED SoilType — CDM SoilType → OED (NEHRP site class)
# OED: 1=Rock(A/B), 2=Stiff soil(C), 3=Soft soil(D), 4=Very soft(E), 5=Mixed
_SOIL_TYPE: Dict[str, int] = {
    "Rock":          1,
    "Chalk":         1,
    "Hard":          1,
    "Gravel":        2,
    "Clay":          3,
    "Sand":          3,
    "Alluvial":      3,
    "Peat":          4,
    "Soft":          4,
    "Mixed":         5,
}

# OED SoilLiquefiable — CDM LiquefactionMitigationProvided inverse proxy
# "Not assessed" / absent → 1 (unknown); "Partial"/"Verified" → 0 (no/mitigated)
_SOIL_LIQUEFIABLE: Dict[str, int] = {
    "Not assessed":  1,
    "Partial":       0,
    "Verified":      0,
    "Enhanced":      0,
}

# OED ServiceEquipmentProtection — CDM ElectricalSystemsAboveFlood proxy
_SEP: Dict[str, int] = {
    "Not assessed":  0,
    "Partial":       1,
    "Verified":      2,
    "Enhanced":      2,
}

# OED PerilsCovered codes (bitfield-style, represented as OED string)
# Derived from CDM HazardProfile classes: None/Low/Medium/High/Extreme
_HAZARD_OASIS_CODE: Dict[str, str] = {
    "FloodHazardClass":   "WF",   # Windstorm Flood
    "WindHazardClass":    "WSS",  # Windstorm Straight-line
    "SeismicHazardClass": "QEQ",  # Earthquake
    "FireHazardClass":    "BFR",  # Bushfire
}
_HAZARD_ACTIVE_CLASSES = {"Medium", "High", "Extreme", "Very High"}

# OED RoofAnchorage proxy from roof-related CDM booleans
# "RoofRatedForDesignWind" / "RoofEdgeDetailWindResistant"
_ROOF_ANCHORAGE: Dict[str, int] = {
    "Not assessed":  1,
    "Partial":       2,
    "Verified":      3,
    "Enhanced":      3,
}

# OED WindowProtection proxy from OpeningsWindResistant
_WINDOW_PROTECTION: Dict[str, int] = {
    "Not assessed":  0,
    "Partial":       1,
    "Verified":      2,
    "Enhanced":      2,
}

# OED CladdingType proxy from CladdingRatedForDesignWind
_CLADDING: Dict[str, int] = {
    "Not assessed":  0,
    "Partial":       1,
    "Verified":      2,
    "Enhanced":      2,
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _currency() -> str:
    """ISO 4217 currency code for the active catchment (OED LocCurrency).

    Function-local import keeps oed_export importable without forcing a
    config load at module import time. Falls back to GBP defensively.
    """
    try:
        from config import config
        return config.CURRENCY
    except Exception:
        return "GBP"


def _lookup(table: Dict[str, int], key: Optional[str], default: int = 0) -> int:
    if key is None:
        return default
    return table.get(key, default)


def _lookup_str(table: Dict[str, str], key: Optional[str], default: str = "") -> str:
    if key is None:
        return default
    return table.get(key, default)


def _perils_covered(hazard_profile: dict) -> str:
    """Build the OED LocPerilsCovered string from CDM HazardProfile.

    WF (flood) is always included unless FloodHazardClass is explicitly None —
    this is a flood risk platform and every property is subject to flood modelling.
    All other perils require Medium or above to be included.
    """
    active = []
    flood_class = hazard_profile.get("FloodHazardClass")
    if flood_class not in (None, "None", ""):
        active.append("WF")
    for cdm_field, oasis_code in _HAZARD_OASIS_CODE.items():
        if oasis_code == "WF":
            continue
        val = hazard_profile.get(cdm_field)
        if val and val in _HAZARD_ACTIVE_CLASSES:
            active.append(oasis_code)
    return ";".join(active) if active else "WF"


def _street_address(location: dict) -> str:
    parts = [
        location.get("BuildingNumber", ""),
        location.get("StreetName", ""),
    ]
    return " ".join(p for p in parts if p).strip()


def _bri_user_defs(governing: dict, ref_gauges: list) -> dict:
    """Pack BRI fields into OED LocUserDef slots 1–5."""
    sub_scores = "|".join(str(governing.get(f"BRI{h}Score", "")) for h in ("Flood", "Wind", "Fire", "Seismic"))
    sub_ratings = "|".join(governing.get(f"BRI{h}Rating", "N/A") for h in ("Flood", "Wind", "Fire", "Seismic"))
    gauges = "|".join(ref_gauges[:3]) if ref_gauges else ""
    return {
        "LocUserDef1": governing.get("BRIRating", ""),
        "LocUserDef2": str(round(governing.get("BRIScore", 0.0), 4)),
        "LocUserDef3": sub_scores,
        "LocUserDef4": sub_ratings,
        "LocUserDef5": gauges,
    }


# ---------------------------------------------------------------------------
# Main converter
# ---------------------------------------------------------------------------

_OED_FIELDS = [
    "PortNumber", "AccNumber", "LocNumber", "IsTenant",
    "BuildingID", "LocName",
    "CountryCode", "Latitude", "Longitude",
    "StreetAddress", "PostalCode", "City", "State",
    "LocPerilsCovered",
    "BuildingTIV", "OtherTIV", "ContentsTIV", "BITIV",
    "LocCurrency",
    "LocGrossPremium",
    "OccupancyCode", "ConstructionCode",
    "OrgOccupancyScheme", "OrgOccupancyCode",
    "YearBuilt", "NumberOfStoreys", "NumberOfBuildings",
    "YearUpgraded",
    "FloorArea",
    "BuildingHeight", "BuildingHeightUnit",
    "GroundFloorHeight", "GroundFloorHeightUnit",
    "GroundElevation", "GroundElevationUnit",
    "FloodZone",
    "FloodDefenseHeight", "FloodDefenseHeightUnit",
    "Basement",
    "BuildingCondition",
    "FoundationType",
    "TerrainRoughness",
    "SoilType", "SoilLiquefiable",
    "ServiceEquipmentProtection",
    "RoofAnchorage", "WindowProtection", "Cladding",
    "LocUserDef1", "LocUserDef2", "LocUserDef3", "LocUserDef4", "LocUserDef5",
]


def cdm_to_oed_row(prop: dict) -> dict:
    """Convert a single property CDM record to an OED Location row dict."""
    ph = prop.get("PropertyHeader", {})
    header = ph.get("Header", {})
    valuation = ph.get("Valuation", {})
    attrs = ph.get("PropertyAttributes", {})
    construction = ph.get("Construction", {})
    location = ph.get("Location", {})
    risk = ph.get("RiskAssessment", {})
    ref_gauges = ph.get("ReferenceGauges", [])

    pm = prop.get("ProtectionMeasures", {})
    pm_risk = pm.get("RiskAssessment", {})
    governing = pm_risk.get("GoverningBodyRatings", {})
    hazard_profile = pm.get("HazardProfile", {})
    resilience = pm.get("ResilienceMeasures", {})
    building_assessment = resilience.get("BuildingAssessment", {})
    flood_protection = resilience.get("FloodProtection", {})
    site = resilience.get("SiteAndDrainage", {})

    prop_type = header.get("propertyType", "residential")
    occupancy_raw = attrs.get("OccupancyType") or attrs.get("PropertyResi") or prop_type
    construction_type = construction.get("ConstructionType", "")

    # TIV — use PropertyValue; contents/other not held in CDM
    tiv = float(valuation.get("PropertyValue") or 0.0)

    # FloodDefenseHeight — boolean gates → 1.0 m proxy when present
    has_flood_defense = (
        flood_protection.get("PermanentFloodProofingAtEntries") not in (None, "Not assessed", "")
        or flood_protection.get("DeployableBarriersProvided") not in (None, "Not assessed", "")
    )

    # YearUpgraded — extract year from LastMajorWorksDate (ISO date string)
    last_works = attrs.get("LastMajorWorksDate", "")
    year_upgraded = int(last_works[:4]) if last_works and len(last_works) >= 4 else ""

    row: Dict[str, Any] = {
        "PortNumber":    1,
        "AccNumber":     header.get("CatchmentID", ""),
        "LocNumber":     header.get("PropertyID", ""),
        "IsTenant":      0,
        "BuildingID":    header.get("UPRN", ""),
        "LocName":       _street_address(location),
        "CountryCode":   "GB",
        "Latitude":      location.get("LatitudeDegrees", ""),
        "Longitude":     location.get("LongitudeDegrees", ""),
        "StreetAddress": _street_address(location),
        "PostalCode":    location.get("Postcode", ""),
        "City":          location.get("TownCity", ""),
        "State":         location.get("County", ""),
        "LocPerilsCovered": _perils_covered(hazard_profile),
        "BuildingTIV":   tiv,
        "OtherTIV":      0.0,
        "ContentsTIV":   0.0,
        "BITIV":         0.0,
        "LocCurrency":   _currency(),
        "LocGrossPremium": float(
            prop.get("TransactionHistory", {}).get("Insurance", {}).get("InsurancePremium") or 0.0
        ),
        "OccupancyCode":    _lookup(_OCCUPANCY_CODE, occupancy_raw, 1000),
        "ConstructionCode": _lookup(_CONSTRUCTION_CODE, construction_type, 5999),
        "OrgOccupancyScheme": "MKM-CDM",
        "OrgOccupancyCode":   occupancy_raw,
        "YearBuilt":        attrs.get("ConstructionYear", ""),
        "NumberOfStoreys":  attrs.get("NumberOfStoreys", ""),
        "NumberOfBuildings": 1,
        "YearUpgraded":     year_upgraded,
        "FloorArea":        attrs.get("PropertyAreaSqm", ""),
        "BuildingHeight":     attrs.get("HeightMeters", ""),
        "BuildingHeightUnit": "M",
        "GroundFloorHeight":     max(0.0, float(construction.get("FloorLevelMeters") or 0.0)),
        "GroundFloorHeightUnit": "M",
        "GroundElevation":     risk.get("GroundLevelMeters", ""),
        "GroundElevationUnit": "M",
        "FloodZone":          risk.get("EAFloodZone", ""),
        "FloodDefenseHeight":     1.0 if has_flood_defense else 0.0,
        "FloodDefenseHeightUnit": "M",
        "Basement":           1 if construction.get("BasementPresent") else 0,
        "BuildingCondition":  _lookup(_BUILDING_CONDITION, attrs.get("PropertyCondition"), 2),
        "FoundationType":     _lookup(_FOUNDATION_CODE, construction.get("FoundationType"), 99),
        "TerrainRoughness":   _lookup(_TERRAIN_ROUGHNESS, location.get("UrbanRuralClassification"), 3),
        "SoilType":           _lookup(_SOIL_TYPE, risk.get("SoilType"), 5),
        "SoilLiquefiable":    _lookup(_SOIL_LIQUEFIABLE, site.get("LiquefactionMitigationProvided"), 1),
        "ServiceEquipmentProtection": _lookup(_SEP, flood_protection.get("ElectricalSystemsAboveFlood"), 0),
        "RoofAnchorage":     _lookup(_ROOF_ANCHORAGE, building_assessment.get("RoofRatedForDesignWind"), 1),
        "WindowProtection":  _lookup(_WINDOW_PROTECTION, building_assessment.get("OpeningsWindResistant"), 0),
        "Cladding":          _lookup(_CLADDING, building_assessment.get("CladdingRatedForDesignWind"), 0),
    }

    row.update(_bri_user_defs(governing, ref_gauges))
    return row


def cdm_to_oed_rows(properties: Iterable[dict]) -> List[dict]:
    """Convert an iterable of property CDM records to a list of OED Location rows."""
    return [cdm_to_oed_row(p) for p in properties]


def export_oed_csv(
    properties: Iterable[dict],
    path: Optional[Path | str] = None,
) -> str:
    """Write OED Location CSV.

    Args:
        properties: Iterable of property CDM records.
        path: Output file path.  If None, returns the CSV as a string.

    Returns:
        The CSV content as a string (regardless of whether ``path`` was given).
    """
    rows = cdm_to_oed_rows(properties)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_OED_FIELDS, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    content = buf.getvalue()

    if path is not None:
        Path(path).write_text(content, encoding="utf-8")

    return content
