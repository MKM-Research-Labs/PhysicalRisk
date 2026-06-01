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
Tests for cluster storms, negative equity, and cross-sequence isolation.

Covers:
- Cluster sequence: per-storm queries for a three-storm cluster.
- Negative equity: severe storm in persistent sequence drives negative equity.
- Sequence isolation: storms from different sequences don't contaminate each other.
"""

import json

import pytest

from .conftest import (
    _prop_flood_file, _property_json, _mortgage_json, make_test_client,
)


@pytest.fixture
def cluster_env(tmp_path, monkeypatch):
    """Three-storm cluster sequence. One property flooded by all three storms."""
    def setup(pts_dir):
        _prop_flood_file(pts_dir, "PROP-X", [
            {"storm_id": "STORM-cl1", "sequence_id": "STORM-cluster1", "flooded": True, "exceeded_severe": True, "flood_depth_m": 0.30, "damage_ratio": 0.07},
            {"storm_id": "STORM-cl2", "sequence_id": "STORM-cluster1", "flooded": True, "exceeded_severe": True, "flood_depth_m": 0.55, "damage_ratio": 0.15},
            {"storm_id": "STORM-cl3", "sequence_id": "STORM-cluster1", "flooded": True, "exceeded_severe": True, "flood_depth_m": 0.45, "damage_ratio": 0.11},
        ])

    _property_json(tmp_path / "property.json", [("PROP-X", 500_000)])
    _mortgage_json(tmp_path / "loan.json", [("PROP-X", 380_000, 500_000)])
    return make_test_client(tmp_path, monkeypatch, setup)


@pytest.fixture
def neg_equity_env(tmp_path, monkeypatch):
    """
    Severe storm in a persistent sequence drives a property into negative equity.
    Property value 300k, mortgage 280k. Storm causes 15% damage -> 255k < 280k.
    """
    def setup(pts_dir):
        _prop_flood_file(pts_dir, "PROP-NE", [
            {"storm_id": "STORM-severe", "sequence_id": "STORM-persistent1", "flooded": True, "exceeded_severe": True, "flood_depth_m": 1.5, "damage_ratio": 0.15},
        ])

    _property_json(tmp_path / "property.json", [("PROP-NE", 300_000)])
    _mortgage_json(tmp_path / "loan.json", [("PROP-NE", 280_000, 300_000)])
    return make_test_client(tmp_path, monkeypatch, setup)


# ---------------------------------------------------------------------------
# Cluster sequence — per-storm queries
# ---------------------------------------------------------------------------

class TestClusterIndividualStorms:

    def test_each_cluster_storm_individually_queryable(self, cluster_env):
        for storm_id in ("STORM-cl1", "STORM-cl2", "STORM-cl3"):
            r = cluster_env.get(f"/api/v1/propertyts/{storm_id}/portfolio-impact")
            assert r.status_code == 200, f"{storm_id} returned {r.status_code}"
            data = json.loads(r.data)
            assert data["status"] == "success"

    def test_largest_cluster_storm_has_most_damage(self, cluster_env):
        """STORM-cl2 (damage_ratio=0.15) causes more damage than cl1 or cl3."""
        damages = {}
        for storm_id in ("STORM-cl1", "STORM-cl2", "STORM-cl3"):
            r = cluster_env.get(f"/api/v1/propertyts/{storm_id}/portfolio-impact")
            damages[storm_id] = json.loads(r.data)["portfolio"]["total_damage"]

        assert damages["STORM-cl2"] > damages["STORM-cl1"]
        assert damages["STORM-cl2"] > damages["STORM-cl3"]

    def test_cluster_mortgage_ltv_computed_per_storm(self, cluster_env):
        """post_damage_ltv is recomputed independently for each storm."""
        ltvs = {}
        for storm_id in ("STORM-cl1", "STORM-cl2", "STORM-cl3"):
            r = cluster_env.get(f"/api/v1/propertyts/{storm_id}/portfolio-impact")
            prop = json.loads(r.data)["properties"][0]
            ltvs[storm_id] = prop["post_damage_ltv"]

        assert ltvs["STORM-cl2"] > ltvs["STORM-cl1"]
        assert ltvs["STORM-cl2"] > ltvs["STORM-cl3"]

    def test_unknown_storm_from_sequence_returns_404(self, cluster_env):
        """Querying a storm_id that didn't breach alert returns 404."""
        r = cluster_env.get("/api/v1/propertyts/STORM-nonexistent/portfolio-impact")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Negative equity from severe storm in persistent sequence
