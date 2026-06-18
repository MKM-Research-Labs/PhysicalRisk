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

"""Resilience generator functions — synthesise a property's resilience
checklist from period/condition/zone priors, plus a sanity-check sampler."""

import random
from typing import Any, Dict, List, Optional

from .generator_constants import (
    _PERIOD_BASE_PROB, _DEFAULT_PERIOD_PROB, _CONDITION_MULTIPLIER,
    _DEFAULT_CONDITION_MULT, _MODERN_ONLY_FIELDS, _FLOOD_PROTECTION_FIELDS,
    _FLOOD_ZONE_UPLIFT, _ALWAYS_LIKELY_TRUE, SECTION_FIELDS,
)
from .bri_rating import compute_bri_rating, distribution_summary


def _level_from_score(score: float) -> str:
    """Map a 0-1 propensity score to one of the 5 resilience levels.

    Bucket boundaries: 0-0.2 Not assessed, 0.2-0.4 Partial, 0.4-0.6 Meets minimum,
    0.6-0.8 Enhanced, 0.8-1.0 Verified.
    """
    if score < 0.20: return "Not assessed"
    if score < 0.40: return "Partial"
    if score < 0.60: return "Meets minimum"
    if score < 0.80: return "Enhanced"
    return "Verified"


def _field_probability(
    field: str,
    base: float,
    cond_mult: float,
    flood_uplift: float,
    is_modern_period: bool,
) -> float:
    """Per-field True-probability after applying period/condition/zone modifiers."""
    p = base * cond_mult
    if field in _FLOOD_PROTECTION_FIELDS:
        p += flood_uplift
    if field in _MODERN_ONLY_FIELDS and not is_modern_period:
        p *= 0.20
    if field in _ALWAYS_LIKELY_TRUE:
        p = max(p, 0.75)
    return max(0.02, min(0.95, p))


def _basement_strategy(
    basement_present: bool,
    period: str,
    cond_mult: float,
    rng: random.Random,
) -> str:
    """Pick BasementFloodStrategy consistent with whether a basement exists."""
    if not basement_present:
        return "No basement"
    is_modern = period in {"2000-2008", "2009-Present"}
    if is_modern and rng.random() < 0.6 * cond_mult:
        return rng.choices(
            ["Flood-resistant basement", "Deliberately floodable with protection"],
            weights=[0.7, 0.3],
        )[0]
    return "None"


def _extract_metadata(property_data: Dict[str, Any]) -> Dict[str, Any]:
    """Pull the fields the resilience generator needs out of a built property record."""
    ph = property_data.get("PropertyHeader", {})
    attrs = ph.get("PropertyAttributes", {})
    construction = ph.get("Construction", {})
    risk = ph.get("RiskAssessment", {})
    return {
        "period":           attrs.get("PropertyPeriod", "1976-1999"),
        "condition":        attrs.get("PropertyCondition", "Fair"),
        "flood_zone":       risk.get("EAFloodZone", "Zone 1"),
        "basement_present": bool(construction.get("BasementPresent", False)),
    }


def generate_resilience(
    property_data: Dict[str, Any],
    rng: Optional[random.Random] = None,
) -> Dict[str, Dict[str, Any]]:
    """Build the ``ProtectionMeasures.ResilienceMeasures`` dict for one property."""
    rng = rng or random
    meta = _extract_metadata(property_data)
    period = meta["period"]
    is_modern_period = period in {"1976-1999", "2000-2008", "2009-Present"}
    base = _PERIOD_BASE_PROB.get(period, _DEFAULT_PERIOD_PROB)
    cond_mult = _CONDITION_MULTIPLIER.get(meta["condition"], _DEFAULT_CONDITION_MULT)
    flood_uplift = _FLOOD_ZONE_UPLIFT.get(meta["flood_zone"], 0.0)

    resilience: Dict[str, Dict[str, Any]] = {}
    for section, fields in SECTION_FIELDS.items():
        section_data: Dict[str, Any] = {}
        for field in fields:
            p = _field_probability(field, base, cond_mult, flood_uplift, is_modern_period)
            score = max(0.0, min(1.0, p + rng.uniform(-0.20, 0.20)))
            section_data[field] = _level_from_score(score)
        resilience[section] = section_data

    resilience["SiteAndDrainage"]["BasementFloodStrategy"] = _basement_strategy(
        meta["basement_present"], period, cond_mult,
        rng if isinstance(rng, random.Random) else random.Random(),
    )

    return resilience


# Sanity-check distribution helpers ------------------------------------------

# Plausible Thames-stock distribution by construction period.
_PERIOD_WEIGHTS: List[tuple] = [
    ("Pre-1919",     0.18),
    ("1919-1944",    0.16),
    ("1945-1975",    0.24),
    ("1976-1999",    0.20),
    ("2000-2008",    0.12),
    ("2009-Present", 0.10),
]

_CONDITION_WEIGHTS: List[tuple] = [
    ("Excellent", 0.10), ("Good", 0.35), ("Fair", 0.35),
    ("Poor", 0.15), ("Very poor", 0.05),
]

_FLOOD_ZONE_WEIGHTS: List[tuple] = [
    ("Zone 1", 0.55), ("Zone 2", 0.25), ("Zone 3a", 0.15), ("Zone 3b", 0.05),
]


def _weighted_choice(weights: List[tuple], rng: random.Random) -> str:
    options, ws = zip(*weights)
    return rng.choices(options, weights=ws)[0]


def _synthetic_property(rng: random.Random) -> Dict[str, Any]:
    return {
        "PropertyHeader": {
            "PropertyAttributes": {
                "PropertyPeriod":    _weighted_choice(_PERIOD_WEIGHTS, rng),
                "PropertyCondition": _weighted_choice(_CONDITION_WEIGHTS, rng),
            },
            "Construction": {"BasementPresent": rng.random() < 0.25},
            "RiskAssessment": {"EAFloodZone": _weighted_choice(_FLOOD_ZONE_WEIGHTS, rng)},
        }
    }


def sanity_check_distribution(sample_size: int = 1000, seed: int = 42) -> Dict[str, Any]:
    """Generate ``sample_size`` synthetic Thames properties, score them, and
    report the BRI rating distribution alongside the Thames target."""
    rng = random.Random(seed)
    ratings: List[str] = []
    scores: List[float] = []
    examples: List[Dict[str, Any]] = []
    for i in range(sample_size):
        prop = _synthetic_property(rng)
        prop["ProtectionMeasures"] = {"ResilienceMeasures": generate_resilience(prop, rng)}
        result = compute_bri_rating(prop["ProtectionMeasures"]["ResilienceMeasures"])
        ratings.append(result["rating"])
        scores.append(result["score"])
        if i < 3:
            attrs = prop["PropertyHeader"]["PropertyAttributes"]
            examples.append({
                "period":    attrs["PropertyPeriod"],
                "condition": attrs["PropertyCondition"],
                "zone":      prop["PropertyHeader"]["RiskAssessment"]["EAFloodZone"],
                "rating":    result["rating"],
                "score":     result["score"],
            })

    return {
        "sample_size": sample_size,
        "distribution": distribution_summary(ratings),
        "mean_score": round(sum(scores) / len(scores), 4),
        "examples": examples,
    }
