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

"""Tests for the CDM boundary adapter (cdm_adapter.py).

Covers the two-tier resilience resolution the adapter implements:
- the BRI fire grade is read from BRIFireRating, else inferred from FireCodes
- a populated granular checklist overrides the grade fallback
- Grade B maps to "Partial" (below the internal-sprinkler reach threshold) so a
  tall Grade-B building is suppression-unreachable; Grade A maps to "Enhanced"
  so it stays reachable — the headline fire-truck-reach behaviour
- records with no asset id / commercial type are skipped by the portfolio builder
"""

import pytest

from config.fire import load_fire_config
from models.fire.cdm_adapter import (
    CONSTRUCTION_TO_STRUCTURAL_LEVEL,
    FIRE_GRADE_A_CODE,
    GRADE_TO_LEVEL,
    commercial_features_from_record,
    commercial_fire_grade,
    commercial_portfolio_features,
)
from models.fire.response_effectiveness import derive_response_profile


def _record(*, property_id="C1", commercial_type="Office", storeys=10,
            bri_fire_rating=None, fire_codes=None, resilience=None,
            construction_type=None):
    """A minimal commercial CDM record skeleton for the adapter."""
    governing = {}
    if bri_fire_rating is not None:
        governing["BRIFireRating"] = bri_fire_rating
    if fire_codes is not None:
        governing["IndustryGroups"] = {"FireCodes": fire_codes}

    protection = {"RiskAssessment": {"GoverningBodyRatings": governing}}
    if resilience is not None:
        protection["ResilienceMeasures"] = resilience

    body = {
        "Header": {"PropertyID": property_id},
        "CommercialAttributes": {
            "CommercialType": commercial_type,
            "NumberOfStoreys": storeys,
        },
    }
    if construction_type is not None:
        body["Construction"] = {"ConstructionType": construction_type}

    return {
        "CommercialAsset": body,
        "ProtectionMeasures": protection,
    }


# ===========================================================================
# Grade resolution
# ===========================================================================


def test_grade_from_explicit_rating():
    assert commercial_fire_grade(_record(bri_fire_rating="A")) == "A"
    assert commercial_fire_grade(_record(bri_fire_rating="B+")) == "B"


def test_grade_from_fire_codes_fallback():
    # FI09 present -> Grade A; any other fire package -> Grade B.
    assert commercial_fire_grade(_record(fire_codes=[FIRE_GRADE_A_CODE])) == "A"
    assert commercial_fire_grade(_record(fire_codes=["FI04", "FI12"])) == "B"


def test_grade_none_when_no_signal():
    assert commercial_fire_grade(_record()) is None


# ===========================================================================
# Feature mapping
# ===========================================================================


def test_grade_b_maps_to_partial_across_fire_fields():
    feat = commercial_features_from_record(_record(fire_codes=["FI04"]))
    assert feat is not None
    expected = GRADE_TO_LEVEL["B"]
    assert feat.suppression_systems_level == expected
    assert feat.structural_fire_resistance_level == expected
    assert feat.compartments_level == expected


def test_grade_a_maps_to_enhanced():
    feat = commercial_features_from_record(_record(fire_codes=[FIRE_GRADE_A_CODE]))
    assert feat.suppression_systems_level == GRADE_TO_LEVEL["A"]


def test_granular_checklist_overrides_grade():
    # A populated checklist value wins over the grade fallback; "Not assessed"
    # and missing fields defer to it.
    resilience = {
        "FireProtection": {
            "SuppressionSystemsInstalled": "Verified",
            "AutomaticDetectionInstalled": "Not assessed",
        },
    }
    feat = commercial_features_from_record(
        _record(fire_codes=["FI04"], resilience=resilience))
    assert feat.suppression_systems_level == "Verified"
    # "Not assessed" carries no info -> falls back to the Grade-B level.
    assert feat.automatic_detection_level == GRADE_TO_LEVEL["B"]


