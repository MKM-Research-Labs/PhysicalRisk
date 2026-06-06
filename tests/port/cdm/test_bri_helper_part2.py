# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for the BRI helper (src/port/cdm/asset/residential/bri.py) (part 2).

Covers:
  - apply_bri_rating writes the eight rating + metadata fields back into
    ProtectionMeasures.RiskAssessment.GoverningBodyRatings.
  - The five score fields are intentionally NOT written (a downstream
    methodology is responsible for them).
  - Missing HazardProfile is handled (every hazard treated as applicable).
  - When a hazard's class is "None", the corresponding rating is "N/A".
  - Optional agent + rating_date kwargs override the defaults.
"""

from datetime import date

import pytest

import port.cdm.asset.residential.bri as bri_mod
from port.cdm.asset.residential.bri import _weaker_rating, apply_bri_rating


_LEVELS_HIGH = "Verified"
_LEVELS_LOW = "Not assessed"


def _resilience(level_high: bool) -> dict:
    """Build a uniformly-high or uniformly-low resilience checklist."""
    val = _LEVELS_HIGH if level_high else _LEVELS_LOW
    return {
        "BuildingAssessment": {
            "SiteExposureAssessed": val, "OrientationMitigatesWind": val,
            "StructureDesignedForHazardWind": val, "ContinuousLoadPathProvided": val,
            "LateralBracingAdequate": val, "RoofRatedForDesignWind": val,
            "RoofEdgeDetailWindResistant": val, "CladdingRatedForDesignWind": val,
            "OpeningsWindResistant": val, "LargeDoorsReinforced": val,
            "RooftopEquipmentAnchored": val, "FacadeAttachmentsAnchored": val,
            "StructuralFireResistanceAdequate": val, "CompartmentsProvided": val,
            "FireStoppingAtPenetrations": val, "ExternalMaterialsFireResistant": val,
            "SiteGeotechnicalAssessed": val, "StructureMeetsSeismicCode": val,
            "SeismicDetailingToStandard": val, "StructuralRegularityAdequate": val,
            "FoundationSuitableForHazard": val, "NonstructuralComponentsAnchored": val,
            "HeavyEquipmentAnchored": val,
        },
        "SiteAndDrainage": {
            "SiteFloodHazardAssessed": val, "HighRiskZoneAvoidedOrJustified": val,
            "FinishedFloorAboveDesignFlood": val, "OccupiedLevelsElevated": val,
            "BasementFloodStrategy": "No basement",
            "OnsiteDrainageSizedForDesignStorm": val, "OverlandFlowPathsMaintained": val,
            "PermeableOrRetentionMeasures": val, "WildfireDefensibleSpace": val,
            "WildfireNonCombustiblePerimeter": val, "HighRiskGroundAvoidedOrMitigated": val,
            "LiquefactionMitigationProvided": val,
        },
        "FloodProtection": {
            "PermanentFloodProofingAtEntries": val, "DeployableBarriersProvided": val,
            "BackflowPreventionInstalled": val, "ElectricalSystemsAboveFlood": val,
            "MechanicalSystemsAboveFlood": val, "FuelAndHazardousStoresProtected": val,
            "FloodGates": val, "FloodBarriers": val, "SumpPump": val, "FloodWarningSystem": val,
        },
        "FireProtection": {
            "AutomaticDetectionInstalled": val, "SuppressionSystemsInstalled": val,
        },
        "ContinuityMeasures": {
            "BackupPowerInstalled": val, "BackupPowerProtectedFromHazard": val,
            "BackupWaterSupplyProvided": val, "WaterSystemsProtectedFromHazard": val,
            "TelecomRedundancyProvided": val, "CriticalITProtected": val,
            "AccessRouteResilient": val, "AccessDesignConsidersHazards": val,
            "BusinessContinuityPlanInPlace": val, "EmergencyProceduresTested": val,
        },
    }


def _record(level_high: bool, hazard_profile: dict = None) -> dict:
    return {
        "PropertyHeader": {"Header": {"PropertyID": "P-TEST"}},
        "ProtectionMeasures": {
            "ResilienceMeasures": _resilience(level_high),
            "HazardProfile": hazard_profile if hazard_profile is not None else {
                "FloodHazardClass": "High",
                "WindHazardClass": "Medium",
                "FireHazardClass": "Low",
                "SeismicHazardClass": "None",
            },
        },
    }


# ---------------------------------------------------------------------------
# Return value mirrors the writes (and includes the unwritten scores)
# ---------------------------------------------------------------------------

class TestReturnValue:

    def test_return_value_carries_score_breakdown(self):
        """Even though apply_bri_rating doesn't WRITE scores into the record,
        it does RETURN them — so future code (e.g. the new model) can inspect
        them without re-running compute_bri_rating."""
        rec = _record(level_high=True)
        result = apply_bri_rating(rec)
        assert "rating" in result
        assert "score" in result and isinstance(result["score"], float)
        assert "section_scores" in result
        assert "hazard_ratings" in result
        assert "hazard_scores" in result
        # Score breakdown isn't written to the record but is in the result.
        assert set(result["hazard_scores"]) == {"Flood", "Wind", "Fire", "Seismic"}


# ---------------------------------------------------------------------------
# _weaker_rating helper
# ---------------------------------------------------------------------------

class TestWeakerRating:

    def test_a_none_returns_b(self):
        assert _weaker_rating(None, "A") == "A"

    def test_b_none_returns_a(self):
        assert _weaker_rating("AA", None) == "AA"

    def test_returns_weaker_of_two(self):
        # "B" (index 2) is weaker than "A" (index 1).
        assert _weaker_rating("A", "B") == "B"
        assert _weaker_rating("B", "A") == "B"

    def test_equal_returns_first(self):
        assert _weaker_rating("A", "A") == "A"

    def test_invalid_rating_na_fallback(self):
        # "ZZ" not in order → ValueError; a=="N/A"? no → return a.
        assert _weaker_rating("ZZ", "A") == "ZZ"

    def test_invalid_rating_with_na_first(self):
        # a == "N/A" → ValueError branch returns b.
        assert _weaker_rating("N/A", "ZZ") == "ZZ"


# ---------------------------------------------------------------------------
# Water / Flash envelope branches in apply_bri_rating (lines 100/102/104)
# ---------------------------------------------------------------------------

class TestWaterFlashEnvelope:

    def _patch_ratings(self, monkeypatch, hazard_ratings):
        def fake_compute(resilience, hazard_profile=None):
            return {"rating": "A", "score": 0.6,
                    "section_scores": {}, "hazard_ratings": hazard_ratings,
                    "hazard_scores": {}}
        monkeypatch.setattr(bri_mod, "compute_bri_rating", fake_compute)

    def test_water_and_flash_envelope_is_weakest(self, monkeypatch):
        self._patch_ratings(monkeypatch, {
            "Wind": "A", "Fire": "A", "Seismic": "A",
            "Water": "AA", "Flash": "B"})
        rec = {}
        apply_bri_rating(rec)
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        assert gbr["BRIWaterRating"] == "AA"
        assert gbr["BRIFlashRating"] == "B"
        assert gbr["BRIFloodRating"] == "B"  # weakest of (AA, B)

    def test_only_water_present(self, monkeypatch):
        self._patch_ratings(monkeypatch, {
            "Wind": "A", "Fire": "A", "Seismic": "A", "Water": "A"})
        rec = {}
        apply_bri_rating(rec)
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        assert gbr["BRIWaterRating"] == "A"
        assert "BRIFlashRating" not in gbr
        assert gbr["BRIFloodRating"] == "A"

    def test_neither_water_nor_flash_uses_flood(self, monkeypatch):
        self._patch_ratings(monkeypatch, {
            "Wind": "A", "Fire": "A", "Seismic": "A", "Flood": "AA"})
        rec = {}
        apply_bri_rating(rec)
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        assert gbr["BRIFloodRating"] == "AA"
