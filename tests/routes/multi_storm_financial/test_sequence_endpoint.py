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

"""
Tests for the sequence endpoint: max-depth damage model and negative equity.

Covers:
- Sequence endpoint returns max-depth flood event per property across the
  whole sequence (damage = max depth reached in the window).
- Cross-sequence isolation in the sequence endpoint.
- Negative equity driven by the worst storm in a persistent sequence.
"""

import json

import pytest

from .conftest import (
    _prop_flood_file, _property_json, _mortgage_json, make_test_client,
)


@pytest.fixture
def seq_env(tmp_path, monkeypatch):
    """
    Two-property portfolio with a doublet sequence (STORM-test1: d1a + d1b).

    PROP-A: smaller first storm (0.4m), larger second storm (0.65m) — max=0.65m
    PROP-B: only second storm causes flooding (0.55m) — max=0.55m
    PROP-C: flooded by a different sequence (STORM-other) — should not appear
    """
    def setup(pts_dir):
        _prop_flood_file(pts_dir, "PROP-A", [
            {"storm_id": "STORM-d1a", "sequence_id": "STORM-test1", "flooded": True, "exceeded_severe": True, "flood_depth_m": 0.40, "damage_ratio": 0.10},
            {"storm_id": "STORM-d1b", "sequence_id": "STORM-test1", "flooded": True, "exceeded_severe": True, "flood_depth_m": 0.65, "damage_ratio": 0.18},
        ])
        _prop_flood_file(pts_dir, "PROP-B", [
            {"storm_id": "STORM-d1a", "sequence_id": "STORM-test1", "flooded": False, "exceeded_severe": True, "flood_depth_m": 0.0,  "damage_ratio": 0.0},
            {"storm_id": "STORM-d1b", "sequence_id": "STORM-test1", "flooded": True, "exceeded_severe": True, "flood_depth_m": 0.55, "damage_ratio": 0.14},
        ])
        _prop_flood_file(pts_dir, "PROP-C", [
            {"storm_id": "STORM-other1", "sequence_id": "STORM-other", "flooded": True, "exceeded_severe": True, "flood_depth_m": 0.8, "damage_ratio": 0.20},
        ])

    _property_json(tmp_path / "property.json", [
        ("PROP-A", 350_000),
        ("PROP-B", 420_000),
        ("PROP-C", 300_000),
    ])
    _mortgage_json(tmp_path / "loan.json", [
        ("PROP-A", 250_000, 350_000),
        ("PROP-B", 300_000, 420_000),
    ])
    return make_test_client(tmp_path, monkeypatch, setup)


class TestSequenceEndpoint:

    def test_sequence_endpoint_returns_200(self, seq_env):
        r = seq_env.get("/api/v1/propertyts/sequence/STORM-test1/portfolio-impact")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["status"] == "success"

    def test_sequence_id_in_response(self, seq_env):
        r = seq_env.get("/api/v1/propertyts/sequence/STORM-test1/portfolio-impact")
        data = json.loads(r.data)
        assert data["sequence_id"] == "STORM-test1"

    def test_damage_model_is_max_depth(self, seq_env):
        """Response declares the max_depth damage model."""
        r = seq_env.get("/api/v1/propertyts/sequence/STORM-test1/portfolio-impact")
        data = json.loads(r.data)
        assert data["damage_model"] == "max_depth"

    def test_prop_a_uses_max_depth_event(self, seq_env):
        """PROP-A: second storm (0.65m) is worst — sequence damage uses 0.18 ratio."""
        r = seq_env.get("/api/v1/propertyts/sequence/STORM-test1/portfolio-impact")
        data = json.loads(r.data)
        prop_a = next(p for p in data["properties"] if p["property_id"] == "PROP-A")
        assert prop_a["damage_ratio"] == pytest.approx(0.18)
        assert prop_a["damage_amount"] == pytest.approx(350_000 * 0.18)
        assert prop_a["worst_storm_id"] == "STORM-d1b"

    def test_prop_a_not_double_counted(self, seq_env):
        """Damage is max depth, not 0.10 + 0.18 = 0.28."""
        r = seq_env.get("/api/v1/propertyts/sequence/STORM-test1/portfolio-impact")
        data = json.loads(r.data)
        prop_a = next(p for p in data["properties"] if p["property_id"] == "PROP-A")
        assert prop_a["damage_ratio"] < 0.20  # not additive

    def test_prop_b_included_via_second_storm(self, seq_env):
        """PROP-B: first storm depth=0 so excluded, second storm 0.55m -> included."""
        r = seq_env.get("/api/v1/propertyts/sequence/STORM-test1/portfolio-impact")
        data = json.loads(r.data)
        prop_ids = {p["property_id"] for p in data["properties"]}
        assert "PROP-B" in prop_ids

    def test_prop_c_excluded_from_different_sequence(self, seq_env):
        """PROP-C is flooded by STORM-other, not STORM-test1 — must not appear."""
        r = seq_env.get("/api/v1/propertyts/sequence/STORM-test1/portfolio-impact")
        data = json.loads(r.data)
        prop_ids = {p["property_id"] for p in data["properties"]}
        assert "PROP-C" not in prop_ids

    def test_num_floods_per_property_reported(self, seq_env):
        """Each property entry includes num_sequence_floods."""
        r = seq_env.get("/api/v1/propertyts/sequence/STORM-test1/portfolio-impact")
        data = json.loads(r.data)
        prop_a = next(p for p in data["properties"] if p["property_id"] == "PROP-A")
        assert prop_a["num_sequence_floods"] >= 1

    def test_num_storms_in_sequence_reported(self, seq_env):
        """Response includes num_storms_in_sequence."""
        r = seq_env.get("/api/v1/propertyts/sequence/STORM-test1/portfolio-impact")
        data = json.loads(r.data)
        assert "num_storms_in_sequence" in data
        assert data["num_storms_in_sequence"] >= 1

    def test_unknown_sequence_returns_404(self, seq_env):
        r = seq_env.get("/api/v1/propertyts/sequence/STORM-nonexistent/portfolio-impact")
        assert r.status_code == 404

    def test_sequence_damage_less_than_sum_of_storms(self, seq_env):
        """Sequence total damage < sum of individual storm damages (not additive)."""
        r_seq = seq_env.get("/api/v1/propertyts/sequence/STORM-test1/portfolio-impact")
        r_d1a = seq_env.get("/api/v1/propertyts/STORM-d1a/portfolio-impact")
        r_d1b = seq_env.get("/api/v1/propertyts/STORM-d1b/portfolio-impact")

        seq_damage = json.loads(r_seq.data)["portfolio"]["total_damage"]
        dmg_d1a = json.loads(r_d1a.data)["portfolio"]["total_damage"] if r_d1a.status_code == 200 else 0
        dmg_d1b = json.loads(r_d1b.data)["portfolio"]["total_damage"]

        assert seq_damage < dmg_d1a + dmg_d1b  # max, not sum

    def test_sequence_endpoint_options(self, seq_env):
        r = seq_env.options("/api/v1/propertyts/sequence/STORM-test1/portfolio-impact")
        assert r.status_code == 200


