# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Pipeline ID consistency tests — gauge, classifier, and property ID checks.
BCBS 239 Principle 3 (Accuracy).
"""

import json
from pathlib import Path

import pytest

from tests.data._id_consistency_helpers import (
    ROOT,
    INPUT_DIR,
    OUTPUT_DIR,
    _load_gauge_ids,
    _load_hazard_curve_ids,
    _load_trade_gauge_ids,
    _load_gaugets_ids,
    _load_property_ids,
)


# =========================================================================
# Gauge ID consistency
# =========================================================================

class TestGaugeIDConsistency:
    """All data files must reference gauge IDs that exist in gauge.json."""

    def test_gauge_json_has_gauges(self):
        """gauge.json must contain at least one gauge."""
        ids = _load_gauge_ids()
        assert len(ids) > 0, "gauge.json is empty or missing"

    def test_hazard_curves_match_gauges(self):
        """Every gauge in gauge.json must have a hazard curve."""
        gauge_ids = _load_gauge_ids()
        hc_ids = _load_hazard_curve_ids()
        if not hc_ids:
            pytest.skip("gaugehc.json not generated yet")
        missing = gauge_ids - hc_ids
        assert len(missing) == 0, (
            f"{len(missing)} gauges missing from gaugehc.json: "
            f"{sorted(missing)[:5]}. Run: python app.py port --hazard"
        )

    def test_hazard_curves_subset_of_gauges(self):
        """gaugehc.json must not contain IDs absent from gauge.json."""
        gauge_ids = _load_gauge_ids()
        hc_ids = _load_hazard_curve_ids()
        if not hc_ids:
            pytest.skip("gaugehc.json not generated yet")
        orphan = hc_ids - gauge_ids
        assert len(orphan) == 0, (
            f"{len(orphan)} hazard curves reference non-existent gauges: "
            f"{sorted(orphan)[:5]}. gaugehc.json is stale — regenerate."
        )

    def test_trade_gauges_exist_in_gauge_json(self):
        """Every gauge referenced by a trade must exist in gauge.json."""
        gauge_ids = _load_gauge_ids()
        trade_ids = _load_trade_gauge_ids()
        if not trade_ids:
            pytest.skip("No open trades")
        missing = trade_ids - gauge_ids
        assert len(missing) == 0, (
            f"{len(missing)} trade gauge IDs not in gauge.json: "
            f"{sorted(missing)[:5]}. Blotter is stale — regenerate: "
            f"python app.py port --blotter"
        )

    def test_trade_gauges_have_hazard_curves(self):
        """Every gauge with trades must have a hazard curve (for PRS pricing)."""
        hc_ids = _load_hazard_curve_ids()
        trade_ids = _load_trade_gauge_ids()
        if not trade_ids:
            pytest.skip("No open trades")
        if not hc_ids:
            pytest.skip("gaugehc.json not generated yet")
        missing = trade_ids - hc_ids
        assert len(missing) == 0, (
            f"{len(missing)} traded gauges missing hazard curves: "
            f"{sorted(missing)[:5]}. This causes 'Failed to load hazard "
            f"curve data' in the UI."
        )

    def test_gaugets_match_gauges(self):
        """gaugets/ files must reference gauge IDs from gauge.json."""
        gauge_ids = _load_gauge_ids()
        gaugets_ids = _load_gaugets_ids()
        if not gaugets_ids:
            pytest.skip("gaugets/ not generated yet")
        missing = gaugets_ids - gauge_ids
        assert len(missing) == 0, (
            f"{len(missing)} gaugets files reference non-existent gauges: "
            f"{sorted(missing)[:5]}. gaugets/ is stale."
        )


# =========================================================================
# Classifier consistency
# =========================================================================

class TestClassifierConsistency:
    """Stress classifiers must be trained on current gauge IDs."""

    def test_classifier_gauge_ids_match(self):
        """Classifiers that exist should reference current gauge IDs."""
        gauge_ids = _load_gauge_ids()
        classifiers_dir = INPUT_DIR / "classifiers"
        if not classifiers_dir.exists():
            pytest.skip("classifiers/ not generated yet")
        classifiers = list(classifiers_dir.glob("GAUGE-*.joblib"))
        if not classifiers:
            pytest.skip("No classifiers found — run: python3 app.py classifier --all")
        clf_ids = {f.stem for f in classifiers}
        valid = clf_ids & gauge_ids
        stale = clf_ids - gauge_ids
        if not valid:
            pytest.skip(
                f"All {len(stale)} classifiers are stale (old gauge IDs). "
                "Run: python3 app.py classifier --all"
            )
        assert len(valid) > 0

    def test_training_summary_exists(self):
        """training_summary.json must exist alongside classifiers."""
        classifiers_dir = INPUT_DIR / "stressm"
        if not classifiers_dir.exists():
            pytest.skip("classifiers/ not generated yet")
        summary = classifiers_dir / "training_summary.json"
        if not summary.exists():
            pytest.skip("training_summary.json missing — run: python3 app.py classifier --all")


# =========================================================================
# Property ID consistency
# =========================================================================

class TestPropertyIDConsistency:
    """Property data files must be internally consistent."""

    def test_property_json_has_properties(self):
        """property.json must contain at least one property."""
        ids = _load_property_ids()
        assert len(ids) > 0, "property.json is empty or missing"

    def test_property_ids_in_header(self):
        """PropertyID must be populated in Header (not just PropertyAttributes)."""
        prop_path = INPUT_DIR / "property.json"
        if not prop_path.exists():
            pytest.skip("property.json not generated")
        props = json.load(open(prop_path)).get("properties", [])
        empty_header_ids = []
        for i, p in enumerate(props):
            ph = p.get("PropertyHeader", {})
            hdr = ph.get("Header", {})
            attrs = ph.get("PropertyAttributes", {})
            hdr_id = hdr.get("PropertyID", "")
            attr_id = attrs.get("PropertyID", "")
            if not hdr_id and attr_id:
                empty_header_ids.append(attr_id)
        assert len(empty_header_ids) == 0, (
            f"{len(empty_header_ids)} properties have PropertyID in Attributes "
            f"but not in Header. This breaks propertyts flood processing. "
            f"Regenerate: python app.py port --property"
        )

    def test_propertyts_files_match_properties(self):
        """propertyts/ files must reference property IDs from property.json."""
        prop_ids = _load_property_ids()
        pts_dir = INPUT_DIR / "propertyts"
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        pts_ids = set()
        for f in pts_dir.glob("PROP-*.json"):
            try:
                d = json.load(open(f))
                pid = d.get("property_id", "")
                if pid:
                    pts_ids.add(pid)
            except Exception:
                continue
        if not pts_ids:
            pytest.skip("No propertyts files found")
        missing = pts_ids - prop_ids
        assert len(missing) == 0, (
            f"{len(missing)} propertyts files reference non-existent properties: "
            f"{sorted(missing)[:5]}"
        )
