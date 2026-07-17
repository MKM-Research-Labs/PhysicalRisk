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

"""Tests for the resilience generator (part 1)
(src/port/rand/thames/property/property_random/resilience.py).

Covers:
  - _level_from_score bucket boundaries.
  - generate_resilience produces all 5 sub-sections with valid menu values.
  - Period bias: 2009-Present should average a higher score than 1945-1975.
  - Condition multiplier: Excellent should beat Very poor at fixed period.
  - Flood-zone uplift: Zone 3a should beat Zone 1 on flood fields.
  - Basement strategy depends on BasementPresent.
  - sanity_check_distribution hits the Thames target band within tolerance.
"""

import random
from collections import Counter
from statistics import mean

import pytest

import port.rand.halong.property.property_random.resilience as halong_resilience
from port.rand.halong.property.property_random.resilience import (
    RESILIENCE_LEVEL_CREDIT,
    TARGET_DISTRIBUTION_THAMES,
    compute_bri_rating,
)
from port.rand.halong.property.property_random.resilience import (
    _field_credit,
    _level_from_score,
    _synthetic_property,
    generate_resilience,
    recalibrate_thresholds_from_scores,
    sanity_check_distribution,
    score_hazard,
    score_section,
    validate_weights,
)


# ---------------------------------------------------------------------------
# Direct-call coverage for the scoring/utility helpers
# ---------------------------------------------------------------------------

class TestFieldCredit:

    def test_none_value_zero(self):
        assert _field_credit("AnyField", None) == 0.0

    def test_bool_true_full_credit(self):
        assert _field_credit("AnyField", True) == 1.0

    def test_bool_false_zero(self):
        assert _field_credit("AnyField", False) == 0.0

    def test_basement_strategy_vocabulary(self):
        # BasementFloodStrategy uses its own credit table.
        assert isinstance(_field_credit("BasementFloodStrategy", "No basement"), float)

    def test_enum_level_credit(self):
        assert _field_credit("X", "Verified") == RESILIENCE_LEVEL_CREDIT["Verified"]

    def test_unknown_string_zero(self):
        assert _field_credit("X", "garbage") == 0.0


class TestScoreSectionAndHazard:

    def test_score_section_empty_returns_zero(self):
        assert score_section("FloodProtection", {}) == 0.0

    def test_score_hazard_unknown_returns_zero(self):
        assert score_hazard("NotAHazard", {}) == 0.0


class TestThresholdUtilities:

    def test_recalibrate_empty_scores_returns_defaults(self):
        out = recalibrate_thresholds_from_scores([])
        assert set(out) >= {"AA", "A", "B"}

    def test_recalibrate_with_scores(self):
        scores = [0.1, 0.3, 0.5, 0.7, 0.9]
        out = recalibrate_thresholds_from_scores(scores)
        assert out["AA"] >= out["A"] >= out["B"]

    def test_validate_weights_passes_for_default(self):
        # Default SECTION_WEIGHTS sum to 1.0 → no raise.
        assert validate_weights() is None

    def test_validate_weights_raises_when_unbalanced(self, monkeypatch):
        monkeypatch.setattr(halong_resilience, "SECTION_WEIGHTS", {"A": 0.5})
        with pytest.raises(ValueError):
            validate_weights()


# ---------------------------------------------------------------------------
# _level_from_score
# ---------------------------------------------------------------------------

class TestLevelFromScore:

    @pytest.mark.parametrize("score,expected", [
        (-0.1, "Not assessed"),  # clamped behaviour
        (0.0,  "Not assessed"),
        (0.19, "Not assessed"),
        (0.20, "Partial"),
        (0.39, "Partial"),
        (0.40, "Meets minimum"),
        (0.59, "Meets minimum"),
        (0.60, "Enhanced"),
        (0.79, "Enhanced"),
        (0.80, "Verified"),
        (1.0,  "Verified"),
        (1.5,  "Verified"),  # out-of-range
    ])
    def test_bucket_boundaries(self, score, expected):
        assert _level_from_score(score) == expected


# ---------------------------------------------------------------------------
# Structural shape
# ---------------------------------------------------------------------------

class TestGenerateResilienceStructure:

    def _property(self, period="1976-1999", condition="Fair", zone="Zone 1",
                  basement=False) -> dict:
        return {
            "PropertyHeader": {
                "PropertyAttributes": {"PropertyPeriod": period, "PropertyCondition": condition},
                "Construction": {"BasementPresent": basement},
                "RiskAssessment": {"EAFloodZone": zone},
            }
        }

    def test_emits_all_five_sub_sections(self):
        r = generate_resilience(self._property())
        assert set(r) == {
            "BuildingAssessment", "SiteAndDrainage", "FloodProtection",
            "FireProtection", "ContinuityMeasures",
        }

    def test_all_values_in_valid_menu(self):
        r = generate_resilience(self._property())
        for section, vals in r.items():
            for field, value in vals.items():
                if field == "BasementFloodStrategy":
                    assert value in {
                        "None", "No basement", "Flood-resistant basement",
                        "Deliberately floodable with protection",
                    }
                else:
                    assert value in RESILIENCE_LEVEL_CREDIT, \
                        f"{section}.{field} = {value!r} not in RESILIENCE_LEVEL_CREDIT"

    def test_deterministic_with_seeded_rng(self):
        rng1 = random.Random(0)
        rng2 = random.Random(0)
        prop = self._property(period="2009-Present", condition="Good")
        assert generate_resilience(prop, rng1) == generate_resilience(prop, rng2)
