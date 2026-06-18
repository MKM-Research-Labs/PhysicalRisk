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

# Ordering from strongest to weakest. Used to combine Water + Flash sub-ratings
# into the overall BRIFloodRating envelope as min(Water, Flash).
_RATING_ORDER = ["AA", "A", "B", "NR", "N/A"]


def _weaker_rating(a: Optional[str], b: Optional[str]) -> Optional[str]:
    """Return whichever of (a, b) is the weaker BRI letter (higher index)."""
    if a is None:
        return b
    if b is None:
        return a
    try:
        return a if _RATING_ORDER.index(a) >= _RATING_ORDER.index(b) else b
    except ValueError:
        return b if a == "N/A" else a


def apply_bri_rating(
    property_record: Dict[str, Any],
    *,
    version: str = _DEFAULT_VERSION,
    agent: Optional[str] = None,
    rating_date: Optional[str] = None,
    publish_letter_ratings: bool = True,
) -> Dict[str, Any]:
    """Score a property's resilience checklist and stamp the BRI rating in place.

    Args:
        property_record: Full nested property CDM record. Mutated in place.
        version: BRI methodology version string to record (e.g. "BRI v1.6").
        agent: Verifier/certifier that issued the rating (e.g. "Bureau Veritas").
        rating_date: ISO date the rating was assigned; defaults to today.
        publish_letter_ratings: When True (default) the computed per-hazard +
            overall letter grades are written. When False the catchment has no
            certified BRI letter-rating regime, so every letter field is stamped
            ``"NR"`` (No Rating) — the numeric ``BRI*Score`` fields written by
            ``apply_flood_resilience_score`` are unaffected, so resilience-driven
            pricing (BRI-adjusted floor) still works. Driven by the per-catchment
            ``PUBLISH_BRI_LETTER_RATINGS`` flag on the resilience module.

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
    if not publish_letter_ratings:
        # Catchment has no certified BRI letter-rating regime: report "NR"
        # (No Rating) for every letter grade. Scores are written elsewhere.
        for field in ("BRIRating", "BRIWindRating", "BRIFireRating",
                      "BRISeismicRating", "BRIFloodRating"):
            gbr[field] = "NR"
    else:
        gbr["BRIRating"] = result["rating"]
        hazard_ratings = result.get("hazard_ratings", {})
        for hazard in ("Wind", "Fire", "Seismic"):
            gbr[f"BRI{hazard}Rating"] = hazard_ratings.get(hazard, "N/A")

        # Water / Flash sub-ratings — only present once the scorer splits flood
        # (Phase 2). When both are present, BRIFloodRating becomes the envelope
        # = weakest of (Water, Flash). When neither is present, fall back to the
        # legacy flat "Flood" rating from the scorer.
        water_rating = hazard_ratings.get("Water")
        flash_rating = hazard_ratings.get("Flash")
        if water_rating is not None:
            gbr["BRIWaterRating"] = water_rating
        if flash_rating is not None:
            gbr["BRIFlashRating"] = flash_rating
        if water_rating is not None or flash_rating is not None:
            gbr["BRIFloodRating"] = _weaker_rating(water_rating, flash_rating) or "N/A"
        else:
            gbr["BRIFloodRating"] = hazard_ratings.get("Flood", "N/A")

    gbr["BRIDate"] = rating_date or date.today().isoformat()
    gbr["BRIRatingVersion"] = version
    if agent is not None:
        gbr["BRIRatingAgent"] = agent

    return result
