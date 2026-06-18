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

"""Flood-spec scoring functions — aggregate per-measure compliance into the
spec's 1-100 resilience score, derive the damage modifier, and stamp the five
BRI score fields onto a property record."""

import random
from typing import Any, Dict, Optional

from .flood_constants import (
    FLOOD_SPEC_BASE_WEIGHTS, FLOOD_SPEC_REGIME_MULTIPLIERS,
    FLOOD_SPEC_ALPHA_BY_REGIME, REGIME_FROM_FLOOD_RISK_TYPE, DEFAULT_REGIME,
)
from .flood_compliance import compute_compliance, _apply_soft_caps, _get


def compute_flood_resilience_score(
    property_record: Dict[str, Any],
    regime: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute the spec's flood resilience score for a property.

    Args:
        property_record: Full nested property CDM record.
        regime: Override the regime; if omitted, derived from
            ``PropertyHeader.RiskAssessment.FloodRiskType``.

    Returns:
        ``{
            "score_raw":   float,  # 0-100, pre-cap
            "score_final": float,  # 1-100, post-cap, regime-adjusted
            "regime":      str,
            "compliance":  {measure_code: float},
        }``
    """
    if regime is None:
        flood_type = _get(property_record, [
            "PropertyHeader", "RiskAssessment", "FloodRiskType",
        ])
        regime = REGIME_FROM_FLOOD_RISK_TYPE.get(flood_type, DEFAULT_REGIME)
    if regime not in FLOOD_SPEC_REGIME_MULTIPLIERS:
        regime = DEFAULT_REGIME

    compliance: Dict[str, float] = {}
    weighted_sum = 0.0
    weight_total = 0.0
    multipliers = FLOOD_SPEC_REGIME_MULTIPLIERS[regime]
    for code, base_w in FLOOD_SPEC_BASE_WEIGHTS.items():
        c = compute_compliance(code, property_record)
        compliance[code] = round(c, 4)
        w = base_w * multipliers[code]
        weighted_sum += w * c
        weight_total += w

    s_raw = 100.0 * weighted_sum / weight_total if weight_total else 0.0
    s_raw = max(0.0, min(100.0, s_raw))
    s_final = _apply_soft_caps(s_raw, compliance, regime)

    return {
        "score_raw":   round(s_raw, 4),
        "score_final": round(s_final, 4),
        "regime":      regime,
        "compliance":  compliance,
    }


def damage_modifier(score_final: float, regime: str) -> float:
    """M(S, r) = 1 - α_r × (S - 1) / 99. Returns 1.0 at S=1, (1-α) at S=100."""
    alpha = FLOOD_SPEC_ALPHA_BY_REGIME.get(regime, FLOOD_SPEC_ALPHA_BY_REGIME["fluvial"])
    return round(1.0 - alpha * ((score_final - 1.0) / 99.0), 4)


def apply_flood_resilience_score(
    property_record: Dict[str, Any],
    jitter_band: float = 0.05,
    *,
    bri_scores_enabled: bool = True,
) -> Dict[str, Any]:
    """Compute the flood resilience score for the property and write the
    five BRI score fields into ``GoverningBodyRatings``.

    Storage convention: scores are persisted on the 0-1 scale (matching the
    schema's BRIFloodScore description). The spec's 1-100 ``score_final`` is
    divided by 100 before storage. Non-flood hazard scores are jittered copies
    of the flood score within ±``jitter_band`` on the 0-1 scale (default ±0.05
    = ±5 on the spec's 1-100 scale, per the design directive).

    The overall BRIScore is the mean of the four per-hazard scores.

    ``bri_scores_enabled`` is forwarded by the catchment shim from its local
    ``BRI_SCORES_ENABLED`` flag. When False, the five numeric BRIScore fields
    are stamped 0.0 and no BRI-driven floor uplift is applied (the catchment
    does not own a certified BRI regime).

    Returns the full model output dict (raw, final, regime, compliance,
    modifier) for inspection.
    """
    result = compute_flood_resilience_score(property_record)
    modifier = damage_modifier(result["score_final"], result["regime"])

    flood_score = round(result["score_final"] / 100.0, 4)

    pm = property_record.setdefault("ProtectionMeasures", {})
    ra = pm.setdefault("RiskAssessment", {})
    gbr = ra.setdefault("GoverningBodyRatings", {})

    if not bri_scores_enabled:
        # Catchment disables numeric BRI: stamp every score 0.0 and apply no
        # BRI-driven floor uplift (flood filter falls back to raw floor level).
        for field in ("BRIFloodScore", "BRIWindScore", "BRIFireScore",
                      "BRISeismicScore", "BRIScore"):
            gbr[field] = 0.0
        return {
            **result,
            "damage_modifier": modifier,
        }

    # Property-keyed RNG so jitter is deterministic for a given property ID.
    property_id = _get(property_record, ["PropertyHeader", "Header", "PropertyID"], "X")
    rng = random.Random(hash(property_id) % (2**32))

    gbr["BRIFloodScore"] = flood_score
    for hazard in ("Wind", "Fire", "Seismic"):
        score = max(0.01, min(1.0, flood_score + rng.uniform(-jitter_band, jitter_band)))
        gbr[f"BRI{hazard}Score"] = round(score, 4)

    gbr["BRIScore"] = round(
        (gbr["BRIFloodScore"] + gbr["BRIWindScore"]
         + gbr["BRIFireScore"] + gbr["BRISeismicScore"]) / 4.0,
        4,
    )

    # Stamp the BRI-adjusted flood-threshold floor level into Construction.
    # A resilient building only counts as flooded once water rises above this
    # raised floor; the PRS flood filter reads this field. Computed from the
    # 0-1 BRIFloodScore just written above. If the surveyed FloorLevelMeters is
    # missing, leave the field unset — the flood code falls back to deriving it
    # from BRIFloodScore at evaluation time.
    from models.floodrisk.depth_damage import bri_adjusted_floor_level
    construction = property_record.setdefault("PropertyHeader", {}).setdefault(
        "Construction", {})
    floor_level = construction.get("FloorLevelMeters")
    if floor_level is not None:
        try:
            construction["BRIAdjustedFloorLevelMeters"] = round(
                bri_adjusted_floor_level(float(floor_level), flood_score), 2)
        except (TypeError, ValueError):
            pass

    return {
        **result,
        "damage_modifier": modifier,
    }
