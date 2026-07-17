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

"""Tests for synthetic gauge generation and GaugeHistoricalDaily class."""

import pytest

import database
from db_helpers import tmp_catchment
from tests.port.gauge.conftest import write_nrfa_csv, SAMPLE_GAUGE_ENTRY


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend so the migrated gaugehd writers persist per-gauge
    history through database (physically under tmp_path/gaugehd)."""
    with tmp_catchment(tmp_path):
        yield


# ===========================================================================
# generate_from_gauge_portfolio (synthetic.py)
# ===========================================================================

class TestGenerateFromGaugePortfolio:

    def test_returns_dict(self, tmp_path):
        from port.src.gauge.gaugehd.synthetic import generate_from_gauge_portfolio
        result = generate_from_gauge_portfolio(SAMPLE_GAUGE_ENTRY, years=5)
        assert isinstance(result, dict)

    def test_schema_version(self, tmp_path):
        from port.src.gauge.gaugehd.synthetic import generate_from_gauge_portfolio
        result = generate_from_gauge_portfolio(SAMPLE_GAUGE_ENTRY, years=5)
        assert result["schema_version"] == "1.0"

    def test_gauge_metadata_extracted(self, tmp_path):
        from port.src.gauge.gaugehd.synthetic import generate_from_gauge_portfolio
        result = generate_from_gauge_portfolio(SAMPLE_GAUGE_ENTRY, years=5)
        assert result["gauge_metadata"]["gauge_id"] == "GAUGE-TEST01"

    def test_daily_observations_generated(self, tmp_path):
        from port.src.gauge.gaugehd.synthetic import generate_from_gauge_portfolio
        result = generate_from_gauge_portfolio(SAMPLE_GAUGE_ENTRY, years=5)
        assert len(result["daily_observations"]) > 0

    def test_history_persisted(self, tmp_path):
        from port.src.gauge.gaugehd.synthetic import generate_from_gauge_portfolio
        generate_from_gauge_portfolio(SAMPLE_GAUGE_ENTRY, years=5)
        # Persisted as a keyed gauge_history record; read it back via the seam so the
        # assertion holds on both file and pg backends.
        assert database.get_gauge_history(database.active_catchment(), "GAUGE-TEST01")

    def test_default_catchment_persists(self, tmp_path):
        """With no explicit catchment, history persists under the active catchment."""
        from port.src.gauge.gaugehd.synthetic import generate_from_gauge_portfolio
        result = generate_from_gauge_portfolio(SAMPLE_GAUGE_ENTRY, years=5)
        assert isinstance(result, dict)
        assert "GAUGE-TEST01" in list(
            database.iter_gauge_history_ids(database.active_catchment()))

    def test_non_nested_gauge_data(self, tmp_path):
        """Gauge data without FloodGauge wrapper."""
        from port.src.gauge.gaugehd.synthetic import generate_from_gauge_portfolio
        data = {
            "Header": {"GaugeID": "GAUGE-FLAT", "GaugeName": "Flat", "CatchmentID": "thames"},
            "FloodStages": {"FloodAlert": 3.0, "FloodWarning": 4.5, "SevereFloodWarning": 5.5},
            "Location": {},
            "SensorStats": {},
        }
        result = generate_from_gauge_portfolio(data, years=5)
        assert result["gauge_metadata"]["gauge_id"] == "GAUGE-FLAT"


# ===========================================================================
# GaugeHistoricalDaily class
# ===========================================================================

class TestGaugeHistoricalDaily:

    def test_default_years(self):
        from port.src.gauge.gaugehd import GaugeHistoricalDaily
        ghd = GaugeHistoricalDaily()
        assert ghd.years_of_history == 50

    def test_custom_years(self):
        from port.src.gauge.gaugehd import GaugeHistoricalDaily
        ghd = GaugeHistoricalDaily(years_of_history=30)
        assert ghd.years_of_history == 30

    def test_filter_by_years_none(self):
        from port.src.gauge.gaugehd import GaugeHistoricalDaily
        ghd = GaugeHistoricalDaily()
        flows = [{"date": "2020-01-01", "flow_cumecs": 10.0}]
        result = ghd.filter_by_years(flows)
        assert result == flows

    def test_filter_by_years_explicit(self):
        from port.src.gauge.gaugehd import GaugeHistoricalDaily
        ghd = GaugeHistoricalDaily()
        flows = [{"date": "2020-01-01", "flow_cumecs": 10.0}]
        result = ghd.filter_by_years(flows, years=5)
        assert isinstance(result, list)

    def test_parse_nrfa_csv_via_class(self, tmp_path):
        from port.src.gauge.gaugehd import GaugeHistoricalDaily
        ghd = GaugeHistoricalDaily()
        csv_file = write_nrfa_csv(tmp_path, n_rows=10)
        metadata, flows = ghd.parse_nrfa_csv(csv_file)
        assert len(flows) == 10

    def test_calculate_statistics_via_class(self):
        from port.src.gauge.gaugehd import GaugeHistoricalDaily
        ghd = GaugeHistoricalDaily()
        flows = [
            {"date": "2020-01-01", "flow_cumecs": 10.0},
            {"date": "2020-02-01", "flow_cumecs": 20.0},
        ]
        stats = ghd.calculate_statistics(flows)
        assert isinstance(stats, dict)

    def test_generate_from_nrfa_via_class(self, tmp_path):
        from port.src.gauge.gaugehd import GaugeHistoricalDaily
        ghd = GaugeHistoricalDaily(years_of_history=5)
        csv_file = write_nrfa_csv(tmp_path, n_rows=20)
        result = ghd.generate_from_nrfa(csv_file)
        assert isinstance(result, dict)
        # The history was persisted through database (keyed gauge_history).
        assert list(database.iter_gauge_history_ids(database.active_catchment()))

    def test_generate_from_nrfa_uses_default_years(self, tmp_path):
        """When years=None, uses years_of_history."""
        from port.src.gauge.gaugehd import GaugeHistoricalDaily
        ghd = GaugeHistoricalDaily(years_of_history=10)
        csv_file = write_nrfa_csv(tmp_path, n_rows=20)
        result = ghd.generate_from_nrfa(csv_file, years=None)
        assert result["years_included"] == 10

    def test_generate_from_gauge_portfolio_via_class(self, tmp_path):
        """generate_from_gauge_portfolio via class method."""
        from port.src.gauge.gaugehd import GaugeHistoricalDaily
        ghd = GaugeHistoricalDaily(years_of_history=5)
        result = ghd.generate_from_gauge_portfolio(SAMPLE_GAUGE_ENTRY)
        assert isinstance(result, dict)
        assert result["years_included"] == 5

    def test_generate_from_gauge_portfolio_explicit_years(self, tmp_path):
        """generate_from_gauge_portfolio with explicit years overrides default."""
        from port.src.gauge.gaugehd import GaugeHistoricalDaily
        ghd = GaugeHistoricalDaily(years_of_history=50)
        result = ghd.generate_from_gauge_portfolio(SAMPLE_GAUGE_ENTRY, years=3)
        assert result["years_included"] == 3

    def test_calculate_statistics_from_levels(self):
        """calculate_statistics_from_levels via class."""
        from datetime import date, timedelta
        from port.src.gauge.gaugehd import GaugeHistoricalDaily
        ghd = GaugeHistoricalDaily()
        start = date(2020, 1, 1)
        obs = [
            {"date": (start + timedelta(days=i)).isoformat(), "level_meters": 1.0 + (i % 10) * 0.3}
            for i in range(1000)
        ]
        flood_stages = {"FloodAlert": 2.0, "FloodWarning": 3.0, "SevereFloodWarning": 4.0}
        stats = ghd.calculate_statistics_from_levels(obs, flood_stages)
        assert isinstance(stats, dict)

    def test_generate_synthetic_timeseries_via_class(self):
        """generate_synthetic_timeseries via class method."""
        from port.src.gauge.gaugehd import GaugeHistoricalDaily
        ghd = GaugeHistoricalDaily()
        gauge_data = {
            "FloodGauge": {
                "Header": {"GaugeID": "GAUGE-SYN", "GaugeName": "Synthetic"},
                "FloodStages": {"FloodAlert": 2.0, "FloodWarning": 3.0, "SevereFloodWarning": 4.0},
                "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1, "GaugeElevation": 5.0},
                "SensorStats": {"HistoricalHighLevel": 5.0},
            }
        }
        result = ghd.generate_synthetic_timeseries(gauge_data, years=2, seed=42)
        assert isinstance(result, list)
        assert len(result) > 0
