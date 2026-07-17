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

"""Tests for event count PRS spread computation."""

import json

import pytest

from port.src.property.propertyhc import (
    PropertyHazardCurveGenerator,
)


class TestEventCountSpread:
    """Test the event count spread formula: spread = flood_count(severe) / num_storms * 10000."""

    def test_zero_floods_zero_spread(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        # All properties should have spread proportional to flood_count
        for prop_id, pc in data["property_hazard_curves"].items():
            flood_count = pc["flood_count"]
            spreads = pc["term_structure"]["severe"]["prs_spread_bps"]
            expected = round((flood_count / 100) * 10000, 2)  # num_storms=100
            assert spreads[0] == expected, (
                f"{prop_id}: expected {expected}, got {spreads[0]}")

    def test_spread_proportional_to_floods(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        curves = data["property_hazard_curves"]
        # PROP-001 has 5 severe floods (7 total, 2 non-severe excluded)
        # PROP-002 has 2, PROP-003 has 10
        spread1 = curves["PROP-001"]["term_structure"]["severe"]["prs_spread_bps"][0]
        spread2 = curves["PROP-002"]["term_structure"]["severe"]["prs_spread_bps"][0]
        spread3 = curves["PROP-003"]["term_structure"]["severe"]["prs_spread_bps"][0]

        assert spread3 > spread1 > spread2

    def test_spread_is_flat_term_structure(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        spreads = data["property_hazard_curves"]["PROP-001"]["term_structure"]["severe"]["prs_spread_bps"]
        # All tenors should have the same spread (storms are independent)
        assert all(s == spreads[0] for s in spreads)


class TestFloodCountSevereFilter:
    """Verify flood_count only counts events with exceeded_severe=True."""

    def test_flood_count_excludes_non_severe(self, output_dir):
        """PROP-001 has 7 flooded events but only 5 with exceeded_severe=True."""
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        pc = data["property_hazard_curves"]["PROP-001"]
        # 5 severe floods, not 7 total
        assert pc["flood_count"] == 5

    def test_spread_uses_severe_count(self, output_dir):
        """PRS spread must be computed from severe flood count, not total."""
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        pc = data["property_hazard_curves"]["PROP-001"]
        expected_spread = round((5 / 100) * 10000, 2)  # 5 severe / 100 storms
        assert pc["term_structure"]["severe"]["prs_spread_bps"][0] == expected_spread

    def test_all_severe_property_unchanged(self, output_dir):
        """PROP-003 has all events severe — flood_count equals total flooded."""
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        pc = data["property_hazard_curves"]["PROP-003"]
        assert pc["flood_count"] == 10


class TestGetGaugeSevereCount:
    """Test _get_gauge_severe_count static method."""

    def test_returns_severe_event_count(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hc = {"severe_event_count": 7}
        assert gen._get_gauge_severe_count(gauge_hc) == 7

    def test_returns_zero_when_missing(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hc = {"annual_hazard_rate_severe": 0.005}
        assert gen._get_gauge_severe_count(gauge_hc) == 0

    def test_returns_zero_for_empty_dict(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        assert gen._get_gauge_severe_count({}) == 0
