# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Hazard curve data quality and cross-entity consistency (part 2)."""

import json
from pathlib import Path

import pytest

from tests.data._id_consistency_helpers import (
    INPUT_DIR,
    _load_gauge_ids,
    _load_property_ids,
    _load_counterparty_ids,
    _load_trade_counterparty_ids,
    _load_trade_ids,
    _load_propertyhc_ids,
    _load_propertyshd_ids,
    _load_propertyshe_ids,
    CATCHMENT_LAT_BOUNDS,
    CATCHMENT_LON_BOUNDS,
)


def _load_propertyhc_data():
    """Load raw propertyhc.json data."""
    path = INPUT_DIR / "propertyhc.json"
    if not path.exists():
        return {}
    return json.load(open(path)).get("property_hazard_curves", {})


# =========================================================================
# Property hazard curves
# =========================================================================

class TestPropertyHazardCurves:
    """propertyhc.json must be consistent with property.json."""

    def test_propertyhc_count_matches(self):
        """propertyhc.json must have one entry per property."""
        prop_ids = _load_property_ids()
        phc_ids = _load_propertyhc_ids()
        if not phc_ids:
            pytest.skip("propertyhc.json not generated yet")
        assert len(phc_ids) == len(prop_ids), (
            f"propertyhc.json has {len(phc_ids)} entries but property.json "
            f"has {len(prop_ids)}. Regenerate: python app.py port --propertyhc"
        )

    def test_propertyhc_ids_match(self):
        """propertyhc.json IDs must match property.json IDs."""
        prop_ids = _load_property_ids()
        phc_ids = _load_propertyhc_ids()
        if not phc_ids:
            pytest.skip("propertyhc.json not generated yet")
        missing = prop_ids - phc_ids
        extra = phc_ids - prop_ids
        assert len(missing) == 0 and len(extra) == 0, (
            f"propertyhc.json ID mismatch: {len(missing)} missing, "
            f"{len(extra)} extra. Missing: {sorted(missing)[:3]}, "
            f"Extra: {sorted(extra)[:3]}"
        )

    def test_term_structure_exists(self):
        """Every property hazard curve must contain a term_structure."""
        phc = _load_propertyhc_data()
        if not phc:
            pytest.skip("propertyhc.json not generated yet")
        missing = [pid for pid, c in phc.items()
                   if not c.get("term_structure")]
        assert len(missing) == 0, (
            f"{len(missing)} property hazard curves lack term_structure: "
            f"{missing[:5]}"
        )

    def test_severe_trigger_present(self):
        """Every property hazard curve must have a severe flood trigger level."""
        phc = _load_propertyhc_data()
        if not phc:
            pytest.skip("propertyhc.json not generated yet")
        missing = []
        for pid, c in phc.items():
            ts = c.get("term_structure", {})
            if "severe" not in ts:
                missing.append(pid)
        assert len(missing) == 0, (
            f"{len(missing)} property hazard curves lack severe_trigger: "
            f"{missing[:5]}"
        )


# =========================================================================
# Property hazard derived (SHD / SHE)
# =========================================================================

class TestPropertyHazardDerived:
    """propertyshd.json and propertyshe.json must match property.json."""

    def test_propertyshd_count_matches(self):
        """propertyshd.json must have one entry per property."""
        prop_ids = _load_property_ids()
        shd_ids = _load_propertyshd_ids()
        if not shd_ids:
            pytest.skip("propertyshd.json not generated yet")
        assert len(shd_ids) == len(prop_ids), (
            f"propertyshd.json has {len(shd_ids)} entries but property.json "
            f"has {len(prop_ids)}. Regenerate."
        )

    def test_propertyshe_count_matches(self):
        """propertyshe.json must have one entry per property."""
        prop_ids = _load_property_ids()
        she_ids = _load_propertyshe_ids()
        if not she_ids:
            pytest.skip("propertyshe.json not generated yet")
        assert len(she_ids) == len(prop_ids), (
            f"propertyshe.json has {len(she_ids)} entries but property.json "
            f"has {len(prop_ids)}. Regenerate."
        )

    def test_propertyshd_ids_match(self):
        """propertyshd.json IDs must match property.json IDs."""
        prop_ids = _load_property_ids()
        shd_ids = _load_propertyshd_ids()
        if not shd_ids:
            pytest.skip("propertyshd.json not generated yet")
        missing = prop_ids - shd_ids
        assert len(missing) == 0, (
            f"{len(missing)} properties missing from propertyshd.json: "
            f"{sorted(missing)[:5]}"
        )

    def test_propertyshe_ids_match(self):
        """propertyshe.json IDs must match property.json IDs."""
        prop_ids = _load_property_ids()
        she_ids = _load_propertyshe_ids()
        if not she_ids:
            pytest.skip("propertyshe.json not generated yet")
        missing = prop_ids - she_ids
        assert len(missing) == 0, (
            f"{len(missing)} properties missing from propertyshe.json: "
            f"{sorted(missing)[:5]}"
        )
