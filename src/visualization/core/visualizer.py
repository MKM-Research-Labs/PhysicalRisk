# Copyright (c) 2025 MKM Research Labs. All rights reserved.
# 
# This software is provided under license by MKM Research Labs. 
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

"""
Main visualization coordinator module.

This module contains the main TCEventVisualization class that orchestrates
all aspects of the tropical cyclone event visualization system.
Updated to include Phase 5 interactivity integration.
"""

import sys
import warnings
from pathlib import Path
from typing import Optional, Union
from .data_loader import DataLoader
from .map_builder import MapBuilder

# Fix the Python path to find project modules
current_file = Path(__file__).resolve()
# Navigate up to find project root (assuming we're in visualization/core)
project_root = current_file.parent.parent.parent.parent

# Add project root to Python's path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import modules using absolute imports
from src.utilities.project_paths import ProjectPaths




class TCEventVisualization:
    """
    Main coordinator class for tropical cyclone event visualizations.
    
    This class orchestrates the entire visualization process, from data loading
    through map creation and layer addition to final output generation.
    Updated to include Phase 5 interactivity integration.
    """
    
    def __init__(self, input_dir: Optional[Union[str, Path]] = None, 
                 output_dir: Optional[Union[str, Path]] = None,
                 enable_interactivity: bool = True,
                 server_url: str = "http://127.0.0.1:5001",
                 notification_position: str = "top-right"):
        """
        Initialize the visualization system.
        
        Args:
            input_dir: Directory containing input JSON files
            output_dir: Directory for output files
            enable_interactivity: Whether to enable interactive features
            server_url: Backend server URL for interactive features
            notification_position: Position for notifications
        """
        # Initialize core components
        self.data_loader = DataLoader(input_dir)
        self.map_builder = MapBuilder()
        
        # Initialize layer components (Phase 3)
        self._initialize_layer_components()
        
        # Initialize interactivity components (Phase 5)
        self._initialize_interactivity(enable_interactivity, server_url, notification_position)
        
        # Set output directory
        self.output_dir = Path(output_dir) if output_dir else self._get_default_output_dir()
        
        # Store loaded data
        self.loaded_data = None
        
        # Print initialization summary
        self._print_initialization_summary()
    
    def _initialize_layer_components(self):
        """Initialize layer components (Phase 3)."""
        try:
            from ..layers import StormLayer, GaugeLayer, PropertyLayer, MortgageLayer
            self.storm_layer = StormLayer()
            self.gauge_layer = GaugeLayer()
            self.property_layer = PropertyLayer()
            self.mortgage_layer = MortgageLayer()
            self._layers_available = True
            print("✓ Phase 3 layers initialized")
        except ImportError as e:
            print(f"⚠️  Phase 3 layers not available: {e}")
            self._layers_available = False
    
    def _initialize_interactivity(self, enable_interactivity: bool, 
                                server_url: str, notification_position: str):
        """Initialize interactivity components (Phase 5)."""
        self.enable_interactivity = enable_interactivity
        
        if enable_interactivity:
            try:
                from ..interactivity import (
                    InteractivityManager,
                    NotificationPosition
                )
                
                # Convert string position to enum
                try:
                    position_enum = NotificationPosition(notification_position)
                except ValueError:
                    print(f"⚠️  Invalid notification position '{notification_position}', using default")
                    position_enum = NotificationPosition.TOP_RIGHT
                
                self.interactivity = InteractivityManager(
                    server_url=server_url,
                    notification_position=position_enum.value,
                    notification_timeout=5000
                )
                self._interactivity_available = True
                print("✓ Phase 5 interactivity initialized")
                
            except ImportError as e:
                print(f"⚠️  Phase 5 interactivity not available: {e}")
                self._interactivity_available = False
                self.interactivity = None
        else:
            self._interactivity_available = False
            self.interactivity = None
            print("ℹ️  Interactivity disabled by user")
    
    def _print_initialization_summary(self):
        """Print initialization summary."""
        print(f"\nTCEventVisualization initialized:")
        print(f"  Input directory: {self.data_loader.input_dir}")
        print(f"  Output directory: {self.output_dir}")
        print(f"  Layers available: {self._layers_available}")
        print(f"  Interactivity available: {self._interactivity_available}")
        if self._interactivity_available and self.interactivity:
            print(f"  Backend server: {self.interactivity.backend_handler.server_url}")
            print(f"  Notification position: {self.interactivity.notifications.default_position.value}")
    
    def create_event_map(self, ts_filename: str, gauge_filename: str,
                        property_filename: str, mortgage_filename: str,
                        flood_risk_filename: str, output_filename: str) -> Optional[Path]:
        """
        Create a complete tropical cyclone event visualization map.
        
        Args:
            ts_filename: Tropical cyclone timeseries filename
            gauge_filename: Flood gauge data filename
            property_filename: Property portfolio filename
            mortgage_filename: Mortgage portfolio filename
            flood_risk_filename: Flood risk report filename
            output_filename: Output HTML filename
            
        Returns:
            Path to the created visualization or None if creation failed
        """
        try:
            print("\n=== Starting Visualization Creation ===")
            
            # Phase 1: Load all data
            self.loaded_data = self.data_loader.load_all_data(
                ts_filename=ts_filename,
                gauge_filename=gauge_filename,
                property_filename=property_filename,
                mortgage_filename=mortgage_filename,
                flood_risk_filename=flood_risk_filename
            )
            
            # Verify we have minimum required data
            if not self.data_loader.is_data_complete():
                raise ValueError("Insufficient data loaded - TC data is required")
            
            # Phase 2: Create base map
            print("\n=== Creating Base Map ===")
            base_map = self.map_builder.create_base_map(self.loaded_data.tc_data)
            
            # Phase 3: Add layers
            print("\n=== Adding Layers ===")
            self._add_layers_to_map(base_map)
            
            # Phase 5: Add interactivity (replaces the old Phase 4 placeholder)
            print("\n=== Adding Interactivity ===")
            self._add_interactivity_to_map(base_map)
            
            # Phase 6: Finalize and save
            print("\n=== Finalizing Map ===")
            output_path = self.output_dir / output_filename
            result_path = self.map_builder.finalize_map(base_map, output_path)
            
            if result_path:
                print(f"\n✓ Visualization created successfully: {result_path}")
                self._print_creation_summary()
                self._print_usage_instructions()
            else:
                print("\n✗ Failed to save visualization")
            
            return result_path
            
        except Exception as e:
            print(f"\n✗ Error creating visualization: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _add_layers_to_map(self, base_map):
        """
        Add visualization layers to the base map.
        
        Args:
            base_map: Folium map to add layers to
           
    
        """
        if not self._layers_available:
            print("⚠️  Phase 3 layers not available - using placeholder mode")
            self._add_placeholder_layers(base_map)
            return
        
        layers_added = []
        
       
        if self.loaded_data.tc_data:
            try:
                storm_group = self.storm_layer.add_to_map(base_map, self.loaded_data.tc_data)
                layers_added.append("Storm Path")
            except Exception as e:
                print(f"Warning: Storm layer failed: {e}")
        
        # Add gauge layer
        if self.loaded_data.gauge_data:
            try:
                gauge_group = self.gauge_layer.add_to_map(base_map, self.loaded_data)
                layers_added.append("Flood Gauges")
            except Exception as e:
                print(f"Warning: Gauge layer failed: {e}")
        
        # Add property layer
        if self.loaded_data.property_data:
            try:
                property_group = self.property_layer.add_to_map(base_map, self.loaded_data)
                layers_added.append("Properties")
            except Exception as e:
                print(f"Warning: Property layer failed: {e}")
        
        # Add mortgage layer
        if self.loaded_data.mortgage_data and self.loaded_data.property_data:
            try:
                mortgage_group = self.mortgage_layer.add_to_map(base_map, self.loaded_data)
                layers_added.append("Mortgage Risk")
            except Exception as e:
                print(f"Warning: Mortgage layer failed: {e}")
        
        print(f"✓ Added layers: {', '.join(layers_added)}")
    
    def _add_placeholder_layers(self, base_map):
        """
        Add placeholder layers when Phase 3 layers are not available.
        
        Args:
            base_map: Folium map to add placeholders to
        """
        layers_to_add = []
        
        if self.loaded_data.tc_data:
            layers_to_add.append("Storm Path")
            # Add simple storm path as before
            try:
                coordinates = self.map_builder._extract_coordinates(self.loaded_data.tc_data)
                if coordinates:
                    import folium
                    folium.PolyLine(
                        coordinates,
                        weight=4,
                        color='red',
                        opacity=0.8,
                        tooltip="Storm Path (Placeholder)"
                    ).add_to(base_map)
            except Exception as e:
                print(f"Warning: Could not add placeholder storm path: {e}")
        
        if self.loaded_data.gauge_data:
            layers_to_add.append("Flood Gauges")
        
        if self.loaded_data.property_data:
            layers_to_add.append("Properties")
        
        if self.loaded_data.mortgage_data:
            layers_to_add.append("Mortgage Data")
        
        print(f"Placeholder layers: {', '.join(layers_to_add)}")
        print("(Full layer implementation requires Phase 3 modules)")
    
    def _add_interactivity_to_map(self, base_map):
        """
        Add interactive features to the map using Phase 5 modules.
        
        Args:
            base_map: Folium map to add interactivity to
        """
        if not self._interactivity_available or not self.interactivity:
            print("⚠️  Phase 5 interactivity not available - skipping interactive features")
            self._show_interactivity_placeholder()
            return
        
        try:
            # This single line replaces ~1200 lines of embedded JavaScript!
            self.interactivity.setup_map_interactivity(base_map)
            
            # Get statistics about what was added
            stats = self.interactivity.get_statistics()
            
            print("✓ Interactive features added:")
            print(f"  • Context menus: {stats['context_menus']['total_menu_items']} menu items")
            print(f"  • Backend communication: {stats['backend_handler']['total_endpoints']} endpoints")
            print(f"  • Notifications: {len(stats['notifications']['available_types'])} notification types")
            print(f"  • Server: {stats['backend_handler']['server_url']}")
            
        except Exception as e:
            print(f"⚠️  Failed to add interactivity: {e}")
            self._show_interactivity_placeholder()
    
    def _show_interactivity_placeholder(self):
        """Show placeholder information about interactivity features."""
        interactive_features = [
            "Right-click context menus on markers",
            "Property and gauge report generation", 
            "Backend API communication",
            "User notifications and progress tracking",
            "Data export functionality"
        ]
        
        print("Interactive features that would be available:")
        for feature in interactive_features:
            print(f"  • {feature}")
        print("(Install Phase 5 interactivity modules to enable)")
    
    def _print_creation_summary(self):
        """Print a summary of the visualization creation process."""
        print("\n=== Creation Summary ===")
        
        # Data summary
        data_summary = self.data_loader.get_data_summary()
        for data_type, info in data_summary.items():
            status = "✓" if info['loaded'] else "✗"
            print(f"{status} {data_type.replace('_', ' ').title()}: {info['summary']}")
        
        # Validation summary
        validation_results = self.data_loader.get_validation_summary()
        total_warnings = sum(len(result.warnings) for result in validation_results.values())
        total_errors = sum(len(result.errors) for result in validation_results.values())
        
        if total_warnings > 0:
            print(f"⚠️  Total warnings: {total_warnings}")
        if total_errors > 0:
            print(f"❌ Total errors: {total_errors}")
        
        # Component summary
        print(f"\n=== Component Status ===")
        print(f"✓ Data loading: Phase 2 complete")
        print(f"✓ Map building: Phase 2 complete")
        print(f"{'✓' if self._layers_available else '⚠️ '} Layers: {'Phase 3 complete' if self._layers_available else 'Phase 3 pending'}")
        print(f"{'✓' if self._interactivity_available else '⚠️ '} Interactivity: {'Phase 5 complete' if self._interactivity_available else 'Phase 5 pending'}")
        
        print("\n✓ Visualization creation completed")
    
    def _print_usage_instructions(self):
        """Print usage instructions for the created visualization."""
        print(f"\n=== Usage Instructions ===")
        print(f"📖 Open the HTML file in your web browser to view the visualization")
        
        if self._interactivity_available:
            print(f"🖱️  Right-click on property or gauge markers for context menus")
            print(f"📄 Generate reports using the context menu options")
            print(f"🔧 Make sure backend server is running for report generation:")
            print(f"   python server_endpoints.py")
            print(f"   Server should be accessible at: {self.interactivity.backend_handler.server_url}")
        else:
            print(f"ℹ️  Interactive features not available (install Phase 5 modules)")
        
        if not self._layers_available:
            print(f"ℹ️  Advanced layer features not available (install Phase 3 modules)")
    
    def configure_interactivity(self, **kwargs):
        """
        Configure interactivity settings.
        
        Args:
            **kwargs: Configuration options for interactivity components
                     server_url: Backend server URL
                     notification_position: Notification position
                     notification_timeout: Auto-dismiss timeout
                     context_menu_items: Custom context menu items
        """
        if not self._interactivity_available or not self.interactivity:
            print("⚠️  Interactivity not available for configuration")
            return False
        
        try:
            self.interactivity.configure(**kwargs)
            print("✓ Interactivity configured successfully")
            return True
        except Exception as e:
            print(f"⚠️  Failed to configure interactivity: {e}")
            return False
    
    def enable_debug_mode(self):
        """Enable debug mode for more verbose output."""
        # Enable debug mode in components
        self.data_loader.set_debug_mode(True)
        self.map_builder.set_debug_mode(True)
        
        if self._interactivity_available and self.interactivity:
            # Add debug notifications
            try:
                self.interactivity.notifications.configure(
                    custom_templates={
                        "debug": {
                            "icon": "🐛",
                            "color": "#9C27B0",
                            "background": "#F3E5F5"
                        }
                    }
                )
                print("✓ Debug mode enabled for all components")
            except Exception:
                print("✓ Debug mode enabled (interactivity debug unavailable)")
        else:
            print("✓ Debug mode enabled (limited - interactivity unavailable)")
    
    def get_component_statistics(self):
        """
        Get statistics from all components.
        
        Returns:
            Dictionary with component statistics
        """
        stats = {
            'data_loader': self.data_loader.get_statistics() if hasattr(self.data_loader, 'get_statistics') else {},
            'map_builder': self.map_builder.get_statistics() if hasattr(self.map_builder, 'get_statistics') else {},
            'layers_available': self._layers_available,
            'interactivity_available': self._interactivity_available
        }
        
        if self._interactivity_available and self.interactivity:
            stats['interactivity'] = self.interactivity.get_statistics()
        
        return stats
    
    def _get_default_output_dir(self) -> Path:
        """Get default output directory."""
        try:
            # Use ProjectPaths for consistent directory resolution
            return ProjectPaths(__file__).results_dir
        except Exception as e:
            print(f"Warning: Could not use ProjectPaths ({e}), using fallback")
            # Fallback to relative path from project root
            return project_root / "results"
    
    def get_loaded_data(self):
        """
        Get the currently loaded data.
        
        Returns:
            LoadedData container or None if no data loaded
        """
        return self.loaded_data
    
    def configure_map_settings(self, default_zoom: int = 8, 
                             tiles: str = 'OpenStreetMap',
                             controls: dict = None):
        """
        Configure map builder settings.
        
        Args:
            default_zoom: Default zoom level
            tiles: Default tile layer
            controls: Dictionary of control settings
        """
        self.map_builder.set_default_zoom(default_zoom)
        self.map_builder.set_default_tiles(tiles)
        
        if controls:
            self.map_builder.configure_controls(**controls)
        
        print("✓ Map settings configured")
    
    def validate_input_files(self, ts_filename: str, gauge_filename: str,
                           property_filename: str, mortgage_filename: str,
                           flood_risk_filename: str) -> bool:
        """
        Validate that all required input files exist.
        
        Args:
            ts_filename: Tropical cyclone timeseries filename
            gauge_filename: Flood gauge data filename
            property_filename: Property portfolio filename
            mortgage_filename: Mortgage portfolio filename
            flood_risk_filename: Flood risk report filename
            
        Returns:
            True if all files exist, False otherwise
        """
        filenames = [
            ts_filename,
            gauge_filename, 
            property_filename,
            mortgage_filename,
            flood_risk_filename
        ]
        
        missing_files = []
        for filename in filenames:
            file_path = self.data_loader.input_dir / filename
            if not file_path.exists():
                missing_files.append(filename)
        
        if missing_files:
            print(f"Missing files: {', '.join(missing_files)}")
            return False
        
        print("✓ All input files exist")
        return True
    
    def create_test_map(self, tc_filename: str, output_filename: str = "test_map.html") -> Optional[Path]:
        """
        Create a simple test map with just the storm track (for testing Phase 2).
        
        Args:
            tc_filename: Tropical cyclone data filename
            output_filename: Output filename
            
        Returns:
            Path to created map or None if failed
        """
        try:
            print("\n=== Creating Test Map ===")
            
            # Load only TC data
            tc_data = self.data_loader._load_json(tc_filename)
            if not tc_data:
                print("✗ Failed to load TC data")
                return None
            
            # Validate TC data
            validation = self.data_loader._validate_data(tc_data, 'tropical_cyclone')
            if not validation.is_valid:
                print(f"✗ TC data validation failed: {validation.errors}")
                return None
            
            print(f"✓ TC data loaded and validated: {validation.summary}")
            
            # Create base map
            base_map = self.map_builder.create_base_map(tc_data)
            
            # Add a simple storm path placeholder
            coordinates = self.map_builder._extract_coordinates(tc_data)
            if coordinates:
                import folium
                folium.PolyLine(
                    coordinates,
                    weight=4,
                    color='red',
                    opacity=0.8,
                    tooltip="Storm Path (Test)"
                ).add_to(base_map)
                print(f"✓ Added simple storm path with {len(coordinates)} points")
            
            # Add basic interactivity to test map if available
            if self._interactivity_available and self.interactivity:
                try:
                    self.interactivity.setup_map_interactivity(base_map)
                    print("✓ Added interactivity to test map")
                except Exception as e:
                    print(f"⚠️  Could not add interactivity to test map: {e}")
            
            # Save map
            output_path = self.output_dir / output_filename
            result_path = self.map_builder.finalize_map(base_map, output_path)
            
            if result_path:
                print(f"✓ Test map created: {result_path}")
                if self._interactivity_available:
                    print("🖱️  Test the interactive features in your browser")
            
            return result_path
            
        except Exception as e:
            print(f"✗ Error creating test map: {str(e)}")
            return None
    
    def create_interactive_demo(self, output_filename: str = "interactive_demo.html") -> Optional[Path]:
        """
        Create a demonstration map showcasing interactive features.
        
        Args:
            output_filename: Output filename
            
        Returns:
            Path to created demo map or None if failed
        """
        if not self._interactivity_available or not self.interactivity:
            print("⚠️  Interactive demo requires Phase 5 interactivity modules")
            return None
        
        try:
            print("\n=== Creating Interactive Demo ===")
            
            # Create a basic map
            import folium
            demo_map = folium.Map(location=[51.5074, -0.1278], zoom_start=10)
            
            # Add sample markers for demonstration
            folium.Marker(
                location=[51.5074, -0.1278],
                popup="Sample Property: PROP-demo123",
                tooltip="Property: PROP-demo123 | Risk: Medium",
                icon=folium.Icon(color='red', icon='home', prefix='fa')
            ).add_to(demo_map)
            
            folium.Marker(
                location=[51.5100, -0.1200],
                popup="Sample Gauge: GAUGE-demo456",
                tooltip="Gauge: Demo River Gauge | Status: Operational",
                icon=folium.Icon(color='blue', icon='tint', prefix='fa')
            ).add_to(demo_map)
            
            # Add full interactivity
            self.interactivity.setup_map_interactivity(demo_map)
            
            # Save demo map
            output_path = self.output_dir / output_filename
            demo_map.save(output_path)
            
            print(f"✓ Interactive demo created: {output_path}")
            print("🎮 Demo features:")
            print("  • Right-click on markers for context menus")
            print("  • Test report generation (requires backend server)")
            print("  • Notification system demonstration")
            print(f"  • Backend server: {self.interactivity.backend_handler.server_url}")
            
            return output_path
            
        except Exception as e:
            print(f"✗ Error creating interactive demo: {str(e)}")
            return None


# Convenience function for quick usage
def create_tc_visualization(input_dir: Union[str, Path],
                          output_dir: Union[str, Path], 
                          ts_file: str = "single_tceventts.json",
                          gauge_file: str = "flood_gauge_portfolio.json",
                          property_file: str = "property_portfolio.json", 
                          mortgage_file: str = "mortgage_portfolio.json",
                          flood_risk_file: str = "flood_risk_report.json",
                          output_file: str = "tc_visualization.html",
                          enable_interactivity: bool = True,
                          **config) -> Optional[Path]:
    """
    Create a TC visualization with minimal setup.
    
    Args:
        input_dir: Directory containing input files
        output_dir: Directory for output files
        ts_file: TC timeseries filename
        gauge_file: Gauge data filename
        property_file: Property data filename
        mortgage_file: Mortgage data filename
        flood_risk_file: Flood risk data filename
        output_file: Output HTML filename
        enable_interactivity: Whether to enable interactive features
        **config: Additional configuration options
        
    Returns:
        Path to created visualization or None if failed
    """
    # Create visualizer
    viz = TCEventVisualization(
        input_dir=input_dir,
        output_dir=output_dir,
        enable_interactivity=enable_interactivity,
        **config
    )
    
    # Configure if requested
    if config and enable_interactivity:
        viz.configure_interactivity(**config)
    
    # Create visualization
    return viz.create_event_map(
        ts_filename=ts_file,
        gauge_filename=gauge_file,
        property_filename=property_file,
        mortgage_filename=mortgage_file,
        flood_risk_filename=flood_risk_file,
        output_filename=output_file
    )