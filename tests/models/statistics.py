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
Tests for models.statistics.timeseries — timeseries statistics utilities.

Covers: calculate_timeseries_statistics (empty, basic, with flood stages,
flow_cumecs branch), calculate_level_statistics, calculate_flow_statistics.
"""

import pytest


# ===========================================================================
# Helpers
# ===========================================================================

def _make_obs(n=365, value_key="level_meters", base=3.0, peak_on_day=180, peak_val=6.0):
    """Generate synthetic daily observations."""
    obs = []
    for i in range(n):
        year = 2020 + i // 365
        day_of_year = i % 365 + 1
        month = (day_of_year - 1) // 30 + 1
        month = min(month, 12)
        day = (day_of_year - 1) % 30 + 1
        date = f"{year}-{month:02d}-{day:02d}"
        value = peak_val if i == peak_on_day else base
        obs.append({"date": date, value_key: value})
    return obs


_FLOOD_STAGES = {
    "FloodAlert": 4.0,
    "FloodWarning": 4.5,
    "SevereFloodWarning": 5.0,
}


# ===========================================================================
# calculate_timeseries_statistics
# ===========================================================================

class TestCalculateTimeseriesStatistics:

    def test_empty_returns_empty_dict(self):
        from models.statistics.timeseries import calculate_timeseries_statistics
        assert calculate_timeseries_statistics([], "level_meters") == {}

    def test_returns_dict(self):
        from models.statistics.timeseries import calculate_timeseries_statistics
        obs = _make_obs()
        result = calculate_timeseries_statistics(obs, "level_meters")
        assert isinstance(result, dict)

    def test_has_basic_keys(self):
        from models.statistics.timeseries import calculate_timeseries_statistics
        obs = _make_obs()
        result = calculate_timeseries_statistics(obs, "level_meters")
        assert "total_days" in result
        assert "mean_level_meters" in result
        assert "min_level_meters" in result
        assert "max_level_meters" in result

    def test_total_days_correct(self):
        from models.statistics.timeseries import calculate_timeseries_statistics
        obs = _make_obs(100)
        result = calculate_timeseries_statistics(obs, "level_meters")
        assert result["total_days"] == 100

    def test_has_percentiles(self):
        from models.statistics.timeseries import calculate_timeseries_statistics
        obs = _make_obs()
        result = calculate_timeseries_statistics(obs, "level_meters")
        assert "percentiles" in result
        assert "p5" in result["percentiles"]
        assert "p99" in result["percentiles"]

    def test_has_monthly_means(self):
        from models.statistics.timeseries import calculate_timeseries_statistics
        obs = _make_obs()
        result = calculate_timeseries_statistics(obs, "level_meters")
        assert "monthly_means" in result

    def test_has_annual_maxima(self):
        from models.statistics.timeseries import calculate_timeseries_statistics
        obs = _make_obs()
        result = calculate_timeseries_statistics(obs, "level_meters")
        assert "annual_maxima" in result
        assert "years_count" in result["annual_maxima"]

    def test_has_extreme_events(self):
        from models.statistics.timeseries import calculate_timeseries_statistics
        obs = _make_obs()
        result = calculate_timeseries_statistics(obs, "level_meters")
        assert "extreme_events" in result

    def test_single_observation_no_stdev_error(self):
        from models.statistics.timeseries import calculate_timeseries_statistics
        obs = [{"date": "2026-01-01", "level_meters": 3.5}]
        result = calculate_timeseries_statistics(obs, "level_meters")
        assert result["std_dev"] == 0

    def test_flood_stages_adds_exceedances(self):
        from models.statistics.timeseries import calculate_timeseries_statistics
        obs = _make_obs(365, peak_val=6.0)  # 1 day above 5.0
        result = calculate_timeseries_statistics(obs, "level_meters", _FLOOD_STAGES)
        assert "flood_exceedances" in result
        assert result["flood_exceedances"]["severe_warning"]["count"] >= 1

    def test_no_flood_stages_no_exceedances_key(self):
        from models.statistics.timeseries import calculate_timeseries_statistics
        obs = _make_obs()
        result = calculate_timeseries_statistics(obs, "level_meters")
        assert "flood_exceedances" not in result

    def test_flow_cumecs_adds_q_flows(self):
        from models.statistics.timeseries import calculate_timeseries_statistics
        obs = [{"date": f"2026-01-{i+1:02d}", "flow_cumecs": float(i + 1)}
               for i in range(20)]
        result = calculate_timeseries_statistics(obs, "flow_cumecs")
        assert "q95_flow" in result
        assert "q5_flow" in result

    def test_max_date_correct(self):
        from models.statistics.timeseries import calculate_timeseries_statistics
        obs = [
            {"date": "2026-01-01", "level_meters": 3.0},
            {"date": "2026-01-02", "level_meters": 6.0},  # max
            {"date": "2026-01-03", "level_meters": 3.5},
        ]
        result = calculate_timeseries_statistics(obs, "level_meters")
        assert result["max_level_meters_date"] == "2026-01-02"

    def test_record_start_end(self):
        from models.statistics.timeseries import calculate_timeseries_statistics
        obs = [
            {"date": "2020-01-01", "level_meters": 3.0},
            {"date": "2025-12-31", "level_meters": 4.0},
        ]
        result = calculate_timeseries_statistics(obs, "level_meters")
        assert result["record_start"] == "2020-01-01"
        assert result["record_end"] == "2025-12-31"

    def test_all_same_values(self):
        from models.statistics.timeseries import calculate_timeseries_statistics
        obs = [{"date": "2026-01-01", "level_meters": 3.0},
               {"date": "2026-01-02", "level_meters": 3.0}]
        result = calculate_timeseries_statistics(obs, "level_meters")
        assert result["mean_level_meters"] == 3.0
        assert result["std_dev"] == 0.0

    def test_flood_exceedances_zero_when_all_below(self):
        from models.statistics.timeseries import calculate_timeseries_statistics
        obs = _make_obs(100, base=2.0, peak_val=2.5)
        result = calculate_timeseries_statistics(obs, "level_meters", _FLOOD_STAGES)
        assert result["flood_exceedances"]["flood_alert"]["count"] == 0


# ===========================================================================
# calculate_level_statistics
# ===========================================================================

class TestCalculateLevelStatistics:

    def test_returns_dict(self):
        from models.statistics.timeseries import calculate_level_statistics
        obs = _make_obs()
        result = calculate_level_statistics(obs, _FLOOD_STAGES)
        assert isinstance(result, dict)

    def test_has_mean_level_not_mean_level_meters(self):
        """Key remapping: 'level_meters' → 'level'."""
        from models.statistics.timeseries import calculate_level_statistics
        obs = _make_obs()
        result = calculate_level_statistics(obs, _FLOOD_STAGES)
        assert "mean_level" in result
        assert "mean_level_meters" not in result

    def test_has_min_max(self):
        from models.statistics.timeseries import calculate_level_statistics
        obs = _make_obs()
        result = calculate_level_statistics(obs, _FLOOD_STAGES)
        assert "min_level" in result
        assert "max_level" in result


# ===========================================================================
# calculate_flow_statistics
# ===========================================================================

class TestCalculateFlowStatistics:

    def test_returns_dict(self):
        from models.statistics.timeseries import calculate_flow_statistics
        obs = [{"date": f"2026-01-{i+1:02d}", "flow_cumecs": float(i + 10)}
               for i in range(30)]
        result = calculate_flow_statistics(obs)
        assert isinstance(result, dict)

    def test_has_mean_flow_not_flow_cumecs(self):
        """Key remapping: 'flow_cumecs' → 'flow'."""
        from models.statistics.timeseries import calculate_flow_statistics
        obs = [{"date": "2026-01-01", "flow_cumecs": 100.0},
               {"date": "2026-01-02", "flow_cumecs": 200.0}]
        result = calculate_flow_statistics(obs)
        assert "mean_flow" in result
        assert "mean_flow_cumecs" not in result

    def test_has_q_flows(self):
        """Flow stats should include q5_flow and q95_flow."""
        from models.statistics.timeseries import calculate_flow_statistics
        obs = [{"date": f"2026-01-{i+1:02d}", "flow_cumecs": float(i * 10)}
               for i in range(30)]
        result = calculate_flow_statistics(obs)
        assert "q5_flow" in result
        assert "q95_flow" in result
