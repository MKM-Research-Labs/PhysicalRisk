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

"""Tests for the BRI scoring math now consolidated in
port.rand.thames.property.property_random.resilience.

Covers:
  - _field_credit: booleans, 5-level resilience enum, BasementFloodStrategy enum.
  - score_section: weighted sum, empty section, unknown values.
  - score_hazard: filters to hazard-relevant fields, flatten across sub-sections.
  - _map_score_to_rating: threshold mapping.
  - compute_bri_rating: per-hazard letters, weakest-link overall, "+" modifier.
  - distribution_summary and recalibrate_thresholds_from_scores.
  - validate_weights catches drift from 1.0.
"""

import pytest

from port.rand.thames.property.property_random.resilience import (
    _field_credit, _map_score_to_rating,
    BASEMENT_FLOOD_STRATEGY_CREDIT, CONTINUITY_PLUS_THRESHOLD,
    HAZARD_RELEVANT_FIELDS,
    RATING_THRESHOLDS,
    RESILIENCE_LEVEL_CREDIT,
    SECTION_WEIGHTS,
    compute_bri_rating,
    distribution_summary,
    recalibrate_thresholds_from_scores,
    score_hazard,
    score_section,
    validate_weights,
)


# ---------------------------------------------------------------------------
# _field_credit
# ---------------------------------------------------------------------------

class TestFieldCredit:

    def test_none_value_is_zero(self):
        assert _field_credit("anything", None) == 0.0

    def test_boolean_true_full_credit(self):
        assert _field_credit("AnyField", True) == 1.0

    def test_boolean_false_zero_credit(self):
        assert _field_credit("AnyField", False) == 0.0

    @pytest.mark.parametrize("level,expected", list(RESILIENCE_LEVEL_CREDIT.items()))
    def test_resilience_levels(self, level, expected):
        assert _field_credit("AnyField", level) == expected

    @pytest.mark.parametrize("value,expected", list(BASEMENT_FLOOD_STRATEGY_CREDIT.items()))
    def test_basement_flood_strategy(self, value, expected):
        assert _field_credit("BasementFloodStrategy", value) == expected

    def test_unknown_string_zero(self):
        assert _field_credit("AnyField", "Made up value") == 0.0


# ---------------------------------------------------------------------------
# _map_score_to_rating
# ---------------------------------------------------------------------------

class TestMapScoreToRating:

    def test_aa_threshold(self):
        assert _map_score_to_rating(RATING_THRESHOLDS["AA"]) == "AA"
        assert _map_score_to_rating(1.0) == "AA"

    def test_a_threshold(self):
        assert _map_score_to_rating(RATING_THRESHOLDS["A"]) == "A"
        # Just under AA
        assert _map_score_to_rating(RATING_THRESHOLDS["AA"] - 0.001) == "A"

    def test_b_threshold(self):
        assert _map_score_to_rating(RATING_THRESHOLDS["B"]) == "B"

    def test_below_b_is_nr(self):
        assert _map_score_to_rating(0.0) == "NR"
        assert _map_score_to_rating(RATING_THRESHOLDS["B"] - 0.001) == "NR"


# ---------------------------------------------------------------------------
# score_section
# ---------------------------------------------------------------------------

class TestScoreSection:

    def test_empty_section_returns_zero(self):
        assert score_section("BuildingAssessment", {}) == 0.0

    def test_all_verified_is_one(self):
        data = {f: "Verified" for f in ["StructureMeetsSeismicCode", "RoofRatedForDesignWind"]}
        assert score_section("BuildingAssessment", data) == 1.0

    def test_all_not_assessed_is_zero(self):
        data = {f: "Not assessed" for f in ["StructureMeetsSeismicCode", "RoofRatedForDesignWind"]}
        assert score_section("BuildingAssessment", data) == 0.0

    def test_mixed_levels_average_correctly(self):
        # Use a section with no per-field weight overrides so each field counts equally.
        data = {
            "AutomaticDetectionInstalled": "Verified",       # 1.0
            "SuppressionSystemsInstalled": "Not assessed",   # 0.0
        }
        result = score_section("FireProtection", data)
        # Equal weights → average of 1.0 and 0.0 = 0.5
        assert result == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# score_hazard
