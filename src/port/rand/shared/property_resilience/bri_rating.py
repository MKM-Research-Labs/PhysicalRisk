# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""BRI letter-rating functions — section/hazard scoring, rating aggregation,
distribution summaries, threshold recalibration, and weight validation."""

from typing import Any, Dict, Iterable, List, Optional

from .bri_constants import (
    SECTION_WEIGHTS, FIELD_WEIGHTS, RESILIENCE_LEVEL_CREDIT,
    BASEMENT_FLOOD_STRATEGY_CREDIT, RATING_THRESHOLDS, RATING_ORDER,
    HAZARD_RELEVANT_FIELDS, CONTINUITY_PLUS_THRESHOLD,
    TARGET_DISTRIBUTION_THAMES,
)


def _field_credit(field: str, value: Any) -> float:
    """Return 0.0-1.0 credit for a single checklist value.

    Recognised value types:
      - 5-level resilience enum string ("Not assessed".."Verified")
      - BasementFloodStrategy enum (different vocabulary)
      - Legacy boolean (still credited 1.0 / 0.0 for back-compat)
    """
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if field == "BasementFloodStrategy":
        return BASEMENT_FLOOD_STRATEGY_CREDIT.get(value, 0.0)
    if value in RESILIENCE_LEVEL_CREDIT:
        return RESILIENCE_LEVEL_CREDIT[value]
    return 0.0


def score_section(section_name: str, section_data: Dict[str, Any]) -> float:
    """Weighted points-achieved / points-possible for one resilience sub-section."""
    if not section_data:
        return 0.0
    field_weights = FIELD_WEIGHTS.get(section_name, {})
    possible = 0.0
    achieved = 0.0
    for field, value in section_data.items():
        w = field_weights.get(field, 1.0)
        possible += w
        achieved += w * _field_credit(field, value)
    return achieved / possible if possible else 0.0


def _map_score_to_rating(score: float) -> str:
    if score >= RATING_THRESHOLDS["AA"]:
        return "AA"
    if score >= RATING_THRESHOLDS["A"]:
        return "A"
    if score >= RATING_THRESHOLDS["B"]:
        return "B"
    return "NR"


def _flatten_resilience(resilience: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten the nested resilience dict to {field_name: value} for hazard scoring."""
    flat: Dict[str, Any] = {}
    for sub in resilience.values():
        if isinstance(sub, dict):
            flat.update(sub)
    return flat


def score_hazard(hazard: str, resilience: Dict[str, Any]) -> float:
    """Weighted 0-1 score for the resilience fields relevant to one hazard."""
    fields = HAZARD_RELEVANT_FIELDS.get(hazard, [])
    if not fields:
        return 0.0
    flat = _flatten_resilience(resilience)
    all_field_weights: Dict[str, float] = {}
    for section_weights in FIELD_WEIGHTS.values():
        all_field_weights.update(section_weights)
    possible = 0.0
    achieved = 0.0
    for field in fields:
        w = all_field_weights.get(field, 1.0)
        possible += w
        achieved += w * _field_credit(field, flat.get(field))
    return achieved / possible if possible else 0.0


def compute_bri_rating(
    resilience_measures: Dict[str, Any],
    hazard_profile: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Aggregate a property's resilience checklist into a BRI rating.

    Returns ``{rating, score, section_scores, hazard_ratings, hazard_scores}``.
    Overall letter is the weakest of the applicable hazard sub-ratings
    (HazardClass == "None" makes a hazard non-applicable). A "+" suffix is
    appended when continuity is strong and overall is not NR.
    """
    section_scores: Dict[str, float] = {}
    weighted_total = 0.0
    weight_used = 0.0
    for section, weight in SECTION_WEIGHTS.items():
        s = score_section(section, resilience_measures.get(section, {}))
        section_scores[section] = s
        weighted_total += weight * s
        weight_used += weight
    overall_score = weighted_total / weight_used if weight_used else 0.0

    hazard_profile = hazard_profile or {}
    hazard_ratings: Dict[str, str] = {}
    hazard_scores: Dict[str, Any] = {}
    applicable_letters: list = []
    for hazard in ("Flood", "Wind", "Fire", "Seismic"):
        hazard_class = hazard_profile.get(f"{hazard}HazardClass")
        if hazard_class == "None":
            hazard_ratings[hazard] = "N/A"
            hazard_scores[hazard] = None
            continue
        s = score_hazard(hazard, resilience_measures)
        hazard_scores[hazard] = round(s, 4)
        letter = _map_score_to_rating(s)
        hazard_ratings[hazard] = letter
        applicable_letters.append(letter)

    if applicable_letters:
        worst_idx = max(RATING_ORDER.index(l) for l in applicable_letters)
        overall_letter = RATING_ORDER[worst_idx]
    else:
        overall_letter = _map_score_to_rating(overall_score)

    if (
        overall_letter != "NR"
        and section_scores.get("ContinuityMeasures", 0.0) >= CONTINUITY_PLUS_THRESHOLD
    ):
        overall_letter = overall_letter + "+"

    return {
        "rating": overall_letter,
        "score": round(overall_score, 4),
        "section_scores": {k: round(v, 4) for k, v in section_scores.items()},
        "hazard_ratings": hazard_ratings,
        "hazard_scores": hazard_scores,
    }


def distribution_summary(
    ratings: Iterable[str],
    target: Dict[str, float] = None,
) -> Dict[str, Dict[str, float]]:
    """Compare actual rating distribution vs. target. Returns per-rating
    {actual, target, delta} dict."""
    target = target or TARGET_DISTRIBUTION_THAMES
    ratings = list(ratings)
    total = len(ratings) or 1
    counts = {r: 0 for r in RATING_ORDER}
    for r in ratings:
        if r in counts:
            counts[r] += 1
    return {
        r: {
            "actual": counts[r] / total,
            "target": target.get(r, 0.0),
            "delta":  counts[r] / total - target.get(r, 0.0),
        }
        for r in RATING_ORDER
    }


def recalibrate_thresholds_from_scores(
    scores: List[float],
    target: Dict[str, float] = None,
) -> Dict[str, float]:
    """Derive score thresholds that reproduce the target distribution."""
    target = target or TARGET_DISTRIBUTION_THAMES
    if not scores:
        return dict(RATING_THRESHOLDS)
    ranked = sorted(scores, reverse=True)
    n = len(ranked)
    aa_idx = max(0, int(round(target["AA"] * n)) - 1)
    a_idx = max(0, int(round((target["AA"] + target["A"]) * n)) - 1)
    b_idx = max(0, int(round((target["AA"] + target["A"] + target["B"]) * n)) - 1)
    return {"AA": ranked[aa_idx], "A": ranked[a_idx], "B": ranked[b_idx]}


def validate_weights(section_weights: Optional[Dict[str, float]] = None) -> None:
    """Raise ``ValueError`` if the section weights do not sum to 1.0.

    ``section_weights`` lets a catchment shim pass its own (possibly
    monkeypatched) ``SECTION_WEIGHTS`` so the check observes that module's
    rebound value; defaults to this module's ``SECTION_WEIGHTS``.
    """
    weights = SECTION_WEIGHTS if section_weights is None else section_weights
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(
            f"SECTION_WEIGHTS sum to {total:.6f}, expected 1.0. "
            f"Adjust weights in resilience.py."
        )
