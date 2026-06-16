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
CDM boundary adapter for the fire model.

Extracts an :class:`AssetFireFeatures` bundle from a commercial-asset CDM
record (the dict shape produced by the commercial portfolio generator and
persisted in ``commercial.json``). The fire model reads only the bundle, never
the raw CDM, so the CDM schema can evolve independently.

Resilience inputs are resolved in two tiers:

1. The granular CDM fire checklist
   (``ProtectionMeasures.ResilienceMeasures.{FireProtection, BuildingAssessment,
   ContinuityMeasures}``) when populated — these carry RESILIENCE_LEVELS values
   directly.
2. Otherwise the asset's BRI fire **grade** (A or B), the only fire-resilience
   signal the commercial generator writes today. The grade is read from
   ``BRIFireRating`` when present, else inferred from the applied ``FireCodes``
   measure list (the hotel-only differentiator FI09 marks Grade A; any other
   fire-code package is Grade B). The grade maps to a single resilience level
   applied across the fire-relevant fields:

       Grade A -> "Enhanced"   (clears the internal-sprinkler reach threshold)
       Grade B -> "Partial"    (below it: above the fire-truck reach a Grade-B
                                 high-rise has no effective internal suppression
                                 and runs to the point of no return)
       unknown -> None         (treated as the worst level by Model C)

   This Grade-B -> "Partial" choice is a deliberate modelling decision (the
   fire-truck-reach incident the BRI source described): it makes building height
   the live driver for the high-rise commercial portfolio.

