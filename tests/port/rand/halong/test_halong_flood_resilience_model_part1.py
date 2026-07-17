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

"""Tests for the flood-spec resilience model. (part 1)

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
