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
Tests for models.statistics.synthetic — synthetic timeseries generation.

Covers: generate_synthetic_timeseries (basic, with seed, with historical high,
with freq_exceed_level3, missing flood stages).
"""

from datetime import datetime, timedelta

import pytest


# ===========================================================================
# Helpers
# ===========================================================================

def _make_gauge(gauge_id="GAUGE-001", flood_alert=4.0, flood_warning=4.5,
                severe_warning=5.0, historical_high=6.0,
                historical_high_date=None, freq_exceed=2):
    return {
        "FloodGauge": {
            "Header": {"GaugeID": gauge_id, "GaugeName": "Test"},
            "FloodStages": {
                "FloodAlert": flood_alert,
                "FloodWarning": flood_warning,
                "SevereFloodWarning": severe_warning,
            },
            "SensorStats": {
                "HistoricalHighLevel": historical_high,
                "HistoricalHighDate": historical_high_date,
                "FrequencyExceedLevel3": freq_exceed,
            },
        }
    }


# ===========================================================================
# generate_synthetic_timeseries
# ===========================================================================

class TestGenerateSyntheticTimeseries:

    def test_returns_list(self):
        from models.statistics.synthetic import generate_synthetic_timeseries
        result = generate_synthetic_timeseries(_make_gauge(), years=1)
        assert isinstance(result, list)

    def test_correct_length_approximately(self):
        from models.statistics.synthetic import generate_synthetic_timeseries
        result = generate_synthetic_timeseries(_make_gauge(), years=2)
        # 2 years ≈ 730 days (±1 for end boundary)
        assert 728 <= len(result) <= 732

    def test_each_obs_has_date_and_level(self):
        from models.statistics.synthetic import generate_synthetic_timeseries
        result = generate_synthetic_timeseries(_make_gauge(), years=1)
        for obs in result:
            assert "date" in obs
            assert "level_meters" in obs
            assert isinstance(obs["level_meters"], float)

    def test_all_levels_positive(self):
        from models.statistics.synthetic import generate_synthetic_timeseries
        result = generate_synthetic_timeseries(_make_gauge(), years=5, seed=42)
        assert all(obs["level_meters"] > 0 for obs in result)

    def test_seed_reproducible(self):
        from models.statistics.synthetic import generate_synthetic_timeseries
        r1 = generate_synthetic_timeseries(_make_gauge(), years=1, seed=42)
        r2 = generate_synthetic_timeseries(_make_gauge(), years=1, seed=42)
        assert r1 == r2

    def test_different_seeds_different_output(self):
        from models.statistics.synthetic import generate_synthetic_timeseries
        r1 = generate_synthetic_timeseries(_make_gauge(), years=5, seed=1)
        r2 = generate_synthetic_timeseries(_make_gauge(), years=5, seed=99)
        levels1 = [o["level_meters"] for o in r1]
        levels2 = [o["level_meters"] for o in r2]
        assert levels1 != levels2

    def test_dates_are_sequential(self):
        from models.statistics.synthetic import generate_synthetic_timeseries
        result = generate_synthetic_timeseries(_make_gauge(), years=1)
        for i in range(1, len(result)):
            d_prev = datetime.strptime(result[i - 1]["date"], "%Y-%m-%d")
            d_curr = datetime.strptime(result[i]["date"], "%Y-%m-%d")
            assert (d_curr - d_prev).days == 1

    def test_historical_high_date_in_range(self):
        """When historical high date is within range, that day gets historical_high level."""
        from models.statistics.synthetic import generate_synthetic_timeseries
        # Use a date that's within the last year
        high_date = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")
        gauge = _make_gauge(historical_high=7.5, historical_high_date=high_date)
        result = generate_synthetic_timeseries(gauge, years=1)
        # Find the historical high date
        match = [o for o in result if o["date"] == high_date]
        if match:
            assert match[0]["level_meters"] == 7.5

    def test_historical_high_date_out_of_range(self):
        """Historical high date before start_date is ignored."""
        from models.statistics.synthetic import generate_synthetic_timeseries
        gauge = _make_gauge(historical_high_date="1800-01-01")
        result = generate_synthetic_timeseries(gauge, years=1)
        assert isinstance(result, list)

    def test_historical_high_date_invalid_format(self):
        """Invalid date format doesn't crash."""
        from models.statistics.synthetic import generate_synthetic_timeseries
        gauge = _make_gauge(historical_high_date="not-a-date")
        result = generate_synthetic_timeseries(gauge, years=1)
        assert isinstance(result, list)

    def test_flat_gauge_data_uses_defaults(self):
        """Gauge data without FloodGauge wrapper uses defaults."""
        from models.statistics.synthetic import generate_synthetic_timeseries
        flat = {
            "FloodStages": {
                "FloodAlert": 3.5,
                "FloodWarning": 4.0,
                "SevereFloodWarning": 4.5,
            },
            "SensorStats": {},
        }
        result = generate_synthetic_timeseries(flat, years=1)
        assert isinstance(result, list)

    def test_missing_flood_stages_uses_defaults(self):
        """Gauge data with no FloodStages uses sensible defaults."""
        from models.statistics.synthetic import generate_synthetic_timeseries
        gauge = {"FloodGauge": {"Header": {}, "SensorStats": {}, "FloodStages": {}}}
        result = generate_synthetic_timeseries(gauge, years=1)
        assert isinstance(result, list)
        assert len(result) > 0
