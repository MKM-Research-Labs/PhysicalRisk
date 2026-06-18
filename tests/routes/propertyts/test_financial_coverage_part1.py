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

"""Coverage expansion tests for routes/propertyts/financial.py (part 1).

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
# Fixture: environment where property.json / loan.json are missing
# ---------------------------------------------------------------------------

@pytest.fixture
def pts_env_missing_files(tmp_path, monkeypatch):
    """
    Environment where property.json and loan.json do not exist,
    exercising the exception paths in _load_prop_values and _load_rloan_lookup.
    """
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
            "exceeded_severe": True,
            "flood_depth_m": 0.5,
            "damage_ratio": 0.1,
        }],
    }
    (pts_dir / "PROP-001.json").write_text(json.dumps(prop_data))

    # Intentionally do NOT create property.json or loan.json
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
    monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ---------------------------------------------------------------------------
# Fixture: property without mortgage
# ---------------------------------------------------------------------------

@pytest.fixture
def pts_env_no_mortgage(tmp_path, monkeypatch):
    """Environment where property exists in property.json but has no mortgage."""
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
            "exceeded_severe": True,
            "flood_depth_m": 0.5,
            "damage_ratio": 0.1,
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

    # Empty mortgage file — no mortgage for PROP-001
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
# Tests: _load_prop_values exception (lines 64-65)
# ===========================================================================

class TestLoadPropValuesException:
    """When property.json is missing, _load_prop_values catches the exception
    and returns empty dict. Storm endpoint then returns 404 (no properties)."""

    def test_missing_property_json_returns_404(self, pts_env_missing_files):
        r = pts_env_missing_files.get(
            f"/api/v1/propertyts/{STORM_ID}/portfolio-impact"
        )
        # No valuations → prop_id not in prop_values → break → no properties → 404
        assert r.status_code == 404

    def test_missing_property_json_sequence_returns_404(self, pts_env_missing_files):
        r = pts_env_missing_files.get(
            f"/api/v1/propertyts/sequence/{SEQ_ID}/portfolio-impact"
        )
        assert r.status_code == 404


# ===========================================================================
# Tests: _load_rloan_lookup exception (lines 84-85)
# covered implicitly: when loan.json is missing, _load_rloan_lookup
# returns empty dict. Combined with missing property.json above, both
# exception paths run. But let's also test with broken JSON.
# ===========================================================================

class TestLoadMortgageLookupException:

    def test_corrupt_mortgage_json_still_returns_data(self, tmp_path, monkeypatch):
        """When loan.json has invalid JSON, the exception is caught
        and rloan_lookup is empty. Storm endpoint still works if
        property data is fine."""
        from config import config

        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()

        prop_data = {
            "property_id": "PROP-001",
            "flood_events": [{
                "storm_id": STORM_ID,
                "flooded": True,
                "exceeded_severe": True,
                "flood_depth_m": 0.5,
                "damage_ratio": 0.1,
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

        # Write invalid JSON to loan.json
        (tmp_path / "loan.json").write_text("{BROKEN")

        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get(f"/api/v1/propertyts/{STORM_ID}/portfolio-impact")
        assert r.status_code == 200
        # Property should appear without mortgage
        props = r.get_json()["properties"]
        assert len(props) == 1
        assert props[0]["has_rloan"] is False


# ===========================================================================
# Tests: property without mortgage (line 120)
# ===========================================================================

class TestPropertyWithoutMortgage:
    """_build_property_entry else branch (line 120): property has no mortgage."""

    def test_no_mortgage_returns_zero_fill(self, pts_env_no_mortgage):
        r = pts_env_no_mortgage.get(
            f"/api/v1/propertyts/{STORM_ID}/portfolio-impact"
        )
        assert r.status_code == 200
        prop = r.get_json()["properties"][0]
        assert prop["has_rloan"] is False
        assert prop["outstanding_balance"] == 0
        assert prop["current_ltv"] == 0
        assert prop["post_damage_ltv"] == 0
        assert prop["negative_equity"] is False

    def test_no_mortgage_sequence(self, pts_env_no_mortgage):
        r = pts_env_no_mortgage.get(
            f"/api/v1/propertyts/sequence/{SEQ_ID}/portfolio-impact"
        )
        assert r.status_code == 200
        prop = r.get_json()["properties"][0]
        assert prop["has_rloan"] is False
