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

"""Edge arms of the stress hydrograph helpers."""

from unittest.mock import patch

from config import config
from routes.trading.stress._helpers import (
    _get_stress_storms_dir,
    _synthesize_hydrograph,
    build_scaled_hydrograph,
)


def test_the_stress_storm_dir_follows_the_active_catchment():
    """Resolved through config, so a catchment switch moves it too."""
    assert _get_stress_storms_dir() == config.get_input_dir() / 'stress_storms'


class TestBuildScaledHydrograph:
    """The two ways a gauge yields no hydrograph."""

    def test_a_missing_timeseries_yields_none(self):
        with patch('routes.trading.stress._helpers.database'
                   '.get_gauge_timeseries', return_value=None):
            assert build_scaled_hydrograph('GAUGE-404', {}) is None

    def test_a_timeseries_with_no_readings_yields_none(self):
        """Present but empty is not the same as absent, and both must return
        None rather than a flat line — a flat hydrograph would price as a
        storm that never happened."""
        with patch('routes.trading.stress._helpers.database'
                   '.get_gauge_timeseries',
                   return_value={'flood_simulation': {'readings': []}}):
            assert build_scaled_hydrograph('GAUGE-EMPTY', {}) is None

    def test_a_timeseries_missing_the_block_entirely_yields_none(self):
        with patch('routes.trading.stress._helpers.database'
                   '.get_gauge_timeseries', return_value={}):
            assert build_scaled_hydrograph('GAUGE-BARE', {}) is None


class TestSynthesizeHydrograph:
    """Shape of the synthesised rise-peak-decay curve."""

    def test_it_returns_one_level_per_hour(self):
        levels = _synthesize_hydrograph(1.0, 2.0, 24, 0.5, num_hours=12)
        assert len(levels) == 12

    def test_the_peak_never_exceeds_base_plus_change(self):
        levels = _synthesize_hydrograph(1.0, 2.0, 24, 0.5, num_hours=12)
        assert max(levels) <= 3.0
        assert min(levels) >= 1.0

    def test_a_peak_at_hour_zero_decays_from_the_start(self):
        """peak_position 0 puts peak_hour at 0, taking the decay-only arm."""
        levels = _synthesize_hydrograph(1.0, 2.0, 24, 0.0, num_hours=12)
        assert levels == sorted(levels, reverse=True)

    def test_a_late_peak_is_capped_inside_the_window(self):
        """The cap is what makes the remaining <= 0 guard unreachable."""
        levels = _synthesize_hydrograph(1.0, 2.0, 999, 1.0, num_hours=12)
        assert len(levels) == 12
        assert levels[-1] == max(levels)
