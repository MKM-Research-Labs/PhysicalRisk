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

"""Tests for GaugeReportGenerator.generate_report and specialised report methods."""

from pathlib import Path
from unittest.mock import patch

from .conftest import make_generator, minimal_gauge, timeseries_data


class TestGenerateReport:

    def test_returns_path(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        result = gen.generate_report(gauge_data)
        assert isinstance(result, Path)

    def test_pdf_exists(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        assert gen.generate_report(gauge_data).exists()

    def test_pdf_non_empty(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        path = gen.generate_report(gauge_data)
        assert path.stat().st_size > 0

    def test_pdf_suffix(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        assert gen.generate_report(gauge_data).suffix == ".pdf"

    def test_custom_output_filename(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        path = gen.generate_report(gauge_data, output_filename="my_gauge.pdf")
        assert path.name == "my_gauge.pdf"
        assert path.exists()

    def test_custom_pages_to_include(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        path = gen.generate_report(gauge_data, pages_to_include=["title_overview", "data_summary"])
        assert path.exists()

    def test_with_timeseries_data(self, tmp_path, gauge_data, ts_data):
        gen = make_generator(tmp_path)
        path = gen.generate_report(gauge_data, timeseries_data=ts_data)
        assert path.exists()

    def test_auto_select_called_when_pages_none(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        with patch.object(gen, "_auto_select_pages", wraps=gen._auto_select_pages) as spy:
            gen.generate_report(gauge_data, pages_to_include=None)
        spy.assert_called_once()

    def test_auto_select_not_called_when_pages_provided(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        with patch.object(gen, "_auto_select_pages", wraps=gen._auto_select_pages) as spy:
            gen.generate_report(gauge_data, pages_to_include=["title_overview"])
        spy.assert_not_called()

    def test_empty_gauge_data(self, tmp_path):
        gen = make_generator(tmp_path)
        path = gen.generate_report({})
        assert path.exists()

    def test_all_unknown_pages_still_creates_pdf(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        path = gen.generate_report(gauge_data, pages_to_include=["xxx", "yyy"])
        assert path.exists()

    def test_pdf_is_bytes(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        path = gen.generate_report(gauge_data, pages_to_include=["title_overview"])
        content = path.read_bytes()
        assert isinstance(content, bytes)
        assert len(content) > 0


class TestSpecialisedReportMethods:

    def test_generate_basic_report_exists(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        assert gen.generate_basic_report(gauge_data).exists()

    def test_generate_basic_report_non_empty(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        path = gen.generate_basic_report(gauge_data)
        assert path.stat().st_size > 0

    def test_generate_basic_report_custom_filename(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        path = gen.generate_basic_report(gauge_data, output_filename="basic.pdf")
        assert path.name == "basic.pdf"

    def test_generate_basic_with_timeseries(self, tmp_path, gauge_data, ts_data):
        gen = make_generator(tmp_path)
        path = gen.generate_basic_report(gauge_data, timeseries_data=ts_data)
        assert path.exists()

    def test_generate_monitoring_report_exists(self, tmp_path, gauge_data, ts_data):
        gen = make_generator(tmp_path)
        assert gen.generate_monitoring_report(gauge_data, ts_data).exists()

    def test_generate_monitoring_report_custom_filename(self, tmp_path, gauge_data, ts_data):
        gen = make_generator(tmp_path)
        path = gen.generate_monitoring_report(gauge_data, ts_data, output_filename="mon.pdf")
        assert path.name == "mon.pdf"

    def test_generate_monitoring_report_no_timeseries(self, tmp_path, gauge_data):
        """Monitoring report with None timeseries should still succeed."""
        gen = make_generator(tmp_path)
        path = gen.generate_monitoring_report(gauge_data, None)
        assert path.exists()

    def test_generate_analysis_report_exists(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        assert gen.generate_analysis_report(gauge_data).exists()

    def test_generate_analysis_report_with_timeseries(self, tmp_path, gauge_data, ts_data):
        gen = make_generator(tmp_path)
        path = gen.generate_analysis_report(gauge_data, ts_data)
        assert path.exists()

    def test_generate_analysis_report_custom_filename(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        path = gen.generate_analysis_report(gauge_data, output_filename="analysis.pdf")
        assert path.name == "analysis.pdf"


class TestEdgeCases:

    def test_completely_empty_gauge_data(self, tmp_path):
        gen = make_generator(tmp_path)
        path = gen.generate_basic_report({})
        assert path.exists()

    def test_none_flood_gauge_header(self, tmp_path):
        gen = make_generator(tmp_path)
        data = {"FloodGauge": {"Header": None, "SensorDetails": {}, "FloodStage": {}}}
        path = gen.generate_basic_report(data)
        assert path.exists()

    def test_report_with_all_pages(self, tmp_path, gauge_data, ts_data):
        gen = make_generator(tmp_path)
        all_pages = list(gen.pages.keys())
        path = gen.generate_report(gauge_data, timeseries_data=ts_data,
                                   pages_to_include=all_pages)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_single_page_report(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        path = gen.generate_report(gauge_data, pages_to_include=["title_overview"])
        assert path.exists()

    def test_gauge_data_with_hazard_curve_and_timeseries(self, tmp_path):
        gen = make_generator(tmp_path)
        data = minimal_gauge()
        data["FloodGauge"]["hazard_curve"] = {"annual_hazard_rate_alert": 0.1}
        path = gen.generate_report(data, timeseries_data=timeseries_data())
        assert path.exists()

    def test_output_is_non_empty_bytes(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        path = gen.generate_report(gauge_data, pages_to_include=["title_overview"])
        content = path.read_bytes()
        assert isinstance(content, bytes)
        assert len(content) > 0
