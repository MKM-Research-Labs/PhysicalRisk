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

"""Tests for GaugeReportGenerator.__init__ (output-dir resolution, page/category init)."""

from pathlib import Path

from .conftest import make_generator


class TestGaugeReportGeneratorInit:

    def test_explicit_output_dir_string(self, tmp_path):
        from reports.gauge.gauge_generator import GaugeReportGenerator
        gen = GaugeReportGenerator(output_dir=str(tmp_path))
        assert gen.output_dir == tmp_path

    def test_explicit_output_dir_path(self, tmp_path):
        from reports.gauge.gauge_generator import GaugeReportGenerator
        gen = GaugeReportGenerator(output_dir=tmp_path)
        assert isinstance(gen.output_dir, Path)

    def test_output_dir_created(self, tmp_path):
        from reports.gauge.gauge_generator import GaugeReportGenerator
        new_dir = tmp_path / "brand_new_dir"
        GaugeReportGenerator(output_dir=new_dir)
        assert new_dir.exists()

    def test_no_output_dir_uses_config(self, tmp_path, monkeypatch):
        from config import config
        gauge_dir = tmp_path / "gauge_reports"
        monkeypatch.setattr(config, "get_gauge_reports_dir", lambda: gauge_dir)
        from reports.gauge.gauge_generator import GaugeReportGenerator
        gen = GaugeReportGenerator()
        assert gen.output_dir == gauge_dir

    def test_pages_dict_initialized(self, tmp_path):
        gen = make_generator(tmp_path)
        expected = {
            "title_overview", "sensor_details", "location",
            "measurements", "flood_stages",
            "risk_assessment", "data_summary", "flood_history",
            "hazard_curves", "prs_pricing", "current_risk", "trading",
        }
        assert expected <= set(gen.pages.keys())

    def test_categories_dict_initialized(self, tmp_path):
        gen = make_generator(tmp_path)
        assert "gauge_info" in gen.categories
        assert "operational" in gen.categories
        assert "analysis" in gen.categories
        assert "summary" in gen.categories
