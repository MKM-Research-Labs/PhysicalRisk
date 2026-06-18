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
Tests for models.statistics.synthetic — coverage expansion.

Targets uncovered lines: 138-141.
These lines handle injecting historical high when the date was in range
but was not placed during generation (historical_high_placed is False
after the while loop, meaning the date matched a date string but not
via datetime.date() comparison in the main loop).

Line 137: if historical_high_dt and not historical_high_placed:
Line 138:     for obs in daily_observations:
Line 139:         if obs["date"] == historical_high_date:
Line 140:             obs["level_meters"] = historical_high
Line 141:             break
"""

from datetime import datetime, timedelta

import pytest


def _make_gauge(historical_high=6.0, historical_high_date=None):
    return {
        "FloodGauge": {
            "Header": {"GaugeID": "GAUGE-001", "GaugeName": "Test"},
            "FloodStages": {
                "FloodAlert": 4.0,
                "FloodWarning": 4.5,
                "SevereFloodWarning": 5.0,
            },
            "SensorStats": {
                "HistoricalHighLevel": historical_high,
                "HistoricalHighDate": historical_high_date,
                "FrequencyExceedLevel3": 2,
            },
        }
    }


class TestHistoricalHighInjection:

    def test_historical_high_injected_post_loop(self):
        """Lines 138-141: historical high injected after main loop.

        The main loop checks `current_date.date() == historical_high_dt.date()`.
        If the date is in range but the string comparison at line 139 matches,
        the post-loop injection fires. We use a date within range and verify
        the historical high level appears in the output.
        """
        from models.statistics.synthetic import generate_synthetic_timeseries

        # Pick a date well within the 1-year range
        target_date = (datetime.now() - timedelta(days=50)).strftime("%Y-%m-%d")
        gauge = _make_gauge(historical_high=9.99, historical_high_date=target_date)

        result = generate_synthetic_timeseries(gauge, years=1, seed=42)

        # Find the observation for that date
        match = [o for o in result if o["date"] == target_date]
        assert len(match) == 1
        assert match[0]["level_meters"] == 9.99

    def test_historical_high_not_in_range_skipped(self):
        """When historical_high_dt is None (out of range), post-loop block skipped."""
        from models.statistics.synthetic import generate_synthetic_timeseries

        gauge = _make_gauge(historical_high=8.0, historical_high_date="1850-01-01")
        result = generate_synthetic_timeseries(gauge, years=1, seed=42)

        # No observation should have 8.0 (out of range date, so no injection)
        assert all(o["level_meters"] != 8.0 for o in result)

    def test_no_historical_high_date(self):
        """When historical_high_date is None, both branches skipped."""
        from models.statistics.synthetic import generate_synthetic_timeseries

        gauge = _make_gauge(historical_high=7.0, historical_high_date=None)
        result = generate_synthetic_timeseries(gauge, years=1, seed=42)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_post_loop_injects_when_in_loop_check_misses(self, monkeypatch):
        """Lines 175-179: post-loop block injects historical high when the
        in-loop date.date()-equality miss leaves historical_high_placed=False.

        We force a miss by patching the parsed historical_high_dt's `.date()`
        to never equal the iterating current_date.date(), while still making
        comparisons against start_date / end_date pass through to the
        underlying datetime so the in-range check at line 116-117 succeeds.
        """
        from datetime import datetime as _dt
        import models.statistics.synthetic as synth_mod

        # Pick a date near today so the range check passes
        target_date = (_dt.now() - _dt(1970, 1, 1)).days  # arbitrary
        target_str = (_dt.now() - synth_mod.timedelta(days=10)).strftime("%Y-%m-%d")

        class _NoMatchDate:
            """date() return that never equals another date object."""
            def __eq__(self, other):
                return False
            def __ne__(self, other):
                return True
            def __hash__(self):
                return 0

        class _ProxyDT:
            def __init__(self, real):
                self._real = real
            def date(self):
                return _NoMatchDate()
            def __lt__(self, other):
                return self._real < other
            def __gt__(self, other):
                return self._real > other
            def __le__(self, other):
                return self._real <= other
            def __ge__(self, other):
                return self._real >= other
            def __bool__(self):
                return True

        real_datetime = synth_mod.datetime  # capture the real datetime class

        def fake_strptime(s, fmt):
            real = real_datetime.strptime(s, fmt)
            return _ProxyDT(real)

        # Patch only datetime.strptime in the module to wrap the result.
        # datetime.now() etc. still go through to the real datetime class.
        class _FakeDatetime:
            @staticmethod
            def now():
                return real_datetime.now()

            @staticmethod
            def strptime(s, fmt):
                return fake_strptime(s, fmt)

        monkeypatch.setattr(synth_mod, "datetime", _FakeDatetime)

        gauge = _make_gauge(historical_high=9.5, historical_high_date=target_str)
        result = synth_mod.generate_synthetic_timeseries(gauge, years=1, seed=7)

        # Post-loop block should have injected historical_high at target_str
        match = [o for o in result if o["date"] == target_str]
        assert len(match) == 1
        assert match[0]["level_meters"] == 9.5
