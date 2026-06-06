# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for the flood-spec resilience model. (part 2)

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
