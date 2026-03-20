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

"""Tests for GaugeHistoricalDaily.parse_nrfa_csv."""

from port.cdm.gaugehd import GaugeHistoricalDaily

from .conftest import write_nrfa_csv


class TestParseNrfaCsv:

    def test_returns_metadata_and_flows(self, tmp_path):
        csv_path = write_nrfa_csv(tmp_path)
        gen = GaugeHistoricalDaily()
        metadata, flows = gen.parse_nrfa_csv(csv_path)
        assert isinstance(metadata, dict)
        assert isinstance(flows, list)

    def test_metadata_contains_station_name(self, tmp_path):
        csv_path = write_nrfa_csv(tmp_path, station_name="My Test Gauge")
        gen = GaugeHistoricalDaily()
        metadata, _ = gen.parse_nrfa_csv(csv_path)
        assert metadata.get("station_name") == "My Test Gauge"

    def test_flows_have_date_and_flow_cumecs(self, tmp_path):
        csv_path = write_nrfa_csv(tmp_path)
        gen = GaugeHistoricalDaily()
        _, flows = gen.parse_nrfa_csv(csv_path)
        assert len(flows) > 0
        assert "date" in flows[0]
        assert "flow_cumecs" in flows[0]

    def test_flow_values_are_floats(self, tmp_path):
        csv_path = write_nrfa_csv(tmp_path)
        gen = GaugeHistoricalDaily()
        _, flows = gen.parse_nrfa_csv(csv_path)
        for f in flows:
            assert isinstance(f["flow_cumecs"], float)

    def test_invalid_rows_skipped(self, tmp_path):
        lines = [
            "2020-01-01,50.5",
            "not-a-date,SKIP",
            "also-bad,also-bad",
            "2020-01-02,60.0",
        ]
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("\n".join(lines))
        gen = GaugeHistoricalDaily()
        _, flows = gen.parse_nrfa_csv(csv_path)
        assert len(flows) == 2

    def test_metadata_station_id(self, tmp_path):
        csv_path = write_nrfa_csv(tmp_path, station_id="40007")
        gen = GaugeHistoricalDaily()
        metadata, _ = gen.parse_nrfa_csv(csv_path)
        assert metadata.get("station_id") == "40007"

    def test_short_row_skipped(self, tmp_path):
        lines = ["", "2020-01-01,50.0", "2020-01-02,60.0"]
        csv_path = tmp_path / "short.csv"
        csv_path.write_text("\n".join(lines))
        gen = GaugeHistoricalDaily()
        _, flows = gen.parse_nrfa_csv(csv_path)
        assert len(flows) == 2


class TestParseNrfaCsvMetadataEdgeCases:

    def test_metadata_row_with_no_value_uses_empty_string(self, tmp_path):
        lines = [
            "station,name",
            "station,id,39001",
            "2020-01-01,50.0",
        ]
        csv_path = tmp_path / "edge_gdf.csv"
        csv_path.write_text("\n".join(lines))
        gen = GaugeHistoricalDaily()
        metadata, flows = gen.parse_nrfa_csv(csv_path)
        assert metadata.get("station_name") == ""
        assert metadata.get("station_id") == "39001"
        assert len(flows) == 1

    def test_metadata_row_with_three_columns_stores_value(self, tmp_path):
        lines = ["dataType,units,m3/s", "2020-06-01,75.0"]
        csv_path = tmp_path / "units_gdf.csv"
        csv_path.write_text("\n".join(lines))
        gen = GaugeHistoricalDaily()
        metadata, _ = gen.parse_nrfa_csv(csv_path)
        assert metadata.get("dataType_units") == "m3/s"

    def test_flow_row_with_non_numeric_value_skipped(self, tmp_path):
        lines = ["2020-01-01,50.0", "2020-01-02,N/A", "2020-01-03,70.0"]
        csv_path = tmp_path / "partial_gdf.csv"
        csv_path.write_text("\n".join(lines))
        gen = GaugeHistoricalDaily()
        _, flows = gen.parse_nrfa_csv(csv_path)
        assert len(flows) == 2

    def test_all_metadata_categories_parsed(self, tmp_path):
        lines = [
            "file,timestamp,2024-01-01",
            "database,id,7",
            "database,name,NRFA",
            "station,id,39001",
            "station,name,Test Station",
            "station,gridReference,TQ100700",
            "station,descriptionSummary,Summary text",
            "station,descriptionGeneral,General",
            "station,descriptionStationHydrometry,Hydro",
            "station,descriptionFlowRecord,Record",
            "station,descriptionCatchment,Catchment",
            "station,descriptionFlowRegime,Regime",
            "dataType,id,gdf",
            "dataType,name,Gauged Daily Flow",
            "dataType,parameter,Flow",
            "dataType,units,m3/s",
            "dataType,period,daily",
            "dataType,measurementType,mean",
            "data,first,2020-01-01",
            "data,last,2022-12-31",
            "2020-01-01,55.0",
        ]
        csv_path = tmp_path / "full_gdf.csv"
        csv_path.write_text("\n".join(lines))
        gen = GaugeHistoricalDaily()
        metadata, flows = gen.parse_nrfa_csv(csv_path)
        assert metadata.get("file_timestamp") == "2024-01-01"
        assert metadata.get("database_id") == "7"
        assert metadata.get("database_name") == "NRFA"
        assert metadata.get("dataType_period") == "daily"
        assert metadata.get("data_first") == "2020-01-01"
        assert len(flows) == 1