Independently of the BRI grade, the asset's structural frame material
(``Construction.ConstructionType``) is read into ``construction_type``. It is
the physical signal the fire model uses for (a) the structural-fire-resistance
fallback (``CONSTRUCTION_TO_STRUCTURAL_LEVEL``, used when the granular checklist
is silent and taking priority over the grade fallback for that one field) and
(b) the structure's combustibility, resolved downstream in the fire model. A
non-combustible frame (reinforced concrete, steel) resists a full conflagration
even above the fire-service reach, so building material — not height alone —
governs the high-rise conflagration leg.
"""

from typing import List, Optional

from models.fire.data_structures import AssetFireFeatures

__all__ = [
    "GRADE_TO_LEVEL",
    "CONSTRUCTION_TO_STRUCTURAL_LEVEL",
    "FIRE_GRADE_A_CODE",
    "commercial_fire_grade",
    "commercial_features_from_record",
    "commercial_portfolio_features",
]


# Grade -> resilience level applied across the fire-relevant fields when the
# granular CDM checklist is absent. See the module docstring for the rationale.
GRADE_TO_LEVEL = {"A": "Enhanced", "B": "Partial"}

# ConstructionType -> StructuralFireResistanceAdequate fallback level. The CDM
# checklist field is "Primary structural frame has fire-resistance ratings
# appropriate to building type and code", so the structural frame material is
# the physical signal for it. Used only when the granular checklist does not
# carry an explicit StructuralFireResistanceAdequate value; takes priority over
# the BRI-grade fallback (grade A/B is an active-protection signal, not a
# structural one). An unknown / missing construction type returns None so the
# adapter defers to the grade fallback. The combustibility of the frame (which
# drives the conflagration leg) is resolved separately in the fire model from
# config.fire construction.combustibility_by_type.
CONSTRUCTION_TO_STRUCTURAL_LEVEL = {
    "Reinforced concrete": "Verified",
    "Concrete frame": "Verified",
    "Steel frame": "Enhanced",
    "Brick and block": "Enhanced",
    "Masonry": "Enhanced",
    "Stone": "Enhanced",
    "Modern methods": "Meets minimum",
    "Mixed construction": "Partial",
    "Timber frame": "Partial",
}

# The hotel-only BRI fire measure that elevates the fire grade to A
# (port.rand.halong.commercial.bri_codes.HOTEL_FIRE_EXTRA).
FIRE_GRADE_A_CODE = "FI09"

# BRIFireRating menu values that count as the A tier vs the B tier.
_A_TIER_RATINGS = {"AA", "AA+", "A", "A+"}
_B_TIER_RATINGS = {"B", "B+"}


def _as_dict(obj) -> dict:
    """Return *obj* if it is a dict, else an empty dict (defensive accessor)."""
    return obj if isinstance(obj, dict) else {}


def _commercial_body(record: dict) -> dict:
    """The ``CommercialAsset`` body, tolerating an already-unwrapped record."""
    body = record.get("CommercialAsset")
    return body if isinstance(body, dict) else record


def _governing_body_ratings(record: dict) -> dict:
    return _as_dict(
        _as_dict(_as_dict(record.get("ProtectionMeasures")).get("RiskAssessment"))
        .get("GoverningBodyRatings")
    )


def _resilience_measures(record: dict) -> dict:
    return _as_dict(
        _as_dict(record.get("ProtectionMeasures")).get("ResilienceMeasures")
    )


def commercial_fire_grade(record: dict) -> Optional[str]:
    """Resolve the BRI fire grade ("A" / "B") for a commercial record.

    Prefers the explicit ``BRIFireRating`` sub-rating; falls back to the applied
    ``FireCodes`` list (FI09 present -> Grade A, any other fire package ->
    Grade B). Returns None when no fire-resilience signal is present.
    """
    gb = _governing_body_ratings(record)

    rating = gb.get("BRIFireRating")
    if rating in _A_TIER_RATINGS:
        return "A"
    if rating in _B_TIER_RATINGS:
        return "B"

    codes = _as_dict(gb.get("IndustryGroups")).get("FireCodes")
    if isinstance(codes, list) and codes:
        return "A" if FIRE_GRADE_A_CODE in codes else "B"

    return None


def _level(checklist: dict, field: str, fallback: Optional[str]) -> Optional[str]:
    """Granular checklist value for *field* if usefully populated, else fallback.

    A field that is missing, empty, or the sentinel "Not assessed" carries no
    information, so we defer to the grade-derived fallback in that case.
    """
    value = checklist.get(field)
    if value and value != "Not assessed":
        return value
    return fallback


def commercial_features_from_record(record: dict) -> Optional[AssetFireFeatures]:
    """Build an :class:`AssetFireFeatures` from one commercial CDM record.

    Returns None when the record carries no asset id or commercial type (it
    cannot be modelled and is skipped by the portfolio builder).
    """
    body = _commercial_body(record)
    header = _as_dict(body.get("Header"))
    attrs = _as_dict(body.get("CommercialAttributes"))
    construction = _as_dict(body.get("Construction"))

    asset_id = header.get("PropertyID") or header.get("UPRN")
    commercial_type = attrs.get("CommercialType")
    if not asset_id or not commercial_type:
        return None

    grade = commercial_fire_grade(record)
    grade_level = GRADE_TO_LEVEL.get(grade)

    # The structural frame material is the physical signal for structural
    # fire resistance; it takes priority over the grade fallback for that one
    # field. ConstructionType lives in the shared asset Construction sub-section.
    construction_type = construction.get("ConstructionType")
    structural_level = CONSTRUCTION_TO_STRUCTURAL_LEVEL.get(construction_type)

    rm = _resilience_measures(record)
    fire_protection = _as_dict(rm.get("FireProtection"))
    building = _as_dict(rm.get("BuildingAssessment"))
    continuity = _as_dict(rm.get("ContinuityMeasures"))

    fire_incidents = _as_dict(
        _as_dict(record.get("HistoryAndIncidents")).get("FireIncidents")
    )

    storeys = attrs.get("NumberOfStoreys")

    return AssetFireFeatures(
        asset_id=asset_id,
        commercial_type=commercial_type,
        construction_type=construction_type,
        occupancy_status=attrs.get("OccupancyStatus"),
        business_rates_category=attrs.get("BusinessRatesCategory"),
        property_condition=attrs.get("PropertyCondition"),
        automatic_detection_level=_level(
            fire_protection, "AutomaticDetectionInstalled", grade_level),
        suppression_systems_level=_level(
            fire_protection, "SuppressionSystemsInstalled", grade_level),
        emergency_procedures_level=_level(
            continuity, "EmergencyProceduresTested", grade_level),
        structural_fire_resistance_level=_level(
            building, "StructuralFireResistanceAdequate",
            structural_level or grade_level),
        compartments_level=_level(
            building, "CompartmentsProvided", grade_level),
        fire_stopping_level=_level(
            building, "FireStoppingAtPenetrations", grade_level),
        external_materials_level=_level(
            building, "ExternalMaterialsFireResistant", grade_level),
        access_route_level=_level(
            continuity, "AccessRouteResilient", grade_level),
        business_continuity_level=_level(
            continuity, "BusinessContinuityPlanInPlace", grade_level),
        fire_damage_severity=fire_incidents.get("FireDamageSeverity"),
        years_since_last_fire=None,
        number_of_storeys=int(storeys) if isinstance(storeys, (int, float)) else None,
    )


def commercial_portfolio_features(records: List[dict]) -> List[AssetFireFeatures]:
    """Map a list of commercial CDM records to AssetFireFeatures.

    Records that cannot be modelled (no id / no commercial type) are skipped.
    """
    features: List[AssetFireFeatures] = []
    for record in records:
        feat = commercial_features_from_record(record)
        if feat is not None:
            features.append(feat)
    return features
