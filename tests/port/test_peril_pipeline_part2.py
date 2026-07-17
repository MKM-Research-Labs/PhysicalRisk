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

"""Wind-coupled peril scenario pipeline (win / faw / fow). (part 2)

Exercises the two halves of the scenario protocol end to end:

1. :class:`PerilTimeseriesGenerator` derives propertytsw/tsfaw/tsfow from the
   flood spine joined against ``typhoon/damage`` via ``storm_sequences.json``.
2. :class:`PropertyHazardCurveGenerator` prices each derived dir UNCHANGED,
   emitting propertywin/faw/fow.json with the peril spread on the flood spine.

The fixture pins a deterministic flood/wind overlap so the inclusion-exclusion
identities (fow = flood + wind − faw, fow ≥ win, faw ≤ min(flood, wind)) can be
asserted exactly.
"""

import json

import pytest
from db_helpers import tmp_catchment

import database
from port.src.peril import (
    CommercialPerilTimeseriesGenerator,
    PerilTimeseriesGenerator,
)
from port.src.property.propertyhc import PropertyHazardCurveGenerator

NUM_STORMS = 10
# Sequence index → (flood_trigger, wind_trigger). 10 storms, paired 1:1 with
# typhoon events EVT-0000N.
#   flood triggers on 0,1,2,3        → 4
#   wind  triggers on 2,3,4,5,6      → 5
#   faw (∩) = {2,3}                  → 2
#   fow (∪) = {0,1,2,3,4,5,6}        → 7   (== 4 + 5 − 2)
_OVERLAP = {
    0: (True,  False),
    1: (True,  False),
    2: (True,  True),
    3: (True,  True),
    4: (False, True),
    5: (False, True),
    6: (False, True),
    7: (False, False),
    8: (False, False),
    9: (False, False),
}
EXP_FLOOD, EXP_WIND, EXP_FAW, EXP_FOW = 4, 5, 2, 7

# BRI-resilient flood: raising the floor removes the two shallowest floods
# (storms 0 and 1), leaving {2, 3}. Combined with the same wind {2,3,4,5,6}:
#   baw (∩) = {2,3}            → 2
#   bow (∪) = {2,3,4,5,6}      → 5   (== 2 + 5 − 2)
_BRI_FLOOD = {0: False, 1: False, 2: True, 3: True,
              4: False, 5: False, 6: False, 7: False, 8: False, 9: False}
EXP_BRI, EXP_BAW, EXP_BOW = 2, 2, 5


def _write_portfolio(input_dir, ts_subdir, prop_id):
    """Write flood spine ts + typhoon damage + storm_sequences for one asset."""
    pts_dir = input_dir / ts_subdir
    pts_dir.mkdir(parents=True, exist_ok=True)

    flood_events = []
    sequences = []
    damage_dir = input_dir / "typhoon" / "damage"
    damage_dir.mkdir(parents=True, exist_ok=True)

    for i in range(NUM_STORMS):
        sid = f"SEQ-{i}"
        eid = f"EVT-{i:05d}"
        flood, wind = _OVERLAP[i]
        flood_events.append({
            "storm_id": sid,
            "flood_depth_m": 1.0 if flood else 0.0,
            "damage_ratio": 0.4 if flood else 0.0,
            "flooded": flood,
            "exceeded_severe": flood,
        })
        sequences.append({"sequence_id": sid, "event_id": eid})
        # Wind row: peak >= threshold ⇒ is_prs_wind True.
        peak = 60.0 if wind else 10.0
        with open(damage_dir / f"{eid}.json", "w") as f:
            json.dump({
                "event_id": eid,
                "damages": [{
                    "property_id": prop_id,
                    "peak_sustained_ms": peak,
                    "threshold_ms": 50.0,
                }],
            }, f)

    record = {
        "property_id": prop_id,
        "location": {"lat": 51.4, "lon": -0.3},
        "elevation_m": 4.0,
        "floor_level_m": 0.3,
        "flood_zone": "Zone 2",
        "property_type": "Detached",
        "nearest_gauges": [
            {"gauge_id": "GAUGE-001", "distance_m": 1000, "gauge_elevation_m": 3.5},
        ],
        "flood_events": flood_events,
        "summary": {"property_id": prop_id},
    }
    with open(pts_dir / f"{prop_id}.json", "w") as f:
        json.dump(record, f)

    with open(input_dir / "storm_sequences.json", "w") as f:
        json.dump({"sequences": sequences}, f)

    gauge_hc = {
        "metadata": {"catchment_id": "thames", "num_gauges": 1, "num_storms": NUM_STORMS},
        "hazard_curves": {
            "GAUGE-001": {
                "gauge_id": "GAUGE-001",
                "annual_hazard_rate_severe": 0.005,
                "severe_event_count": 4,
            },
        },
    }
    with open(input_dir / "gaugehc.json", "w") as f:
        json.dump(gauge_hc, f)


