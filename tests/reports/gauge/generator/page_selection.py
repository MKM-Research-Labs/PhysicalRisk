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

"""Tests for GaugeReportGenerator._auto_select_pages."""

from .conftest import make_generator


class TestAutoSelectPages:

    def test_returns_list(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        pages = gen._auto_select_pages(gauge_data, None)
        assert isinstance(pages, list)
        assert len(pages) > 0

    def test_all_pages_exist(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        pages = gen._auto_select_pages(gauge_data, None)
        for p in pages:
            assert p in gen.pages

    def test_without_timeseries_or_hazard_no_analysis_pages(self, tmp_path):
        gen = make_generator(tmp_path)
        pages = gen._auto_select_pages({}, None)
        analysis_pages = gen.categories["analysis"]
        assert not any(p in pages for p in analysis_pages)

    def test_with_timeseries_includes_analysis_pages(self, tmp_path, gauge_data, ts_data):
        gen = make_generator(tmp_path)
        pages = gen._auto_select_pages(gauge_data, ts_data)
        analysis_pages = gen.categories["analysis"]
        assert any(p in pages for p in analysis_pages)

    def test_with_hazard_curve_includes_analysis_pages(self, tmp_path):
        gen = make_generator(tmp_path)
        gauge_with_hc = {"hazard_curve": {"annual_hazard_rate_alert": 0.05}}
        pages = gen._auto_select_pages(gauge_with_hc, None)
        analysis_pages = gen.categories["analysis"]
        assert any(p in pages for p in analysis_pages)

    def test_always_includes_summary_pages(self, tmp_path):
        gen = make_generator(tmp_path)
        pages = gen._auto_select_pages({}, None)
        for sp in gen.categories["summary"]:
            assert sp in pages

    def test_always_includes_gauge_info_pages(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        pages = gen._auto_select_pages(gauge_data, None)
        for gp in gen.categories["gauge_info"]:
            assert gp in pages

    def test_always_includes_operational_pages(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        pages = gen._auto_select_pages(gauge_data, None)
        for op in gen.categories["operational"]:
            assert op in pages