class TestSequenceEndpointNegativeEquity:
    """Persistent sequence where worst storm pushes property into negative equity."""

    @pytest.fixture
    def persistent_env(self, tmp_path, monkeypatch):
        def setup(pts_dir):
            _prop_flood_file(pts_dir, "PROP-NE2", [
                {"storm_id": "STORM-p1", "sequence_id": "STORM-persistent2", "flooded": True, "exceeded_severe": True, "flood_depth_m": 0.8, "damage_ratio": 0.10},
                {"storm_id": "STORM-p2", "sequence_id": "STORM-persistent2", "flooded": True, "exceeded_severe": True, "flood_depth_m": 1.2, "damage_ratio": 0.13},
                {"storm_id": "STORM-p3", "sequence_id": "STORM-persistent2", "flooded": True, "exceeded_severe": True, "flood_depth_m": 1.8, "damage_ratio": 0.17},
                {"storm_id": "STORM-p4", "sequence_id": "STORM-persistent2", "flooded": True, "exceeded_severe": True, "flood_depth_m": 1.0, "damage_ratio": 0.11},
            ])

        _property_json(tmp_path / "property.json", [("PROP-NE2", 300_000)])
        _mortgage_json(tmp_path / "loan.json", [("PROP-NE2", 280_000, 300_000)])
        return make_test_client(tmp_path, monkeypatch, setup)

    def test_sequence_selects_worst_storm(self, persistent_env):
        """Sequence damage uses storm p3 (1.8m, ratio=0.17), not p1 or p2."""
        r = persistent_env.get("/api/v1/propertyts/sequence/STORM-persistent2/portfolio-impact")
        data = json.loads(r.data)
        prop = data["properties"][0]
        assert prop["worst_storm_id"] == "STORM-p3"
        assert prop["damage_ratio"] == pytest.approx(0.17)

    def test_sequence_negative_equity_from_worst_storm(self, persistent_env):
        """Worst storm (17% damage on 300k) -> 249k < 280k outstanding -> negative equity."""
        r = persistent_env.get("/api/v1/propertyts/sequence/STORM-persistent2/portfolio-impact")
        data = json.loads(r.data)
        assert data["portfolio"]["mortgages_in_negative_equity"] == 1
        prop = data["properties"][0]
        assert prop["negative_equity"] is True

    def test_sequence_num_floods_is_four(self, persistent_env):
        r = persistent_env.get("/api/v1/propertyts/sequence/STORM-persistent2/portfolio-impact")
        data = json.loads(r.data)
        assert data["properties"][0]["num_sequence_floods"] == 4
