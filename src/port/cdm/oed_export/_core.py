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

from port.cdm.oed_export._lookups import (
    _BUILDING_CONDITION,
    _CLADDING,
    _CONSTRUCTION_CODE,
    _FOUNDATION_CODE,
    _OCCUPANCY_CODE,
    _ROOF_ANCHORAGE,
    _SEP,
    _SOIL_LIQUEFIABLE,
    _SOIL_TYPE,
    _TERRAIN_ROUGHNESS,
    _WINDOW_PROTECTION,
)
from port.cdm.oed_export._helpers import (
    _bri_user_defs,
    _currency,
    _lookup,
    _perils_covered,
    _street_address,
)

__all__ = [
    "cdm_to_oed_row",
    "cdm_to_oed_rows",
    "export_oed_csv",
]


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
