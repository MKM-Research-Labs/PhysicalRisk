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

"""
Tests for LoaderRegistry.

Tests the factory pattern for accessing loaders.
"""

import pytest


class TestLoaderRegistryBasics:
    """Test basic LoaderRegistry functionality."""

    def test_create_registry(self, populated_data_dir):
        """Test creating a registry."""
        from loaders.loader_registry import LoaderRegistry

        registry = LoaderRegistry(data_dir=populated_data_dir)

        assert registry.data_dir == populated_data_dir

    def test_get_available_loaders(self, loader_registry):
        """Test getting list of available loader types."""
        loaders = loader_registry.get_available_loaders()

        assert 'property' in loaders
        assert 'mortgage' in loaders
        assert 'gauge' in loaders
        assert 'timeseries' in loaders
        assert 'storm' in loaders


class TestLoaderRegistryTypedAccessors:
    """Test typed accessor methods."""

    def test_get_property_loader(self, loader_registry):
        """Test getting PropertyLoader."""
        from loaders.property_loader import PropertyLoader

        loader = loader_registry.get_property_loader()

        assert isinstance(loader, PropertyLoader)
        assert loader.count() == 3

    def test_get_mortgage_loader(self, loader_registry):
        """Test getting MortgageLoader."""
        from loaders.mortgage_loader import MortgageLoader

        loader = loader_registry.get_mortgage_loader()

        assert isinstance(loader, MortgageLoader)
        assert loader.count() == 3

    def test_get_gauge_loader(self, loader_registry):
        """Test getting GaugeLoader."""
        from loaders.gauge_loader import GaugeLoader

        loader = loader_registry.get_gauge_loader()

        assert isinstance(loader, GaugeLoader)
        assert loader.count() == 3

    def test_get_timeseries_loader(self, loader_registry):
        """Test getting TimeseriesLoader."""
        from loaders.timeseries_loader import TimeseriesLoader

        loader = loader_registry.get_timeseries_loader()

        assert isinstance(loader, TimeseriesLoader)

    def test_get_storm_loader(self, loader_registry):
        """Test getting StormLoader."""
        from loaders.storm_loader import StormLoader

        loader = loader_registry.get_storm_loader()

        assert isinstance(loader, StormLoader)


class TestLoaderRegistryGenericAccessor:
    """Test generic get_loader method."""

    def test_get_loader_by_name(self, loader_registry):
        """Test getting loader by name string."""
        loader = loader_registry.get_loader('property')

        assert loader is not None
        assert loader.count() == 3

    def test_get_loader_unknown_type(self, loader_registry):
        """Test getting unknown loader type."""
        loader = loader_registry.get_loader('unknown')

        assert loader is None


class TestLoaderRegistryCaching:
    """Test loader instance caching."""

    def test_loader_instances_cached(self, loader_registry):
        """Test that loader instances are cached."""
        loader1 = loader_registry.get_property_loader()
        loader2 = loader_registry.get_property_loader()

        # Should be same instance
        assert loader1 is loader2

    def test_different_loaders_separate_instances(self, loader_registry):
        """Test that different loader types are separate."""
        prop_loader = loader_registry.get_property_loader()
        gauge_loader = loader_registry.get_gauge_loader()

        assert prop_loader is not gauge_loader

    def test_clear_all_caches(self, loader_registry):
        """Test clearing all loader caches."""
        # Load data into caches
        prop_loader = loader_registry.get_property_loader()
        prop_loader.load_all()

        gauge_loader = loader_registry.get_gauge_loader()
        gauge_loader.load_all()

        # Clear all
        loader_registry.clear_all_caches()

        # Caches should be cleared
        assert prop_loader._cache is None
        assert gauge_loader._cache is None


class TestLoaderRegistryFileOverrides:
    """Test custom filename configuration."""

    def test_file_overrides(self, populated_data_dir):
        """Test providing custom filenames."""
        import json

        from loaders.loader_registry import LoaderRegistry

        # Create a custom filename
        custom_file = populated_data_dir / "custom_properties.json"
        with open(custom_file, 'w') as f:
            json.dump({"properties": [
                {"PropertyHeader": {"Header": {"PropertyID": "CUSTOM-001"}}}
            ]}, f)

        registry = LoaderRegistry(
            data_dir=populated_data_dir,
            file_overrides={'property': 'custom_properties.json'}
        )

        loader = registry.get_property_loader()
        props = loader.load_all()

        assert len(props) == 1
        assert loader.get_entity_id(props[0]) == "CUSTOM-001"


class TestLoaderRegistryStatus:
    """Test status and diagnostic methods."""

    def test_check_data_files(self, loader_registry):
        """Test checking data file existence."""
        status = loader_registry.check_data_files()

        assert status['property'] is True
        assert status['mortgage'] is True
        assert status['gauge'] is True
        assert status['timeseries'] is True
        assert status['storm'] is True

class TestCreateRegistryHelper:
    """Test the create_registry convenience function."""

    def test_create_registry(self, populated_data_dir):
        """Test create_registry helper."""
        from loaders.loader_registry import create_registry

        registry = create_registry(str(populated_data_dir))

        assert registry is not None
        assert registry.get_property_loader().count() == 3

    def test_create_registry_with_overrides(self, populated_data_dir):
        """Test create_registry with file overrides."""
        import json

        from loaders.loader_registry import create_registry

        # Create custom file
        custom_file = populated_data_dir / "my_gauges.json"
        with open(custom_file, 'w') as f:
            json.dump({"floodGauges": []}, f)

        registry = create_registry(
            str(populated_data_dir),
            gauge='my_gauges.json'
        )

        loader = registry.get_gauge_loader()
        assert loader.count() == 0  # Empty custom file
