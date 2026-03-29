# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""TCEventVisualization — main coordinator for map visualisation."""

import logging
from pathlib import Path
from typing import Optional, Union

from config import config

from ...layer import (
    GaugeLayer,
    MortgageLayer,
    PropertyLayer,
)
from ..data_loader import DataLoader
from ..map_builder import MapBuilder
from .heatmap import add_flood_heatmap

logger = logging.getLogger(__name__)


class TCEventVisualization:
    """
    Main coordinator class for tropical cyclone event visualizations.

    Orchestrates the visualization process: data loading, map creation,
    layer addition, and output generation.
    """

    def __init__(
        self,
        input_dir: Optional[Union[str, Path]] = None,
        output_dir: Optional[Union[str, Path]] = None,
        enable_interactivity: bool = True,
        server_url: Optional[str] = None,
        notification_position: str = "top-right"
    ):
        """
        Initialize the visualization system.

        Args:
            input_dir: Directory containing input JSON files (defaults to config)
            output_dir: Directory for output files (defaults to config)
            enable_interactivity: Whether to enable interactive features
            server_url: Backend server URL (defaults to config)
            notification_position: Position for notifications
        """
        # Resolve directories from config
        self.input_dir = Path(input_dir) if input_dir else config.get_input_dir()
        self.output_dir = Path(output_dir) if output_dir else config.get_results_dir()
        self._server_url = server_url if server_url is not None else ""

        # Initialize core components
        self.data_loader = DataLoader(self.input_dir)
        self.map_builder = MapBuilder()

        # Initialize optional components
        self._init_layers()
        self._init_interactivity(enable_interactivity, notification_position)

        # Data container
        self.loaded_data = None

    def _init_layers(self):
        """Initialize layer components."""
        try:
            self.gauge_layer = GaugeLayer()
            self.property_layer = PropertyLayer()
            self.mortgage_layer = MortgageLayer()
            self._layers_available = True
        except ImportError:
            self._layers_available = False

    def _init_interactivity(self, enable: bool, notification_position: str):
        """Initialize interactivity components."""
        self._interactivity_available = False
        self.interactivity = None

        if not enable:
            return

        try:
            from ...interactivity import InteractivityManager, NotificationPosition

            try:
                position_enum = NotificationPosition(notification_position)
            except ValueError:
                position_enum = NotificationPosition.TOP_RIGHT

            self.interactivity = InteractivityManager(
                server_url=self._server_url,
                notification_position=position_enum.value,
                notification_timeout=5000
            )
            self._interactivity_available = True
        except ImportError:
            pass

    def create_event_map(
        self,
        output_filename: str
    ) -> Optional[Path]:
        """
        Create a complete tropical cyclone event visualization map.

        Uses JSONFileConfig for all data filenames automatically.

        Args:
            output_filename: Output HTML filename

        Returns:
            Path to the created visualization or None if creation failed
        """
        try:
            # Load all data using JSONFileConfig
            self.loaded_data = self.data_loader.load_all_data()

            if not self.data_loader.is_data_complete():
                raise ValueError("Insufficient data loaded - gauge data is required")

            # Extract all marker coordinates for auto-zoom
            all_coords = self._extract_coordinates()

            # Create base map and fit to all markers
            base_map = self.map_builder.create_map(coordinates=all_coords)
            if len(all_coords) >= 2:
                lats = [c[0] for c in all_coords]
                lons = [c[1] for c in all_coords]
                base_map.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]],
                                   padding=[30, 30])

            # Add layer
            self._add_layer(base_map)

            # Add interactivity
            self._add_interactivity(base_map)

            # Save and return
            output_path = self.output_dir / output_filename
            return self.map_builder.finalize_map(base_map, output_path)

        except Exception as e:
            logger.error("Error creating visualization: %s", e)
            return None

    def _extract_coordinates(self) -> list:
        """Extract all marker coordinates for auto-zoom."""
        all_coords = []
        if self.loaded_data.gauge_data and 'items' in self.loaded_data.gauge_data:
            for gauge in self.loaded_data.gauge_data['items']:
                loc = gauge.get('FloodGauge', {}).get('Location', {})
                lat = loc.get('GaugeLatitude')
                lon = loc.get('GaugeLongitude')
                if lat and lon:
                    all_coords.append((lat, lon))

        if self.loaded_data.property_data:
            from visual.utils import DataExtractor
            props = self.loaded_data.property_data.get('properties',
                self.loaded_data.property_data.get('items', []))
            for prop in props:
                info = DataExtractor.extract_property_info(prop)
                if info and info.get('coordinates'):
                    plat = info['coordinates'].get('latitude')
                    plon = info['coordinates'].get('longitude')
                    if plat and plon:
                        all_coords.append((plat, plon))

        return all_coords

    def _add_layer(self, base_map):
        """Add visualization layer to the map."""
        if not self._layers_available:
            logger.warning("Layer modules not available, map will be basic")
            return

        if self.loaded_data.gauge_data:
            try:
                self.gauge_layer.add_to_map(base_map, self.loaded_data)
            except Exception as e:
                logger.warning("Gauge layer failed: %s", e)

        if self.loaded_data.property_data:
            try:
                self.property_layer.add_to_map(base_map, self.loaded_data)
            except Exception as e:
                logger.warning("Property layer failed: %s", e)

        if self.loaded_data.mortgage_data and self.loaded_data.property_data:
            try:
                self.mortgage_layer.add_to_map(base_map, self.loaded_data)
            except Exception as e:
                logger.warning("Mortgage layer failed: %s", e)

        # Add worst-case storm heatmap overlay
        try:
            self._add_flood_heatmap(base_map)
        except Exception as e:
            logger.warning("Heatmap layer failed: %s", e)

    def _add_interactivity(self, base_map):
        """Add interactive features to the map."""
        if self._interactivity_available and self.interactivity:
            try:
                self.interactivity.setup_map_interactivity(base_map)
            except Exception as e:
                logger.warning("Interactivity setup failed: %s", e)

    # Public configuration methods

    def configure_interactivity(self, **kwargs) -> bool:
        """Configure interactivity settings."""
        if not self._interactivity_available or not self.interactivity:
            return False

        try:
            self.interactivity.configure(**kwargs)
            return True
        except Exception:
            return False

    def configure_map_settings(
        self,
        default_zoom: int = 8,
        tiles: str = "OpenStreetMap",
        controls: Optional[dict] = None
    ):
        """Configure map builder settings."""
        self.map_builder.set_default_zoom(default_zoom)
        self.map_builder.set_default_tiles(tiles)
        if controls:
            self.map_builder.configure_controls(**controls)

    # Public query methods

    def get_loaded_data(self):
        """Get the currently loaded data."""
        return self.loaded_data

    def get_statistics(self) -> dict:
        """Get statistics from all components."""
        stats = {
            "layers_available": self._layers_available,
            "interactivity_available": self._interactivity_available,
        }

        if hasattr(self.data_loader, "get_statistics"):
            stats["data_loader"] = self.data_loader.get_statistics()

        if hasattr(self.map_builder, "get_statistics"):
            stats["map_builder"] = self.map_builder.get_statistics()

        if self._interactivity_available and self.interactivity:
            stats["interactivity"] = self.interactivity.get_statistics()

        return stats

    def validate_input_files(self) -> bool:
        """Validate that all required input files exist using JSONFileConfig."""
        from jsonfiles import JSONFileConfig

        # Core files needed for basic visualization
        required_filenames = [
            JSONFileConfig.GAUGE_PORTFOLIO,
            JSONFileConfig.PROPERTY_PORTFOLIO,
            JSONFileConfig.MORTGAGE_PORTFOLIO,
        ]

        # Optional files
        optional_filenames = [
            JSONFileConfig.HAZARD_CURVES,
        ]

        missing_required = [f for f in required_filenames if not (self.input_dir / f).exists()]

        if missing_required:
            logger.warning("Missing required files: %s", ', '.join(missing_required))
            return False

        # Check for optional files and warn if missing
        missing_optional = [f for f in optional_filenames if not (self.input_dir / f).exists()]
        if missing_optional:
            logger.info("Optional files not found: %s", ', '.join(missing_optional))

        return True

    def _add_flood_heatmap(self, base_map):
        """Backward-compatible delegate to heatmap module."""
        add_flood_heatmap(base_map, self.input_dir, self.loaded_data)

    @property
    def is_fully_configured(self) -> bool:
        """Check if all optional components are available."""
        return self._layers_available and self._interactivity_available
