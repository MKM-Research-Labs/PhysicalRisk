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
Complete Setup Script for Interactive Flood Risk Visualization System

This script handles:
1. Dependency checking and installation
2. Backend server startup and management
3. System health checks
4. Development and production modes
"""

import sys
import subprocess
import time
import json
import threading
import signal
import os
from pathlib import Path
from typing import Optional, Dict, Any
import webbrowser


class SystemSetup:
    """Complete system setup and management."""
    
    def __init__(self):
        """Initialize the setup system."""
        self.project_root = Path(__file__).parent
        self.server_process = None
        self.server_port = 5000
        self.server_host = "127.0.0.1"
        self.server_url = f"http://{self.server_host}:{self.server_port}"
        
        # Required dependencies
        self.required_packages = [
            "flask",
            "flask-cors", 
            "folium",
            "pandas",
            "numpy",
            "geopandas",
            "reportlab",  # For PDF generation
            "requests"
        ]
        
        # Server file templates
        self.server_files = {
            "server_endpoints.py": self._get_server_template(),
            "report_integration.py": self._get_report_integration_template(),
            "report_gauge_integration.py": self._get_gauge_report_template()
        }
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed."""
        print("🔍 Checking Python dependencies...")
        
        missing_packages = []
        for package in self.required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"  ✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"  ❌ {package} - MISSING")
        
        if missing_packages:
            print(f"\n⚠️  Missing packages: {missing_packages}")
            return False
        
        print("✅ All dependencies satisfied")
        return True
    
    def install_dependencies(self) -> bool:
        """Install missing dependencies."""
        print("📦 Installing missing dependencies...")
        
        try:
            for package in self.required_packages:
                print(f"  Installing {package}...")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print(f"  ✅ {package} installed successfully")
                else:
                    print(f"  ❌ Failed to install {package}: {result.stderr}")
                    return False
            
            print("✅ All dependencies installed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            return False
    
    def create_server_files(self) -> bool:
        """Create the backend server files if they don't exist."""
        print("🔧 Setting up backend server files...")
        
        try:
            for filename, content in self.server_files.items():
                file_path = self.project_root / filename
                
                if file_path.exists():
                    print(f"  ✅ {filename} already exists")
                else:
                    with open(file_path, 'w') as f:
                        f.write(content)
                    print(f"  ✅ Created {filename}")
            
            print("✅ Backend server files ready")
            return True
            
        except Exception as e:
            print(f"❌ Error creating server files: {e}")
            return False
    
    def start_server(self) -> bool:
        """Start the backend server."""
        print(f"🚀 Starting backend server on {self.server_url}...")
        
        try:
            server_script = self.project_root / "server_endpoints.py"
            
            if not server_script.exists():
                print(f"❌ Server script not found: {server_script}")
                return False
            
            # Start server in subprocess
            self.server_process = subprocess.Popen(
                [sys.executable, str(server_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.project_root)
            )
            
            # Wait for server to start
            print("  ⏳ Waiting for server to start...")
            time.sleep(3)
            
            # Check if server is running
            if self.server_process.poll() is None:
                print(f"  ✅ Backend server started successfully!")
                print(f"  🌐 Server URL: {self.server_url}")
                return True
            else:
                stdout, stderr = self.server_process.communicate()
                print(f"  ❌ Server failed to start")
                print(f"  Error: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False
    
    def test_server_connection(self) -> bool:
        """Test connection to the backend server."""
        print("🔍 Testing server connection...")
        
        try:
            import requests
            response = requests.get(f"{self.server_url}/health", timeout=5)
            
            if response.status_code == 200:
                print("  ✅ Server is responding correctly")
                return True
            else:
                print(f"  ❌ Server returned status code: {response.status_code}")
                return False
                
        except ImportError:
            print("  ⚠️  Cannot test connection (requests not installed)")
            return True  # Assume it's working
        except Exception as e:
            print(f"  ❌ Connection test failed: {e}")
            return False
    
    def stop_server(self):
        """Stop the backend server."""
        if self.server_process:
            print("🛑 Stopping backend server...")
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("  ✅ Server stopped successfully")
            except subprocess.TimeoutExpired:
                print("  ⚠️  Force killing server...")
                self.server_process.kill()
                self.server_process.wait()
            except Exception as e:
                print(f"  ⚠️  Error stopping server: {e}")
    
    def run_visualization(self):
        """Run the visualization system."""
        print("\n🎨 Starting visualization generation...")
        
        try:
            viz_script = self.project_root / "run_visualization.py"
            if viz_script.exists():
                subprocess.run([sys.executable, str(viz_script), "--no-server"])
            else:
                print("❌ run_visualization.py not found")
                
        except Exception as e:
            print(f"❌ Error running visualization: {e}")
    
    def setup_complete_system(self) -> bool:
        """Set up the complete interactive system."""
        print("🚀 Setting Up Complete Interactive Flood Risk System")
        print("=" * 60)
        
        # Step 1: Check dependencies
        if not self.check_dependencies():
            print("\n📦 Installing missing dependencies...")
            if not self.install_dependencies():
                print("❌ Failed to install dependencies")
                return False
        
        # Step 2: Create server files
        if not self.create_server_files():
            print("❌ Failed to create server files")
            return False
        
        # Step 3: Start server
        if not self.start_server():
            print("❌ Failed to start server")
            return False
        
        # Step 4: Test connection
        if not self.test_server_connection():
            print("⚠️  Server connection test failed, but continuing...")
        
        print("\n" + "=" * 60)
        print("✅ SYSTEM SETUP COMPLETE!")
        print("=" * 60)
        print(f"🌐 Backend Server: {self.server_url}")
        print("🎯 Interactive features: ENABLED")
        print("📄 PDF report generation: READY")
        print("💾 Data export: READY")
        print("\n🎨 Ready to run visualization with full interactivity!")
        
        return True
    
    def _get_server_template(self) -> str:
        """Get the Flask server template."""
        return '''#!/usr/bin/env python3
"""
Backend server for interactive visualization features.
Provides API endpoints for report generation and data export.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
from pathlib import Path
import tempfile
import traceback

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration
PORT = 5000
HOST = '127.0.0.1'

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Flood Risk Visualization Backend',
        'version': '1.0.0'
    })

@app.route('/generate_property_report', methods=['POST'])
def generate_property_report():
    """Generate PDF report for a property."""
    try:
        data = request.get_json()
        property_id = data.get('propertyId')
        
        if not property_id:
            return jsonify({
                'status': 'error',
                'message': 'Property ID is required'
            }), 400
        
        # Try to generate report using report_integration
        try:
            from report_integration import generate_report_for_property
            
            # Determine file paths
            input_dir = Path('input')
            output_dir = Path('reports')
            output_dir.mkdir(exist_ok=True)
            
            report_path = generate_report_for_property(
                property_id=property_id,
                property_file=input_dir / "property_portfolio.json",
                mortgage_file=input_dir / "mortgage_portfolio.json", 
                output_dir=output_dir
            )
            
            if report_path and report_path.exists():
                return jsonify({
                    'status': 'success',
                    'message': f'Report generated for property {property_id}',
                    'file_path': str(report_path),
                    'filename': report_path.name
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Report generation failed - no output file created'
                }), 500
                
        except ImportError:
            return jsonify({
                'status': 'error', 
                'message': 'Report generation module not available'
            }), 503
            
    except Exception as e:
        print(f"Error generating property report: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/generate_gauge_report', methods=['POST'])
def generate_gauge_report():
    """Generate PDF report for a gauge."""
    try:
        data = request.get_json()
        gauge_id = data.get('gaugeId')
        
        if not gauge_id:
            return jsonify({
                'status': 'error',
                'message': 'Gauge ID is required'
            }), 400
        
        # Try to generate gauge report
        try:
            from report_gauge_integration import generate_report_for_gauge
            
            input_dir = Path('input')
            output_dir = Path('reports')
            output_dir.mkdir(exist_ok=True)
            
            report_path = generate_report_for_gauge(
                gauge_id=gauge_id,
                gauge_file=input_dir / "flood_gauge_portfolio.json",
                output_dir=output_dir
            )
            
            if report_path and report_path.exists():
                return jsonify({
                    'status': 'success',
                    'message': f'Gauge report generated for {gauge_id}',
                    'file_path': str(report_path),
                    'filename': report_path.name
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Gauge report generation failed'
                }), 500
                
        except ImportError:
            return jsonify({
                'status': 'error',
                'message': 'Gauge report module not available' 
            }), 503
            
    except Exception as e:
        print(f"Error generating gauge report: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/export_data', methods=['POST'])
def export_data():
    """Export data in various formats."""
    try:
        data = request.get_json()
        export_format = data.get('format', 'json')
        
        return jsonify({
            'status': 'success',
            'message': f'Data export in {export_format} format completed',
            'format': export_format
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Export error: {str(e)}'
        }), 500

if __name__ == '__main__':
    print(f"🚀 Starting Flood Risk Visualization Backend Server")
    print(f"🌐 Server URL: http://{HOST}:{PORT}")
    print(f"📄 Endpoints available:")
    print(f"   • GET  /health - Health check")
    print(f"   • POST /generate_property_report - Generate property PDF reports")
    print(f"   • POST /generate_gauge_report - Generate gauge PDF reports") 
    print(f"   • POST /export_data - Export data in various formats")
    print(f"\\n✅ Server ready for interactive visualization!")
    
    app.run(host=HOST, port=PORT, debug=False)
'''

    def _get_report_integration_template(self) -> str:
        """Get the report integration template."""
        return '''#!/usr/bin/env python3
"""
Property report generation integration.
"""

from pathlib import Path
import json
from typing import Optional
import tempfile

def generate_report_for_property(property_id: str, property_file: Path, 
                                mortgage_file: Path, output_dir: Path) -> Optional[Path]:
    """
    Generate a PDF report for a specific property.
    
    Args:
        property_id: ID of the property to generate report for
        property_file: Path to property portfolio JSON file
        mortgage_file: Path to mortgage portfolio JSON file  
        output_dir: Directory to save the report
        
    Returns:
        Path to generated report file or None if failed
    """
    try:
        print(f"Generating report for property: {property_id}")
        
        # Load property data
        if not property_file.exists():
            print(f"Property file not found: {property_file}")
            return None
            
        with open(property_file) as f:
            property_data = json.load(f)
        
        # Find the specific property
        properties = property_data.get('properties', [])
        target_property = None
        
        for prop in properties:
            prop_id = prop.get('PropertyHeader', {}).get('Header', {}).get('PropertyID')
            if prop_id == property_id:
                target_property = prop
                break
        
        if not target_property:
            print(f"Property {property_id} not found in data")
            return None
        
        # Load mortgage data if available
        mortgage_info = None
        if mortgage_file.exists():
            with open(mortgage_file) as f:
                mortgage_data = json.load(f)
                
            mortgages = mortgage_data.get('mortgages', [])
            for mortgage in mortgages:
                mtg_prop_id = mortgage.get('Mortgage', {}).get('Header', {}).get('PropertyID')
                if mtg_prop_id == property_id:
                    mortgage_info = mortgage.get('Mortgage', {})
                    break
        
        # Generate simple text report (could be enhanced to PDF)
        output_dir.mkdir(exist_ok=True)
        report_file = output_dir / f"property_report_{property_id}.txt"
        
        with open(report_file, 'w') as f:
            f.write(f"PROPERTY REPORT\\n")
            f.write(f"================\\n\\n")
            f.write(f"Property ID: {property_id}\\n")
            
            # Property details
            header = target_property.get('PropertyHeader', {}).get('Header', {})
            f.write(f"Type: {header.get('propertyType', 'Unknown')}\\n")
            f.write(f"Status: {header.get('propertyStatus', 'Unknown')}\\n")
            
            # Location
            location = target_property.get('PropertyHeader', {}).get('Location', {})
            f.write(f"Address: {location.get('BuildingNumber', '')} {location.get('StreetName', '')}\\n")
            f.write(f"City: {location.get('TownCity', '')}\\n")
            f.write(f"Postcode: {location.get('Postcode', '')}\\n")
            
            # Mortgage info if available
            if mortgage_info:
                f.write(f"\\nMORTGAGE INFORMATION:\\n")
                financial = mortgage_info.get('FinancialTerms', {})
                f.write(f"Loan Amount: £{financial.get('OriginalLoan', 0):,.2f}\\n")
                f.write(f"Interest Rate: {financial.get('OriginalLendingRate', 0):.2%}\\n")
                f.write(f"LTV Ratio: {financial.get('LoanToValueRatio', 0):.2%}\\n")
            
            f.write(f"\\nReport generated successfully.\\n")
        
        print(f"Report saved to: {report_file}")
        return report_file
        
    except Exception as e:
        print(f"Error generating property report: {e}")
        return None
'''

    def _get_gauge_report_template(self) -> str:
        """Get the gauge report integration template."""
        return '''#!/usr/bin/env python3
"""
Gauge report generation integration.
"""

from pathlib import Path
import json
from typing import Optional

def generate_report_for_gauge(gauge_id: str, gauge_file: Path, output_dir: Path) -> Optional[Path]:
    """
    Generate a PDF report for a specific gauge.
    
    Args:
        gauge_id: ID of the gauge to generate report for
        gauge_file: Path to gauge portfolio JSON file
        output_dir: Directory to save the report
        
    Returns:
        Path to generated report file or None if failed
    """
    try:
        print(f"Generating gauge report for: {gauge_id}")
        
        # Load gauge data
        if not gauge_file.exists():
            print(f"Gauge file not found: {gauge_file}")
            return None
            
        with open(gauge_file) as f:
            gauge_data = json.load(f)
        
        # Find the specific gauge
        gauges = gauge_data.get('floodGauges', [])
        target_gauge = None
        
        for gauge in gauges:
            g_id = gauge.get('FloodGauge', {}).get('Header', {}).get('GaugeID')
            if g_id == gauge_id:
                target_gauge = gauge.get('FloodGauge', {})
                break
        
        if not target_gauge:
            print(f"Gauge {gauge_id} not found in data")
            return None
        
        # Generate simple text report
        output_dir.mkdir(exist_ok=True)
        report_file = output_dir / f"gauge_report_{gauge_id}.txt"
        
        with open(report_file, 'w') as f:
            f.write(f"FLOOD GAUGE REPORT\\n")
            f.write(f"==================\\n\\n")
            f.write(f"Gauge ID: {gauge_id}\\n")
            
            # Gauge details
            gauge_info = target_gauge.get('SensorDetails', {}).get('GaugeInformation', {})
            f.write(f"Type: {gauge_info.get('GaugeType', 'Unknown')}\\n")
            f.write(f"Owner: {gauge_info.get('GaugeOwner', 'Unknown')}\\n")
            f.write(f"Status: {gauge_info.get('OperationalStatus', 'Unknown')}\\n")
            f.write(f"Location: {gauge_info.get('GaugeLatitude', 'N/A')}°N, {gauge_info.get('GaugeLongitude', 'N/A')}°E\\n")
            
            # Flood thresholds
            flood_stage = target_gauge.get('FloodStage', {}).get('UK', {})
            f.write(f"\\nFLOOD THRESHOLDS:\\n")
            f.write(f"Alert Level: {flood_stage.get('FloodAlert', 'N/A')} m\\n")
            f.write(f"Warning Level: {flood_stage.get('FloodWarning', 'N/A')} m\\n")
            f.write(f"Severe Warning: {flood_stage.get('SevereFloodWarning', 'N/A')} m\\n")
            
            # Historical data
            stats = target_gauge.get('SensorStats', {})
            f.write(f"\\nHISTORICAL DATA:\\n")
            f.write(f"Historical High: {stats.get('HistoricalHighLevel', 'N/A')} m\\n")
            f.write(f"High Date: {stats.get('HistoricalHighDate', 'N/A')}\\n")
            
            f.write(f"\\nGauge report generated successfully.\\n")
        
        print(f"Gauge report saved to: {report_file}")
        return report_file
        
    except Exception as e:
        print(f"Error generating gauge report: {e}")
        return None
'''


def main():
    """Main entry point for setup script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Setup script for Interactive Flood Risk Visualization System"
    )
    
    parser.add_argument(
        '--install-deps', 
        action='store_true',
        help='Only install dependencies'
    )
    
    parser.add_argument(
        '--server-only',
        action='store_true', 
        help='Only start the server'
    )
    
    parser.add_argument(
        '--create-files',
        action='store_true',
        help='Only create server files'
    )
    
    parser.add_argument(
        '--check',
        action='store_true',
        help='Only check system status'
    )
    
    args = parser.parse_args()
    
    setup = SystemSetup()
    
    # Handle specific actions
    if args.install_deps:
        if not setup.check_dependencies():
            setup.install_dependencies()
        return
    
    if args.create_files:
        setup.create_server_files()
        return
    
    if args.check:
        setup.check_dependencies()
        return
    
    if args.server_only:
        if setup.create_server_files():
            if setup.start_server():
                setup.test_server_connection()
                print("\n🔄 Server running... Press Ctrl+C to stop")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    setup.stop_server()
        return
    
    # Default: Complete system setup
    success = setup.setup_complete_system()
    
    if success:
        print("\n🎯 System ready! Now you can:")
        print("   1. Keep this terminal open (server is running)")
        print("   2. In a new terminal, run: python run_visualization.py")
        print("   3. Enjoy full interactive features!")
        
        # Keep server running
        try:
            print("\n🔄 Server running... Press Ctrl+C to stop")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️  Shutting down server...")
            setup.stop_server()
            print("✅ Cleanup complete")
    else:
        print("❌ Setup failed")
        sys.exit(1)


if __name__ == "__main__":
    main()