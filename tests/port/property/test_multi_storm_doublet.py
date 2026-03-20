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
Tests for PropertyTimeSeriesGenerator with doublet (2-storm) sequences.

Doublet sequences produce 2 independent flood events per property.
Each storm event has independent damage computed from its own flood depth.
"""

import json
from unittest.mock import patch

import pytest

from tests.port.property.conftest import (
    make_prop, make_gauge_lookup, make_gaugets_multi_storm, make_generator,
)


class TestDoubletSequence:
    """Two storms in a sequence -> 2 independent flood events per property."""

    STORM_DEFS = [
        ("STORM-d001a", 5.5, True),
        ("STORM-d001b", 5.9, True),
    ]

    def test_doublet_produces_two_flood_events(self, tmp_path):
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

        assert result is not None
        prop_file = pts_dir / "PROP-001.json"
        assert prop_file.exists()

        with open(prop_file) as f:
            data = json.load(f)

        flood_events = data["flood_events"]
        # Both storms breached alert -> 2 flood event records
        assert len(flood_events) == 2

    def test_doublet_events_have_distinct_storm_ids(self, tmp_path):
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
        assert "STORM-d001a" in event_storm_ids
        assert "STORM-d001b" in event_storm_ids

    def test_doublet_each_event_has_independent_damage(self, tmp_path):
        """Each storm computes its own damage_ratio from its own flood depth."""
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
            assert "damage_ratio" in event
            assert 0.0 <= event["damage_ratio"] <= 1.0

    def test_summary_counts_all_doublet_floods(self, tmp_path):
        """floods_at_nearest_gauge == 2 for doublet sequence."""
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

        assert result["summary"]["floods_at_nearest_gauge"] == 2
