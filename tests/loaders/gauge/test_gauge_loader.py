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

"""Tests for GaugeLoader."""

import pytest
from tests.loaders.conftest import gauge_json, write_json


class TestGaugeLoaderBasic:

    def test_load_all_returns_list(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(3))
        assert len(GaugeLoader(tmp_path).load_all()) == 3

    def test_load_missing_file_returns_empty(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        assert GaugeLoader(tmp_path).load_all() == []

    def test_count(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(4))
        assert GaugeLoader(tmp_path).count() == 4

    def test_floodgauges_key_also_works(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        data = {"floodGauges": gauge_json(2)["flood_gauges"]}
        write_json(tmp_path / "gauge.json", data)
        assert GaugeLoader(tmp_path).count() == 2


class TestGaugeLoaderLookup:

    def test_find_by_id_returns_entity(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(3))
        result = GaugeLoader(tmp_path).find_by_id("GAUGE-001")
        assert result is not None
        assert result["FloodGauge"]["Header"]["GaugeID"] == "GAUGE-001"

    def test_find_by_id_missing_returns_none(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(2))
        assert GaugeLoader(tmp_path).find_by_id("GAUGE-999") is None

    def test_exists_true(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(2))
        assert GaugeLoader(tmp_path).exists("GAUGE-000") is True

    def test_exists_false(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(2))
        assert GaugeLoader(tmp_path).exists("GAUGE-999") is False

    def test_list_all_returns_summaries(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(2))
        summaries = GaugeLoader(tmp_path).list_all()
        assert len(summaries) == 2
        assert "gaugeId" in summaries[0]


class TestGaugeLoaderCache:

    def test_caching_works(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(2))
        loader = GaugeLoader(tmp_path)
        assert loader.load_all() is loader.load_all()

    def test_clear_cache(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(2))
        loader = GaugeLoader(tmp_path)
        loader.load_all()
        loader.clear_cache()
        assert not loader._cache_valid

    def test_force_reload(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(2))
        loader = GaugeLoader(tmp_path)
        loader.load_all()
        write_json(tmp_path / "gauge.json", gauge_json(5))
        assert len(loader.load_all(force_reload=True)) == 5


class TestGaugeLoaderStatus:

    def test_get_status_returns_dict(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(1))
        status = GaugeLoader(tmp_path).get_status()
        assert "entity_name" in status
        assert "path" in status
        assert "exists" in status
