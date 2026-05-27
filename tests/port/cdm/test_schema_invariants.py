# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Structural invariants for PROPERTY_SCHEMA after the v10→v11 migration.

These tests are deliberately strict — they fail loudly if a future refactor
silently drops a section, mis-types a leaf, or breaks the menu/options
contract that the v11 spreadsheet and the rand generator both depend on.

Covers:
  - All five expected top-level sections exist.
  - Every sub-section path is present (PropertyHeader.Valuation, ProtectionMeasures.HazardProfile, etc.).
  - Every leaf field has a valid type from the allowed set.
  - Menu fields must declare `options`; the option list is non-empty.
  - BRI rating + score fields exist on GoverningBodyRatings.
  - Resilience checklist uses the 5-level RESILIENCE_LEVELS vocabulary.
  - HazardProfile uses the 5-level hazard-class vocabulary.
"""

import pytest

from port.cdm.asset.residential.schema import PROPERTY_SCHEMA
from port.cdm.asset.resilience import (
    HAZARD_PROFILE_SCHEMA,
    RESILIENCE_LEVELS,
    RESILIENCE_MEASURES_SCHEMA,
)


_VALID_TYPES = {"string", "text", "menu", "decimal", "integer", "boolean", "date"}


def _walk_leaves(node, path=""):
    """Yield (dotted_path, field_def) for every leaf in the schema."""
    if not isinstance(node, dict):
        return
    for k, v in node.items():
        if not isinstance(v, dict):
            continue
        sub_path = f"{path}.{k}" if path else k
        if "type" in v:
            yield sub_path, v
        else:
            yield from _walk_leaves(v, sub_path)


# ---------------------------------------------------------------------------
# Top-level + sub-section presence
# ---------------------------------------------------------------------------

class TestTopLevelSections:

    def test_five_top_level_sections(self):
        assert set(PROPERTY_SCHEMA) == {
            "PropertyHeader", "ProtectionMeasures",
            "EnergyPerformance", "HistoryAndIncidents",
            "TransactionHistory",
        }

    def test_property_header_sub_sections(self):
        assert set(PROPERTY_SCHEMA["PropertyHeader"]) == {
            "Header", "Valuation", "PropertyAttributes",
            "Construction", "Location", "RiskAssessment", "Contents",
        }

    def test_protection_measures_sub_sections(self):
        assert set(PROPERTY_SCHEMA["ProtectionMeasures"]) == {
            "RiskAssessment", "HazardProfile", "ResilienceMeasures",
        }

    def test_protection_measures_risk_assessment_split(self):
        ra = PROPERTY_SCHEMA["ProtectionMeasures"]["RiskAssessment"]
        assert set(ra) == {"InsuranceBodyRatings", "GoverningBodyRatings"}

    def test_resilience_measures_five_buckets(self):
        rm = PROPERTY_SCHEMA["ProtectionMeasures"]["ResilienceMeasures"]
        assert set(rm) == {
            "BuildingAssessment", "SiteAndDrainage",
            "FloodProtection", "FireProtection", "ContinuityMeasures",
        }

    def test_transaction_history_sub_sections(self):
        assert set(PROPERTY_SCHEMA["TransactionHistory"]) == {
            "Purchase", "Sales", "Rental", "Insurance",
        }

    def test_history_and_incidents_sub_sections(self):
        assert set(PROPERTY_SCHEMA["HistoryAndIncidents"]) == {
            "EnvironmentalIssues", "FireIncidents",
            "FloodEvents", "GroundConditions",
        }

    def test_energy_performance_sub_sections(self):
        assert set(PROPERTY_SCHEMA["EnergyPerformance"]) == {
            "Ratings", "EnergyUsage", "BuildingFabric",
        }


# ---------------------------------------------------------------------------
# Leaf-level invariants
# ---------------------------------------------------------------------------

class TestLeafInvariants:

    def test_all_types_are_valid(self):
        for path, fdef in _walk_leaves(PROPERTY_SCHEMA):
            assert fdef["type"] in _VALID_TYPES, (
                f"{path} has invalid type {fdef['type']!r}"
            )

    def test_menu_fields_have_options(self):
        for path, fdef in _walk_leaves(PROPERTY_SCHEMA):
            if fdef["type"] == "menu":
                assert "options" in fdef, f"{path} is menu but has no options"
                assert isinstance(fdef["options"], list)
                assert len(fdef["options"]) > 0, f"{path} has empty options list"

    def test_every_leaf_has_description(self):
        for path, fdef in _walk_leaves(PROPERTY_SCHEMA):
            assert "description" in fdef, f"{path} missing description"
            assert isinstance(fdef["description"], str)
            assert len(fdef["description"]) > 0, f"{path} has empty description"


# ---------------------------------------------------------------------------
# BRI rating + score field contract
# ---------------------------------------------------------------------------

class TestBRIRatingFields:

    @pytest.fixture
    def gbr(self):
        return PROPERTY_SCHEMA["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]

    def test_overall_bri_rating_menu(self, gbr):
        assert gbr["BRIRating"]["type"] == "menu"
        assert gbr["BRIRating"]["options"] == ["AA", "AA+", "A", "A+", "B", "B+", "NR"]

    def test_overall_bri_score_decimal(self, gbr):
        assert gbr["BRIScore"]["type"] == "decimal"

    @pytest.mark.parametrize("hazard", ["Flood", "Wind", "Fire", "Seismic"])
    def test_per_hazard_rating(self, gbr, hazard):
        f = gbr[f"BRI{hazard}Rating"]
        assert f["type"] == "menu"
        assert f["options"] == ["AA", "A", "B", "NR", "N/A"]

    @pytest.mark.parametrize("hazard", ["Flood", "Wind", "Fire", "Seismic"])
    def test_per_hazard_score(self, gbr, hazard):
        f = gbr[f"BRI{hazard}Score"]
        assert f["type"] == "decimal"

    def test_metadata_fields_present(self, gbr):
        for k in ("BRIDate", "BRIRatingVersion", "BRIRatingAgent"):
            assert k in gbr


# ---------------------------------------------------------------------------
# Resilience uses the 5-level vocabulary
# ---------------------------------------------------------------------------

class TestResilienceVocabulary:

    def test_levels_are_the_canonical_five(self):
        assert RESILIENCE_LEVELS == [
            "Not assessed", "Partial", "Meets minimum", "Enhanced", "Verified",
        ]

    def test_every_resilience_field_uses_resilience_levels(self):
        offenders = []
        for section_name, fields in RESILIENCE_MEASURES_SCHEMA.items():
            for fname, fdef in fields.items():
                if fname == "BasementFloodStrategy":
                    continue  # has its own vocabulary
                if fdef.get("options") != RESILIENCE_LEVELS:
                    offenders.append(f"{section_name}.{fname}")
        assert offenders == [], (
            f"Resilience fields not using RESILIENCE_LEVELS: {offenders}"
        )

    def test_basement_flood_strategy_keeps_own_vocab(self):
        f = RESILIENCE_MEASURES_SCHEMA["SiteAndDrainage"]["BasementFloodStrategy"]
        assert f["options"] == [
            "None", "No basement",
            "Flood-resistant basement",
            "Deliberately floodable with protection",
        ]


# ---------------------------------------------------------------------------
# HazardProfile vocabulary
# ---------------------------------------------------------------------------

class TestHazardProfile:

    @pytest.mark.parametrize("hazard", ["Flood", "Wind", "Seismic", "Fire"])
    def test_hazard_class_options(self, hazard):
        f = HAZARD_PROFILE_SCHEMA[f"{hazard}HazardClass"]
        assert f["type"] == "menu"
        assert f["options"] == ["None", "Low", "Medium", "High", "Extreme"]


# ---------------------------------------------------------------------------
# Total leaf count is at least what we expect
# ---------------------------------------------------------------------------

class TestSchemaSize:

    def test_at_least_200_leaf_fields(self):
        leaves = list(_walk_leaves(PROPERTY_SCHEMA))
        assert len(leaves) >= 200, (
            f"PROPERTY_SCHEMA should have at least 200 leaves; got {len(leaves)}. "
            "If you intentionally shrank the schema, update this number."
        )
