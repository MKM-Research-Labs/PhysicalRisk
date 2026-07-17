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

"""
Property resilience — catchment-shared single source of truth.

This package is the consolidated home for everything resilience-related for the
synthetic property pipeline. The calibration here (section/field weights,
thresholds, period/condition/zone priors, flood-spec weights) is identical
across catchments, so every catchment's
``property/property_random/resilience.py`` is a thin shim that delegates here.

It contains, across the submodules:

  1. BRI letter-rating CONSTANTS    — section/field weights, level credits,
     (bri_constants)                  rating thresholds, hazard relevance.
  2. BRI letter-rating FUNCTIONS    — score_section, score_hazard,
     (bri_rating)                     compute_bri_rating, calibration helpers.
  3. Resilience GENERATOR CONSTANTS — period/condition/zone priors used to
     (generator_constants)            synthesise plausible checklists.
  4. Resilience GENERATOR FUNCTIONS — generate_resilience, sanity check.
     (generator)
  5. Flood-spec MODEL CONSTANTS     — 13-measure weights, regime multipliers,
     (flood_constants)                compliance maps, soft caps, alpha.
  6. Flood-spec MODEL FUNCTIONS     — compute_compliance, regime score,
     (flood_compliance/flood_score)   damage modifier, apply_flood_resilience_score.

This ``__init__`` is a pure re-export façade: it contains no functional code,
only imports from the submodules so existing ``from ... import property_resilience``
call sites (and the catchment shims that copy ``vars()`` of this module)
continue to see every public and private symbol unchanged.

The two per-catchment toggles — ``PUBLISH_BRI_LETTER_RATINGS`` (whether the
catchment publishes certified BRI letter grades) and ``BRI_SCORES_ENABLED``
(whether the five numeric BRIScore fields are computed) — are deliberately NOT
defined here. They live in each catchment's shim module, which forwards its
local BRI flag into ``apply_flood_resilience_score`` via ``bri_scores_enabled``.
"""

from .bri_constants import (
    SECTION_WEIGHTS, FIELD_WEIGHTS, RESILIENCE_LEVEL_CREDIT,
    BASEMENT_FLOOD_STRATEGY_CREDIT, RATING_THRESHOLDS, RATING_ORDER,
    HAZARD_RELEVANT_FIELDS, CONTINUITY_PLUS_THRESHOLD,
    TARGET_DISTRIBUTION_THAMES,
)
from .bri_rating import (
    _field_credit, score_section, _map_score_to_rating, _flatten_resilience,
    score_hazard, compute_bri_rating, distribution_summary,
    recalibrate_thresholds_from_scores, validate_weights,
)
from .generator_constants import (
    _PERIOD_BASE_PROB, _DEFAULT_PERIOD_PROB, _CONDITION_MULTIPLIER,
    _DEFAULT_CONDITION_MULT, _MODERN_ONLY_FIELDS, _FLOOD_PROTECTION_FIELDS,
    _FLOOD_ZONE_UPLIFT, _ALWAYS_LIKELY_TRUE, SECTION_FIELDS,
    _RESILIENCE_LEVELS,
)
from .generator import (
    _level_from_score, _field_probability, _basement_strategy,
    _extract_metadata, generate_resilience, _PERIOD_WEIGHTS,
    _CONDITION_WEIGHTS, _FLOOD_ZONE_WEIGHTS, _weighted_choice,
    _synthetic_property, sanity_check_distribution,
)
from .flood_constants import (
    FLOOD_SPEC_BASE_WEIGHTS, FLOOD_SPEC_REGIME_MULTIPLIERS,
    LOWEST_FLOOR_ELEVATION_BANDS, HISTORIC_WATER_AREA_COMPLIANCE,
    LOWER_LEVEL_DESIGN_COMPLIANCE, FLOOD_SPEC_SOFT_CAPS,
    FLOOD_SPEC_ALPHA_BY_REGIME, REGIME_FROM_FLOOD_RISK_TYPE, DEFAULT_REGIME,
    DEFAULT_MISSING_COMPLIANCE,
)
from .flood_compliance import (
    _elevation_to_compliance, _ordinal_5level_compliance, _get,
    compute_compliance, _apply_soft_caps,
)
from .flood_score import (
    compute_flood_resilience_score, damage_modifier,
    apply_flood_resilience_score,
)

__all__ = [
    # bri_constants
    "SECTION_WEIGHTS", "FIELD_WEIGHTS", "RESILIENCE_LEVEL_CREDIT",
    "BASEMENT_FLOOD_STRATEGY_CREDIT", "RATING_THRESHOLDS", "RATING_ORDER",
    "HAZARD_RELEVANT_FIELDS", "CONTINUITY_PLUS_THRESHOLD",
    "TARGET_DISTRIBUTION_THAMES",
    # bri_rating
    "score_section", "score_hazard", "compute_bri_rating",
    "distribution_summary", "recalibrate_thresholds_from_scores",
    "validate_weights",
    # generator_constants
    "SECTION_FIELDS",
    # generator
    "generate_resilience", "sanity_check_distribution",
    # flood_constants
    "FLOOD_SPEC_BASE_WEIGHTS", "FLOOD_SPEC_REGIME_MULTIPLIERS",
    "LOWEST_FLOOR_ELEVATION_BANDS", "HISTORIC_WATER_AREA_COMPLIANCE",
    "LOWER_LEVEL_DESIGN_COMPLIANCE", "FLOOD_SPEC_SOFT_CAPS",
    "FLOOD_SPEC_ALPHA_BY_REGIME", "REGIME_FROM_FLOOD_RISK_TYPE",
    "DEFAULT_REGIME", "DEFAULT_MISSING_COMPLIANCE",
    # flood model
    "compute_compliance", "compute_flood_resilience_score", "damage_modifier",
    "apply_flood_resilience_score",
]
