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

"""Tests for stress test hydrograph synthesis."""

import math
import pytest


def _synthesize_hydrograph(base_level, level_change, duration_hours,
                           peak_position, num_hours=168):
    """Local copy of the hydrograph function for unit testing.
    Default num_hours=168 matches STORM_HOURS in routes/trading/stress.py.
    """
    peak_hour = min(duration_hours * peak_position, num_hours - 1)
    levels = []
    for h in range(num_hours):
        if peak_hour <= 0:
            t_decay = h / max(num_hours - 1, 1)
            frac = math.exp(-3.0 * t_decay)
        elif h <= peak_hour:
            t_rise = h / peak_hour
            frac = math.sin(t_rise * math.pi / 2)
        else:
            remaining = num_hours - peak_hour
            if remaining <= 0:
                frac = 1.0
            else:
                t_decay = (h - peak_hour) / remaining
                frac = math.exp(-3.0 * t_decay)
        levels.append(round(base_level + level_change * frac, 4))
    return levels


class TestSynthesizeHydrograph:
    """Tests for hydrograph synthesis used in stress scenarios."""

    def test_returns_168_hours(self):
        """Default hydrograph must return 168 hourly values (STORM_HOURS = 7-day window)."""
        levels = _synthesize_hydrograph(2.0, 3.0, 40, 0.4)
        assert len(levels) == 168

    def test_starts_at_base_level(self):
        """Hour 0 should be at base level."""
        levels = _synthesize_hydrograph(2.0, 3.0, 40, 0.4)
        assert abs(levels[0] - 2.0) < 0.01

    def test_peak_level(self):
        """Peak should reach base + level_change."""
        base = 2.0
        change = 3.0
        levels = _synthesize_hydrograph(base, change, 40, 0.4)
        peak = max(levels)
        # Peak should be approximately base + change (within tolerance
        # because peak_hour might not be exactly an integer hour)
        assert peak >= base + change * 0.9
        assert peak <= base + change + 0.1

    def test_recession_after_peak(self):
        """Water level should decrease after peak."""
        levels = _synthesize_hydrograph(2.0, 3.0, 40, 0.3)
        peak_idx = levels.index(max(levels))
        # Tail should be lower than peak (storm has long recession in 168h window)
        if peak_idx < 160:
            assert levels[-1] < levels[peak_idx]

    def test_monotonic_rise(self):
        """Water levels should be non-decreasing before peak."""
        levels = _synthesize_hydrograph(2.0, 3.0, 40, 0.4)
        peak_idx = levels.index(max(levels))
        for i in range(1, peak_idx):
            assert levels[i] >= levels[i - 1] - 0.01  # Allow tiny rounding

    def test_all_above_base(self):
        """All levels should be >= base level (positive level_change)."""
        base = 2.0
        levels = _synthesize_hydrograph(base, 3.0, 40, 0.4)
        for lvl in levels:
            assert lvl >= base - 0.01

    def test_custom_num_hours(self):
        """Custom num_hours should produce the right length."""
        levels = _synthesize_hydrograph(1.5, 2.0, 30, 0.5, num_hours=100)
        assert len(levels) == 100

    def test_zero_duration(self):
        """Zero duration should still produce valid levels."""
        levels = _synthesize_hydrograph(2.0, 3.0, 0, 0.5)
        assert len(levels) == 168
        # Should be decay from peak (peak_hour = 0)
        assert levels[0] > 2.0  # Starts at elevated level

    def test_short_storm(self):
        """Very short storm peaks early."""
        levels = _synthesize_hydrograph(1.0, 4.0, 10, 0.3)
        peak_idx = levels.index(max(levels))
        # Peak should be in first 10 hours
        assert peak_idx <= 10


