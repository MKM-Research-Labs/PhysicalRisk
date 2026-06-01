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

"""
Tests for doublet sequence — individual storm queries.

Covers per-storm endpoint behaviour: each storm in a doublet sequence
is queryable independently with correct damage amounts.
"""

import json

import pytest

from .conftest import (
    _prop_flood_file, _property_json, _mortgage_json, make_test_client,
)


@pytest.fixture
def doublet_env(tmp_path, monkeypatch):
    """
    Two-property portfolio hit by a doublet sequence (STORM-d1a + STORM-d1b).

    PROP-A: flooded by both storms (elevation low enough)
    PROP-B: flooded by storm d1b only (higher elevation, misses smaller d1a)
    """
    def setup(pts_dir):
        _prop_flood_file(pts_dir, "PROP-A", [
            {"storm_id": "STORM-d1a", "sequence_id": "STORM-doublet1", "flooded": True, "exceeded_severe": True, "flood_depth_m": 0.40, "damage_ratio": 0.10},
            {"storm_id": "STORM-d1b", "sequence_id": "STORM-doublet1", "flooded": True, "exceeded_severe": True, "flood_depth_m": 0.65, "damage_ratio": 0.18},
        ])
        _prop_flood_file(pts_dir, "PROP-B", [
            {"storm_id": "STORM-d1a", "sequence_id": "STORM-doublet1", "flooded": False, "exceeded_severe": True, "flood_depth_m": 0.0, "damage_ratio": 0.0},
            {"storm_id": "STORM-d1b", "sequence_id": "STORM-doublet1", "flooded": True, "exceeded_severe": True, "flood_depth_m": 0.55, "damage_ratio": 0.14},
        ])

    _property_json(tmp_path / "property.json", [
        ("PROP-A", 350_000),
        ("PROP-B", 420_000),
    ])
    _mortgage_json(tmp_path / "loan.json", [
        ("PROP-A", 250_000, 350_000),
        ("PROP-B", 300_000, 420_000),
    ])
    return make_test_client(tmp_path, monkeypatch, setup)


class TestDoubletIndividualStorms:

    def test_first_storm_returns_only_flooded_properties(self, doublet_env):
        """Query STORM-d1a: only PROP-A (depth>0) appears; PROP-B depth=0 excluded."""
        r = doublet_env.get("/api/v1/propertyts/STORM-d1a/portfolio-impact")
        assert r.status_code == 200
        data = json.loads(r.data)
        prop_ids = {p["property_id"] for p in data["properties"]}
        assert "PROP-A" in prop_ids
        assert "PROP-B" not in prop_ids  # depth was 0.0

    def test_second_storm_returns_both_properties(self, doublet_env):
        """Query STORM-d1b: both PROP-A and PROP-B have positive depth."""
        r = doublet_env.get("/api/v1/propertyts/STORM-d1b/portfolio-impact")
        assert r.status_code == 200
        data = json.loads(r.data)
        prop_ids = {p["property_id"] for p in data["properties"]}
        assert "PROP-A" in prop_ids
        assert "PROP-B" in prop_ids

    def test_first_storm_damage_is_independent_of_second(self, doublet_env):
        """STORM-d1a damage for PROP-A uses only that storm's damage_ratio."""
        r = doublet_env.get("/api/v1/propertyts/STORM-d1a/portfolio-impact")
        data = json.loads(r.data)
        prop_a = next(p for p in data["properties"] if p["property_id"] == "PROP-A")
        expected_damage = round(350_000 * 0.10, 2)
        assert prop_a["damage_amount"] == pytest.approx(expected_damage)

    def test_second_storm_larger_damage_for_prop_a(self, doublet_env):
        """STORM-d1b causes more damage to PROP-A (deeper flood)."""
        r1 = doublet_env.get("/api/v1/propertyts/STORM-d1a/portfolio-impact")
        r2 = doublet_env.get("/api/v1/propertyts/STORM-d1b/portfolio-impact")
        d1 = json.loads(r1.data)
        d2 = json.loads(r2.data)

        dmg1 = next(p["damage_amount"] for p in d1["properties"]
                    if p["property_id"] == "PROP-A")
        dmg2 = next(p["damage_amount"] for p in d2["properties"]
                    if p["property_id"] == "PROP-A")

        assert dmg2 > dmg1  # second (deeper) storm causes more damage

    def test_portfolio_totals_differ_between_storms(self, doublet_env):
        """Total damage is different for each storm in the doublet."""
        r1 = doublet_env.get("/api/v1/propertyts/STORM-d1a/portfolio-impact")
        r2 = doublet_env.get("/api/v1/propertyts/STORM-d1b/portfolio-impact")
        total1 = json.loads(r1.data)["portfolio"]["total_damage"]
        total2 = json.loads(r2.data)["portfolio"]["total_damage"]
        assert total2 > total1

    def test_storm_id_in_response_matches_query(self, doublet_env):
        """Response storm_id matches the queried storm."""
        r = doublet_env.get("/api/v1/propertyts/STORM-d1b/portfolio-impact")
        data = json.loads(r.data)
        assert data["storm_id"] == "STORM-d1b"
