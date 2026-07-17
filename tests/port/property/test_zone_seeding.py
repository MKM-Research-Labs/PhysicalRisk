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

"""Stratified zone seeding in property-location generation.

The distance x gradient placement model cannot reach the functional
floodplain (MIN_RIVER_DISTANCE_M x the minimum gradient already exceeds
Zone 3b's 0.5 m ceiling), so _generate_locations seeds one property per EA
flood zone at a representative in-band offset. These tests lock in that every
zone — including Zone 3b — is represented.
"""

import random
from unittest.mock import MagicMock

from port.src.property.main.locations import (
    LocationsMixin,
    _zone_from_offset,
    _zone_seed_offsets,
)

ALL_ZONES = {"Zone 1", "Zone 2", "Zone 3a", "Zone 3b"}


def test_seed_offsets_one_per_zone_and_classify_correctly():
    from config.port import EA_FLOOD_ZONE_ELEVATION_BOUNDS

    seeds = _zone_seed_offsets()
    assert len(seeds) == len(EA_FLOOD_ZONE_ELEVATION_BOUNDS)
    # Each seed offset must classify back to its own zone.
    for zone, offset in zip(EA_FLOOD_ZONE_ELEVATION_BOUNDS.keys(), seeds):
        assert _zone_from_offset(offset) == zone
    # The Zone 3b seed must sit in the functional floodplain (< 0.5 m).
    assert _zone_from_offset(seeds[0]) == "Zone 3b"
    assert 0.0 <= seeds[0] < 0.5


class _FakeGen(LocationsMixin):
    """Minimal LocationsMixin host with a handful of synthetic gauges."""

    def __init__(self):
        self.params = MagicMock()
        self.params.AREAS = ["A", "B", "C"]
        self.params.CENTER_LAT = 20.95
        self.params.CENTER_LON = 107.05
        del self.params.GAUGE_POINTS   # force direction fallback
        del self.params.GAUGEPOINTS
        self.params.STREETS = {}
        self.params.AREA_VALUE_FACTORS = {"A": 1.0, "B": 1.0, "C": 1.0}

    def log(self, *a, **k):
        pass

    def _load_synthetic_gauges(self):
        return [
            {"gauge_id": f"SYNTH-{k}", "lat": 20.95 + 0.01 * k,
             "lon": 107.05 + 0.01 * k, "elevation": 5.0 + k}
            for k in range(6)
        ]


class TestZoneSeedingInGenerator:
    def test_all_four_zones_represented(self):
        random.seed(20260615)
        locs = _FakeGen()._generate_locations(24)
        zones = {loc["flood_zone"] for loc in locs}
        assert ALL_ZONES <= zones, f"missing zones: {ALL_ZONES - zones}"

    def test_zone_3b_present_even_for_small_portfolio(self):
        # As few as one property per zone — count == number of zones.
        random.seed(1)
        locs = _FakeGen()._generate_locations(4)
        assert "Zone 3b" in {loc["flood_zone"] for loc in locs}

    def test_seeded_3b_elevation_just_above_gauge(self):
        random.seed(7)
        locs = _FakeGen()._generate_locations(12)
        z3b = [l for l in locs if l["flood_zone"] == "Zone 3b"]
        assert z3b
        for loc in z3b:
            offset = loc["elevation"] - loc["synthetic_gauge_elevation"]
            assert 0.0 <= offset < 0.5
