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
Loader registry for MKM Research Labs PRS Platform.

Provides factory pattern access to all data loaders.
Centralizes loader instantiation and configuration.

Usage:
    from loaders import LoaderRegistry
    from config import config

    # Create registry using catchment-specific directory (recommended)
    registry = LoaderRegistry()  # Uses config.get_catchment_input_dir()

    # Or create with explicit directory
    registry = LoaderRegistry(data_dir='/path/to/input/thames')

    # Get specific loaders
    property_loader = registry.get_property_loader()
    gauge_loader = registry.get_gauge_loader()

    # Or get by name
    loader = registry.get_loader('property')
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Type

from config import config

from .base_loader import BaseLoader
from .gauge_loader import GaugeLoader
from .rloan_loader import RLoanLoader
from .property_loader import PropertyLoader
from .storm_loader import StormLoader
from .timeseries_loader import TimeseriesLoader

logger = logging.getLogger(__name__)


class LoaderRegistry:
    """
    Central registry for all data loaders.

    Benefits:
    - Single point of configuration
    - Lazy instantiation of loaders
    - Caching of loader instances
    - Easy addition of new loader types
    - Catchment-aware by default
    """

    # Maps loader names to classes
    LOADER_CLASSES: Dict[str, Type[BaseLoader]] = {
        'property': PropertyLoader,
        'rloan': RLoanLoader,
        'gauge': GaugeLoader,
        'timeseries': TimeseriesLoader,
        'storm': StormLoader,
    }

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        file_overrides: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the registry.

        Args:
            data_dir: Directory containing data files.
                     Defaults to config.get_catchment_input_dir() (e.g., input/thames/)
            file_overrides: Optional dict mapping loader names to custom filenames
        """
        # Use catchment-specific directory by default
        if data_dir is None:
            self.data_dir = config.get_catchment_input_dir()
        else:
            self.data_dir = Path(data_dir)

        self.file_overrides = file_overrides or {}

        # Cache for instantiated loaders
        self._loaders: Dict[str, BaseLoader] = {}

        logger.debug(f"LoaderRegistry initialized with data_dir: {self.data_dir}")
        logger.debug(f"Active catchment: {config.CATCHMENT}")

    def _get_or_create_loader(
        self,
        name: str,
        loader_class: Type[BaseLoader]
    ) -> BaseLoader:
        """
        Get cached loader or create new instance.

        Args:
            name: Loader name (for caching)
            loader_class: Class to instantiate

        Returns:
            Loader instance
        """
        if name not in self._loaders:
            filename = self.file_overrides.get(name)
            self._loaders[name] = loader_class(
                data_dir=self.data_dir,
                filename=filename
            )
            logger.debug(f"Created {name} loader")

        return self._loaders[name]

    # =========================================================================
    # Typed accessor methods (preferred for IDE support)
    # =========================================================================

    def get_property_loader(self) -> PropertyLoader:
        """Get the property loader."""
        return self._get_or_create_loader('property', PropertyLoader)

    def get_rloan_loader(self) -> RLoanLoader:
        """Get the mortgage loader."""
        return self._get_or_create_loader('rloan', RLoanLoader)

    def get_gauge_loader(self) -> GaugeLoader:
        """Get the gauge loader."""
        return self._get_or_create_loader('gauge', GaugeLoader)

    def get_timeseries_loader(self) -> TimeseriesLoader:
        """Get the timeseries loader."""
        return self._get_or_create_loader('timeseries', TimeseriesLoader)

    def get_storm_loader(self) -> StormLoader:
        """Get the storm loader."""
        return self._get_or_create_loader('storm', StormLoader)

    # =========================================================================
    # Generic accessor
    # =========================================================================

    def get_loader(self, name: str) -> Optional[BaseLoader]:
        """
        Get a loader by name.

        Args:
            name: Loader name ('property', 'mortgage', 'gauge', etc.)

        Returns:
            Loader instance or None if name not recognized
        """
        loader_class = self.LOADER_CLASSES.get(name)
        if loader_class:
            return self._get_or_create_loader(name, loader_class)

        logger.warning(f"Unknown loader type: {name}")
        return None

    def get_available_loaders(self) -> list:
        """Get list of available loader names."""
        return list(self.LOADER_CLASSES.keys())

    # =========================================================================
    # Utility methods
    # =========================================================================

    def clear_all_caches(self) -> None:
        """Clear caches for all instantiated loaders."""
        for name, loader in self._loaders.items():
            loader.clear_cache()
            logger.debug(f"Cleared cache for {name} loader")

    def invalidate_all_caches(self) -> None:
        """Invalidate caches for all instantiated loaders."""
        for name, loader in self._loaders.items():
            loader.invalidate_cache()

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status for all instantiated loaders.

        Returns:
            Dictionary mapping loader names to their status
        """
        status = {}
        for name, loader in self._loaders.items():
            status[name] = loader.get_status()
        return status

    def check_data_files(self) -> Dict[str, bool]:
        """
        Check existence of all default data files.

        Returns:
            Dictionary mapping loader names to file existence
        """
        results = {}
        for name, loader_class in self.LOADER_CLASSES.items():
            filename = self.file_overrides.get(name, loader_class.DEFAULT_FILENAME)
            filepath = self.data_dir / filename
            results[name] = filepath.exists()
        return results

    def get_data_dir(self) -> Path:
        """Get the data directory path."""
        return self.data_dir

    def get_catchment(self) -> str:
        """Get the current catchment name."""
        return config.CATCHMENT


# Convenience function for quick setup
def create_registry(data_dir: Optional[str] = None, **file_overrides) -> LoaderRegistry:
    """
    Create a loader registry with optional file overrides.

    Args:
        data_dir: Path to data directory (defaults to catchment input dir)
        **file_overrides: Keyword args mapping loader names to filenames

    Returns:
        Configured LoaderRegistry

    Example:
        # Use default catchment directory
        registry = create_registry()

        # Use custom directory
        registry = create_registry('/path/to/input/thames')

        # With file overrides
        registry = create_registry(
            property='custom_properties.json',
            gauge='my_gauges.json'
        )
    """
    return LoaderRegistry(
        data_dir=Path(data_dir) if data_dir else None,
        file_overrides=file_overrides if file_overrides else None
    )
