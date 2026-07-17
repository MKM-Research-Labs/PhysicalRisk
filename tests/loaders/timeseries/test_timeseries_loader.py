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

"""Tests for TimeseriesLoader."""

import json
from datetime import datetime
from pathlib import Path

from tests.loaders.conftest import make_gauge_ts_file, seed_gauge_ts


def _gaugets(tmp_path) -> Path:
    """Create and return a gaugets/ directory under tmp_path."""
    d = tmp_path / "gaugets"
    d.mkdir(exist_ok=True)
    return d


class TestTimeseriesLoaderBasic:

    def test_load_all_from_directory(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        d = _gaugets(tmp_path)
        make_gauge_ts_file(d, "GAUGE-001")
        make_gauge_ts_file(d, "GAUGE-002")
        assert len(TimeseriesLoader(tmp_path).load_all()) >= 1

    def test_missing_dir_returns_empty(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        assert TimeseriesLoader(tmp_path / "nonexistent").load_all() == []

    def test_count_returns_number_of_gauge_files(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        d = _gaugets(tmp_path)
        make_gauge_ts_file(d, "GAUGE-001")
        make_gauge_ts_file(d, "GAUGE-002")
        assert TimeseriesLoader(tmp_path).count() == 2

    def test_list_all_returns_summaries(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        d = _gaugets(tmp_path)
        make_gauge_ts_file(d, "GAUGE-001")
        assert isinstance(TimeseriesLoader(tmp_path).list_all(), list)

    def test_get_available_gauge_ids(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        d = _gaugets(tmp_path)
        make_gauge_ts_file(d, "GAUGE-001")
        make_gauge_ts_file(d, "GAUGE-002")
        ids = TimeseriesLoader(tmp_path).get_available_gauge_ids()
        assert "GAUGE-001" in ids
        assert "GAUGE-002" in ids

    def test_get_available_gauge_ids_missing_dir(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        assert TimeseriesLoader(tmp_path / "nonexistent").get_available_gauge_ids() == []


class TestTimeseriesLoaderReadings:

    def test_get_readings_for_gauge(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        make_gauge_ts_file(_gaugets(tmp_path), "GAUGE-001")
        result = TimeseriesLoader(tmp_path).get_readings_for_gauge("GAUGE-001")
        assert isinstance(result, list) and len(result) >= 1

    def test_get_readings_missing_gauge_returns_empty(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        _gaugets(tmp_path)
        assert TimeseriesLoader(tmp_path).get_readings_for_gauge("GAUGE-999") == []

    def test_get_readings_for_gauge_by_name_fallback(self, tmp_path):
        """Gauge ID not found — fallback to gauge_name search."""
        from loaders.timeseries_loader import TimeseriesLoader
        f = _gaugets(tmp_path) / "GAUGE-001.json"
        f.write_text(json.dumps({
            "gauge_id": "GAUGE-001",
            "flood_simulation": {"readings": [
                {"timestamp": "2024-01-01T00:00:00", "waterLevel": 3.5, "name": "Test Gauge"}
            ]}
        }))
        result = TimeseriesLoader(tmp_path).get_readings_for_gauge(
            "GAUGE-MISSING", gauge_name="Test Gauge")
        assert isinstance(result, list)

    def test_get_latest_reading(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        make_gauge_ts_file(_gaugets(tmp_path), "GAUGE-001")
        assert TimeseriesLoader(tmp_path).get_latest_reading("GAUGE-001") is not None

    def test_get_latest_reading_missing_returns_none(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        _gaugets(tmp_path)
        assert TimeseriesLoader(tmp_path).get_latest_reading("GAUGE-999") is None

    def test_get_peak_reading(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        make_gauge_ts_file(_gaugets(tmp_path), "GAUGE-001")
        assert TimeseriesLoader(tmp_path).get_peak_reading("GAUGE-001") is not None

    def test_get_peak_reading_missing_returns_none(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        _gaugets(tmp_path)
        assert TimeseriesLoader(tmp_path).get_peak_reading("GAUGE-999") is None

    def test_get_storm_responses(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        seed_gauge_ts(_gaugets(tmp_path), "GAUGE-001", {
            "gauge_id": "GAUGE-001",
            "flood_simulation": {"readings": []},
            "storm_responses": {"responses": [
                {"storm_id": "STORM-0001", "peak_level_m": 5.2}
            ]}
        })
        responses = TimeseriesLoader(tmp_path).get_storm_responses("GAUGE-001")
        assert len(responses) == 1
        assert responses[0]["storm_id"] == "STORM-0001"

    def test_get_storm_responses_missing_gauge(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        _gaugets(tmp_path)
        assert TimeseriesLoader(tmp_path).get_storm_responses("GAUGE-999") == []


class TestTimeseriesLoaderRangeQueries:

    def test_get_readings_in_range_for_gauge(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        make_gauge_ts_file(_gaugets(tmp_path), "GAUGE-001")
        result = TimeseriesLoader(tmp_path).get_readings_in_range(
            datetime(2023, 1, 1), datetime(2025, 12, 31), gauge_id="GAUGE-001")
        assert isinstance(result, list)

    def test_get_readings_in_range_all_gauges(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        make_gauge_ts_file(_gaugets(tmp_path), "GAUGE-001")
        result = TimeseriesLoader(tmp_path).get_readings_in_range(
            datetime(2023, 1, 1), datetime(2025, 12, 31))
        assert isinstance(result, list)

    def test_bad_timestamp_skipped_gauge_path(self, tmp_path):
        """Readings with unparseable timestamps are skipped (gauge_id path)."""
        from loaders.timeseries_loader import TimeseriesLoader
        seed_gauge_ts(_gaugets(tmp_path), "GAUGE-001", {
            "gauge_id": "GAUGE-001",
            "flood_simulation": {"readings": [
                {"timestamp": "NOT-A-DATE", "waterLevel": 3.5},
                {"timestamp": "2024-06-01T00:00:00", "waterLevel": 4.0},
            ]}
        })
        result = TimeseriesLoader(tmp_path).get_readings_in_range(
            datetime(2024, 1, 1), datetime(2025, 1, 1), gauge_id="GAUGE-001")
        assert len(result) == 1

    def test_bad_timestamp_skipped_all_gauges_path(self, tmp_path):
        """Readings with unparseable timestamps are skipped (all-gauges path)."""
        from loaders.timeseries_loader import TimeseriesLoader
        seed_gauge_ts(_gaugets(tmp_path), "GAUGE-001", {
            "gauge_id": "GAUGE-001",
            "flood_simulation": {"readings": [
                {"timestamp": "INVALID", "waterLevel": 3.5},
                {"timestamp": "2024-06-01T00:00:00", "waterLevel": 4.0},
            ]}
        })
        result = TimeseriesLoader(tmp_path).get_readings_in_range(
            datetime(2024, 1, 1), datetime(2025, 1, 1))
        assert len(result) == 1


class TestTimeseriesLoaderStatistics:

    def test_get_gauge_statistics_with_data(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        make_gauge_ts_file(_gaugets(tmp_path), "GAUGE-001")
        stats = TimeseriesLoader(tmp_path).get_gauge_statistics("GAUGE-001")
        assert "reading_count" in stats
        assert stats["reading_count"] >= 1

    def test_get_gauge_statistics_missing_gauge(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        _gaugets(tmp_path)
        stats = TimeseriesLoader(tmp_path).get_gauge_statistics("GAUGE-999")
        assert stats["reading_count"] == 0
        assert "error" in stats

    def test_get_gauge_statistics_no_numeric_levels(self, tmp_path):
        """Readings with no numeric level field return error in stats."""
        from loaders.timeseries_loader import TimeseriesLoader
        (_gaugets(tmp_path) / "GAUGE-001.json").write_text(json.dumps({
            "gauge_id": "GAUGE-001",
            "flood_simulation": {"readings": [
                {"timestamp": "2024-01-01T00:00:00", "status": "Normal"}
            ]}
        }))
        stats = TimeseriesLoader(tmp_path).get_gauge_statistics("GAUGE-001")
        assert "error" in stats


class TestTimeseriesLoaderCache:

    def test_clear_cache(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        make_gauge_ts_file(_gaugets(tmp_path), "GAUGE-001")
        loader = TimeseriesLoader(tmp_path)
        loader.load_all()
        loader.clear_cache()
        assert not loader._cache_valid

    def test_invalidate_cache(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        loader = TimeseriesLoader(tmp_path)
        loader.invalidate_cache()
        assert not loader._cache_valid

    def test_force_reload(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        d = _gaugets(tmp_path)
        make_gauge_ts_file(d, "GAUGE-001")
        loader = TimeseriesLoader(tmp_path)
        loader.load_all()
        make_gauge_ts_file(d, "GAUGE-002")
        loader.load_all(force_reload=True)
        assert "GAUGE-002" in loader.get_available_gauge_ids()


class TestTimeseriesLoaderStatus:

    def test_get_status_returns_dict(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        make_gauge_ts_file(_gaugets(tmp_path), "GAUGE-001")
        status = TimeseriesLoader(tmp_path).get_status()
        assert "entity_name" in status
        assert "exists" in status

    def test_get_file_status_alias(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        assert "entity_name" in TimeseriesLoader(tmp_path).get_file_status()

    def test_exists_by_timestamp(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        make_gauge_ts_file(_gaugets(tmp_path), "GAUGE-001")
        loader = TimeseriesLoader(tmp_path)
        result = loader.load_all()
        if result:
            assert loader.exists(result[0]["timestamp"]) is True

    def test_find_by_id_not_found_returns_none(self, tmp_path):
        from loaders.timeseries_loader import TimeseriesLoader
        make_gauge_ts_file(_gaugets(tmp_path), "GAUGE-001")
        assert TimeseriesLoader(tmp_path).find_by_id("1999-01-01T00:00:00") is None
