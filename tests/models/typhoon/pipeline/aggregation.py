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

"""Tests for models.typhoon.pipeline.aggregation."""

import pytest

from config.typhoon import PropertyPoint
from models.typhoon.data_structures import WindFieldOutput
from models.typhoon.pipeline.aggregation import aggregate_property_winds


def _wf_output(peak: float, point_id: str = "P1", duration_above=None):
    return WindFieldOutput(
        point_id=point_id,
        longitude=5.0,
        latitude=5.0,
        time_hours=[0.0, 1.0, 2.0],
        sustained_ms=[peak * 0.5, peak, peak * 0.5],
        peak_sustained_ms=peak,
        time_of_peak_hours=1.0,
        distance_at_peak_km=50.0,
        azimuth_at_peak_deg=0.0,
        duration_above_ms=duration_above or {},
    )


class TestAggregatePropertyWinds:

    def test_empty_realizations(self):
        prop = PropertyPoint(property_id="P1", longitude=5.0, latitude=5.0)
        s = aggregate_property_winds(prop, [], thresholds_ms=[17.5, 30.0])
        assert s.n_realizations == 0
        assert s.peak_sustained_samples == []
        assert s.threshold_exceedance == {17.5: 0.0, 30.0: 0.0}

    def test_mean_and_quantiles(self):
        prop = PropertyPoint(property_id="P1", longitude=5.0, latitude=5.0)
        peaks = [10.0, 20.0, 30.0, 40.0, 50.0]
        realizations = [_wf_output(p) for p in peaks]
        s = aggregate_property_winds(prop, realizations, thresholds_ms=[])
        assert s.n_realizations == 5
        assert s.peak_sustained_mean == pytest.approx(30.0)
        assert s.peak_sustained_p50 == pytest.approx(30.0)
        assert s.peak_sustained_p95 == pytest.approx(48.0, abs=2.0)
        assert s.peak_sustained_p99 == pytest.approx(49.6, abs=1.0)

    def test_threshold_exceedance(self):
        prop = PropertyPoint(property_id="P1", longitude=5.0, latitude=5.0)
        # Realization 1 exceeded 17.5; realization 2 didn't.
        r1 = _wf_output(40.0, duration_above={17.5: 3.0})
        r2 = _wf_output(15.0, duration_above={17.5: 0.0})
        s = aggregate_property_winds(prop, [r1, r2], thresholds_ms=[17.5])
        assert s.threshold_exceedance[17.5] == 0.5
        assert s.mean_duration_above_ms[17.5] == pytest.approx(1.5)
