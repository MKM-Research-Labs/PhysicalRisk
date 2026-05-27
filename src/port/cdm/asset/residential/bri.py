# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
BRI rating helper for Residential Asset CDM records.

Reads ``ProtectionMeasures.ResilienceMeasures`` from a property record, runs
the weighted-checklist aggregation defined in
``port.rand.thames.property.property_random.resilience``,
and writes the result into ``ProtectionMeasures.RiskAssessment.GoverningBodyRatings``.

This keeps the CDM utility-agnostic (no BRI logic in the schema) while giving
generators and downstream tools a one-call way to populate the rating.
"""

from datetime import date
from typing import Any, Dict, Optional

from port.rand.thames.property.property_random.resilience import compute_bri_rating

_DEFAULT_VERSION = "BRI v1.6"


def apply_bri_rating(
    property_record: Dict[str, Any],
    *,
    version: str = _DEFAULT_VERSION,
    agent: Optional[str] = None,
    rating_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Score a property's resilience checklist and stamp the BRI rating in place.

    Args:
        property_record: Full nested property CDM record. Mutated in place.
        version: BRI methodology version string to record (e.g. "BRI v1.6").
        agent: Verifier/certifier that issued the rating (e.g. "Bureau Veritas").
        rating_date: ISO date the rating was assigned; defaults to today.

    Returns:
        The aggregation result from ``compute_bri_rating``:
        ``{"rating": str, "score": float, "section_scores": {section: float}}``.
        The rating is also written to
        ``property_record["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]``.
    """
    pm = property_record.get("ProtectionMeasures", {})
    resilience = pm.get("ResilienceMeasures", {})
    hazard_profile = pm.get("HazardProfile", {})

    result = compute_bri_rating(resilience, hazard_profile=hazard_profile)

    pm = property_record.setdefault("ProtectionMeasures", {})
    ra = pm.setdefault("RiskAssessment", {})
    gbr = ra.setdefault("GoverningBodyRatings", {})
    # BRI *score* fields (BRIScore + per-hazard *Score) are deliberately NOT
    # written here — they are reserved for a forthcoming methodology model.
    # This helper only stamps the letter ratings and rating metadata.
    gbr["BRIRating"] = result["rating"]
    hazard_ratings = result.get("hazard_ratings", {})
    for hazard in ("Flood", "Wind", "Fire", "Seismic"):
        gbr[f"BRI{hazard}Rating"] = hazard_ratings.get(hazard, "N/A")
    gbr["BRIDate"] = rating_date or date.today().isoformat()
    gbr["BRIRatingVersion"] = version
    if agent is not None:
        gbr["BRIRatingAgent"] = agent

    return result
