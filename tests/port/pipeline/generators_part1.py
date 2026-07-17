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

"""Tests for individual pipeline step generators (steps 4, 6, 8, 10). (part 1 of 2)"""

import json

import pytest

from config import config
from tests.port.pipeline.conftest import N_GAUGES, N_PROPERTIES


class TestGaugeTimeSeries:
    """Tests for GaugeTimeSeriesGenerator (step 4)."""

    def test_generates_per_gauge_files(self, pipeline_dir):
        gaugets_dir = pipeline_dir / "gaugets"
        assert gaugets_dir.exists()
        assert len(list(gaugets_dir.glob("GAUGE-*.json"))) >= N_GAUGES

    def test_output_file_has_readings(self, pipeline_dir):
        gauge_files = list((pipeline_dir / "gaugets").glob("GAUGE-*.json"))
        assert len(gauge_files) > 0
        for gf in gauge_files[:3]:
            with open(gf) as f:
                data = json.load(f)
            assert "flood_simulation" in data
            assert len(data["flood_simulation"]["readings"]) > 0

    def test_requires_gauge_portfolio(self, tmp_path):
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        from db_helpers import tmp_catchment
        # Empty backend (no gauge portfolio) → the generator must refuse.
        with tmp_catchment(tmp_path):
            with pytest.raises(FileNotFoundError):
                GaugeTimeSeriesGenerator(verbose=False).generate(simulation_hours=12)


class TestGaugeHistoricalDaily:
    """Tests for generate_all_gauge_histories (step 6)."""

    def test_generates_per_gauge_files(self, pipeline_dir):
        gaugehd_dir = pipeline_dir / "gaugehd"
        assert gaugehd_dir.exists()
        assert len(list(gaugehd_dir.glob("gauge_*_hd.json"))) == N_GAUGES

    def test_output_has_daily_observations(self, pipeline_dir):
        for hf in list((pipeline_dir / "gaugehd").glob("gauge_*_hd.json"))[:3]:
            with open(hf) as f:
                data = json.load(f)
            assert "daily_observations" in data
            assert len(data["daily_observations"]) > 0

    def test_statistics_computed(self, pipeline_dir):
        for hf in list((pipeline_dir / "gaugehd").glob("gauge_*_hd.json"))[:3]:
            with open(hf) as f:
                data = json.load(f)
            assert "statistics" in data
            assert "mean_level" in data["statistics"]
            assert "max_level" in data["statistics"]


class TestPropertyTimeSeries:
    """Tests for PropertyTimeSeriesGenerator (step 8)."""

    def test_generates_per_property_files(self, pipeline_dir):
        pts_dir = pipeline_dir / "propertyts"
        assert pts_dir.exists()
        assert (pts_dir / "portfolio_flood_summary.json").exists()

    def test_portfolio_summary_has_statistics(self, pipeline_dir):
        with open(pipeline_dir / "propertyts" / "portfolio_flood_summary.json") as f:
            data = json.load(f)
        s = data["summary"]
        assert "total_properties" in s
        assert s["total_properties"] == N_PROPERTIES
        assert "total_gauges" in s

    def test_per_property_files_have_flood_data(self, pipeline_dir):
        prop_files = list((pipeline_dir / "propertyts").glob("PROP-*.json"))
        if not prop_files:
            pytest.skip("No per-property files generated (may have 0 floods)")
        for pf in prop_files[:3]:
            with open(pf) as f:
                data = json.load(f)
            assert "property_id" in data
            assert "nearest_gauges" in data
            assert "flood_events" in data


class TestCounterparty:
    """Tests for CounterpartyPortfolioGenerator (step 10)."""

    def test_generates_counterparty_file(self, pipeline_dir):
        assert (pipeline_dir / "counterparty.json").exists()

    def test_all_counterparties_have_party_id(self, pipeline_dir):
        with open(pipeline_dir / "counterparty.json") as f:
            data = json.load(f)
        counterparties = data["counterparties"]
        assert len(counterparties) > 0
        for ctpy in counterparties:
            assert ctpy["CounterpartySet"]["Party"]["PartyID"].startswith("CTPY-")

    def test_cdm_structure(self, pipeline_dir):
        with open(pipeline_dir / "counterparty.json") as f:
            data = json.load(f)
        ctpy = data["counterparties"][0]["CounterpartySet"]
        assert "Party" in ctpy
        assert "PartyID" in ctpy["Party"]
        assert "ContactInformation" in ctpy["Party"]

    def test_custom_count(self, tmp_path):
        from port.src.counterparty import CounterpartyPortfolioGenerator
        from db_helpers import tmp_catchment
        # The migrated writer persists through database; isolate it in a tmp backend.
        with tmp_catchment(tmp_path):
            gen = CounterpartyPortfolioGenerator(verbose=False)
            # +1 REIT prepended to the external pool of size ``count``
            result = gen.generate(count=3)
        assert len(result["data"]) == 4
