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
Tests for Phase 3: sequence gauge response — main function validation.
"""

import numpy as np
import pytest

from port.src.storm_multi.models.hydrology import HydrologicalState
from port.src.storm_multi.models.sequence_response import (
    EVENT_WINDOW_HOURS,
    SequenceGaugeParams,
    _make_precip_series,
    compute_sequence_gauge_response,
)


# ---------------------------------------------------------------------------
# compute_sequence_gauge_response — main function
# ---------------------------------------------------------------------------

class TestComputeSequenceGaugeResponse:

    def test_output_shape(self, doublet_batch, default_gauge):
        levels = compute_sequence_gauge_response(doublet_batch[0], default_gauge)
        assert levels.shape == (EVENT_WINDOW_HOURS,)

    def test_no_negative_levels(self, doublet_batch, default_gauge):
        """River level must always be >= base_level."""
        for seq in doublet_batch[:30]:
            levels = compute_sequence_gauge_response(seq, default_gauge)
            assert np.all(levels >= default_gauge.base_level - 1e-6), (
                f"Negative excess level for {seq.sequence_id}: min={levels.min():.3f}"
            )

    def test_level_above_base_during_storm(self, default_gauge):
        """Severe storm should raise level above baseline."""
        from port.src.storm_multi.generators.sequence_generator import SequenceGenerator
        gen = SequenceGenerator(seed=5)
        seq = gen.generate("severe", 2.0, force_sequence_type="isolated")
        levels = compute_sequence_gauge_response(seq, default_gauge)
        assert np.max(levels) > default_gauge.base_level + 0.5

    def test_drainage_window_level_declining(self, severe_batch, default_gauge):
        """Level should be declining in the later part of the drainage window.

        Hours 156-159 may still rise due to the 2h response lag processing
        quickflow from precipitation ending at hour 155. From hour 160 onward
        there is no new input and the level must decline monotonically.
        """
        for seq in severe_batch[:20]:
            levels = compute_sequence_gauge_response(seq, default_gauge)
            # After lag clears: hours 160-167 must be non-increasing
            tail = levels[160:]
            assert np.all(np.diff(tail) <= 0.01), (
                f"Level rising after lag window for {seq.sequence_id}"
            )

    def test_no_precip_in_drainage_window(self, doublet_batch):
        """Spec constraint: no precipitation after hour 156."""
        for seq in doublet_batch[:20]:
            p = _make_precip_series(seq)
            assert np.all(p[156:] == pytest.approx(0.0))

    def test_higher_intensity_higher_level(self, default_gauge):
        """Extreme storm should produce higher peak than moderate."""
        from port.src.storm_multi.generators.sequence_generator import SequenceGenerator
        gen = SequenceGenerator(seed=42)
        moderate = gen.generate("moderate", 1.0, force_sequence_type="isolated")
        gen2 = SequenceGenerator(seed=42)
        extreme = gen2.generate("extreme", 3.0, force_sequence_type="isolated")
        l_mod = compute_sequence_gauge_response(moderate, default_gauge)
        l_ext = compute_sequence_gauge_response(extreme, default_gauge)
        assert np.max(l_ext) > np.max(l_mod)

    def test_isolated_vs_doublet_same_first_storm(self, default_gauge):
        """With identical first storm parameters, doublet produces >= isolated peak."""
        from port.src.storm_multi.generators.sequence_generator import SequenceGenerator
        gen = SequenceGenerator(seed=10)
        isolated = gen.generate("severe", 1.8, force_sequence_type="isolated")
        gen2 = SequenceGenerator(seed=10)
        doublet = gen2.generate("severe", 1.8, force_sequence_type="doublet")
        if doublet.num_storms == 2:
            l_iso = compute_sequence_gauge_response(isolated, default_gauge)
            l_dbl = compute_sequence_gauge_response(doublet, default_gauge)
            assert np.max(l_dbl) >= np.max(l_iso)

    def test_recovery_near_baseline_by_hour_168(self, severe_batch, default_gauge):
        """Level at hour 167 should be below the peak level (recovering, not diverging).

        With decay=24h and the minimum 12h drainage window, up to ~60% of
        peak excess can remain at hour 167 for late-ending storms. We therefore
        check only that level[167] < peak_level — the system is decaying, not
        growing. For sequences ending before hour 136 (>=32h drainage) we apply
        a stricter 1.5m excess limit.
        """
        for seq in severe_batch[:30]:
            levels = compute_sequence_gauge_response(seq, default_gauge)
            peak = float(np.max(levels))
            final = levels[167]
            # Always: final level must be below or equal to peak (recovering)
            assert final <= peak + 0.01, (
                f"Level at hour 167 exceeds peak for {seq.sequence_id}"
            )
            # Stricter check for sequences with adequate drainage time
            last_end = max(
                int(round(s.start_time_hours + s.duration_hours))
                for s in seq.storms
            )
            if last_end <= 136:
                final_excess = final - default_gauge.base_level
                assert final_excess < 1.5, (
                    f"Insufficient recovery for {seq.sequence_id} "
                    f"(last storm ends h{last_end}): excess={final_excess:.2f}m"
                )

    def test_antecedent_wetness_increases_peak(self, default_gauge):
        """Pre-wetting the catchment before the same storm raises the peak."""
        from port.src.storm_multi.generators.sequence_generator import SequenceGenerator
        gen = SequenceGenerator(seed=7)
        seq = gen.generate("severe", 1.8, force_sequence_type="isolated")
        dry = compute_sequence_gauge_response(seq, default_gauge)
        wet = compute_sequence_gauge_response(
            seq, default_gauge,
            initial_state=HydrologicalState(soil_moisture=40.0, groundwater=15.0),
        )
        assert np.max(wet) > np.max(dry)
