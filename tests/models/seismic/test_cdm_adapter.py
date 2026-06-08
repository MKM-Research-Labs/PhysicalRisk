# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use is prohibited
# unless separately authorized in writing by MKM Research Labs.

"""Tests for the seismic CDM boundary adapter (cdm_adapter.py).

Covers: the construction-type -> fragility-class mapping; derivation of the
binary GS01-GS18 measure set from the applied SeismicCodes list; extraction of
geometry and site-class fields; and the portfolio builder skipping records that
cannot be modelled.
"""

import pytest

from models.seismic.cdm_adapter import (
    CONSTRUCTION_FRAGILITY_MAP,
    DEFAULT_FRAGILITY_CLASS,
    commercial_features_from_record,
    commercial_portfolio_features,
    map_construction_type,
    seismic_measures_from_record,
)


def _record(*, property_id="C1", commercial_type="Office",
            construction_type="Brick and block", storeys=4,
            latitude=20.95, longitude=107.02, soil_type="Unknown",
            vs30=488.0, hazard_class="Medium", design_pga=0.075,
            seismic_codes=("GS02", "GS08", "GS11", "GS15", "GS16",
                           "GS01", "GS09", "GS10", "GS14")):
    """A minimal commercial CDM record skeleton for the adapter.

    Mirrors the persisted shape: ``ProtectionMeasures`` is a TOP-LEVEL sibling
    of ``CommercialAsset`` (not nested inside it), as written by the commercial
    generator.
    """
    body = {
        "Header": {"PropertyID": property_id},
        "CommercialAttributes": {
            "CommercialType": commercial_type,
            "NumberOfStoreys": storeys,
        },
        "Construction": {"ConstructionType": construction_type},
        "Location": {
            "LatitudeDegrees": latitude,
            "LongitudeDegrees": longitude,
        },
        "RiskAssessment": {"SoilType": soil_type, "SoilVs30Mps": vs30},
    }
    protection = {
        "HazardProfile": {
            "SeismicHazardClass": hazard_class,
            "DesignSeismicPGA": design_pga,
        },
        "RiskAssessment": {
            "GoverningBodyRatings": {
                "IndustryGroups": {
                    "SeismicCodes": list(seismic_codes),
                },
            },
        },
    }
    return {"CommercialAsset": body, "ProtectionMeasures": protection}


# ===========================================================================
# Construction taxonomy
# ===========================================================================


def test_construction_map_covers_every_cdm_menu_value():
    # Every CDM ConstructionType menu option resolves to a known fragility key.
    menu = ["Brick and block", "Timber frame", "Stone",
            "Modern methods", "Mixed construction"]
    for value in menu:
        assert value in CONSTRUCTION_FRAGILITY_MAP


def test_construction_mapping_values():
    assert map_construction_type("Brick and block") == "Masonry_RC"
    assert map_construction_type("Stone") == "Masonry_URM"
    assert map_construction_type("Timber frame") == "Timber"
    assert map_construction_type("Modern methods") == "RC_Modern"
    assert map_construction_type("Mixed construction") == "Default"


def test_construction_mapping_real_commercial_values():
    # The values the commercial generator actually emits (halong + thames).
    assert map_construction_type("Concrete frame") == "RC_PreCode"
    assert map_construction_type("Reinforced concrete") == "RC_Modern"
    assert map_construction_type("Steel frame") == "Steel_MRF"


def test_unknown_or_missing_construction_is_default():
    assert map_construction_type("Cob and thatch") == DEFAULT_FRAGILITY_CLASS
    assert map_construction_type(None) == DEFAULT_FRAGILITY_CLASS


# ===========================================================================
# Geoseismic measures
# ===========================================================================


def test_measures_derived_from_seismic_codes():
    feat = commercial_features_from_record(_record())
    assert feat is not None
    assert feat.has("GS08")
    assert feat.has("GS12") is False  # not in the applied list
    assert "GS15" in feat.measures


def test_measures_uppercased_and_non_gs_dropped():
    rec = _record(seismic_codes=["gs08", "GS12", "WT05", "", "FI09"])
    measures = seismic_measures_from_record(rec)
    assert measures == frozenset({"GS08", "GS12"})


def test_missing_seismic_codes_yield_empty_set():
    rec = _record(seismic_codes=())
    assert seismic_measures_from_record(rec) == frozenset()


# ===========================================================================
# Field extraction
# ===========================================================================


def test_geometry_and_site_class_fields_extracted():
    feat = commercial_features_from_record(_record())
    assert feat.asset_id == "C1"
    assert feat.commercial_type == "Office"
    assert feat.construction_type == "Masonry_RC"
    assert feat.number_of_storeys == 4
    assert feat.latitude == pytest.approx(20.95)
    assert feat.longitude == pytest.approx(107.02)
    assert feat.soil_vs30_mps == pytest.approx(488.0)
    assert feat.seismic_hazard_class == "Medium"
    assert feat.design_seismic_pga == pytest.approx(0.075)
    # Fault proximity is computed at run time from the catchment trace.
    assert feat.fault_proximity_km is None


def test_falls_back_to_uprn_for_asset_id():
    rec = _record(property_id=None)
    rec["CommercialAsset"]["Header"] = {"UPRN": "61910067"}
    feat = commercial_features_from_record(rec)
    assert feat.asset_id == "61910067"


def test_unmodellable_records_return_none():
    no_id = _record()
    no_id["CommercialAsset"]["Header"]["PropertyID"] = None
    assert commercial_features_from_record(no_id) is None

    no_type = _record()
    no_type["CommercialAsset"]["CommercialAttributes"]["CommercialType"] = None
    assert commercial_features_from_record(no_type) is None


def test_portfolio_builder_skips_bad_records():
    good = _record(property_id="GOOD")
    bad = _record(property_id="BAD")
    bad["CommercialAsset"]["CommercialAttributes"]["CommercialType"] = None
    feats = commercial_portfolio_features([good, bad])
    assert [f.asset_id for f in feats] == ["GOOD"]
