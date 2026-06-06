# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage expansion tests for routes/propertyts/financial.py (part 2).

Targets uncovered lines: 64-65, 84-85, 120, 193, 258.
- 64-65: _load_prop_values exception path (property.json missing/broken)
- 84-85: _load_rloan_lookup exception path (loan.json missing/broken)
- 120: property without mortgage → zero-fill branch in _build_property_entry
- 193: property_id not in prop_values → break (per-storm)
- 258: property_id not in prop_values → continue (sequence)
"""

import json

import pytest

from tests.routes.propertyts.conftest import SEQ_ID, STORM_ID


# ---------------------------------------------------------------------------
# Fixture: environment where property has no matching valuation data
# ---------------------------------------------------------------------------

@pytest.fixture
def pts_env_no_valuation(tmp_path, monkeypatch):
    """Environment where a PROP file exists but property.json has no matching property."""
    from config import config

    pts_dir = tmp_path / "propertyts"
    pts_dir.mkdir()
    gaugets_dir = tmp_path / "gaugets"
    gaugets_dir.mkdir()

    # Property flood file with an ID that won't appear in property.json
    prop_data = {
        "property_id": "PROP-ORPHAN",
        "flood_events": [{
            "storm_id": STORM_ID,
            "sequence_id": SEQ_ID,
            "flooded": True,
            "exceeded_severe": True,
            "flood_depth_m": 0.8,
            "damage_ratio": 0.15,
        }],
    }
    (pts_dir / "PROP-ORPHAN.json").write_text(json.dumps(prop_data))

    # property.json has a DIFFERENT property
    property_data = {"properties": [{
        "PropertyHeader": {
            "Header": {"PropertyID": "PROP-OTHER"},
            "Valuation": {"PropertyValue": 500000},
        }
    }]}
    (tmp_path / "property.json").write_text(json.dumps(property_data))

    rloan_data = {"loans": []}
    (tmp_path / "loan.json").write_text(json.dumps(rloan_data))

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
    monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ===========================================================================
# Tests: property_id not in prop_values (lines 193, 258)
# ===========================================================================

class TestPropertyNotInPropValues:
    """When property_id from PROP-*.json has no matching entry in property.json,
    the code skips that property."""

    def test_storm_orphan_property_returns_404(self, pts_env_no_valuation):
        """Line 193: break when prop_id not in prop_values → no properties → 404."""
        r = pts_env_no_valuation.get(
            f"/api/v1/propertyts/{STORM_ID}/portfolio-impact"
        )
        assert r.status_code == 404

    def test_sequence_orphan_property_returns_404(self, pts_env_no_valuation):
        """Line 258: continue when prop_id not in prop_values → no properties → 404."""
        r = pts_env_no_valuation.get(
            f"/api/v1/propertyts/sequence/{SEQ_ID}/portfolio-impact"
        )
        assert r.status_code == 404


# ===========================================================================
# Tests: is_prs_flood severe filter
# ===========================================================================

class TestSevereFloodFilter:
    """Portfolio impact must only include PRS-countable floods
    (flooded=True AND exceeded_severe=True)."""

    @pytest.fixture
    def pts_env_sub_severe(self, tmp_path, monkeypatch):
        """Property floods but gauge did NOT exceed severe."""
        from config import config

        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()

        prop_data = {
            "property_id": "PROP-001",
            "flood_events": [{
                "storm_id": STORM_ID,
                "sequence_id": SEQ_ID,
                "flooded": True,
                "exceeded_severe": False,
                "flood_depth_m": 0.3,
                "damage_ratio": 0.06,
            }],
        }
        (pts_dir / "PROP-001.json").write_text(json.dumps(prop_data))

        property_data = {"properties": [{
            "PropertyHeader": {
                "Header": {"PropertyID": "PROP-001"},
                "Valuation": {"PropertyValue": 400000},
            }
        }]}
        (tmp_path / "property.json").write_text(json.dumps(property_data))
        (tmp_path / "loan.json").write_text(json.dumps({"loans": []}))

        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        return app.test_client()

    def test_sub_severe_storm_excluded(self, pts_env_sub_severe):
        """Flood with exceeded_severe=False must not appear in portfolio impact."""
        r = pts_env_sub_severe.get(
            f"/api/v1/propertyts/{STORM_ID}/portfolio-impact"
        )
        assert r.status_code == 404

    def test_sub_severe_sequence_excluded(self, pts_env_sub_severe):
        """Flood with exceeded_severe=False must not appear in sequence impact."""
        r = pts_env_sub_severe.get(
            f"/api/v1/propertyts/sequence/{SEQ_ID}/portfolio-impact"
        )
        assert r.status_code == 404
