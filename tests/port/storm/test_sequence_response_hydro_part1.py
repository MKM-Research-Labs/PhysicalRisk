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
Tests for Phase 3: hydrology model unit tests and precipitation series.
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
    _make_precip_series,
)


# ---------------------------------------------------------------------------
# HydrologyModel — unit tests
# ---------------------------------------------------------------------------

class TestHydrologyModelStep:

    def test_dry_start_no_precip_no_quickflow(self):
        model = HydrologyModel()
        state = HydrologicalState()
        new_state, qf = model.step(state, precip_mm=0.0)
        assert qf == pytest.approx(0.0)
        assert new_state.soil_moisture == pytest.approx(0.0)
        assert new_state.groundwater == pytest.approx(0.0)

    def test_precip_increases_soil_moisture(self):
        model = HydrologyModel()
        state = HydrologicalState()
        new_state, _ = model.step(state, precip_mm=10.0)
        assert new_state.soil_moisture > 0.0

    def test_precip_produces_quickflow(self):
        model = HydrologyModel()
        state = HydrologicalState()
        _, qf = model.step(state, precip_mm=10.0)
        assert qf > 0.0

    def test_soil_moisture_drains_without_rain(self):
        model = HydrologyModel()
        # Pre-wet the soil
        state = HydrologicalState(soil_moisture=50.0)
        new_state, _ = model.step(state, precip_mm=0.0)
        assert new_state.soil_moisture < 50.0

    def test_groundwater_accumulates_from_soil(self):
        model = HydrologyModel()
        state = HydrologicalState(soil_moisture=100.0)
        new_state, _ = model.step(state, precip_mm=0.0)
        assert new_state.groundwater > 0.0

    def test_wet_soil_raises_quickflow(self):
        """Elevated antecedent state produces more quickflow per mm."""
        model = HydrologyModel()
        dry_state = HydrologicalState()
        wet_state = HydrologicalState(soil_moisture=40.0, groundwater=10.0)
        precip = 5.0
        _, qf_dry = model.step(dry_state, precip)
        _, qf_wet = model.step(wet_state, precip)
        assert qf_wet > qf_dry

    def test_negative_precip_treated_as_zero(self):
        model = HydrologyModel()
        state = HydrologicalState()
        new_state, qf = model.step(state, precip_mm=-5.0)
        assert qf >= 0.0
        assert new_state.soil_moisture >= 0.0


class TestHydrologyModelRunSeries:

    def test_shape(self):
        model = HydrologyModel()
        qf, states = model.run_series(np.zeros(168))
        assert qf.shape == (168,)
        assert len(states) == 168

    def test_no_rain_no_quickflow(self):
        model = HydrologyModel()
        qf, _ = model.run_series(np.zeros(168))
        assert np.all(qf == pytest.approx(0.0))

    def test_consistent_with_step(self):
        """run_series result matches manual step-by-step."""
        model = HydrologyModel()
        precip = np.array([5.0, 10.0, 8.0, 3.0, 0.0, 0.0])
        qf_series, _ = model.run_series(precip)
        state = HydrologicalState()
        for h, p in enumerate(precip):
            state, qf = model.step(state, p)
            assert qf == pytest.approx(qf_series[h], rel=1e-6)

    def test_quickflow_positive(self):
        model = HydrologyModel()
        precip = np.random.default_rng(0).uniform(0, 10, 168)
        qf, _ = model.run_series(precip)
        assert np.all(qf >= 0.0)

    def test_initial_state_affects_output(self):
        """Wet initial state produces higher early quickflow."""
        model = HydrologyModel()
        precip = np.full(24, 3.0)
        dry = HydrologicalState()
        wet = HydrologicalState(soil_moisture=50.0, groundwater=20.0)
        qf_dry, _ = model.run_series(precip, initial_state=dry)
        qf_wet, _ = model.run_series(precip, initial_state=wet)
        # First few hours: wet state should give higher quickflow
        assert qf_wet[:6].mean() > qf_dry[:6].mean()

    def test_state_decays_without_rain(self):
        """Soil moisture drains to near zero after long dry period."""
        model = HydrologyModel()
        precip = np.zeros(500)
        init = HydrologicalState(soil_moisture=100.0, groundwater=50.0)
        _, states = model.run_series(precip, initial_state=init)
        # After 500 dry hours, soil moisture should be near zero
        assert states[-1].soil_moisture < 1.0


# ---------------------------------------------------------------------------
# _make_precip_series — precipitation profile
# ---------------------------------------------------------------------------

class TestMakePrecipSeries:

    def test_output_shape(self, doublet_batch):
        seq = doublet_batch[0]
        p = _make_precip_series(seq)
        assert p.shape == (EVENT_WINDOW_HOURS,)

    def test_no_precip_outside_storms(self, doublet_batch):
        """Drainage window (hours 156-167) must be precipitation-free."""
        for seq in doublet_batch[:20]:
            p = _make_precip_series(seq)
            assert np.all(p[156:] == pytest.approx(0.0)), (
                f"Precipitation in drainage window for {seq.sequence_id}"
            )

    def test_total_precip_conserved(self, doublet_batch):
        """Sum of hourly series == sum of storm precipitation_mm values."""
        for seq in doublet_batch[:30]:
            p = _make_precip_series(seq)
            expected = sum(s.precipitation_mm for s in seq.storms)
            assert p.sum() == pytest.approx(expected, rel=1e-4), (
                f"Precip not conserved: {p.sum():.2f} != {expected:.2f}"
            )

    def test_non_negative(self, doublet_batch):
        for seq in doublet_batch[:20]:
            p = _make_precip_series(seq)
            assert np.all(p >= 0.0)

    def test_isolated_single_storm_peak(self):
        """Peak precipitation is in the storm's active window."""
        from port.src.storm_multi.generators.sequence_generator import SequenceGenerator
        gen = SequenceGenerator(seed=1)
        seq = gen.generate("severe", 1.8, force_sequence_type="isolated")
        p = _make_precip_series(seq)
        storm = seq.storms[0]
        start = int(round(storm.start_time_hours))
        end = start + int(round(storm.duration_hours))
        if end > start:
            peak_in_storm = np.max(p[start:end])
            peak_outside = np.max(p[:start]) if start > 0 else 0
            peak_outside = max(peak_outside, np.max(p[end:]) if end < 168 else 0)
            assert peak_in_storm >= peak_outside
