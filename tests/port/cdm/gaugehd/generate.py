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

"""Tests for GaugeHistoricalDaily.generate — full pipeline."""

import json
from unittest.mock import patch

from port.cdm.gaugehd import GaugeHistoricalDaily

from .conftest import write_nrfa_csv


class TestGenerate:

    def test_returns_dict_with_required_keys(self, tmp_path):
        csv_path = write_nrfa_csv(tmp_path)
        gen = GaugeHistoricalDaily(years_of_history=2)
        output_path = tmp_path / "output.json"
        with patch("port.cdm.gaugehd.generator.config") as mock_config:
            mock_config.input_dir = tmp_path
            result = gen.generate(csv_path, output_path=output_path, years=2)
        for key in ("schema_version", "data_type", "generated_at",
                    "station_metadata", "statistics", "daily_flows"):
            assert key in result

    def test_output_file_written(self, tmp_path):
        csv_path = write_nrfa_csv(tmp_path)
        gen = GaugeHistoricalDaily(years_of_history=2)
        output_path = tmp_path / "output.json"
        with patch("port.cdm.gaugehd.generator.config") as mock_config:
            mock_config.input_dir = tmp_path
            gen.generate(csv_path, output_path=output_path, years=2)
        assert output_path.exists()
        with open(output_path) as f:
            assert json.load(f)["data_type"] == "GaugeHistoricalDaily"

    def test_explicit_gauge_id_overrides_metadata(self, tmp_path):
        csv_path = write_nrfa_csv(tmp_path, station_id="39001")
        gen = GaugeHistoricalDaily(years_of_history=2)
        output_path = tmp_path / "output.json"
        with patch("port.cdm.gaugehd.generator.config") as mock_config:
            mock_config.input_dir = tmp_path
            result = gen.generate(csv_path, output_path=output_path,
                                  years=2, gauge_id="OVERRIDE-ID")
        assert result["station_metadata"]["station_id"] == "OVERRIDE-ID"

    def test_daily_flows_filtered_by_years(self, tmp_path):
        csv_path = write_nrfa_csv(tmp_path, n_years=3)
        gen = GaugeHistoricalDaily(years_of_history=10)
        output_path = tmp_path / "out.json"
        with patch("port.cdm.gaugehd.generator.config") as mock_config:
            mock_config.input_dir = tmp_path
            result_3yr = gen.generate(csv_path, output_path=output_path, years=3)
            result_1yr = gen.generate(csv_path, output_path=output_path, years=1)
        assert len(result_3yr["daily_flows"]) > len(result_1yr["daily_flows"])


class TestGenerateWithNoOutputPath:

    def test_generate_output_path_none_uses_config_input_dir(self, tmp_path):
        csv_path = write_nrfa_csv(tmp_path, station_id="39001")
        gen = GaugeHistoricalDaily()
        with patch("port.cdm.gaugehd.generator.config") as mock_config:
            mock_config.input_dir = tmp_path
            result = gen.generate(csv_path, output_path=None, years=2)
        assert isinstance(result, dict)
        assert (tmp_path / "gaugehd_39001.json").exists()


class TestGenerateUsesInstanceDefault:

    def test_instance_years_used_when_no_years_arg(self, tmp_path):
        csv_path = write_nrfa_csv(tmp_path, n_years=3)
        output_path = tmp_path / "out.json"
        gen = GaugeHistoricalDaily(years_of_history=2)
        with patch("port.cdm.gaugehd.generator.config") as mock_cfg:
            mock_cfg.input_dir = tmp_path
            result = gen.generate(csv_path, output_path=output_path)
        assert result["years_included"] == 2

    def test_explicit_years_overrides_instance_default(self, tmp_path):
        csv_path = write_nrfa_csv(tmp_path, n_years=3)
        output_path = tmp_path / "out.json"
        gen = GaugeHistoricalDaily(years_of_history=50)
        with patch("port.cdm.gaugehd.generator.config") as mock_cfg:
            mock_cfg.input_dir = tmp_path
            result = gen.generate(csv_path, output_path=output_path, years=1)
        assert result["years_included"] == 1
