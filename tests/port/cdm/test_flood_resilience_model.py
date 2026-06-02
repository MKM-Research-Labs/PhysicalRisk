# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for the flood-spec resilience model.

The model lives in
``port.rand.thames.property.property_random.resilience`` (sections 5 & 6
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

import port.rand.thames.property.property_random.resilience as thames_resilience
from port.rand.thames.property.property_random.resilience import (
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
# Constants
# ---------------------------------------------------------------------------

class TestSpecConstants:

    def test_base_weights_sum_to_100(self):
        assert sum(FLOOD_SPEC_BASE_WEIGHTS.values()) == 100

    def test_thirteen_measures(self):
        assert len(FLOOD_SPEC_BASE_WEIGHTS) == 13

    @pytest.mark.parametrize("regime", ["pluvial", "fluvial", "coastal"])
    def test_regime_multipliers_cover_every_measure(self, regime):
        assert set(FLOOD_SPEC_REGIME_MULTIPLIERS[regime]) == set(FLOOD_SPEC_BASE_WEIGHTS)

    def test_alpha_per_regime(self):
        assert FLOOD_SPEC_ALPHA_BY_REGIME["pluvial"] == 0.65
        assert FLOOD_SPEC_ALPHA_BY_REGIME["fluvial"] == 0.60
        assert FLOOD_SPEC_ALPHA_BY_REGIME["coastal"] == 0.50


# ---------------------------------------------------------------------------
# Elevation banding
# ---------------------------------------------------------------------------

class TestElevationCompliance:

    @pytest.mark.parametrize("meters,expected", [
        (-1.0, 0.00),    # below 0
        (0.0,  0.20),    # 0–1 m
        (0.5,  0.20),
        (0.999, 0.20),
        (1.0,  0.50),
        (2.5,  0.50),
        (3.0,  0.75),
        (4.99, 0.75),
        (5.0,  0.90),
        (5.99, 0.90),
        (6.0,  1.00),
        (15.0, 1.00),
    ])
    def test_band_boundaries(self, meters, expected):
        assert _elevation_to_compliance(meters) == expected

    def test_none_returns_default(self):
        assert _elevation_to_compliance(None) == DEFAULT_MISSING_COMPLIANCE

    def test_non_numeric_returns_default(self):
        assert _elevation_to_compliance("not a number") == DEFAULT_MISSING_COMPLIANCE


# ---------------------------------------------------------------------------
# compute_compliance — per-measure D2 mapping
# ---------------------------------------------------------------------------

class TestComputeCompliance:

    def test_lowest_floor_elevation_reads_floor_meters(self):
        rec = _record(floor_meters=2.0)
        assert compute_compliance("lowest_occupied_floor_elevation", rec) == 0.50

    def test_lowest_floor_missing_returns_default(self):
        rec = _record(floor_meters=2.0)
        del rec["PropertyHeader"]["Construction"]["FloorLevelMeters"]
        assert compute_compliance("lowest_occupied_floor_elevation", rec) == DEFAULT_MISSING_COMPLIANCE

    def test_critical_systems_elevation_uses_5level(self):
        rec = _record(resilience_level="Verified")
        assert compute_compliance("critical_systems_elevation", rec) == 1.0
        rec = _record(resilience_level="Not assessed")
        assert compute_compliance("critical_systems_elevation", rec) == 0.0
        rec = _record(resilience_level="Partial")
        assert compute_compliance("critical_systems_elevation", rec) == RESILIENCE_LEVEL_CREDIT["Partial"]

    @pytest.mark.parametrize("strategy,expected", list(LOWER_LEVEL_DESIGN_COMPLIANCE.items()))
    def test_lower_level_design_uses_basement_strategy(self, strategy, expected):
        rec = _record(basement_strategy=strategy)
        assert compute_compliance("lower_level_flood_compatible_design", rec) == expected

    @pytest.mark.parametrize("severity,expected", list(HISTORIC_WATER_AREA_COMPLIANCE.items()))
    def test_historic_water_uses_flood_damage_severity(self, severity, expected):
        rec = _record(flood_damage_severity=severity)
        assert compute_compliance("historic_water_area_flag", rec) == expected

    def test_historic_water_missing_is_clear(self):
        """No flood event recorded → property is in the 'clear' state."""
        rec = _record()
        del rec["HistoryAndIncidents"]
        assert compute_compliance("historic_water_area_flag", rec) == 1.0

    def test_sump_pumps_backup_power_is_min_of_both(self):
        """Spec measure is min(SumpPump credit, BackupPower credit)."""
        rec = _record(resilience_level="Verified")
        # Override one to be weaker
        rec["ProtectionMeasures"]["ResilienceMeasures"]["ContinuityMeasures"][
            "BackupPowerInstalled"] = "Partial"
        assert compute_compliance("sump_pumps_backup_power", rec) == RESILIENCE_LEVEL_CREDIT["Partial"]

    def test_unknown_measure_raises(self):
        with pytest.raises(KeyError):
            compute_compliance("not_a_real_measure", _record())


# ---------------------------------------------------------------------------
# Soft caps
# ---------------------------------------------------------------------------

class TestSoftCaps:

    def test_no_cap_when_all_above_zero(self):
        comp = {c: 1.0 for c in FLOOD_SPEC_BASE_WEIGHTS}
        assert _apply_soft_caps(85.0, comp, "fluvial") == 85.0

    def test_floor_elevation_zero_caps_at_40(self):
        comp = {c: 1.0 for c in FLOOD_SPEC_BASE_WEIGHTS}
        comp["lowest_occupied_floor_elevation"] = 0.0
        assert _apply_soft_caps(80.0, comp, "fluvial") == 40.0

    def test_critical_systems_zero_caps_at_60(self):
        comp = {c: 1.0 for c in FLOOD_SPEC_BASE_WEIGHTS}
        comp["critical_systems_elevation"] = 0.0
        assert _apply_soft_caps(80.0, comp, "fluvial") == 60.0

    def test_pluvial_drainage_double_zero_caps_at_55(self):
        comp = {c: 1.0 for c in FLOOD_SPEC_BASE_WEIGHTS}
        comp["onsite_retainage_capacity"] = 0.0
        comp["site_drainage_topography"] = 0.0
        assert _apply_soft_caps(80.0, comp, "pluvial") == 55.0
        # Not pluvial → no cap from this rule.
        assert _apply_soft_caps(80.0, comp, "fluvial") == 80.0

    @pytest.mark.parametrize("regime", ["fluvial", "coastal"])
    def test_fluvial_coastal_lower_level_zero_caps_at_65(self, regime):
        comp = {c: 1.0 for c in FLOOD_SPEC_BASE_WEIGHTS}
        comp["lower_level_flood_compatible_design"] = 0.0
        comp["water_resistant_materials"] = 0.0
        assert _apply_soft_caps(80.0, comp, regime) == 65.0
        # Not in fluvial/coastal regimes → no cap from this rule.
        assert _apply_soft_caps(80.0, comp, "pluvial") == 80.0

    def test_score_clipped_to_minimum_1(self):
        comp = {c: 0.0 for c in FLOOD_SPEC_BASE_WEIGHTS}
        # Even with raw=0, final must be >= 1.0
        assert _apply_soft_caps(0.0, comp, "fluvial") == 1.0


# ---------------------------------------------------------------------------
# Regime mapping
# ---------------------------------------------------------------------------

class TestRegimeMapping:

    @pytest.mark.parametrize("flood_type,regime", [
        ("Fluvial", "fluvial"),
        ("Pluvial", "pluvial"),
        ("GroundWater", "pluvial"),
        ("Coastal", "coastal"),
        ("Multiple", "pluvial"),
    ])
    def test_each_flood_risk_type_maps_correctly(self, flood_type, regime):
        assert REGIME_FROM_FLOOD_RISK_TYPE[flood_type] == regime

    def test_default_regime_used_when_field_missing(self):
        rec = _record()
        del rec["PropertyHeader"]["RiskAssessment"]["FloodRiskType"]
        result = compute_flood_resilience_score(rec)
        assert result["regime"] == DEFAULT_REGIME

    def test_explicit_regime_override(self):
        rec = _record(flood_risk_type="Pluvial")
        result = compute_flood_resilience_score(rec, regime="coastal")
        assert result["regime"] == "coastal"

    def test_invalid_regime_falls_back_to_default(self):
        rec = _record()
        result = compute_flood_resilience_score(rec, regime="bogus")
        assert result["regime"] == DEFAULT_REGIME


# ---------------------------------------------------------------------------
# damage_modifier
# ---------------------------------------------------------------------------

class TestDamageModifier:

    @pytest.mark.parametrize("regime,alpha", list(FLOOD_SPEC_ALPHA_BY_REGIME.items()))
    def test_score_1_gives_no_mitigation(self, regime, alpha):
        # At S=1: 1 - α × 0/99 = 1.0
        assert damage_modifier(1.0, regime) == 1.0

    @pytest.mark.parametrize("regime,alpha", list(FLOOD_SPEC_ALPHA_BY_REGIME.items()))
    def test_score_100_gives_max_mitigation(self, regime, alpha):
        # At S=100: 1 - α × 99/99 = 1 - α
        assert damage_modifier(100.0, regime) == round(1.0 - alpha, 4)

    def test_modifier_monotonic(self):
        # Higher score → lower damage modifier
        assert damage_modifier(75.0, "fluvial") < damage_modifier(50.0, "fluvial")
        assert damage_modifier(50.0, "fluvial") < damage_modifier(25.0, "fluvial")

    def test_unknown_regime_defaults_to_fluvial(self):
        assert damage_modifier(50.0, "bogus") == damage_modifier(50.0, "fluvial")


# ---------------------------------------------------------------------------
# End-to-end compute_flood_resilience_score
# ---------------------------------------------------------------------------

class TestComputeFloodResilienceScore:

    def test_all_verified_high_floor_max_scores(self):
        rec = _record(floor_meters=10.0, resilience_level="Verified")
        result = compute_flood_resilience_score(rec)
        assert result["score_raw"] == pytest.approx(100.0, abs=0.5)
        assert result["score_final"] == pytest.approx(100.0, abs=0.5)
        assert result["regime"] == "fluvial"
        assert set(result["compliance"]) == set(FLOOD_SPEC_BASE_WEIGHTS)

    def test_all_not_assessed_zero_floor_hits_floor_cap(self):
        rec = _record(floor_meters=-1.0, resilience_level="Not assessed",
                      basement_strategy="None", flood_damage_severity="Severe damage")
        result = compute_flood_resilience_score(rec)
        # lowest_occupied_floor_elevation = 0 → 40 cap; final must be <= 40.
        assert result["score_final"] <= 40.0
        assert result["score_final"] >= 1.0  # but clipped above 0

    def test_compliance_dict_keys(self):
        result = compute_flood_resilience_score(_record())
        assert set(result["compliance"]) == set(FLOOD_SPEC_BASE_WEIGHTS)


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
        monkeypatch.setattr(thames_resilience, "BRI_SCORES_ENABLED", True)

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
# BRI disabled for Thames — scores stamped 0.0, no floor uplift
# ---------------------------------------------------------------------------

class TestBriScoresDisabled:
    """Thames ships with ``BRI_SCORES_ENABLED = False`` because BRI is not a
    Thames concept. In that mode apply_flood_resilience_score must stamp every
    numeric BRI score 0.0 and apply no BRI-adjusted floor uplift, while still
    returning the underlying model output for inspection."""

    def test_flag_is_false_for_thames(self):
        assert thames_resilience.BRI_SCORES_ENABLED is False

    def test_all_five_scores_zeroed(self):
        rec = _record(floor_meters=10.0, resilience_level="Verified")
        apply_flood_resilience_score(rec)
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        for field in ("BRIFloodScore", "BRIWindScore", "BRIFireScore",
                      "BRISeismicScore", "BRIScore"):
            assert gbr[field] == 0.0, f"{field} should be 0.0; got {gbr[field]!r}"

    def test_no_floor_uplift_written(self):
        rec = _record(floor_meters=5.0, resilience_level="Verified")
        apply_flood_resilience_score(rec)
        construction = rec["PropertyHeader"]["Construction"]
        assert "BRIAdjustedFloorLevelMeters" not in construction

    def test_return_value_still_carries_model_output(self):
        rec = _record()
        result = apply_flood_resilience_score(rec)
        assert "damage_modifier" in result
        assert "score_final" in result
