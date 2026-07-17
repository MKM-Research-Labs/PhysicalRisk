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

"""Tests for port.src.stressm.pipeline._helpers._extract_pulse_peaks.

Targets the start_h >= end_h skip branch (line 24) and main success path.
"""

from types import SimpleNamespace

import numpy as np

from port.src.stressm.pipeline._helpers import _extract_pulse_peaks


def _make_storm(storm_index, start_time_hours, duration_hours, precip_mm=10.0):
    return SimpleNamespace(
        storm_index=storm_index,
        start_time_hours=start_time_hours,
        duration_hours=duration_hours,
        precipitation_mm=precip_mm,
    )


def _make_seq(storms):
    return SimpleNamespace(storms=storms)


class TestExtractPulsePeaks:
    def test_single_storm_within_window(self):
        levels = np.zeros(168)
        levels[10:20] = 1.0
        levels[15] = 5.0
        seq = _make_seq([_make_storm(0, 10.0, 8.0, precip_mm=25.0)])

        result = _extract_pulse_peaks(levels, seq, lag=2)
        assert len(result) == 1
        assert result[0]["storm_index"] == 0
        assert result[0]["peak_m"] == 5.0
        assert result[0]["start_hour"] == 10.0
        assert result[0]["duration_hours"] == 8.0
        assert result[0]["precip_mm"] == 25.0

    def test_storm_starting_past_window_skipped(self):
        """Line 24: start_h >= end_h → continue (skip pulse)."""
        levels = np.zeros(168)
        # Storm starts at hour 168 (i.e. >= n) — start_h is clamped to 168,
        # end_h is also clamped to 168, so start_h >= end_h triggers skip.
        seq = _make_seq([_make_storm(0, 168.0, 12.0)])

        result = _extract_pulse_peaks(levels, seq, lag=2)
        assert result == []

    def test_mix_valid_and_skipped(self):
        levels = np.linspace(0, 5, 168)
        seq = _make_seq([
            _make_storm(0, 5.0, 4.0),       # valid
            _make_storm(1, 200.0, 6.0),     # past end → skipped (line 24)
        ])
        result = _extract_pulse_peaks(levels, seq, lag=2)
        assert len(result) == 1
        assert result[0]["storm_index"] == 0

    def test_negative_start_time_clamped_to_zero(self):
        levels = np.zeros(168)
        levels[0:5] = 3.0
        seq = _make_seq([_make_storm(0, -2.5, 5.0)])

        result = _extract_pulse_peaks(levels, seq, lag=2)
        assert len(result) == 1
        assert result[0]["peak_m"] == 3.0
