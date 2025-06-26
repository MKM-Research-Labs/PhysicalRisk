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

#!/usr/bin/env python3
"""
Complete Visualization Runner

This script:
1. Generates the interactive flood risk visualization 
2. Opens the visualization in your default browser
3. Provides easy management of the system
"""

import sys
import webbrowser
from pathlib import Path
import signal

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.visualization.core.visualizer import TCEventVisualization


class VisualizationRunner:
    """Complete visualization system runner."""
    
    def __init__(self):
        """Initialize the visualization runner."""
        self.visualization_path = None
        
    def generate_visualization(self, output_filename="interactive_visualization.html"):
        """
        Generate the interactive visualization
        
        Args:
            output_filename: Name of the output HTML file
            
        Returns:
            Path to generated visualization or None if failed
        """
        print("🚀 Starting Interactive Flood Risk Visualization System")
        print("=" * 60)
        
        try:
            # Create visualizer
            viz = TCEventVisualization()
            
            # Generate visualization
            self.visualization_path = viz.create_event_map(
                ts_filename="single_tceventts.json",
                gauge_filename="flood_gauge_portfolio.json", 
                property_filename="property_portfolio.json",
                mortgage_filename="mortgage_portfolio.json",
                flood_risk_filename="flood_risk_report.json",
                output_filename=output_filename
            )
            
            if self.visualization_path:
                print(f"\n✅ Visualization Successfully Generated!")
                print(f"📁 File: {self.visualization_path}")
                print(f"📏 File size: {self.visualization_path.stat().st_size / 1024:.1f} KB")
                return self.visualization_path
            else:
                print("\n❌ Visualization generation failed")
                return None
                
        except Exception as e:
            print(f"\n❌ Error generating visualization: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def open_visualization(self):
        """Open the visualization in the default browser."""
        if self.visualization_path and self.visualization_path.exists():
            print(f"\n🌐 Opening Visualization in Browser...")
            try:
                webbrowser.open(f"file://{self.visualization_path.absolute()}")
                print("✅ Visualization opened in your default browser")
                return True
            except Exception as e:
                print(f"❌ Could not open browser automatically: {e}")
                print(f"📁 Manually open: {self.visualization_path}")
                return False
        else:
            print("❌ No visualization file to open")
            return False
    
    def print_usage_instructions(self):
        """Print instructions for using the interactive visualization."""
        print("\n" + "=" * 60)
        print("🎯 INTERACTIVE VISUALIZATION READY!")
        print("=" * 60)
        
        print("\n🖱️  How to Use Your Interactive Map:")
        print("   • 🗺️  Pan and zoom to explore the flood risk area")
        print("   • 📍 Click markers for detailed property/gauge information")
        print("   • 🎛️  Use layer controls to toggle:")
        print("       - 🌪️  Storm Path")
        print("       - 🌊 Flood Gauges") 
        print("       - 🏠 Properties")
        print("       - 💰 Mortgage Risk")
        
        print(f"\n📁 Visualization File: {self.visualization_path}")
        print("🌐 The map is fully interactive and ready to use!")
    
    def run_complete_system(self, output_filename="interactive_visualization.html", 
                           open_browser=True):
        """
        Run the complete interactive visualization system.
        
        Args:
            output_filename: Name of output HTML file
            open_browser: Whether to open browser automatically
        """
        # Generate visualization
        viz_path = self.generate_visualization(output_filename)
        if not viz_path:
            print("❌ Cannot continue without visualization")
            return False
        
        # Open in browser (optional)
        if open_browser:
            self.open_visualization()
        
        # Print usage instructions
        self.print_usage_instructions()
        
        print("\n✅ Visualization system ready!")
        
        return True


def main():
    """Main entry point."""
    # Create runner
    runner = VisualizationRunner()
    
    # Setup signal handler for clean shutdown
    def signal_handler(sig, frame):
        print(f"\n\n⚠️  Received interrupt signal...")
        print("✅ Visualization system shutdown complete")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run the complete system
    success = runner.run_complete_system()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()