def test_unmodellable_records_return_none():
    no_id = _record(property_id=None)
    no_id["CommercialAsset"]["Header"]["PropertyID"] = None
    assert commercial_features_from_record(no_id) is None

    no_type = _record()
    no_type["CommercialAsset"]["CommercialAttributes"]["CommercialType"] = None
    assert commercial_features_from_record(no_type) is None


def test_portfolio_builder_skips_bad_records():
    good = _record(property_id="GOOD", fire_codes=["FI04"])
    bad = _record(property_id="BAD")
    bad["CommercialAsset"]["CommercialAttributes"]["CommercialType"] = None
    feats = commercial_portfolio_features([good, bad])
    assert [f.asset_id for f in feats] == ["GOOD"]


# ===========================================================================
# End-to-end: the headline fire-truck-reach behaviour
# ===========================================================================


def test_tall_grade_b_is_suppression_unreachable():
    # A tall Grade-B asset (Partial suppression) above the fire-truck reach has
    # no effective internal sprinklers -> unreachable -> runs to the PNR.
    cfg = load_fire_config()
    reach = cfg.progression.fire_service_reach
    feat = commercial_features_from_record(
        _record(fire_codes=["FI04"], storeys=reach["reach_storeys"] + 5))
    profile = derive_response_profile(feat, cfg.progression)
    assert not profile.suppression_reachable


def test_tall_grade_a_stays_reachable():
    # The Grade-A hotel (FI09 -> Enhanced) clears the internal-sprinkler
    # threshold, so it remains suppression-reachable at the same height.
    cfg = load_fire_config()
    reach = cfg.progression.fire_service_reach
    feat = commercial_features_from_record(
        _record(commercial_type="Hotel", fire_codes=[FIRE_GRADE_A_CODE],
                storeys=reach["reach_storeys"] + 5))
    profile = derive_response_profile(feat, cfg.progression)
    assert profile.suppression_reachable


# ===========================================================================
# Construction type — building-material wiring
# ===========================================================================


def test_construction_type_is_read_from_construction_section():
    feat = commercial_features_from_record(
        _record(construction_type="Reinforced concrete"))
    assert feat.construction_type == "Reinforced concrete"


def test_missing_construction_type_is_none():
    assert commercial_features_from_record(_record()).construction_type is None


def test_construction_drives_structural_fire_resistance_fallback():
    # With no granular checklist, a non-combustible frame raises the structural-
    # fire-resistance level above the Grade-B fallback — material is the physical
    # signal for that field and takes priority over the grade.
    feat = commercial_features_from_record(
        _record(fire_codes=["FI04"], construction_type="Reinforced concrete"))
    assert feat.structural_fire_resistance_level == (
        CONSTRUCTION_TO_STRUCTURAL_LEVEL["Reinforced concrete"])
    # Suppression (an active-protection field) still follows the grade.
    assert feat.suppression_systems_level == GRADE_TO_LEVEL["B"]


def test_granular_checklist_still_overrides_construction():
    # An explicit StructuralFireResistanceAdequate value wins over the
    # construction-derived fallback.
    resilience = {
        "BuildingAssessment": {"StructuralFireResistanceAdequate": "Partial"},
    }
    feat = commercial_features_from_record(
        _record(fire_codes=["FI04"], construction_type="Reinforced concrete",
                resilience=resilience))
    assert feat.structural_fire_resistance_level == "Partial"


def test_tall_grade_b_concrete_is_not_combustible():
    # The headline fix: a tall Grade-B reinforced-concrete building is still
    # suppression-unreachable, but its structure is non-combustible, so it does
    # NOT run to the point of no return the way an unknown/combustible frame does.
    cfg = load_fire_config()
    reach = cfg.progression.fire_service_reach
    feat = commercial_features_from_record(
        _record(fire_codes=["FI04"], construction_type="Reinforced concrete",
                storeys=reach["reach_storeys"] + 5))
    profile = derive_response_profile(feat, cfg.progression)
    assert not profile.suppression_reachable
    assert not profile.structure_combustible
