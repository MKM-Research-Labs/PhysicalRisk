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

"""Tests for hydrograph superposition module -- part 2 (compound hydrograph)."""

import numpy as np
import pytest

from models.floodrisk.hydrograph import build_compound_property_hydrograph


# ---------------------------------------------------------------------------
# build_compound_property_hydrograph (orchestrator)
# ---------------------------------------------------------------------------

class TestBuildCompoundPropertyHydrograph:

    @pytest.fixture
    def single_pulse(self):
        return [{
            "storm_index": 0,
            "peak_m": 10.0,
            "start_hour": 20.0,
            "duration_hours": 40.0,
            "precip_mm": 80.0,
        }]

    @pytest.fixture
    def cluster_pulses(self):
        return [
            {"storm_index": 0, "peak_m": 8.0, "start_hour": 0.0,
             "duration_hours": 30.0, "precip_mm": 60.0},
            {"storm_index": 1, "peak_m": 8.5, "start_hour": 35.0,
             "duration_hours": 30.0, "precip_mm": 70.0},
            {"storm_index": 2, "peak_m": 9.0, "start_hour": 70.0,
             "duration_hours": 30.0, "precip_mm": 80.0},
            {"storm_index": 3, "peak_m": 9.5, "start_hour": 105.0,
             "duration_hours": 30.0, "precip_mm": 90.0},
        ]

    def test_output_schema(self, single_pulse):
        result = build_compound_property_hydrograph(
            pulse_peaks=single_pulse,
            sequence_type="isolated",
            base_level=3.0,
            gauge_elevation=5.0,
            prop_elevation=6.0,
            floor_level=0.3,
            travel_time_hrs=0.5,
            retention=1.0,
        )
        assert len(result) == 168
        assert all('hour' in r for r in result)
        assert all('wse_m' in r for r in result)
        assert all('depth_m' in r for r in result)
        assert all('flooded' in r for r in result)

    def test_isolated_produces_flood(self, single_pulse):
        """A big isolated pulse should flood the property."""
        result = build_compound_property_hydrograph(
            pulse_peaks=single_pulse,
            sequence_type="isolated",
            base_level=3.0,
            gauge_elevation=5.0,
            prop_elevation=6.0,
            floor_level=0.3,
            travel_time_hrs=0.1,
            retention=1.0,
        )
        max_depth = max(r['depth_m'] for r in result)
        # peak_m=10 (stage reading) -> water_above=10, threshold=(6-5)+0.3=1.3
        # depth ~ 10 - 1.3 = 8.7 (before infiltration)
        assert max_depth > 2.0

    def test_cluster_higher_than_single_worst_pulse(self, cluster_pulses):
        """Compound cluster should produce more flooding than its best pulse alone."""
        # Single worst pulse only (storm_index=3, peak=9.5)
        single = [cluster_pulses[3]]
        result_single = build_compound_property_hydrograph(
            pulse_peaks=single,
            sequence_type="cluster",
            base_level=3.0,
            gauge_elevation=5.0,
            prop_elevation=6.5,
            floor_level=0.3,
            travel_time_hrs=0.1,
            retention=1.0,
        )
        max_single = max(r['depth_m'] for r in result_single)

        # Full 4-pulse cluster
        result_cluster = build_compound_property_hydrograph(
            pulse_peaks=cluster_pulses,
            sequence_type="cluster",
            base_level=3.0,
            gauge_elevation=5.0,
            prop_elevation=6.5,
            floor_level=0.3,
            travel_time_hrs=0.1,
            retention=1.0,
        )
        max_cluster = max(r['depth_m'] for r in result_cluster)

        assert max_cluster > max_single

    def test_cluster_longer_duration(self, cluster_pulses, single_pulse):
        """Cluster should have longer flood duration than isolated."""
        # Use a high property elevation so only the peak of the hydrograph
        # exceeds the flood threshold.  gauge_wse is a stage reading;
        # threshold = prop_elevation - gauge_elevation + floor_level.
        # With peaks ~8-10m (stage), set threshold ~9m so isolated barely
        # floods while cluster (with saturation amplification) floods longer.
        result_iso = build_compound_property_hydrograph(
            pulse_peaks=single_pulse,
            sequence_type="isolated",
            base_level=3.0,
            gauge_elevation=5.0,
            prop_elevation=14.0,
            floor_level=0.3,
            travel_time_hrs=0.1,
            retention=1.0,
        )
        result_cluster = build_compound_property_hydrograph(
            pulse_peaks=cluster_pulses,
            sequence_type="cluster",
            base_level=3.0,
            gauge_elevation=5.0,
            prop_elevation=14.0,
            floor_level=0.3,
            travel_time_hrs=0.1,
            retention=1.0,
        )
        dur_iso = sum(1 for r in result_iso if r['flooded'])
        dur_cluster = sum(1 for r in result_cluster if r['flooded'])
        assert dur_cluster > dur_iso

    def test_large_travel_time_clips_source_index(self):
        """Line 123: src >= n_hours → continue (skipped hours at end of window)."""
        # With travel_time > 0, the last `shift` hours have src >= n_hours
        # and are skipped. Use a large travel time to ensure this branch is hit.
        pulse = [{"storm_index": 0, "peak_m": 10.0, "start_hour": 0.0,
                  "duration_hours": 20.0, "precip_mm": 80.0}]
        result = build_compound_property_hydrograph(
            pulse_peaks=pulse,
            sequence_type="isolated",
            base_level=3.0,
            gauge_elevation=5.0,
            prop_elevation=6.0,
            floor_level=0.3,
            travel_time_hrs=160.0,  # shift=160 → most src values are < 0 or >= 168
            retention=1.0,
            n_hours=168,
        )
        assert len(result) == 168
        # With travel_time=160, only hours 160-167 have valid src (0-7)
        # Remaining hours should have depth_m == 0
        early_depths = [r['depth_m'] for r in result[:150]]
        assert all(d == 0.0 for d in early_depths)

    def test_no_flood_when_below_threshold(self):
        """Property too high above gauge -> no flooding."""
        # peak_m=6.0 is a stage reading (water column at gauge).
        # threshold = prop_elevation - gauge_elevation + floor_level
        # = 17 - 5 + 0.5 = 12.5m → well above 6.0m peak → no flood
        pulse = [{"storm_index": 0, "peak_m": 6.0, "start_hour": 20.0,
                  "duration_hours": 30.0, "precip_mm": 40.0}]
        result = build_compound_property_hydrograph(
            pulse_peaks=pulse,
            sequence_type="isolated",
            base_level=3.0,
            gauge_elevation=5.0,
            prop_elevation=17.0,  # 12m above gauge
            floor_level=0.5,
            travel_time_hrs=0.1,
            retention=1.0,
        )
        max_depth = max(r['depth_m'] for r in result)
        assert max_depth == 0.0
