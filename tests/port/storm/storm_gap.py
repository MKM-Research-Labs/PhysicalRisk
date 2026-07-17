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

"""Tests for inter-storm gap sampler and validation."""

import numpy as np
import pytest

from port.src.storm_multi.core.data_structures import GapType, SequenceType
from port.src.storm_multi.generators.gap_sampler import GAP_PARAMS, get_gap_range, sample_gap
from port.src.storm_multi.utils.validation import (
    EVENT_WINDOW_HOURS,
    MAX_PRECIP_END_HOUR,
    MIN_DRAINAGE_WINDOW_HOURS,
    fits_in_window,
    validate_sequence,
)
from port.src.storm_multi.core.data_structures import SequenceStorm, StormSequence


class TestGapParams:
    """Tests for gap parameter definitions."""

    def test_short_gaps(self):
        assert GAP_PARAMS[GapType.SHORT] == (6, 18, 36)

    def test_medium_gaps(self):
        assert GAP_PARAMS[GapType.MEDIUM] == (24, 48, 72)

    def test_long_gaps(self):
        assert GAP_PARAMS[GapType.LONG] == (48, 96, 144)


class TestSampleGap:
    """Tests for gap sampling."""

    def test_isolated_returns_zero(self):
        assert sample_gap(SequenceType.ISOLATED) == 0.0

    @pytest.mark.parametrize("seq_type", [
        SequenceType.DOUBLET,
        SequenceType.CLUSTER,
        SequenceType.PERSISTENT,
    ])
    def test_within_bounds(self, seq_type):
        rng = np.random.RandomState(42)
        gap_range = get_gap_range(seq_type)
        low, mode, high = gap_range
        for _ in range(200):
            g = sample_gap(seq_type, rng)
            assert low <= g <= high, f"{seq_type}: {g} not in [{low}, {high}]"

    def test_doublet_uses_medium(self):
        """Doublet gaps should fall in medium range (24-72h)."""
        rng = np.random.RandomState(42)
        gaps = [sample_gap(SequenceType.DOUBLET, rng) for _ in range(100)]
        assert all(24 <= g <= 72 for g in gaps)

    def test_persistent_uses_short(self):
        """Persistent gaps should fall in short range (6-36h)."""
        rng = np.random.RandomState(42)
        gaps = [sample_gap(SequenceType.PERSISTENT, rng) for _ in range(100)]
        assert all(6 <= g <= 36 for g in gaps)

    def test_reproducibility(self):
        rng1 = np.random.RandomState(99)
        rng2 = np.random.RandomState(99)
        g1 = [sample_gap(SequenceType.DOUBLET, rng1) for _ in range(10)]
        g2 = [sample_gap(SequenceType.DOUBLET, rng2) for _ in range(10)]
        assert g1 == g2

    def test_no_rng_uses_default(self):
        """Line 49: rng=None → creates np.random.RandomState() internally."""
        low, mode, high = GAP_PARAMS[GapType.MEDIUM]
        g = sample_gap(SequenceType.DOUBLET)  # no rng → hits line 49
        assert low <= g <= high


class TestGetGapRange:
    """Tests for get_gap_range helper."""

    def test_isolated_zero(self):
        assert get_gap_range(SequenceType.ISOLATED) == (0, 0, 0)

    def test_doublet_medium(self):
        assert get_gap_range(SequenceType.DOUBLET) == (24, 48, 72)


class TestValidation:
    """Tests for sequence validation."""

    def _make_valid_doublet(self):
        """Create a valid doublet sequence for testing."""
        storms = [
            SequenceStorm(
                storm_id="STORM-val00001",
                scenario_id="STORM-val00001",
                storm_index=0,
                start_time_hours=0.0,
                duration_hours=24.0,
                intensity_category="moderate",
                intensity_factor=1.0,
                precipitation_mm=35.0,
                peak_position=0.5,
            ),
            SequenceStorm(
                storm_id="STORM-val00002",
                scenario_id="STORM-val00001",
                storm_index=1,
                start_time_hours=72.0,  # 24h storm + 48h gap
                duration_hours=24.0,
                intensity_category="moderate",
                intensity_factor=1.1,
                precipitation_mm=38.5,
                peak_position=0.5,
            ),
        ]
        return StormSequence(
            sequence_id="STORM-val00001",
            sequence_type="doublet",
            sequence_start="2026-01-01T00:00:00",
            total_duration_hours=96.0,  # 24 + 48 + 24
            storms=storms,
            num_storms=2,
            inter_storm_gaps_hours=[48.0],
            total_precipitation_mm=73.5,
            max_intensity_factor=1.1,
            avg_intensity_factor=1.05,
            cumulative_intensity_factor=2.1,
        )

    def test_valid_doublet(self):
        seq = self._make_valid_doublet()
        errors = validate_sequence(seq)
        assert errors == []

    def test_invalid_sequence_type(self):
        seq = self._make_valid_doublet()
        seq.sequence_type = "invalid"
        errors = validate_sequence(seq)
        assert any("Invalid sequence_type" in e for e in errors)

    def test_storm_count_mismatch(self):
        seq = self._make_valid_doublet()
        seq.num_storms = 3
        errors = validate_sequence(seq)
        assert any("num_storms" in e for e in errors)

    def test_too_many_storms(self):
        seq = self._make_valid_doublet()
        for i in range(4):
            seq.storms.append(SequenceStorm(
                storm_id=f"STORM-extra{i:04d}",
                scenario_id=seq.sequence_id,
                storm_index=i + 2,
                start_time_hours=100.0 + i,
                duration_hours=1.0,
                intensity_category="minimal",
                intensity_factor=0.3,
                precipitation_mm=10.0,
                peak_position=0.5,
            ))
        seq.num_storms = 6
        errors = validate_sequence(seq)
        assert any("not in [1, 5]" in e for e in errors)

    def test_exceeds_precip_window(self):
        seq = self._make_valid_doublet()
        # Push second storm past hour 156
        seq.storms[1].start_time_hours = 140.0
        seq.storms[1].duration_hours = 24.0  # ends at 164 > 156
        errors = validate_sequence(seq)
        assert any("MAX_PRECIP_END_HOUR" in e for e in errors)

    def test_overlapping_storms(self):
        seq = self._make_valid_doublet()
        seq.storms[1].start_time_hours = 20.0  # starts before storm 0 ends at 24
        errors = validate_sequence(seq)
        assert any("starts at" in e and "before storm" in e for e in errors)

    def test_invalid_intensity_category(self):
        seq = self._make_valid_doublet()
        seq.storms[0].intensity_category = "mega"
        errors = validate_sequence(seq)
        assert any("invalid intensity" in e for e in errors)

    def test_duration_mismatch(self):
        seq = self._make_valid_doublet()
        seq.total_duration_hours = 999.0
        errors = validate_sequence(seq)
        assert any("total_duration_hours" in e for e in errors)


class TestFitsInWindow:
    """Tests for fits_in_window utility."""

    def test_simple_doublet_fits(self):
        assert fits_in_window([24.0, 24.0], [48.0])  # 96 < 156

    def test_exceeds_window(self):
        assert not fits_in_window([72.0, 72.0], [48.0])  # 192 > 156

    def test_exact_boundary(self):
        assert fits_in_window([78.0, 78.0], [0.0])  # 156 == 156

    def test_single_storm(self):
        assert fits_in_window([100.0], [])

    def test_constants(self):
        assert EVENT_WINDOW_HOURS == 168
        assert MIN_DRAINAGE_WINDOW_HOURS == 12
        assert MAX_PRECIP_END_HOUR == 156
