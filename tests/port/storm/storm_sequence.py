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

"""Tests for storm sequence data structures."""

import pytest

from port.src.storm_multi.core.data_structures import (
    GapType,
    SequenceStorm,
    SequenceType,
    StormSequence,
    SEQUENCE_GAP_TYPE,
    SEQUENCE_TYPE_STORM_COUNTS,
    make_sequence_id,
    make_storm_id,
)


class TestSequenceStorm:
    """Tests for SequenceStorm dataclass."""

    def test_create_basic(self):
        storm = SequenceStorm(
            storm_id="STORM-abc12345",
            scenario_id="STORM-def67890",
            storm_index=0,
            start_time_hours=0.0,
            duration_hours=24.0,
            intensity_category="moderate",
            intensity_factor=1.0,
            precipitation_mm=35.0,
            peak_position=0.5,
        )
        assert storm.storm_id == "STORM-abc12345"
        assert storm.duration_hours == 24.0

    def test_to_dict(self):
        storm = SequenceStorm(
            storm_id="STORM-test1234",
            scenario_id="STORM-parent01",
            storm_index=1,
            start_time_hours=48.0,
            duration_hours=36.0,
            intensity_category="severe",
            intensity_factor=1.8,
            precipitation_mm=63.0,
            peak_position=0.4,
            catchment_id="thames",
        )
        d = storm.to_dict()
        assert d["storm_id"] == "STORM-test1234"
        assert d["start_time_hours"] == 48.0
        assert d["intensity_factor"] == 1.8
        assert d["catchment_id"] == "thames"

    def test_from_dict_round_trip(self):
        original = SequenceStorm(
            storm_id="STORM-rt123456",
            scenario_id="STORM-rt789012",
            storm_index=0,
            start_time_hours=0.0,
            duration_hours=12.0,
            intensity_category="baseline",
            intensity_factor=0.6,
            precipitation_mm=21.0,
            peak_position=0.3,
        )
        d = original.to_dict()
        restored = SequenceStorm.from_dict(d)
        assert restored.storm_id == original.storm_id
        assert restored.duration_hours == original.duration_hours
        assert restored.intensity_factor == original.intensity_factor

    def test_precipitation_rounding(self):
        storm = SequenceStorm(
            storm_id="STORM-prec1234",
            scenario_id="STORM-prec5678",
            storm_index=0,
            start_time_hours=0.0,
            duration_hours=24.0,
            intensity_category="moderate",
            intensity_factor=1.23456789,
            precipitation_mm=35.123456,
            peak_position=0.55555,
        )
        d = storm.to_dict()
        assert d["precipitation_mm"] == 35.12
        assert d["intensity_factor"] == 1.234568
        assert d["peak_position"] == 0.5555


