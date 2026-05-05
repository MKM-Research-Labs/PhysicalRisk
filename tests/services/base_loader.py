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
Tests for BaseLoader abstract class.

Tests the shared functionality inherited by all entity loaders.
"""

import json

import pytest


class TestBaseLoaderInterface:
    """Test that BaseLoader provides correct interface."""

    def test_abstract_methods_enforced(self, temp_data_dir):
        """Verify abstract methods must be implemented."""
        from loaders.base_loader import BaseLoader

        # Can't instantiate BaseLoader directly
        with pytest.raises(TypeError):
            BaseLoader(data_dir=temp_data_dir)

    def test_subclass_must_implement_get_entity_id(self, temp_data_dir):
        """Subclass must implement get_entity_id."""
        from loaders.base_loader import BaseLoader

        class IncompleteLoader(BaseLoader):
            ENTITY_NAME = 'test'

            def get_entity_summary(self, entity):
                return {}

        with pytest.raises(TypeError):
            IncompleteLoader(data_dir=temp_data_dir)

    def test_subclass_must_implement_get_entity_summary(self, temp_data_dir):
        """Subclass must implement get_entity_summary."""
        from loaders.base_loader import BaseLoader

        class IncompleteLoader(BaseLoader):
            ENTITY_NAME = 'test'

            def get_entity_id(self, entity):
                return entity.get('id')

        with pytest.raises(TypeError):
            IncompleteLoader(data_dir=temp_data_dir)


class TestBaseLoaderJsonLoading:
    """Test JSON loading and normalization."""

    def test_load_list_format(self, temp_data_dir):
        """Load data when JSON is a direct list."""
        from loaders.property_loader import PropertyLoader

        # Create file with list at root
        data = [{"PropertyHeader": {"Header": {"PropertyID": "P1"}}}]
        filepath = temp_data_dir / "property.json"
        with open(filepath, 'w') as f:
            json.dump(data, f)

        loader = PropertyLoader(data_dir=temp_data_dir)
        result = loader.load_all()

        assert len(result) == 1
        assert result[0]['PropertyHeader']['Header']['PropertyID'] == 'P1'

    def test_load_dict_with_container_key(self, temp_data_dir):
        """Load data when JSON has container key."""
        from loaders.property_loader import PropertyLoader

        data = {"properties": [
            {"PropertyHeader": {"Header": {"PropertyID": "P1"}}},
            {"PropertyHeader": {"Header": {"PropertyID": "P2"}}}
        ]}
        filepath = temp_data_dir / "property.json"
        with open(filepath, 'w') as f:
            json.dump(data, f)

        loader = PropertyLoader(data_dir=temp_data_dir)
        result = loader.load_all()

        assert len(result) == 2

    def test_load_alternative_container_key(self, temp_data_dir):
        """Load data with alternative container key (portfolio)."""
        from loaders.property_loader import PropertyLoader

        data = {"portfolio": [
            {"PropertyHeader": {"Header": {"PropertyID": "P1"}}}
        ]}
        filepath = temp_data_dir / "property.json"
        with open(filepath, 'w') as f:
            json.dump(data, f)

        loader = PropertyLoader(data_dir=temp_data_dir)
        result = loader.load_all()

        assert len(result) == 1

    def test_load_single_object(self, temp_data_dir):
        """Load data when JSON is single object."""
        from loaders.property_loader import PropertyLoader

        data = {"PropertyHeader": {"Header": {"PropertyID": "P1"}}}
        filepath = temp_data_dir / "property.json"
        with open(filepath, 'w') as f:
            json.dump(data, f)

        loader = PropertyLoader(data_dir=temp_data_dir)
        result = loader.load_all()

        assert len(result) == 1

    def test_load_missing_file(self, temp_data_dir):
        """Handle missing file gracefully."""
        from loaders.property_loader import PropertyLoader

        loader = PropertyLoader(data_dir=temp_data_dir)
        result = loader.load_all()

        assert result == []

class TestBaseLoaderCaching:
    """Test caching behavior."""

    def test_caching_prevents_reload(self, temp_data_dir, sample_property_file):
        """Verify data is cached after first load."""
        from loaders.property_loader import PropertyLoader

        loader = PropertyLoader(data_dir=temp_data_dir)

        # First load
        result1 = loader.load_all()

        # Modify the file
        with open(sample_property_file, 'w') as f:
            json.dump({"properties": []}, f)

        # Second load should return cached data
        result2 = loader.load_all()

        assert len(result1) == len(result2) == 3  # Original data

    def test_force_reload_bypasses_cache(self, temp_data_dir, sample_property_file):
        """Verify force_reload bypasses cache."""
        from loaders.property_loader import PropertyLoader

        loader = PropertyLoader(data_dir=temp_data_dir)

        # First load
        result1 = loader.load_all()
        assert len(result1) == 3

        # Modify the file
        with open(sample_property_file, 'w') as f:
            json.dump({"properties": []}, f)

        # Force reload
        result2 = loader.load_all(force_reload=True)

        assert len(result2) == 0  # New data

    def test_clear_cache(self, temp_data_dir, sample_property_file):
        """Test cache clearing."""
        from loaders.property_loader import PropertyLoader

        loader = PropertyLoader(data_dir=temp_data_dir)

        # Load and cache
        loader.load_all()
        assert loader._cache is not None

        # Clear cache
        loader.clear_cache()
        assert loader._cache is None
        assert loader._cache_valid is False

    def test_invalidate_cache(self, temp_data_dir, sample_property_file):
        """Test cache invalidation."""
        from loaders.property_loader import PropertyLoader

        loader = PropertyLoader(data_dir=temp_data_dir)

        # Load and cache
        loader.load_all()
        assert loader._cache_valid is True

        # Invalidate
        loader.invalidate_cache()
        assert loader._cache_valid is False

        # Next load should reload
        # (cache still exists but is marked invalid)


class TestBaseLoaderQueries:
    """Test query methods."""

    def test_find_by_id(self, property_loader):
        """Test finding entity by ID."""
        result = property_loader.find_by_id("PROP-001")

        assert result is not None
        assert result['PropertyHeader']['Header']['PropertyID'] == "PROP-001"

    def test_find_by_id_not_found(self, property_loader):
        """Test finding non-existent entity."""
        result = property_loader.find_by_id("NONEXISTENT")

        assert result is None

    def test_list_all(self, property_loader):
        """Test listing all entities."""
        result = property_loader.list_all()

        assert len(result) == 3
        assert all('propertyId' in item for item in result)

    def test_count(self, property_loader):
        """Test count method."""
        assert property_loader.count() == 3

    def test_exists(self, property_loader):
        """Test exists method."""
        assert property_loader.exists("PROP-001") is True
        assert property_loader.exists("NONEXISTENT") is False
