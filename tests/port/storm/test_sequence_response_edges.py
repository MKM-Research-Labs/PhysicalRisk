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

"""Degenerate-storm arms in the sequence response model.

A generated sequence never contains a zero-length storm or one starting past
the event window, but a hand-built scenario or a rounding edge can produce
either — and both would index outside the hourly series if they were not
skipped. The peak fallback matters for the same reason: a storm whose window
collapses must report the base level, not raise or report a peak from
somewhere else in the series.
"""

import numpy as np

from port.src.storm_multi.core.data_structures import SequenceStorm, StormSequence
from port.src.storm_multi.models.sequence_response import (
    EVENT_WINDOW_HOURS,
    SequenceGaugeParams,
    _make_precip_series,
    compute_storm_peaks,
)


def _storm(index, start, duration, precip=50.0, peak_position=0.5):
    return SequenceStorm(
        storm_id=f"STORM-{index}", scenario_id="SEQ-1", storm_index=index,
        start_time_hours=start, duration_hours=duration,
        intensity_category="severe", intensity_factor=1.0,
        precipitation_mm=precip, peak_position=peak_position,
    )


def _sequence(storms):
    return StormSequence(
        sequence_id="SEQ-1", sequence_type="cluster",
        sequence_start="2026-01-01T00:00:00", total_duration_hours=168.0,
        storms=storms, num_storms=len(storms),
    )


def _params():
    return SequenceGaugeParams(
        gauge_id="GAUGE-1", base_level=1.5, flood_alert=3.0,
        flood_warning=4.0, severe_warning=5.0,
    )


class TestPrecipSeriesSkips:

    def test_a_zero_length_storm_contributes_nothing(self):
        series = _make_precip_series(_sequence([_storm(0, 10.0, 0.0)]))
        assert series.shape == (EVENT_WINDOW_HOURS,)
        assert float(np.sum(series)) == 0.0

    def test_a_storm_starting_past_the_window_contributes_nothing(self):
        # Indexing from start_h would otherwise run off the end of the array.
        series = _make_precip_series(
            _sequence([_storm(0, EVENT_WINDOW_HOURS + 5.0, 6.0)]))
        assert float(np.sum(series)) == 0.0

    def test_a_valid_storm_alongside_a_degenerate_one_still_lands(self):
        """The skip must drop the bad storm, not the sequence."""
        series = _make_precip_series(_sequence([
            _storm(0, 10.0, 0.0),          # zero length — skipped
            _storm(1, 20.0, 6.0, precip=40.0),
        ]))
        assert float(np.sum(series)) > 0.0


class TestStormPeakFallback:

    def test_a_collapsed_window_reports_the_base_level(self):
        """start_h == end_h leaves no slice to take a maximum over, so the
        gauge is reported at its base level rather than raising on an empty
        np.max."""
        peaks = compute_storm_peaks(
            _sequence([_storm(0, EVENT_WINDOW_HOURS + 10.0, 0.0)]), _params())
        assert peaks == [(0, 1.5)]

    def test_a_normal_storm_reports_a_level_at_or_above_base(self):
        # Guards the fallback above from passing for the wrong reason: a real
        # storm must not also come back at exactly the base level.
        peaks = compute_storm_peaks(
            _sequence([_storm(0, 12.0, 24.0, precip=120.0)]), _params())
        assert len(peaks) == 1
        assert peaks[0][1] >= 1.5


class TestFromGaugeConfig:
    """The adapter from a stormgauge GaugeConfig.

    It is the seam between the gauge model and the sequence model, so a field
    dropped here silently reverts that parameter to its dataclass default —
    sensitivity in particular, where a missed mapping means every gauge
    responds identically and the spatial variation disappears without error.
    """

    class _GaugeConfig:
        gauge_id = "GAUGE-042"
        base_level = 1.75
        flood_alert = 3.4
        flood_warning = 4.5
        severe_warning = 5.6
        sensitivity = 1.8

    def test_every_field_is_carried_across(self):
        params = SequenceGaugeParams.from_gauge_config(self._GaugeConfig())
        assert params.gauge_id == "GAUGE-042"
        assert params.base_level == 1.75
        assert params.flood_alert == 3.4
        assert params.flood_warning == 4.5
        assert params.severe_warning == 5.6
        assert params.sensitivity == 1.8

    def test_sensitivity_is_not_left_at_its_default(self):
        # The default is 1.0, so a dropped mapping would be invisible unless
        # the source value differs from it.
        assert SequenceGaugeParams.sensitivity != self._GaugeConfig.sensitivity
        params = SequenceGaugeParams.from_gauge_config(self._GaugeConfig())
        assert params.sensitivity == self._GaugeConfig.sensitivity

    def test_routing_parameters_keep_their_defaults(self):
        """The adapter maps thresholds only; the hydraulic routing constants
        are the sequence model's own and must not be pulled from the gauge."""
        params = SequenceGaugeParams.from_gauge_config(self._GaugeConfig())
        assert params.response_lag_hours == 2
        assert params.rise_factor == 3.0