class TestStormSequence:
    """Tests for StormSequence dataclass."""

    def _make_sequence(self, num_storms=2):
        storms = []
        gaps = []
        current_time = 0.0
        for i in range(num_storms):
            storms.append(SequenceStorm(
                storm_id=f"STORM-s{i:07d}",
                scenario_id="STORM-test0001",
                storm_index=i,
                start_time_hours=current_time,
                duration_hours=24.0,
                intensity_category="moderate",
                intensity_factor=1.0 + i * 0.1,
                precipitation_mm=35.0,
                peak_position=0.5,
            ))
            current_time += 24.0
            if i < num_storms - 1:
                gap = 48.0
                gaps.append(gap)
                current_time += gap

        return StormSequence(
            sequence_id="STORM-test0001",
            sequence_type="doublet" if num_storms == 2 else "cluster",
            sequence_start="2026-01-01T00:00:00",
            total_duration_hours=sum(s.duration_hours for s in storms) + sum(gaps),
            storms=storms,
            num_storms=num_storms,
            inter_storm_gaps_hours=gaps,
            total_precipitation_mm=sum(s.precipitation_mm for s in storms),
            max_intensity_factor=max(s.intensity_factor for s in storms),
            avg_intensity_factor=sum(s.intensity_factor for s in storms) / num_storms,
            cumulative_intensity_factor=sum(s.intensity_factor for s in storms),
        )

    def test_create_doublet(self):
        seq = self._make_sequence(2)
        assert seq.num_storms == 2
        assert len(seq.storms) == 2
        assert len(seq.inter_storm_gaps_hours) == 1
        assert seq.sequence_type == "doublet"

    def test_to_dict(self):
        seq = self._make_sequence(2)
        d = seq.to_dict()
        assert d["sequence_id"] == "STORM-test0001"
        assert d["num_storms"] == 2
        assert len(d["storms"]) == 2
        assert len(d["inter_storm_gaps_hours"]) == 1

    def test_from_dict_round_trip(self):
        seq = self._make_sequence(2)
        d = seq.to_dict()
        restored = StormSequence.from_dict(d)
        assert restored.sequence_id == seq.sequence_id
        assert restored.num_storms == seq.num_storms
        assert len(restored.storms) == 2
        assert restored.storms[0].storm_id == seq.storms[0].storm_id
        assert restored.total_precipitation_mm == seq.total_precipitation_mm

    def test_isolated_no_gaps(self):
        seq = self._make_sequence(1)
        seq.sequence_type = "isolated"
        assert len(seq.inter_storm_gaps_hours) == 0

    def test_spatial_correlation_defaults(self):
        seq = self._make_sequence(2)
        assert seq.spatial_correlation_enabled is False
        assert seq.spatial_correlation_range_km is None

    def test_spatial_correlation_enabled(self):
        seq = self._make_sequence(2)
        seq.spatial_correlation_enabled = True
        seq.spatial_correlation_range_km = 43.2
        d = seq.to_dict()
        assert d["spatial_correlation_enabled"] is True
        assert d["spatial_correlation_range_km"] == 43.2

    def test_antecedent_defaults(self):
        seq = self._make_sequence(2)
        assert seq.antecedent_soil_moisture == "normal"
        assert seq.antecedent_groundwater == "normal"


class TestEnums:
    """Tests for SequenceType and GapType enums."""

    def test_sequence_types(self):
        assert SequenceType.ISOLATED.value == "isolated"
        assert SequenceType.DOUBLET.value == "doublet"
        assert SequenceType.CLUSTER.value == "cluster"
        assert SequenceType.PERSISTENT.value == "persistent"

    def test_gap_types(self):
        assert GapType.SHORT.value == "short"
        assert GapType.MEDIUM.value == "medium"
        assert GapType.LONG.value == "long"

    def test_sequence_gap_mapping(self):
        assert SEQUENCE_GAP_TYPE[SequenceType.DOUBLET] == GapType.MEDIUM
        assert SEQUENCE_GAP_TYPE[SequenceType.CLUSTER] == GapType.MEDIUM
        assert SEQUENCE_GAP_TYPE[SequenceType.PERSISTENT] == GapType.SHORT
        assert SequenceType.ISOLATED not in SEQUENCE_GAP_TYPE

    def test_storm_count_ranges(self):
        assert SEQUENCE_TYPE_STORM_COUNTS[SequenceType.ISOLATED] == (1, 1)
        assert SEQUENCE_TYPE_STORM_COUNTS[SequenceType.DOUBLET] == (2, 2)
        assert SEQUENCE_TYPE_STORM_COUNTS[SequenceType.CLUSTER] == (3, 4)
        assert SEQUENCE_TYPE_STORM_COUNTS[SequenceType.PERSISTENT] == (4, 5)


class TestIDGeneration:
    """Tests for ID generation helpers."""

    def test_storm_id_format(self):
        sid = make_storm_id()
        assert sid.startswith("STORM-")
        assert len(sid) == 14  # STORM- + 8 hex chars

    def test_sequence_id_format(self):
        sid = make_sequence_id()
        assert sid.startswith("STORM-")
        assert len(sid) == 14  # STORM- + 8 hex chars

    def test_ids_unique(self):
        ids = {make_storm_id() for _ in range(100)}
        assert len(ids) == 100

    def test_sequence_ids_unique(self):
        ids = {make_sequence_id() for _ in range(100)}
        assert len(ids) == 100
