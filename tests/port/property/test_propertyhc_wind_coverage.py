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