# ---------------------------------------------------------------------------

class TestScoreHazard:

    def _flat_to_nested(self, flat_values: dict) -> dict:
        """Wrap a flat field→level dict into a fake resilience tree the
        hazard scorer can flatten."""
        return {"FloodProtection": flat_values}

    def test_unknown_hazard_returns_zero(self):
        assert score_hazard("NotARealHazard", {}) == 0.0

    def test_hazard_with_all_verified_is_one(self):
        flood_fields = HAZARD_RELEVANT_FIELDS["Flood"]
        # BasementFloodStrategy uses its own credit vocabulary, not the
        # 5-level resilience enum — set it to a full-credit choice.
        resilience = {"FloodProtection": {}}
        for f in flood_fields:
            if f == "BasementFloodStrategy":
                resilience["FloodProtection"][f] = "No basement"
            else:
                resilience["FloodProtection"][f] = "Verified"
        assert score_hazard("Flood", resilience) == pytest.approx(1.0)

    def test_seismic_hazard_isolated(self):
        # Only seismic fields contribute; flood values should be ignored.
        seismic_fields = HAZARD_RELEVANT_FIELDS["Seismic"]
        resilience = {
            "BuildingAssessment": {f: "Verified" for f in seismic_fields},
            "FloodProtection": {"PermanentFloodProofingAtEntries": "Not assessed"},
        }
        score = score_hazard("Seismic", resilience)
        assert score == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# compute_bri_rating — overall logic
# ---------------------------------------------------------------------------

class TestComputeBriRating:

    def _make_resilience(self, level: str) -> dict:
        from port.cdm.asset.resilience import RESILIENCE_MEASURES_SCHEMA
        out = {}
        for section, fields in RESILIENCE_MEASURES_SCHEMA.items():
            out[section] = {}
            for fname, fdef in fields.items():
                if fname == "BasementFloodStrategy":
                    out[section][fname] = "No basement"
                else:
                    out[section][fname] = level
        return out

    def test_empty_input(self):
        r = compute_bri_rating({})
        assert r["rating"] == "NR"
        assert r["score"] == 0.0

    def test_all_verified_no_hazard_profile_is_top_rating(self):
        r = compute_bri_rating(self._make_resilience("Verified"))
        # No hazard profile → fall back to overall score path; high score → AA or AA+.
        assert r["rating"] in ("AA", "AA+")
        assert r["score"] == pytest.approx(1.0)

    def test_all_not_assessed_is_NR(self):
        r = compute_bri_rating(self._make_resilience("Not assessed"))
        assert r["rating"] == "NR"

    def test_weakest_link_picks_worst_hazard(self):
        # All sections high EXCEPT flood — should still get NR because Flood
        # hazard sub-score drives the weakest-link overall.
        resilience = self._make_resilience("Verified")
        for f in HAZARD_RELEVANT_FIELDS["Flood"]:
            for sect in resilience:
                if f in resilience[sect]:
                    resilience[sect][f] = "Not assessed"
        result = compute_bri_rating(resilience, hazard_profile={
            "FloodHazardClass": "High",
            "WindHazardClass": "Medium",
            "FireHazardClass": "Medium",
            "SeismicHazardClass": "Medium",
        })
        assert result["hazard_ratings"]["Flood"] == "NR"
        assert result["rating"] == "NR"  # weakest-link

    def test_none_hazards_excluded_from_weakest_link(self):
        # Wind/Fire/Seismic = "None" so they shouldn't drag the overall down.
        # Even if their resilience is low, overall should match Flood-only result.
        resilience = self._make_resilience("Verified")
        for f in HAZARD_RELEVANT_FIELDS["Wind"]:
            for sect in resilience:
                if f in resilience[sect]:
                    resilience[sect][f] = "Not assessed"
        result = compute_bri_rating(resilience, hazard_profile={
            "FloodHazardClass": "Medium",
            "WindHazardClass": "None",
            "FireHazardClass": "None",
            "SeismicHazardClass": "None",
        })
        assert result["hazard_ratings"]["Wind"] == "N/A"
        assert result["rating"] in ("AA", "AA+")  # not dragged down

    def test_plus_modifier_when_continuity_strong(self):
        # All Verified + applicable hazards → AA, and continuity score is
        # 1.0 ≥ CONTINUITY_PLUS_THRESHOLD → "+" appended.
        result = compute_bri_rating(self._make_resilience("Verified"), hazard_profile={
            "FloodHazardClass": "Medium", "WindHazardClass": "Medium",
            "FireHazardClass": "Medium", "SeismicHazardClass": "Medium",
        })
        assert result["rating"] == "AA+"

    def test_plus_modifier_not_applied_to_nr(self):
        result = compute_bri_rating(self._make_resilience("Not assessed"), hazard_profile={
            "FloodHazardClass": "Medium",
        })
        assert "+" not in result["rating"]

    def test_returns_full_breakdown(self):
        r = compute_bri_rating(self._make_resilience("Verified"))
        assert set(r) == {"rating", "score", "section_scores", "hazard_ratings", "hazard_scores"}
        assert set(r["section_scores"]) == set(SECTION_WEIGHTS)
        assert set(r["hazard_ratings"]) == {"Flood", "Wind", "Fire", "Seismic"}
        assert set(r["hazard_scores"]) == {"Flood", "Wind", "Fire", "Seismic"}