class TestStressKnockOutLogic:
    """Regression: Stress test knock-out logic in the backend.

    When water level exceeds a trade's trigger level, the contract
    pays out full notional and expires (knock-out). It must NOT
    revert when water recedes.
    """

    def _simulate_knock_out(self, hydrograph, trades, trigger_levels):
        """Simulate the knock-out logic from stress.py."""
        trade_triggered_hour = {}
        hourly = []

        for h in range(len(hydrograph)):
            water_level = hydrograph[h]
            per_trade = []
            portfolio_cash = 0

            for t in trades:
                swap_id = t['swap_id']
                direction = 1.0 if t['is_payer'] else -1.0
                trig = t.get('trigger', 'severe')
                trig_level = trigger_levels.get(trig, 0)

                if swap_id in trade_triggered_hour:
                    cash_price = t['notional'] * direction
                elif trig_level > 0 and water_level >= trig_level:
                    trade_triggered_hour[swap_id] = h
                    cash_price = t['notional'] * direction
                else:
                    cash_price = t['notional'] * 0.5 * direction  # dummy

                per_trade.append({
                    'swap_id': swap_id,
                    'cash_price': cash_price,
                    'triggered': swap_id in trade_triggered_hour,
                })
                portfolio_cash += cash_price

            hourly.append({
                'hour': h,
                'water_level': water_level,
                'portfolio_cash': portfolio_cash,
                'per_trade': per_trade,
            })

        return hourly, trade_triggered_hour

    def test_trade_knocks_out_at_trigger(self):
        """Trade must knock out when water >= trigger level."""
        # Hydrograph: rises above 5.0m at hour 3, then falls back
        hydro = [2.0, 3.0, 4.0, 5.5, 6.0, 4.0, 3.0, 2.0]
        trades = [{'swap_id': 'T1', 'is_payer': True,
                   'notional': 1_000_000, 'trigger': 'severe'}]
        triggers = {'severe': 5.0}
        hourly, triggered = self._simulate_knock_out(hydro, trades, triggers)

        assert 'T1' in triggered
        assert triggered['T1'] == 3  # First hour >= 5.0

    def test_cash_price_stays_at_notional_after_ko(self):
        """After knock-out, cash price must stay at full notional."""
        hydro = [2.0, 3.0, 5.5, 6.0, 3.0, 2.0, 1.5, 1.0]
        trades = [{'swap_id': 'T1', 'is_payer': True,
                   'notional': 1_000_000, 'trigger': 'severe'}]
        triggers = {'severe': 5.0}
        hourly, _ = self._simulate_knock_out(hydro, trades, triggers)

        # At hour 2: triggers (water=5.5 >= 5.0)
        assert hourly[2]['per_trade'][0]['triggered'] is True
        assert hourly[2]['per_trade'][0]['cash_price'] == 1_000_000

        # At hours 4-7: water is below trigger, but cash stays at notional
        for h in range(4, 8):
            pt = hourly[h]['per_trade'][0]
            assert pt['triggered'] is True, \
                f"Hour {h}: trade must remain triggered"
            assert pt['cash_price'] == 1_000_000, \
                f"Hour {h}: cash must stay at full notional after KO"

    def test_no_ko_when_below_trigger(self):
        """Trade must NOT knock out if water stays below trigger."""
        hydro = [2.0, 3.0, 4.0, 4.5, 3.0, 2.0]
        trades = [{'swap_id': 'T1', 'is_payer': True,
                   'notional': 1_000_000, 'trigger': 'severe'}]
        triggers = {'severe': 5.0}
        _, triggered = self._simulate_knock_out(hydro, trades, triggers)

        assert 'T1' not in triggered

    def test_different_triggers_ko_independently(self):
        """Alert trade KOs before severe trade."""
        hydro = [2.0, 3.5, 4.0, 5.5, 3.0, 2.0]
        trades = [
            {'swap_id': 'ALERT', 'is_payer': True,
             'notional': 1_000_000, 'trigger': 'alert'},
            {'swap_id': 'SEVERE', 'is_payer': True,
             'notional': 1_000_000, 'trigger': 'severe'},
        ]
        triggers = {'alert': 3.2, 'warning': 4.0, 'severe': 5.0}
        _, triggered = self._simulate_knock_out(hydro, trades, triggers)

        assert 'ALERT' in triggered
        assert 'SEVERE' in triggered
        assert triggered['ALERT'] < triggered['SEVERE'], \
            "Alert trade should KO before severe trade"

    def test_receiver_ko_cash_is_negative(self):
        """Receiver (short protection) gets negative cash on KO."""
        hydro = [2.0, 5.5, 3.0]
        trades = [{'swap_id': 'RCV', 'is_payer': False,
                   'notional': 1_000_000, 'trigger': 'severe'}]
        triggers = {'severe': 5.0}
        hourly, _ = self._simulate_knock_out(hydro, trades, triggers)

        # Receiver direction = -1, so cash = -notional
        assert hourly[1]['per_trade'][0]['cash_price'] == -1_000_000
