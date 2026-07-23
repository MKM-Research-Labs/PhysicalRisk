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

"""Coverage tests for the property-HC wind mixin — the unmapped-flood union
branch plus the seq/damage-index cache and malformed-file fallbacks."""

import json

from port.src.property.hc.pricing._wind import _WindMixin


class _Host(_WindMixin):
    def __init__(self, output_dir):
        self.output_dir = output_dir


def _write(path, obj):
    path.write_text(json.dumps(obj))


class TestWindMixinCoverage:
    def test_wind_union_counts_unmapped_flood(self, tmp_path):
        # Non-empty wind index so _wind_union does not early-return None.
        dmg = tmp_path / "typhoon" / "damage"
        dmg.mkdir(parents=True)
        _write(dmg / "EVT-00001.json", {"damages": [
            {"property_id": "PROP-1", "peak_sustained_ms": 70.0,
             "threshold_ms": 50.0, "v_50_eff_ms": 50.0}]})
        # No storm_sequences.json -> seq map empty -> the flooded storm is
        # unmapped and counts on its own (line 59).
        host = _Host(tmp_path)
        flood_events = [{"flooded": True, "exceeded_severe": True, "storm_id": "SEQ-9"}]
        res = host._wind_union("PROP-2", flood_events, num_storms=100)
        assert res is not None
        assert res["union_count"] == 1   # flood_unmapped += 1
        assert res["joint_count"] == 0

    def test_seq_to_event_map_caches_and_swallows_bad_file(self, tmp_path):
        (tmp_path / "storm_sequences.json").write_text("{ broken")  # line 96
        host = _Host(tmp_path)
        first = host._seq_to_event_map()
        assert first == {}
        assert host._seq_to_event_map() is first  # cache hit -> line 84

    def test_wind_damage_index_skips_bad_file(self, tmp_path):
        dmg = tmp_path / "typhoon" / "damage"
        dmg.mkdir(parents=True)
        (dmg / "EVT-00002.json").write_text("not json")  # lines 119-120
        host = _Host(tmp_path)
        assert host._wind_damage_index() == {}


class TestWindLegAnnualisation:
    """The wind leg moves onto the frequency layer with the flood leg.

    Leaving one annualised and the other not would make the union and
    intersection legs internally inconsistent — the BOW/BAW products are
    priced off exactly those two — so both move together or neither does.
    """

    @staticmethod
    def _setup(tmp_path, wind_events=("EVT-00001",)):
        """A host whose sequences pair 1:1 with typhoon events."""
        dmg = tmp_path / "typhoon" / "damage"
        dmg.mkdir(parents=True)
        for event in wind_events:
            _write(dmg / f"{event}.json", {"damages": [
                {"property_id": "PROP-1", "peak_sustained_ms": 70.0,
                 "threshold_ms": 50.0, "v_50_eff_ms": 50.0}]})
        _write(tmp_path / "storm_sequences.json", {"sequences": [
            {
                "sequence_id": f"SEQ-{i}",
                "event_id": f"EVT-{i:05d}",
                "storms": [{
                    "storm_id": f"ST-{i}", "precipitation_mm": 30.0,
                    "duration_hours": 12, "intensity_factor": 1.0,
                    "intensity_category": "severe",
                }],
            }
            for i in range(4)
        ]})
        return _Host(tmp_path)

    @staticmethod
    def _frame(tmp_path):
        from models.frequency import build_event_frame
        from models.hazard.io import load_storms_from_sequences
        return build_event_frame(load_storms_from_sequences(
            json.loads((tmp_path / "storm_sequences.json").read_text())))

    def test_without_a_frame_the_legacy_ratio_is_unchanged(self, tmp_path):
        """An unmigrated caller must price exactly as it did before."""
        host = self._setup(tmp_path)
        result = host._wind_union("PROP-1", [], num_storms=100)
        assert result["wind_count"] == 1
        assert result["wind_spread_bps"] == 100.0      # 1 / 100

    def test_with_a_frame_the_legs_are_annualised(self, tmp_path):
        from models.frequency import annual_exceedance_probability
        host = self._setup(tmp_path)
        frame = self._frame(tmp_path)

        result = host._wind_union(
            "PROP-1", [], num_storms=100, frame=frame, lambda_per_year=4.5)

        expected = annual_exceedance_probability(
            4.5, frame.conditional_probability(["SEQ-1"]))
        assert result["wind_spread_bps"] == round(expected * 10000, 2)
        assert result["wind_spread_bps"] != 100.0

    def test_union_and_intersection_stay_coherent(self, tmp_path):
        """Union at least both legs, intersection at most either — the property
        that makes BOW and BAW meaningful."""
        host = self._setup(tmp_path, wind_events=("EVT-00001", "EVT-00002"))
        frame = self._frame(tmp_path)
        flood_events = [
            {"flooded": True, "exceeded_severe": True, "storm_id": "SEQ-1"},
            {"flooded": True, "exceeded_severe": True, "storm_id": "SEQ-3"},
        ]

        r = host._wind_union("PROP-1", flood_events, num_storms=100,
                             frame=frame, lambda_per_year=4.5)

        assert r["union_count"] == 3          # SEQ-1, SEQ-2, SEQ-3
        assert r["joint_count"] == 1          # SEQ-1 only
        assert r["union_spread_bps"] >= max(r["wind_spread_bps"], 0.0)
        assert r["joint_spread_bps"] <= r["wind_spread_bps"]

    def test_inclusion_exclusion_holds_on_counts(self, tmp_path):
        host = self._setup(tmp_path, wind_events=("EVT-00001", "EVT-00002"))
        frame = self._frame(tmp_path)
        flood_events = [
            {"flooded": True, "exceeded_severe": True, "storm_id": "SEQ-1"},
            {"flooded": True, "exceeded_severe": True, "storm_id": "SEQ-3"},
        ]
        r = host._wind_union("PROP-1", flood_events, num_storms=100,
                             frame=frame, lambda_per_year=4.5)
        flood_count = 2
        assert r["union_count"] == flood_count + r["wind_count"] - r["joint_count"]

    def test_a_wind_event_with_no_paired_sequence_is_dropped(self, tmp_path):
        """It cannot be placed on the flood timeline, so it cannot be unioned
        with one. Counting it anyway would inflate the union leg."""
        host = self._setup(tmp_path, wind_events=("EVT-99999",))
        frame = self._frame(tmp_path)
        r = host._wind_union("PROP-1", [], num_storms=100,
                             frame=frame, lambda_per_year=4.5)
        assert r["wind_count"] == 0
        assert r["wind_spread_bps"] == 0.0
