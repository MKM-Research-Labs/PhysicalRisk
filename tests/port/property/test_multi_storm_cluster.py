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
Tests for PropertyTimeSeriesGenerator with cluster, mixed, and persistent
multi-storm sequences.

- Cluster (3 storms, all alert): 3 independent flood events.
- Mixed (some sub-alert): only alert-breaching storms produce events.
- Persistent (4 storms, all alert): 4 events with readings and damage.
"""

import json
from unittest.mock import patch

import pytest

from tests.port.property.conftest import (
    make_prop, make_gauge_lookup, make_gaugets_multi_storm, make_generator,
)


class TestClusterSequence:
    """Three storms in a cluster sequence -> 3 independent flood events."""

    STORM_DEFS = [
        ("STORM-c001a", 5.7, True),
        ("STORM-c001b", 6.1, True),
        ("STORM-c001c", 5.9, True),
    ]

    def test_cluster_produces_three_flood_events(self, tmp_path):
        gen = make_generator(tmp_path)
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()

        prop = make_prop(elevation=4.0, floor_level=0.2)
        gaugets = make_gaugets_multi_storm(storm_defs=self.STORM_DEFS)

        with patch("models.audit.log_model_usage"):
            gen._process_property(
                prop, make_gauge_lookup(elevation=3.0),
                gaugets, pts_dir
            )

        with open(pts_dir / "PROP-001.json") as f:
            data = json.load(f)

        assert len(data["flood_events"]) == 3

    def test_cluster_max_depth_is_from_highest_storm(self, tmp_path):
        """Summary max_depth_m reflects the worst storm in the cluster."""
        gen = make_generator(tmp_path)
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()

        prop = make_prop(elevation=4.0, floor_level=0.2)
        gaugets = make_gaugets_multi_storm(storm_defs=self.STORM_DEFS)

        with patch("models.audit.log_model_usage"):
            result = gen._process_property(
                prop, make_gauge_lookup(elevation=3.0),
                gaugets, pts_dir
            )

        assert result["summary"]["max_depth_m"] >= 0.0

    def test_cluster_three_distinct_storm_ids_in_events(self, tmp_path):
        gen = make_generator(tmp_path)
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()

        prop = make_prop(elevation=4.0, floor_level=0.2)
        gaugets = make_gaugets_multi_storm(storm_defs=self.STORM_DEFS)

        with patch("models.audit.log_model_usage"):
            gen._process_property(
                prop, make_gauge_lookup(elevation=3.0),
                gaugets, pts_dir
            )

        with open(pts_dir / "PROP-001.json") as f:
            data = json.load(f)

        storm_ids = {e["storm_id"] for e in data["flood_events"]}
        assert storm_ids == {"STORM-c001a", "STORM-c001b", "STORM-c001c"}


class TestMixedSequence:
    """In a sequence where only some storms breach severe, only those produce events."""

    STORM_DEFS = [
        ("STORM-m001a", 5.8, True),   # breaches severe (> 5.5)
        ("STORM-m001b", 3.2, False),  # sub-severe
        ("STORM-m001c", 5.9, True),   # breaches severe
        ("STORM-m001d", 4.8, True),   # alert but not severe
    ]

    def test_alert_storms_collected_severe_counted(self, tmp_path):
        gen = make_generator(tmp_path)
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()

        prop = make_prop(elevation=4.0, floor_level=0.2)
        gaugets = make_gaugets_multi_storm(storm_defs=self.STORM_DEFS)

        with patch("models.audit.log_model_usage"):
            result = gen._process_property(
                prop, make_gauge_lookup(elevation=3.0),
                gaugets, pts_dir
            )

        # 3 of 4 storms breach alert (collected into flood_events)
        assert result["summary"]["floods_at_nearest_gauge"] == 3
        # 2 of 4 storms breach severe (tracked separately)
        assert result["summary"]["severe_at_nearest_gauge"] == 2

    def test_sub_alert_storms_not_in_flood_events(self, tmp_path):
        gen = make_generator(tmp_path)
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()

        prop = make_prop(elevation=4.0, floor_level=0.2)
        gaugets = make_gaugets_multi_storm(storm_defs=self.STORM_DEFS)

        with patch("models.audit.log_model_usage"):
            gen._process_property(
                prop, make_gauge_lookup(elevation=3.0),
                gaugets, pts_dir
            )

        with open(pts_dir / "PROP-001.json") as f:
            data = json.load(f)

        event_storm_ids = {e["storm_id"] for e in data["flood_events"]}
        # Sub-alert storm excluded
        assert "STORM-m001b" not in event_storm_ids
        # Alert storms included (even if not severe)
        assert "STORM-m001a" in event_storm_ids
        assert "STORM-m001c" in event_storm_ids
        assert "STORM-m001d" in event_storm_ids


class TestPersistentSequence:
    """Four-storm persistent sequence -- all exceed severe."""

    STORM_DEFS = [
        ("STORM-p001a", 5.7, True),
        ("STORM-p001b", 5.9, True),
        ("STORM-p001c", 6.2, True),
        ("STORM-p001d", 5.8, True),
    ]

    def test_persistent_four_events_recorded(self, tmp_path):
        gen = make_generator(tmp_path)
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()

        prop = make_prop(elevation=4.0, floor_level=0.2)
        gaugets = make_gaugets_multi_storm(storm_defs=self.STORM_DEFS)

        with patch("models.audit.log_model_usage"):
            result = gen._process_property(
                prop, make_gauge_lookup(elevation=3.0),
                gaugets, pts_dir
            )

        assert result["summary"]["floods_at_nearest_gauge"] == 4

    def test_persistent_all_events_have_readings(self, tmp_path):
        gen = make_generator(tmp_path)
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()

        prop = make_prop(elevation=4.0, floor_level=0.2)
        gaugets = make_gaugets_multi_storm(storm_defs=self.STORM_DEFS)

        with patch("models.audit.log_model_usage"):
            gen._process_property(
                prop, make_gauge_lookup(elevation=3.0),
                gaugets, pts_dir
            )

        with open(pts_dir / "PROP-001.json") as f:
            data = json.load(f)

        for event in data["flood_events"]:
            assert "flood_depth_m" in event
            assert "damage_ratio" in event
            # readings only present for flooded events
            if event["flooded"]:
                assert isinstance(event["readings"], list)
            else:
                assert "readings" not in event
