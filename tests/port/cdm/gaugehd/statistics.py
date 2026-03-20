# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for GaugeHistoricalDaily.calculate_statistics."""

import datetime as dt

import pytest

from port.cdm.gaugehd import GaugeHistoricalDaily


class TestCalculateStatistics:

    def test_empty_returns_empty_dict(self):
        assert GaugeHistoricalDaily().calculate_statistics([]) == {}

    def test_basic_stats_keys(self):
        gen = GaugeHistoricalDaily()
        flows = [
            {"date": "2020-01-01", "flow_cumecs": 50.0},
            {"date": "2020-01-02", "flow_cumecs": 60.0},
            {"date": "2020-01-03", "flow_cumecs": 70.0},
        ]
        stats = gen.calculate_statistics(flows)
        for key in ("record_start", "record_end", "total_days", "mean_flow",
                    "median_flow", "min_flow", "max_flow"):
            assert key in stats

    def test_mean_correct(self):
        gen = GaugeHistoricalDaily()
        flows = [
            {"date": "2020-01-01", "flow_cumecs": 10.0},
            {"date": "2020-01-02", "flow_cumecs": 20.0},
            {"date": "2020-01-03", "flow_cumecs": 30.0},
        ]
        assert gen.calculate_statistics(flows)["mean_flow"] == pytest.approx(20.0)

    def test_min_max_correct(self):
        gen = GaugeHistoricalDaily()
        flows = [
            {"date": "2020-01-01", "flow_cumecs": 5.0},
            {"date": "2020-01-02", "flow_cumecs": 100.0},
        ]
        stats = gen.calculate_statistics(flows)
        assert stats["min_flow"] == pytest.approx(5.0)
        assert stats["max_flow"] == pytest.approx(100.0)

    def test_percentiles_present(self):
        gen = GaugeHistoricalDaily()
        flows = [{"date": f"2020-01-{i+1:02d}", "flow_cumecs": float(i+1)}
                 for i in range(20)]
        stats = gen.calculate_statistics(flows)
        assert "percentiles" in stats
        for p in ("p5", "p25", "p50", "p75", "p95"):
            assert p in stats["percentiles"]

    def test_monthly_means_present(self):
        gen = GaugeHistoricalDaily()
        flows = [
            {"date": "2020-01-15", "flow_cumecs": 40.0},
            {"date": "2020-02-15", "flow_cumecs": 30.0},
        ]
        stats = gen.calculate_statistics(flows)
        assert "01" in stats["monthly_means"]
        assert "02" in stats["monthly_means"]

    def test_annual_maxima_present(self):
        gen = GaugeHistoricalDaily()
        flows = [
            {"date": "2020-06-01", "flow_cumecs": 80.0},
            {"date": "2021-06-01", "flow_cumecs": 90.0},
        ]
        stats = gen.calculate_statistics(flows)
        assert "annual_maxima" in stats
        assert stats["annual_maxima"]["years_count"] == 2

    def test_extreme_events_above_p99(self):
        gen = GaugeHistoricalDaily()
        flows = [{"date": f"2020-01-{i+1:02d}", "flow_cumecs": float(i+1)}
                 for i in range(20)]
        stats = gen.calculate_statistics(flows)
        assert "extreme_events" in stats
        assert stats["extreme_events"]["count"] >= 1

    def test_single_flow_no_std_dev_error(self):
        gen = GaugeHistoricalDaily()
        flows = [{"date": "2020-01-01", "flow_cumecs": 55.0}]
        assert gen.calculate_statistics(flows)["std_dev"] == 0


class TestCalculateStatisticsEdgeCases:

    def test_single_year_annual_maxima_std_dev_zero(self):
        gen = GaugeHistoricalDaily()
        flows = [
            {"date": "2020-03-01", "flow_cumecs": 80.0},
            {"date": "2020-06-15", "flow_cumecs": 50.0},
            {"date": "2020-09-01", "flow_cumecs": 60.0},
        ]
        stats = gen.calculate_statistics(flows)
        assert stats["annual_maxima"]["years_count"] == 1
        assert stats["annual_maxima"]["std_dev"] == 0

    def test_two_flow_std_dev_non_zero(self):
        gen = GaugeHistoricalDaily()
        flows = [
            {"date": "2020-01-01", "flow_cumecs": 10.0},
            {"date": "2020-01-02", "flow_cumecs": 30.0},
        ]
        assert gen.calculate_statistics(flows)["std_dev"] > 0

    def test_max_flow_date_correctly_identified(self):
        gen = GaugeHistoricalDaily()
        flows = [
            {"date": "2020-01-01", "flow_cumecs": 50.0},
            {"date": "2020-01-02", "flow_cumecs": 200.0},
            {"date": "2020-01-03", "flow_cumecs": 75.0},
        ]
        stats = gen.calculate_statistics(flows)
        assert stats["max_flow_date"] == "2020-01-02"
        assert stats["max_flow"] == pytest.approx(200.0)

    def test_total_years_approximate(self):
        gen = GaugeHistoricalDaily()
        flows = [{"date": f"2020-01-{i+1:02d}", "flow_cumecs": float(50 + i)}
                 for i in range(20)]
        stats = gen.calculate_statistics(flows)
        assert stats["total_days"] == 20
        assert stats["total_years"] == round(20 / 365.25, 1)

    def test_q95_flow_equals_p5(self):
        gen = GaugeHistoricalDaily()
        flows = [{"date": f"2020-01-{i+1:02d}", "flow_cumecs": float(i+1)}
                 for i in range(20)]
        stats = gen.calculate_statistics(flows)
        assert stats["q95_flow"] == stats["percentiles"]["p5"]

    def test_q5_flow_equals_p95(self):
        gen = GaugeHistoricalDaily()
        flows = [{"date": f"2020-01-{i+1:02d}", "flow_cumecs": float(i+1)}
                 for i in range(20)]
        stats = gen.calculate_statistics(flows)
        assert stats["q5_flow"] == stats["percentiles"]["p95"]

    def test_annual_maxima_events_capped_at_ten(self):
        gen = GaugeHistoricalDaily()
        flows = []
        for year in range(2000, 2015):
            flows.append({"date": dt.date(year, 6, 1).isoformat(),
                          "flow_cumecs": float(year)})
        stats = gen.calculate_statistics(flows)
        assert len(stats["annual_maxima"]["events"]) <= 10

    def test_extreme_events_top_10_capped(self):
        gen = GaugeHistoricalDaily()
        flows = [{"date": f"2020-01-{i+1:02d}", "flow_cumecs": float(100 + i)}
                 for i in range(20)]
        stats = gen.calculate_statistics(flows)
        assert len(stats["extreme_events"]["top_10"]) <= 10

    def test_record_start_and_end_match_data(self):
        gen = GaugeHistoricalDaily()
        flows = [
            {"date": "2018-05-01", "flow_cumecs": 40.0},
            {"date": "2021-08-15", "flow_cumecs": 55.0},
            {"date": "2019-12-01", "flow_cumecs": 45.0},
        ]
        stats = gen.calculate_statistics(flows)
        assert stats["record_start"] == "2018-05-01"
        assert stats["record_end"] == "2021-08-15"

    def test_all_percentile_keys_present(self):
        gen = GaugeHistoricalDaily()
        flows = [{"date": f"2020-01-{i+1:02d}", "flow_cumecs": float(i+1)}
                 for i in range(20)]
        stats = gen.calculate_statistics(flows)
        for p in ("p5", "p10", "p25", "p50", "p75", "p90", "p95", "p99"):
            assert p in stats["percentiles"]