# ---------------------------------------------------------------------------
# Calibration helpers
# ---------------------------------------------------------------------------

class TestCalibrationHelpers:

    def test_distribution_summary_counts(self):
        ratings = ["AA"] * 1 + ["A"] * 2 + ["B"] * 4 + ["NR"] * 3
        summary = distribution_summary(ratings, target={"AA": 0.1, "A": 0.2, "B": 0.4, "NR": 0.3})
        assert summary["AA"]["actual"] == pytest.approx(0.1)
        assert summary["A"]["actual"] == pytest.approx(0.2)
        assert summary["B"]["actual"] == pytest.approx(0.4)
        assert summary["NR"]["actual"] == pytest.approx(0.3)
        # delta = 0 when actual matches target
        for k in ("AA", "A", "B", "NR"):
            assert summary[k]["delta"] == pytest.approx(0.0)

    def test_distribution_summary_empty(self):
        # Should not divide by zero.
        summary = distribution_summary([])
        for k in ("AA", "A", "B", "NR"):
            assert summary[k]["actual"] == 0.0

    def test_recalibrate_thresholds_hits_target(self):
        # Use a synthetic, sorted distribution. Top 10 % → AA, etc.
        scores = [i / 99 for i in range(100)]
        thresholds = recalibrate_thresholds_from_scores(
            scores, target={"AA": 0.1, "A": 0.2, "B": 0.4, "NR": 0.3}
        )
        # The 10th-ranked-from-top should be the AA threshold
        # i.e. the score that puts ~10 properties at or above AA.
        assert thresholds["AA"] > thresholds["A"] > thresholds["B"]

    def test_recalibrate_empty_returns_current(self):
        thresholds = recalibrate_thresholds_from_scores([])
        assert thresholds == RATING_THRESHOLDS


# ---------------------------------------------------------------------------
# validate_weights
# ---------------------------------------------------------------------------

class TestValidateWeights:

    def test_current_weights_sum_to_one(self):
        validate_weights()  # should not raise

    def test_raises_on_drift(self, monkeypatch):
        # Patch SECTION_WEIGHTS to a known broken value.
        from port.rand.thames.property.property_random import resilience as br
        monkeypatch.setitem(br.SECTION_WEIGHTS, "FireProtection", 0.99)
        with pytest.raises(ValueError):
            br.validate_weights()
