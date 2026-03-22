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
Tests for Phase 3: compound sequence criteria and storm peak analysis.

Spec Section 5 validation criteria:
  - Storm 2 peak > Storm 1 peak in >= 60% of generated doublets
  - Observable drainage during gap (level drops from Storm 1 peak)
"""

import numpy as np
import pytest

from port.src.storm_multi.models.hydrology import (
    HydrologicalState,
    HydrologyModel,
    HydrologyParams,
)
from port.src.storm_multi.models.sequence_response import (
    EVENT_WINDOW_HOURS,
    SequenceGaugeParams,
    _make_precip_series,
    _route_quickflow_to_level,
    compute_sequence_gauge_response,
    compute_storm_peaks,
)
from port.src.storm_multi.generators.batch_generator import generate_event_set
from port.src.storm_multi.core.data_structures import SequenceType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def default_gauge():
    return SequenceGaugeParams.default_thames()


@pytest.fixture(scope="module")
def doublet_batch():
    """200 forced-doublet sequences for compounding validation."""
    return generate_event_set(count=200, force_sequence_type="doublet", seed=42)


@pytest.fixture(scope="module")
def severe_batch():
    """200 severe sequences (natural type mix)."""
    return generate_event_set(
        count=200,
        intensity_weights={"severe": 1.0},
        seed=7,
    )


# ---------------------------------------------------------------------------
# Compounding criterion: Storm 2 peak > Storm 1 peak in >= 60% of doublets
# (Spec Section 5, validation criterion)
# ---------------------------------------------------------------------------

class TestCompoundingCriterion:

    def test_storm2_peak_exceeds_storm1_majority(self, doublet_batch, default_gauge):
        """Spec requirement: Storm 2 peak > Storm 1 peak in >= 60% of doublets."""
        doublets_only = [s for s in doublet_batch if s.num_storms == 2]
        if len(doublets_only) < 10:
            pytest.skip("Too few doublets to assess (fallback to isolated dominated)")

        storm2_exceeds = 0
        for seq in doublets_only:
            peaks = compute_storm_peaks(seq, default_gauge)
            if len(peaks) >= 2:
                _, peak1 = peaks[0]
                _, peak2 = peaks[1]
                if peak2 > peak1:
                    storm2_exceeds += 1

        fraction = storm2_exceeds / len(doublets_only)
        assert fraction >= 0.60, (
            f"Storm 2 peak exceeds Storm 1 in only {fraction:.1%} of doublets "
            f"({storm2_exceeds}/{len(doublets_only)}). Spec requires >= 60%."
        )

    def test_compounding_stronger_for_short_gaps(self, default_gauge):
        """Persistent sequences (SHORT gaps) should show stronger compounding than doublets (MEDIUM gaps)."""
        doublets = generate_event_set(
            count=100, force_sequence_type="doublet",
            intensity_weights={"severe": 1.0}, seed=1,
        )
        persistent = generate_event_set(
            count=100, force_sequence_type="persistent",
            intensity_weights={"severe": 1.0}, seed=1,
        )

        def _mean_peak2_excess(seqs):
            excesses = []
            for seq in seqs:
                if seq.num_storms >= 2:
                    peaks = compute_storm_peaks(seq, default_gauge)
                    if len(peaks) >= 2:
                        excesses.append(peaks[1][1] - peaks[0][1])
            return np.mean(excesses) if excesses else 0.0

        doublet_excess = _mean_peak2_excess(doublets)
        persistent_excess = _mean_peak2_excess(persistent)
        # Persistent (shorter gaps) should show at least as much compounding
        assert persistent_excess >= doublet_excess - 0.1

    def test_gap_drainage_observable(self, default_gauge):
        """During the gap, level should drop from Storm 1 peak."""
        from port.src.storm_multi.generators.sequence_generator import SequenceGenerator
        gen = SequenceGenerator(seed=99)
        seq = gen.generate("severe", 2.0, force_sequence_type="doublet")
        if seq.num_storms < 2:
            pytest.skip("Sequence fell back to isolated")

        levels = compute_sequence_gauge_response(seq, default_gauge)
        storm1 = seq.storms[0]
        storm2 = seq.storms[1]
        s1_end = int(round(storm1.start_time_hours + storm1.duration_hours))
        s2_start = int(round(storm2.start_time_hours))

        if s2_start > s1_end:
            # Peak during Storm 1 window
            s1_peak = np.max(levels[:s2_start])
            # Level at start of Storm 2
            level_at_gap_end = levels[s2_start]
            # Gap drainage: level at s2_start should be lower than s1 peak
            assert level_at_gap_end < s1_peak, (
                f"No drainage during gap: level at gap end ({level_at_gap_end:.3f}) "
                f">= Storm 1 peak ({s1_peak:.3f})"
            )

    def test_short_gap_no_baseline_recovery(self, default_gauge):
        """For a short-gap persistent sequence, level does not return to baseline during gap."""
        from port.src.storm_multi.generators.sequence_generator import SequenceGenerator
        # Generate severe persistent sequences until we find one with a short gap
        for seed in range(10, 30):
            gen = SequenceGenerator(seed=seed)
            seq = gen.generate("severe", 2.0, force_sequence_type="persistent")
            if seq.num_storms >= 2:
                storm1 = seq.storms[0]
                storm2 = seq.storms[1]
                gap = storm2.start_time_hours - (storm1.start_time_hours + storm1.duration_hours)
                if gap <= 20:  # Short gap (within SHORT range 6-36h)
                    levels = compute_sequence_gauge_response(seq, default_gauge)
                    s1_end = int(round(storm1.start_time_hours + storm1.duration_hours))
                    s2_start = int(round(storm2.start_time_hours))
                    if s1_end < s2_start:
                        gap_levels = levels[s1_end:s2_start]
                        level_at_gap_end = float(gap_levels[-1]) if len(gap_levels) > 0 else default_gauge.base_level
                        assert level_at_gap_end > default_gauge.base_level + 0.05, (
                            f"Level returned to baseline during short {gap:.0f}h gap"
                        )
                    return  # Found a suitable sequence, test done
        pytest.skip("Could not find a sequence with short gap in test seeds")


# ---------------------------------------------------------------------------
# compute_storm_peaks helper
# ---------------------------------------------------------------------------

class TestComputeStormPeaks:

    def test_returns_one_peak_per_storm(self, doublet_batch, default_gauge):
        for seq in doublet_batch[:20]:
            peaks = compute_storm_peaks(seq, default_gauge)
            assert len(peaks) == seq.num_storms

    def test_peak_indices_match_storm_indices(self, doublet_batch, default_gauge):
        for seq in doublet_batch[:10]:
            peaks = compute_storm_peaks(seq, default_gauge)
            for (idx, _), storm in zip(peaks, seq.storms):
                assert idx == storm.storm_index

    def test_peak_above_base(self, severe_batch, default_gauge):
        for seq in severe_batch[:20]:
            peaks = compute_storm_peaks(seq, default_gauge)
            for _, peak in peaks:
                assert peak >= default_gauge.base_level