def _write_bri_ts(input_dir, normal_subdir, bri_subdir, prop_id):
    """Derive a BRI-resilient ts from the normal ts (floor raised → fewer floods).

    The BRI ts carries the SAME storms but re-stamps flooded/exceeded_severe per
    ``_BRI_FLOOD``, mirroring how the BRI ts generator (mode='bri') re-floors the
    flood test. bow/baw read their flood leg off this dir.
    """
    with open(input_dir / normal_subdir / f"{prop_id}.json") as f:
        record = json.load(f)
    for i, e in enumerate(record["flood_events"]):
        bri = _BRI_FLOOD[i]
        e["flooded"] = bri
        e["exceeded_severe"] = bri
    bri_dir = input_dir / bri_subdir
    bri_dir.mkdir(parents=True, exist_ok=True)
    with open(bri_dir / f"{prop_id}.json", "w") as f:
        json.dump(record, f)


@pytest.fixture
def property_dir(tmp_path):
    input_dir = tmp_path / "input" / "thames"
    input_dir.mkdir(parents=True)
    _write_portfolio(input_dir, "propertyts", "PROP-001")
    return input_dir


@pytest.fixture
def property_dir_bri(property_dir):
    """property_dir plus a BRI-resilient ts dir (enables bow/baw)."""
    _write_bri_ts(property_dir, "propertyts", "propertytsb", "PROP-001")
    return property_dir


@pytest.fixture
def commercial_dir(tmp_path):
    input_dir = tmp_path / "input" / "thames"
    input_dir.mkdir(parents=True)
    _write_portfolio(input_dir, "commercialts", "CPROP-001")
    return input_dir


@pytest.fixture
def commercial_dir_bri(commercial_dir):
    _write_bri_ts(commercial_dir, "commercialts", "commercialtsb", "CPROP-001")
    return commercial_dir


def _triggers(ts_dir, prop_id):
    """Count re-stamped PRS triggers (flooded AND exceeded_severe) in a ts dir."""
    with open(ts_dir / f"{prop_id}.json") as f:
        data = json.load(f)
    return sum(1 for e in data["flood_events"]
               if e["flooded"] and e["exceeded_severe"])


class TestPerilSpreadDecomposition:
    """attach_spread_decomposition sources the peril fan canonically from the
    win/faw/fow scenario files (Option A), so the basis-Explorer fan and the
    /win|/faw|/fow routes agree by construction."""

    def _decompose(self, input_dir, prop_id):
        """Build normal + win/faw/fow hc, re-attach decomposition, return it.

        The generators read/write hazard curves through the database seam; bind a
        scratch backend rooted at ``input_dir`` so they resolve there (the same
        path the fixture stages the ts/gaugehc inputs under)."""
        with tmp_catchment(input_dir, "thames"):
            PerilTimeseriesGenerator(input_dir, verbose=False).generate()
            # Normal flood spine first (the decomposition writes onto this curve).
            PropertyHazardCurveGenerator(input_dir, verbose=False).generate()
            for mode in ("win", "faw", "fow"):
                PropertyHazardCurveGenerator(
                    input_dir, verbose=False, mode=mode).generate()
            gen = PropertyHazardCurveGenerator(input_dir, verbose=False)
            n = gen.attach_spread_decomposition()
            assert n >= 1
            data = database.get_property_hazard_curves("thames")
        return data["property_hazard_curves"][prop_id]["spread_decomposition"]

    def test_peril_fan_sourced_from_scenario_files(self, property_dir):
        dec = self._decompose(property_dir, "PROP-001")
        po = dec["peril_outcomes"]
        assert po["source"] == "scenario_files"
        assert po["flood_only"]["count"] == EXP_FLOOD
        assert po["wind_only"]["count"] == EXP_WIND
        assert po["flood_and_wind"]["count"] == EXP_FAW
        assert po["flood_or_wind"]["count"] == EXP_FOW

    def test_scenario_scalar_spreads_attached(self, property_dir):
        dec = self._decompose(property_dir, "PROP-001")
        assert dec["win_spread_bps"] == round(EXP_WIND / NUM_STORMS * 10000, 2)
        assert dec["faw_spread_bps"] == round(EXP_FAW / NUM_STORMS * 10000, 2)
        assert dec["fow_spread_bps"] == round(EXP_FOW / NUM_STORMS * 10000, 2)

    def test_fan_inclusion_exclusion_holds(self, property_dir):
        po = self._decompose(property_dir, "PROP-001")["peril_outcomes"]
        f = po["flood_only"]["count"]
        w = po["wind_only"]["count"]
        faw = po["flood_and_wind"]["count"]
        fow = po["flood_or_wind"]["count"]
        # union = flood + wind − intersection; union ≥ wind; intersection ≤ min.
        assert fow == f + w - faw
        assert fow >= w
        assert faw <= min(f, w)
