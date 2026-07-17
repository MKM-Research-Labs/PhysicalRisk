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
Stage 2 — typhoon stage reads the storm event drivers for 1:1 coupling.

Covers app/commands/port/stages/typhoon._load_storm_event_drivers: it pulls
(event_id, base_intensity, seed) per storm sequence, preserves file order, and
degrades gracefully (returns []) when the storm set is absent or is a
pre-coupling file lacking event_id — in which case the stage falls back to the
standalone --num-typhoon-events count.
"""

import json
from types import SimpleNamespace

import pytest

from app.commands.port.stages.typhoon import (
    _load_storm_event_drivers,
    _severity_quantiles,
)


def _ctx(tmp_path):
    return SimpleNamespace(input_dir=tmp_path)


def _write_sequences(tmp_path, sequences):
    (tmp_path / "storm_sequences.json").write_text(
        json.dumps({"num_sequences": len(sequences), "sequences": sequences})
    )


def test_returns_drivers_in_file_order(tmp_path):
    _write_sequences(tmp_path, [
        {"sequence_id": "SEQ-a", "event_id": "EVT-00000",
         "base_intensity": 1.05, "seed": 111},
        {"sequence_id": "SEQ-b", "event_id": "EVT-00001",
         "base_intensity": 5.80, "seed": 222},
    ])
    drivers = _load_storm_event_drivers(_ctx(tmp_path))
    assert [d["event_id"] for d in drivers] == ["EVT-00000", "EVT-00001"]
    assert drivers[0]["base_intensity"] == pytest.approx(1.05)
    assert drivers[1]["seed"] == 222


def test_missing_file_returns_empty(tmp_path):
    assert _load_storm_event_drivers(_ctx(tmp_path)) == []


def test_pre_coupling_file_without_event_id_returns_empty(tmp_path):
    # A file that predates Stage 2 has no event_id — cannot pair, so the loader
    # bails entirely rather than producing a partial/misaligned pairing.
    _write_sequences(tmp_path, [
        {"sequence_id": "SEQ-a", "base_intensity": 1.0},
        {"sequence_id": "SEQ-b", "base_intensity": 2.0},
    ])
    assert _load_storm_event_drivers(_ctx(tmp_path)) == []


def test_malformed_json_returns_empty(tmp_path):
    (tmp_path / "storm_sequences.json").write_text("{not valid json")
    assert _load_storm_event_drivers(_ctx(tmp_path)) == []


def test_seed_and_base_intensity_defaults(tmp_path):
    # event_id present but the optional numeric fields missing -> safe defaults.
    _write_sequences(tmp_path, [{"sequence_id": "SEQ-a", "event_id": "EVT-00000"}])
    drivers = _load_storm_event_drivers(_ctx(tmp_path))
    assert drivers == [{"event_id": "EVT-00000", "base_intensity": 0.0, "seed": 0}]


# ===========================================================================
# _severity_quantiles — z -> q = rank(z)/(N+1)  (coupling_spec.md §3, Stage 3)
# ===========================================================================


def test_severity_quantiles_empty():
    assert _severity_quantiles([]) == []


def test_severity_quantiles_strictly_inside_unit_interval():
    # The (N+1) denominator keeps every q in the OPEN interval (0,1) so the
    # §4 inverse-survival map never hits the degenerate endpoints.
    q = _severity_quantiles([3.0, 1.0, 2.0, 5.0])
    assert all(0.0 < x < 1.0 for x in q)


def test_severity_quantiles_preserve_order_ranking():
    # Largest z -> largest q; aligned 1:1 with input order.
    z = [10.0, 1.0, 5.0]
    q = _severity_quantiles(z)
    assert q[0] > q[2] > q[1]          # 10 > 5 > 1
    # rank/(N+1): ranks 3,1,2 over N=3 -> 0.75, 0.25, 0.5
    assert q == pytest.approx([0.75, 0.25, 0.5])


def test_severity_quantiles_average_ties():
    # Ties share the average rank.
    q = _severity_quantiles([2.0, 2.0, 1.0])
    # ranks: 2.0->avg(2,3)=2.5, 2.0->2.5, 1.0->1 ; /(N+1=4)
    assert q == pytest.approx([0.625, 0.625, 0.25])
