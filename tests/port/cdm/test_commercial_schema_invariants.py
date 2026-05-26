# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Structural invariants for COMMERCIAL_SCHEMA.

Fail loudly if a future refactor silently drops a section, mis-types a
leaf, or breaks the menu/options contract that downstream tooling depends
on.
"""

import pytest

from port.cdm.asset.commercial.schema import (
    ACCESSIBILITY_FEATURES_SCHEMA,
    COMMERCIAL_ATTRIBUTES_SCHEMA,
    COMMERCIAL_HEADER_SCHEMA,
    COMMERCIAL_SCHEMA,
    COMMERCIAL_TYPE_OPTIONS,
    DEFAULT_ELEVATION,
    TENANCY_SCHEMA,
)
from port.cdm.asset.resilience import (
    HAZARD_PROFILE_SCHEMA,
    RESILIENCE_LEVELS,
    RESILIENCE_MEASURES_SCHEMA,
)


_VALID_TYPES = {"string", "text", "menu", "decimal", "integer", "boolean", "date"}


def _walk_leaves(node, path=""):
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
        assert set(COMMERCIAL_SCHEMA) == {
            "CommercialAsset",
            "ProtectionMeasures",
            "EnergyPerformance",
            "HistoryAndIncidents",
            "TransactionHistory",
        }

    def test_commercial_asset_subsections(self):
        assert set(COMMERCIAL_SCHEMA["CommercialAsset"]) == {
            "Header",
            "Valuation",
            "CommercialAttributes",
            "AccessibilityFeatures",
            "Tenancy",
            "Construction",
            "Location",
            "RiskAssessment",
        }

    def test_protection_measures_subsections(self):
        assert set(COMMERCIAL_SCHEMA["ProtectionMeasures"]) == {
            "RiskAssessment",
            "HazardProfile",
            "ResilienceMeasures",
        }

    def test_resilience_measures_is_shared_5_section_block(self):
        # COMMERCIAL_SCHEMA must use the same shared resilience dict as residential.
        rm = COMMERCIAL_SCHEMA["ProtectionMeasures"]["ResilienceMeasures"]
        assert rm is RESILIENCE_MEASURES_SCHEMA
        assert set(rm) == {
            "BuildingAssessment",
            "SiteAndDrainage",
            "FloodProtection",
            "FireProtection",
            "ContinuityMeasures",
        }

    def test_hazard_profile_is_shared(self):
        assert (COMMERCIAL_SCHEMA["ProtectionMeasures"]["HazardProfile"]
                is HAZARD_PROFILE_SCHEMA)

    def test_default_elevation_present(self):
        assert isinstance(DEFAULT_ELEVATION, float)
        assert DEFAULT_ELEVATION > 0


# ---------------------------------------------------------------------------
# Commercial-only schema content
# ---------------------------------------------------------------------------


class TestCommercialAttributes:

    def test_required_fields_present(self):
        required = {
            "CommercialType", "UseClassUKO", "BusinessRatesCategory",
            "OccupancyStatus", "PropertyAreaSqm", "NetInternalAreaSqm",
            "NetLettableAreaSqm", "NumberOfStoreys", "ConstructionYear",
            "PropertyPeriod", "PropertyCondition", "TotalUnits",
            "ParkingSpaces", "LoadingBays", "PlantRoomLocation",
            "ServiceCore", "LastMajorWorksDate",
        }
        assert required <= set(COMMERCIAL_ATTRIBUTES_SCHEMA)

    def test_commercial_type_options(self):
        # User-stated portfolio mix in this slice excludes Industrial /
        # Infrastructure — they live in their own asset sub-packages.
        ct = COMMERCIAL_ATTRIBUTES_SCHEMA["CommercialType"]
        assert ct["type"] == "menu"
        assert set(ct["options"]) == set(COMMERCIAL_TYPE_OPTIONS)
        for required_option in ["Office", "Retail", "Hotel", "Leisure",
                                "Healthcare", "MultiFamily", "MixedUse", "Other"]:
            assert required_option in ct["options"]
        assert "Industrial" not in ct["options"]
        assert "Infrastructure" not in ct["options"]

    def test_business_rates_category_options(self):
        opts = COMMERCIAL_ATTRIBUTES_SCHEMA["BusinessRatesCategory"]["options"]
        for required in ["Office", "Shop and Premises", "Hotel"]:
            assert required in opts

    def test_property_period_options_match_residential(self):
        # Vocabulary must match residential so cross-portfolio queries work.
        opts = COMMERCIAL_ATTRIBUTES_SCHEMA["PropertyPeriod"]["options"]
        assert opts == ["Pre-1919", "1919-1944", "1945-1975", "1976-1999",
                        "2000-2008", "2009-Present"]


class TestAccessibilityFeatures:

    def test_expected_fields_present(self):
        assert set(ACCESSIBILITY_FEATURES_SCHEMA) == {
            "DisabledAccess", "GoodsLiftCount", "GoodsLiftCapacityKg",
            "EmergencyExits", "DeliveryBays",
        }

    def test_disabled_access_is_boolean(self):
        assert ACCESSIBILITY_FEATURES_SCHEMA["DisabledAccess"]["type"] == "boolean"


class TestTenancy:

    def test_expected_fields_present(self):
        assert set(TENANCY_SCHEMA) == {
            "AnchorTenant", "WAULT", "ServiceChargeGbpPerSqm",
            "NetInitialYield", "EquivalentYield", "ReversionaryYield",
            "CovenantStrength",
        }

    def test_yields_are_decimal(self):
        for k in ("NetInitialYield", "EquivalentYield", "ReversionaryYield"):
            assert TENANCY_SCHEMA[k]["type"] == "decimal"

    def test_wault_is_decimal(self):
        assert TENANCY_SCHEMA["WAULT"]["type"] == "decimal"

    def test_covenant_strength_options(self):
        opts = TENANCY_SCHEMA["CovenantStrength"]["options"]
        for required in ["AAA", "AA", "A", "BBB", "BB", "B", "Unrated"]:
            assert required in opts


# ---------------------------------------------------------------------------
# Leaf-level type + menu invariants
# ---------------------------------------------------------------------------


class TestLeafInvariants:

    def test_every_leaf_has_valid_type(self):
        for path, fdef in _walk_leaves(COMMERCIAL_SCHEMA):
            assert fdef["type"] in _VALID_TYPES, (
                f"{path}: invalid type {fdef['type']!r}")

    def test_every_leaf_has_description(self):
        for path, fdef in _walk_leaves(COMMERCIAL_SCHEMA):
            assert "description" in fdef, f"{path}: missing description"
            assert isinstance(fdef["description"], str) and fdef["description"]

    def test_menu_fields_have_nonempty_options(self):
        for path, fdef in _walk_leaves(COMMERCIAL_SCHEMA):
            if fdef["type"] == "menu":
                assert "options" in fdef, f"{path}: menu missing options"
                assert isinstance(fdef["options"], list) and fdef["options"]

    def test_resilience_checklist_uses_5_level_vocabulary(self):
        rm = COMMERCIAL_SCHEMA["ProtectionMeasures"]["ResilienceMeasures"]
        for section_name, section in rm.items():
            for field_name, fdef in section.items():
                if field_name == "BasementFloodStrategy":
                    continue  # BasementFloodStrategy uses its own vocab.
                assert fdef.get("options") == RESILIENCE_LEVELS, (
                    f"{section_name}.{field_name}: expected 5-level RESILIENCE_LEVELS, "
                    f"got {fdef.get('options')!r}")

    def test_minimum_leaf_count(self):
        leaves = list(_walk_leaves(COMMERCIAL_SCHEMA))
        assert len(leaves) >= 200, f"Expected ≥200 leaves; got {len(leaves)}"


# ---------------------------------------------------------------------------
# Shared dict identity — guard against accidental copy-paste divergence
# ---------------------------------------------------------------------------


class TestSharedAssetDictsAreShared:

    def test_header_section_shared_with_asset_header(self):
        from port.cdm.asset.header import HEADER_SCHEMA as ASSET_HEADER
        ca = COMMERCIAL_HEADER_SCHEMA
        assert ca["Header"] is ASSET_HEADER["Header"]
        assert ca["Valuation"] is ASSET_HEADER["Valuation"]
        assert ca["Construction"] is ASSET_HEADER["Construction"]
        assert ca["Location"] is ASSET_HEADER["Location"]
