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

"""Tests for GaugeHistoricalDaily.get_nrfa_metadata_for_cdm."""

import pytest

from port.cdm.gaugehd import GaugeHistoricalDaily


class TestGetNrfaMetadataForCdm:

    def test_returns_expected_keys(self):
        gen = GaugeHistoricalDaily()
        stats = {
            "record_start": "2020-01-01",
            "record_end": "2022-12-31",
            "mean_flow": 55.0,
            "median_flow": 50.0,
            "q95_flow": 30.0,
            "q5_flow": 90.0,
            "max_flow": 150.0,
            "max_flow_date": "2021-02-15",
        }
        station_metadata = {
            "station_id": "39001",
            "grid_reference": "TQ177695",
            "database_name": "NRFA",
            "units": "m3/s",
            "description_flow_record": "Good quality data",
        }
        result = gen.get_nrfa_metadata_for_cdm(stats, station_metadata, "gaugehd_39001.json")
        assert result["NRFAStationID"] == "39001"
        assert result["MeanFlow"] == pytest.approx(55.0)
        assert result["HistoricalDataFile"] == "gaugehd_39001.json"
        assert result["FlowUnits"] == "m3/s"

    def test_truncates_data_quality_notes(self):
        gen = GaugeHistoricalDaily()
        station_metadata = {
            "station_id": "X",
            "description_flow_record": "A" * 600,
        }
        result = gen.get_nrfa_metadata_for_cdm({}, station_metadata, "f.json")
        assert len(result["DataQualityNotes"]) <= 500


class TestGetNrfaMetadataForCdmMissingKeys:

    def test_missing_stats_keys_return_none(self):
        gen = GaugeHistoricalDaily()
        result = gen.get_nrfa_metadata_for_cdm({}, {"station_id": "X"}, "file.json")
        for key in ("RecordStartDate", "RecordEndDate", "MeanFlow", "MedianFlow",
                    "Q95Flow", "Q5Flow", "MaxRecordedFlow", "MaxRecordedFlowDate"):
            assert result[key] is None

    def test_catchment_area_always_none(self):
        gen = GaugeHistoricalDaily()
        result = gen.get_nrfa_metadata_for_cdm({}, {}, "f.json")
        assert result["CatchmentArea"] is None

    def test_database_source_from_station_metadata(self):
        gen = GaugeHistoricalDaily()
        result = gen.get_nrfa_metadata_for_cdm({}, {"database_name": "TestDB"}, "f.json")
        assert result["DatabaseSource"] == "TestDB"

    def test_missing_database_source_returns_none(self):
        gen = GaugeHistoricalDaily()
        assert gen.get_nrfa_metadata_for_cdm({}, {}, "f.json")["DatabaseSource"] is None

    def test_default_flow_units_m3_per_s(self):
        gen = GaugeHistoricalDaily()
        assert gen.get_nrfa_metadata_for_cdm({}, {}, "f.json")["FlowUnits"] == "m3/s"

    def test_custom_flow_units(self):
        gen = GaugeHistoricalDaily()
        assert gen.get_nrfa_metadata_for_cdm({}, {"units": "ft3/s"}, "f.json")["FlowUnits"] == "ft3/s"

    def test_empty_data_quality_notes_when_no_description(self):
        gen = GaugeHistoricalDaily()
        assert gen.get_nrfa_metadata_for_cdm({}, {}, "f.json")["DataQualityNotes"] == ""

    def test_all_expected_keys_present(self):
        gen = GaugeHistoricalDaily()
        result = gen.get_nrfa_metadata_for_cdm({}, {}, "f.json")
        for key in ("NRFAStationID", "GridReference", "CatchmentArea",
                    "RecordStartDate", "RecordEndDate", "MeanFlow", "MedianFlow",
                    "Q95Flow", "Q5Flow", "MaxRecordedFlow", "MaxRecordedFlowDate",
                    "HistoricalDataFile", "DatabaseSource", "FlowUnits", "DataQualityNotes"):
            assert key in result, f"Missing key: {key}"