# ---------------------------------------------------------------------------

class TestNegativeEquityFromSequence:

    def test_severe_storm_triggers_negative_equity(self, neg_equity_env):
        r = neg_equity_env.get("/api/v1/propertyts/STORM-severe/portfolio-impact")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["portfolio"]["mortgages_in_negative_equity"] == 1

    def test_post_damage_ltv_exceeds_100_pct(self, neg_equity_env):
        """LTV > 100% when outstanding > post-damage value."""
        r = neg_equity_env.get("/api/v1/propertyts/STORM-severe/portfolio-impact")
        data = json.loads(r.data)
        prop = data["properties"][0]
        assert prop["post_damage_ltv"] > 100.0

    def test_damage_amount_computed_correctly(self, neg_equity_env):
        r = neg_equity_env.get("/api/v1/propertyts/STORM-severe/portfolio-impact")
        data = json.loads(r.data)
        prop = data["properties"][0]
        expected = round(300_000 * 0.15, 2)
        assert prop["damage_amount"] == pytest.approx(expected)

    def test_negative_equity_flag_set_on_property(self, neg_equity_env):
        r = neg_equity_env.get("/api/v1/propertyts/STORM-severe/portfolio-impact")
        data = json.loads(r.data)
        assert data["properties"][0]["negative_equity"] is True


# ---------------------------------------------------------------------------
# Sequence isolation
# ---------------------------------------------------------------------------

class TestSequenceIsolation:
    """Two sequences (A and B) affecting the same property — queries are isolated."""

    @pytest.fixture
    def two_sequence_env(self, tmp_path, monkeypatch):
        def setup(pts_dir):
            _prop_flood_file(pts_dir, "PROP-001", [
                {"storm_id": "STORM-seqA1", "sequence_id": "STORM-A", "flooded": True, "exceeded_severe": True, "flood_depth_m": 0.5, "damage_ratio": 0.12},
                {"storm_id": "STORM-seqA2", "sequence_id": "STORM-A", "flooded": True, "exceeded_severe": True, "flood_depth_m": 0.6, "damage_ratio": 0.16},
                {"storm_id": "STORM-seqB1", "sequence_id": "STORM-B", "flooded": True, "exceeded_severe": True, "flood_depth_m": 0.3, "damage_ratio": 0.06},
            ])

        _property_json(tmp_path / "property.json", [("PROP-001", 400_000)])
        _mortgage_json(tmp_path / "loan.json", [("PROP-001", 270_000, 400_000)])
        return make_test_client(tmp_path, monkeypatch, setup)

    def test_seqA_first_storm_returns_only_its_damage(self, two_sequence_env):
        r = two_sequence_env.get("/api/v1/propertyts/STORM-seqA1/portfolio-impact")
        data = json.loads(r.data)
        prop = data["properties"][0]
        assert prop["damage_amount"] == pytest.approx(400_000 * 0.12)

    def test_seqB_storm_returns_only_seqB_damage(self, two_sequence_env):
        r = two_sequence_env.get("/api/v1/propertyts/STORM-seqB1/portfolio-impact")
        data = json.loads(r.data)
        prop = data["properties"][0]
        assert prop["damage_amount"] == pytest.approx(400_000 * 0.06)

    def test_cross_sequence_no_contamination(self, two_sequence_env):
        """Querying seqA1 does not return seqB damage."""
        r1 = two_sequence_env.get("/api/v1/propertyts/STORM-seqA1/portfolio-impact")
        r2 = two_sequence_env.get("/api/v1/propertyts/STORM-seqB1/portfolio-impact")
        dmg_a = json.loads(r1.data)["portfolio"]["total_damage"]
        dmg_b = json.loads(r2.data)["portfolio"]["total_damage"]
        assert dmg_a != dmg_b
        assert dmg_a != dmg_a + dmg_b
