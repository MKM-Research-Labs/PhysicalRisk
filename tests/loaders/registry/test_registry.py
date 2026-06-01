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

"""Tests for LoaderRegistry and create_registry."""

from tests.loaders.conftest import gauge_json, property_json, write_json


class TestLoaderRegistryLoaders:

    def test_get_gauge_loader(self, tmp_path):
        from loaders.loader_registry import LoaderRegistry
        from loaders.gauge_loader import GaugeLoader
        assert isinstance(LoaderRegistry(data_dir=tmp_path).get_gauge_loader(), GaugeLoader)

    def test_get_property_loader(self, tmp_path):
        from loaders.loader_registry import LoaderRegistry
        from loaders.property_loader import PropertyLoader
        assert isinstance(LoaderRegistry(data_dir=tmp_path).get_property_loader(), PropertyLoader)

    def test_get_rloan_loader(self, tmp_path):
        from loaders.loader_registry import LoaderRegistry
        from loaders.rloan_loader import RLoanLoader
        assert isinstance(LoaderRegistry(data_dir=tmp_path).get_rloan_loader(), RLoanLoader)

    def test_get_storm_loader(self, tmp_path):
        from loaders.loader_registry import LoaderRegistry
        from loaders.storm_loader import StormLoader
        assert isinstance(LoaderRegistry(data_dir=tmp_path).get_storm_loader(), StormLoader)

    def test_get_timeseries_loader(self, tmp_path):
        from loaders.loader_registry import LoaderRegistry
        from loaders.timeseries_loader import TimeseriesLoader
        assert isinstance(LoaderRegistry(data_dir=tmp_path).get_timeseries_loader(), TimeseriesLoader)

    def test_loader_cached_on_repeated_access(self, tmp_path):
        from loaders.loader_registry import LoaderRegistry
        registry = LoaderRegistry(data_dir=tmp_path)
        assert registry.get_property_loader() is registry.get_property_loader()

    def test_get_loader_by_name(self, tmp_path):
        from loaders.loader_registry import LoaderRegistry
        assert LoaderRegistry(data_dir=tmp_path).get_loader("gauge") is not None

    def test_get_loader_unknown_name_returns_none(self, tmp_path):
        from loaders.loader_registry import LoaderRegistry
        assert LoaderRegistry(data_dir=tmp_path).get_loader("nonexistent") is None

    def test_get_available_loaders(self, tmp_path):
        from loaders.loader_registry import LoaderRegistry
        available = LoaderRegistry(data_dir=tmp_path).get_available_loaders()
        assert "property" in available
        assert "gauge" in available
        assert "rloan" in available


class TestLoaderRegistryDataFiles:

    def test_check_data_files_all_missing(self, tmp_path):
        from loaders.loader_registry import LoaderRegistry
        result = LoaderRegistry(data_dir=tmp_path).check_data_files()
        assert all(v is False for v in result.values())

    def test_check_data_files_present(self, tmp_path):
        from loaders.loader_registry import LoaderRegistry
        write_json(tmp_path / "property.json", property_json(1))
        result = LoaderRegistry(data_dir=tmp_path).check_data_files()
        assert result["property"] is True
        assert result["gauge"] is False

    def test_get_data_dir(self, tmp_path):
        from loaders.loader_registry import LoaderRegistry
        assert LoaderRegistry(data_dir=tmp_path).get_data_dir() == tmp_path

    def test_file_overrides(self, tmp_path):
        from loaders.loader_registry import LoaderRegistry
        write_json(tmp_path / "custom_gauges.json", gauge_json(3))
        registry = LoaderRegistry(data_dir=tmp_path,
                                   file_overrides={"gauge": "custom_gauges.json"})
        assert registry.get_gauge_loader().count() == 3


class TestLoaderRegistryCache:

    def test_clear_all_caches(self, tmp_path):
        from loaders.loader_registry import LoaderRegistry
        write_json(tmp_path / "property.json", property_json(1))
        registry = LoaderRegistry(data_dir=tmp_path)
        loader = registry.get_property_loader()
        loader.load_all()
        registry.clear_all_caches()
        assert not loader._cache_valid

    def test_invalidate_all_caches(self, tmp_path):
        from loaders.loader_registry import LoaderRegistry
        registry = LoaderRegistry(data_dir=tmp_path)
        registry.get_gauge_loader()
        registry.invalidate_all_caches()  # must not raise

    def test_get_all_status(self, tmp_path):
        from loaders.loader_registry import LoaderRegistry
        write_json(tmp_path / "gauge.json", gauge_json(1))
        registry = LoaderRegistry(data_dir=tmp_path)
        registry.get_gauge_loader().load_all()
        status = registry.get_all_status()
        assert "gauge" in status
        assert "entity_name" in status["gauge"]


class TestCreateRegistry:

    def test_creates_registry(self, tmp_path):
        from loaders.loader_registry import create_registry
        assert create_registry(str(tmp_path)) is not None

    def test_with_file_overrides(self, tmp_path):
        from loaders.loader_registry import create_registry
        write_json(tmp_path / "my_gauge.json", gauge_json(2))
        registry = create_registry(str(tmp_path), gauge="my_gauge.json")
        assert registry.get_gauge_loader().count() == 2
