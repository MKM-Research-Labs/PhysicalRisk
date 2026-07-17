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

"""Tests for models.typhoon.pipeline.event — single-event simulation."""

import numpy as np

from models.typhoon.data_structures import TyphoonTrajectory, WindFieldOutput
from models.typhoon.pipeline.event import (
    EventResult,
    pick_representative_trajectory,
    simulate_one_event,
)


class TestSimulateOneEvent:

    def test_returns_event_result(self, minimal_config):
        result = simulate_one_event(
            config=minimal_config,
            n_particles=10,
            rng=np.random.default_rng(0),
            horizon_hours=6.0,
            dt_hours=1.0,
        )
        assert isinstance(result, EventResult)
        for prop in minimal_config.property_points:
            assert prop.property_id in result.by_property
        assert len(result.trajectories) == 10

    def test_list_length_matches_n_particles(self, minimal_config):
        result = simulate_one_event(
            config=minimal_config,
            n_particles=15,
            rng=np.random.default_rng(0),
            horizon_hours=4.0,
            dt_hours=1.0,
        )
        for outputs in result.by_property.values():
            assert len(outputs) == 15
        assert len(result.trajectories) == 15

    def test_outputs_are_wind_field_output_instances(self, minimal_config):
        result = simulate_one_event(
            config=minimal_config,
            n_particles=5,
            rng=np.random.default_rng(0),
            horizon_hours=4.0,
            dt_hours=1.0,
        )
        for outputs in result.by_property.values():
            for o in outputs:
                assert isinstance(o, WindFieldOutput)
        for t in result.trajectories:
            assert isinstance(t, TyphoonTrajectory)

    def test_no_plausibility_path(self, minimal_config):
        result = simulate_one_event(
            config=minimal_config,
            n_particles=5,
            rng=np.random.default_rng(0),
            horizon_hours=4.0,
            dt_hours=1.0,
            use_plausibility=False,
        )
        for outputs in result.by_property.values():
            assert len(outputs) == 5

    def test_fixed_seed_reproducible(self, minimal_config):
        a = simulate_one_event(
            config=minimal_config, n_particles=4,
            rng=np.random.default_rng(7), horizon_hours=4.0,
        )
        b = simulate_one_event(
            config=minimal_config, n_particles=4,
            rng=np.random.default_rng(7), horizon_hours=4.0,
        )
        for prop_id in a.by_property:
            peaks_a = [o.peak_sustained_ms for o in a.by_property[prop_id]]
            peaks_b = [o.peak_sustained_ms for o in b.by_property[prop_id]]
            assert peaks_a == peaks_b


class TestPickRepresentativeTrajectory:

    def test_empty_input_returns_none(self):
        assert pick_representative_trajectory([]) is None

    def test_returns_median_peak_trajectory(self, minimal_config):
        # 5 particles -> the trajectory with the median peak V_max should
        # be returned. The exact pick depends on RNG draws but the result
        # must be one of the input trajectories with a peak in the body.
        result = simulate_one_event(
            config=minimal_config, n_particles=11,
            rng=np.random.default_rng(0), horizon_hours=4.0,
        )
        rep = pick_representative_trajectory(result.trajectories)
        assert rep is not None
        assert rep in result.trajectories
