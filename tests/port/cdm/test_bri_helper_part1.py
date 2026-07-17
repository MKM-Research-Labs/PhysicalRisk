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

"""Tests for the BRI helper (src/port/cdm/asset/residential/bri.py) (part 1).

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
# apply_bri_rating writes the expected field set
# ---------------------------------------------------------------------------

class TestApplyBriRatingFieldSet:

    def test_ratings_and_metadata_are_written(self):
        rec = _record(level_high=True)
        apply_bri_rating(rec, agent="Bureau Veritas")
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        # Letter ratings
        assert gbr["BRIRating"] in ("AA", "AA+", "A", "A+", "B", "B+", "NR")
        for h in ("Flood", "Wind", "Fire", "Seismic"):
            assert gbr[f"BRI{h}Rating"] in ("AA", "A", "B", "NR", "N/A")
        # Metadata
        assert gbr["BRIRatingVersion"] == "BRI v1.6"
        assert gbr["BRIRatingAgent"] == "Bureau Veritas"
        assert gbr["BRIDate"] == date.today().isoformat()

    def test_score_fields_are_NOT_written(self):
        """A downstream methodology owns the score fields; this helper must not
        write them. The five score fields must be absent from the dict."""
        rec = _record(level_high=True)
        apply_bri_rating(rec)
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        for k in ("BRIScore", "BRIFloodScore", "BRIWindScore", "BRIFireScore", "BRISeismicScore"):
            assert k not in gbr, f"{k} should not be written by apply_bri_rating; got {gbr.get(k)!r}"


# ---------------------------------------------------------------------------
# Hazard applicability
# ---------------------------------------------------------------------------

class TestHazardApplicability:

    def test_none_hazard_class_produces_na(self):
        rec = _record(level_high=True, hazard_profile={
            "FloodHazardClass": "Medium",
            "WindHazardClass": "None",
            "FireHazardClass": "None",
            "SeismicHazardClass": "None",
        })
        apply_bri_rating(rec)
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        assert gbr["BRIFloodRating"] != "N/A"
        assert gbr["BRIWindRating"] == "N/A"
        assert gbr["BRIFireRating"] == "N/A"
        assert gbr["BRISeismicRating"] == "N/A"

    def test_missing_hazard_profile_defaults_all_applicable(self):
        rec = {
            "PropertyHeader": {"Header": {"PropertyID": "P-TEST"}},
            "ProtectionMeasures": {"ResilienceMeasures": _resilience(level_high=False)},
        }
        apply_bri_rating(rec)
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        # With no HazardProfile, every hazard is treated as applicable, so
        # no rating should be "N/A".
        for h in ("Flood", "Wind", "Fire", "Seismic"):
            assert gbr[f"BRI{h}Rating"] != "N/A"


# ---------------------------------------------------------------------------
# kwargs
# ---------------------------------------------------------------------------

class TestApplyBriRatingKwargs:

    def test_rating_date_override(self):
        rec = _record(level_high=True)
        apply_bri_rating(rec, rating_date="2024-01-15")
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        assert gbr["BRIDate"] == "2024-01-15"

    def test_agent_optional(self):
        rec = _record(level_high=True)
        apply_bri_rating(rec)  # no agent passed
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        assert "BRIRatingAgent" not in gbr or gbr["BRIRatingAgent"] is None

    def test_version_override(self):
        rec = _record(level_high=True)
        apply_bri_rating(rec, version="BRI v2.0-alpha")
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        assert gbr["BRIRatingVersion"] == "BRI v2.0-alpha"


# ---------------------------------------------------------------------------
# publish_letter_ratings gate (catchments without a certified BRI regime)
# ---------------------------------------------------------------------------

class TestPublishLetterRatingsGate:
    """When a catchment has no certified BRI letter-rating regime (e.g. Thames,
    PUBLISH_BRI_LETTER_RATINGS=False) every letter grade is stamped 'NR' while
    the numeric score fields (written by a separate helper) stay untouched."""

    _LETTER_FIELDS = ("BRIRating", "BRIWindRating", "BRIFireRating",
                      "BRISeismicRating", "BRIFloodRating")

    def test_all_letter_ratings_are_NR_when_not_publishing(self):
        # level_high=True would normally yield strong (AA/A) grades.
        rec = _record(level_high=True)
        apply_bri_rating(rec, agent="Bureau Veritas",
                         publish_letter_ratings=False)
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        for field in self._LETTER_FIELDS:
            assert gbr[field] == "NR", f"{field} should be NR; got {gbr[field]!r}"

    def test_metadata_still_written_when_not_publishing(self):
        rec = _record(level_high=True)
        apply_bri_rating(rec, agent="Bureau Veritas",
                         publish_letter_ratings=False)
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        assert gbr["BRIRatingVersion"] == "BRI v1.6"
        assert gbr["BRIDate"] == date.today().isoformat()

    def test_water_flash_subratings_not_written_when_not_publishing(self):
        rec = _record(level_high=True)
        apply_bri_rating(rec, publish_letter_ratings=False)
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        assert "BRIWaterRating" not in gbr
        assert "BRIFlashRating" not in gbr

    def test_default_publishes_real_grades(self):
        """Sanity: the default (publish=True) path still emits real grades."""
        rec = _record(level_high=True)
        apply_bri_rating(rec)
        gbr = rec["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
        # Strong resilience should not collapse every grade to NR.
        assert any(gbr[f] != "NR" for f in self._LETTER_FIELDS)
