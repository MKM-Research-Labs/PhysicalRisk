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

"""Tests for the flood-spec resilience model. (part 3)

The model lives in
``port.rand.halong.property.property_random.resilience`` (sections 5 & 6
of that file). It computes a continuous 1-100 flood resilience score from
13 weighted measures, applies regime multipliers + soft caps, and converts
the result into a damage modifier.

Covers:
  - Spec base weights sum to 100 + regime multipliers are 13-keyed.
  - compute_compliance: each of the 13 measures via the D2 mapping.
  - Elevation-band table for lowest_occupied_floor_elevation.
  - 5-level ordinal compliance default for missing values.
  - Soft caps: each cap trigger + non-trigger.
  - Regime mapping from FloodRiskType.
  - damage_modifier: α boundaries (S=1 → 1.0, S=100 → 1-α).
  - apply_flood_resilience_score: writes BRIFloodScore + ±jitter siblings +
    overall BRIScore; deterministic for a given PropertyID.
"""

from copy import deepcopy

import pytest

import port.rand.halong.property.property_random.resilience as halong_resilience
from port.rand.halong.property.property_random.resilience import (
    DEFAULT_MISSING_COMPLIANCE,
    DEFAULT_REGIME,
    FLOOD_SPEC_ALPHA_BY_REGIME,
    FLOOD_SPEC_BASE_WEIGHTS,
    FLOOD_SPEC_REGIME_MULTIPLIERS,
    HISTORIC_WATER_AREA_COMPLIANCE,
    LOWER_LEVEL_DESIGN_COMPLIANCE,
    LOWEST_FLOOR_ELEVATION_BANDS,
    REGIME_FROM_FLOOD_RISK_TYPE,
    RESILIENCE_LEVEL_CREDIT,
    _apply_soft_caps,
    _elevation_to_compliance,
    apply_flood_resilience_score,
    compute_compliance,
    compute_flood_resilience_score,
    damage_modifier,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _record(
    floor_meters=4.0,
    flood_risk_type="Fluvial",
    flood_damage_severity="No damage",
    basement_strategy="No basement",
    resilience_level="Verified",
    property_id="P-TEST",
):
    """Build a property record with sane defaults for the flood model."""
    return {
        "PropertyHeader": {
            "Header": {"PropertyID": property_id},
            "Construction": {"FloorLevelMeters": floor_meters},
            "RiskAssessment": {"FloodRiskType": flood_risk_type},
        },
        "ProtectionMeasures": {
            "ResilienceMeasures": {
                "BuildingAssessment": {
                    "OpeningsWindResistant":           resilience_level,
                    "RoofRatedForDesignWind":          resilience_level,
                    "RoofEdgeDetailWindResistant":     resilience_level,
                },
                "SiteAndDrainage": {
                    "OverlandFlowPathsMaintained":      resilience_level,
                    "OnsiteDrainageSizedForDesignStorm": resilience_level,
                    "PermeableOrRetentionMeasures":     resilience_level,
                    "BasementFloodStrategy":            basement_strategy,
                },
                "FloodProtection": {
                    "ElectricalSystemsAboveFlood":     resilience_level,
                    "BackflowPreventionInstalled":     resilience_level,
                    "PermanentFloodProofingAtEntries": resilience_level,
                    "SumpPump":                        resilience_level,
                },
                "ContinuityMeasures": {
                    "BackupPowerInstalled":            resilience_level,
                },
            },
        },
        "HistoryAndIncidents": {
            "FloodEvents": {"FloodDamageSeverity": flood_damage_severity},
        },
    }


# ---------------------------------------------------------------------------
# apply_flood_resilience_score — write-back semantics
# ---------------------------------------------------------------------------

class TestApplyFloodResilienceScore:
    """Exercises the score write-back machinery. BRI is disabled for Thames in
    production (``BRI_SCORES_ENABLED = False`` → all scores zeroed; see
    ``TestBriScoresDisabled``), so these tests flip the flag on to verify the
    scoring/jitter/mean logic that other catchments (e.g. Halong) rely on."""

    @pytest.fixture(autouse=True)
    def _enable_bri_scores(self, monkeypatch):
        monkeypatch.setattr(halong_resilience, "BRI_SCORES_ENABLED", True)

    def test_writes_flood_and_three_jittered_scores(self):
        rec = _record(floor_meters=5.0, resilience_level="Meets minimum")
        apply_flood_resilience_score(rec)
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        assert "BRIFloodScore" in gbr
        for hazard in ("Wind", "Fire", "Seismic"):
            assert f"BRI{hazard}Score" in gbr

    def test_jittered_scores_within_band(self):
        rec = _record()
        apply_flood_resilience_score(rec, jitter_band=0.05)
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        flood = gbr["BRIFloodScore"]
        for h in ("Wind", "Fire", "Seismic"):
            assert abs(gbr[f"BRI{h}Score"] - flood) <= 0.051  # tiny slack for clip

    def test_overall_is_mean_of_four(self):
        rec = _record()
        apply_flood_resilience_score(rec)
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        expected = round(
            (gbr["BRIFloodScore"] + gbr["BRIWindScore"]
             + gbr["BRIFireScore"] + gbr["BRISeismicScore"]) / 4.0, 4
        )
        assert gbr["BRIScore"] == expected

    def test_score_persisted_on_0_to_1_scale(self):
        rec = _record(floor_meters=10.0, resilience_level="Verified")
        apply_flood_resilience_score(rec)
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        # Strong resilience → high score; on 0-1 scale, very close to 1.0
        assert 0.0 <= gbr["BRIFloodScore"] <= 1.0
        assert gbr["BRIFloodScore"] > 0.9

    def test_deterministic_for_same_property_id(self):
        rec1 = _record(property_id="P-FIXED")
        rec2 = _record(property_id="P-FIXED")
        apply_flood_resilience_score(rec1)
        apply_flood_resilience_score(rec2)
        gbr1 = rec1["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        gbr2 = rec2["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        assert gbr1["BRIFloodScore"] == gbr2["BRIFloodScore"]
        assert gbr1["BRIWindScore"] == gbr2["BRIWindScore"]

    def test_different_property_ids_give_different_jitter(self):
        rec1 = _record(property_id="P-AAA")
        rec2 = _record(property_id="P-ZZZ")
        apply_flood_resilience_score(rec1)
        apply_flood_resilience_score(rec2)
        # Flood score is deterministic from inputs, so same flood. But jitter
        # uses PropertyID-keyed RNG → siblings should differ.
        gbr1 = rec1["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        gbr2 = rec2["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        assert gbr1["BRIFloodScore"] == gbr2["BRIFloodScore"]
        # At least one sibling should differ
        assert (gbr1["BRIWindScore"] != gbr2["BRIWindScore"]
                or gbr1["BRIFireScore"] != gbr2["BRIFireScore"]
                or gbr1["BRISeismicScore"] != gbr2["BRISeismicScore"])

    def test_return_value_includes_damage_modifier(self):
        rec = _record()
        result = apply_flood_resilience_score(rec)
        assert "damage_modifier" in result
        assert 0.0 < result["damage_modifier"] <= 1.0
        assert "score_raw" in result
        assert "score_final" in result
        assert "compliance" in result


# ---------------------------------------------------------------------------
# BRI enabled for Halong — scores written, BRI-adjusted floor stamped
# ---------------------------------------------------------------------------

class TestBriScoresEnabled:
    """Halong ships with ``BRI_SCORES_ENABLED = True`` (BRI/typhoon catchment).
    apply_flood_resilience_score must write all five numeric BRI scores and the
    BRI-adjusted floor level."""

    def test_flag_is_true_for_halong(self):
        assert halong_resilience.BRI_SCORES_ENABLED is True

    def test_all_five_scores_written(self):
        rec = _record(floor_meters=10.0, resilience_level="Verified")
        apply_flood_resilience_score(rec)
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        for field in ("BRIFloodScore", "BRIWindScore", "BRIFireScore",
                      "BRISeismicScore", "BRIScore"):
            assert isinstance(gbr[field], float)

    def test_floor_uplift_written(self):
        rec = _record(floor_meters=5.0, resilience_level="Verified")
        apply_flood_resilience_score(rec)
        construction = rec["PropertyHeader"]["Construction"]
        assert "BRIAdjustedFloorLevelMeters" in construction
        assert construction["BRIAdjustedFloorLevelMeters"] >= 5.0

    def test_return_value_still_carries_model_output(self):
        rec = _record()
        result = apply_flood_resilience_score(rec)
        assert "damage_modifier" in result
        assert "score_final" in result
