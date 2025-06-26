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
Server endpoint to handle property report generation.

This module provides a Flask endpoint to receive requests for property report generation
and uses the report_generator to create PDF reports.
"""

import os
import json
from flask import Flask, request, jsonify
from pathlib import Path
import sys

# Fix the Python path to find project modules
current_file = Path(__file__).resolve()
project_root = current_file.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utilities.project_paths import ProjectPaths

# Import the report generators - corrected imports
from src.utilities.report_generator import generate_property_report
from src.utilities.report_integration import *  # Report integration utilities
from src.utilities.gauge_report_generator import generate_gauge_report
from src.utilities.report_gauge_integration import generate_report_for_gauge, get_available_gauges
from flask_cors import CORS

app = Flask(__name__)

# Enhanced CORS configuration to fix 403 errors
CORS(app, 
     origins=['http://127.0.0.1:5500', 'http://localhost:5500', 'http://127.0.0.1:8000', 'http://localhost:8000', 'null'],
     methods=['GET', 'POST', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=True)

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint for setup scripts."""
    return jsonify({
        'status': 'ok',
        'message': 'MKM Research Labs Report Server is running',
        'endpoints': [
            'POST /generate_property_report',
            'POST /generate_gauge_report',
            'GET /list_gauges'
        ]
    })

@app.route('/generate_property_report', methods=['POST', 'OPTIONS'])
def handle_report_generation():
    """
    Handle POST requests to generate property reports.
    
    Expects JSON with a propertyId field.
    Returns JSON response with status and message.
    """
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        # Get the request data
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No JSON data provided'}), 400
            
        property_id = data.get('propertyId')
        
        if not property_id:
            return jsonify({'status': 'error', 'message': 'Property ID is required'}), 400
        
        print(f"[DEBUG] Received property report request for: {property_id}")
        
        # Use ProjectPaths like visualization.py does
        try:
            paths = ProjectPaths(__file__)
            data_dir = paths.input_dir
            output_dir = paths.results_dir
            print(f"[DEBUG] ProjectPaths succeeded - data_dir: {data_dir}, output_dir: {output_dir}")
            
            # Check if the property file actually exists at this path
            property_file_test = data_dir / 'property_portfolio.json'
            if not property_file_test.exists():
                print(f"[DEBUG] ProjectPaths gave wrong path, file doesn't exist at {property_file_test}")
                raise Exception("ProjectPaths returned incorrect path")
                
        except Exception as e:
            # Fallback to relative paths from project root
            print(f"[DEBUG] ProjectPaths failed ({e}), using fallback")
            # Since server is in root, and input is in root/input
            project_root = Path(__file__).parent  # This is the physrisk directory
            data_dir = project_root / 'input'
            output_dir = project_root / 'reports'
            print(f"[DEBUG] Fallback paths - data_dir: {data_dir}, output_dir: {output_dir}")

        property_file = data_dir / 'property_portfolio.json'
        mortgage_file = data_dir / 'mortgage_portfolio.json'
        
        # Debug output
        print(f"[DEBUG] Property file path: {property_file}")
        print(f"[DEBUG] Property file exists: {property_file.exists()}")
        print(f"[DEBUG] Looking for property ID: {property_id}")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Load property data
        if not property_file.exists():
            return jsonify({'status': 'error', 'message': f'Property file not found at: {property_file}'}), 404
        
        with open(property_file, 'r') as f:
            property_data = json.load(f)
        
        # Load mortgage data if available
        mortgage_data = None
        if mortgage_file.exists():
            with open(mortgage_file, 'r') as f:
                mortgage_data = json.load(f)
        
        # Find the specific property
        target_property = None
        mortgage_for_property = None
        
        # Handle different property file formats
        if isinstance(property_data, dict):
            if 'properties' in property_data:
                properties = property_data['properties']
            elif 'portfolio' in property_data:
                properties = property_data['portfolio']
            else:
                properties = [property_data]
        elif isinstance(property_data, list):
            properties = property_data
        else:
            properties = []
        
        # Find the specific property
        for prop in properties:
            prop_id = prop.get('PropertyHeader', {}).get('Header', {}).get('PropertyID')
            if prop_id == property_id:
                target_property = prop
                break
        
        if target_property is None:
            return jsonify({
                'status': 'error', 
                'message': f'Property with ID {property_id} not found'
            }), 404
        
        # Find corresponding mortgage
        if mortgage_data:
            if isinstance(mortgage_data, dict):
                if 'mortgages' in mortgage_data:
                    mortgages = mortgage_data['mortgages']
                else:
                    mortgages = [mortgage_data]
            elif isinstance(mortgage_data, list):
                mortgages = mortgage_data
            else:
                mortgages = []
            
            for mortgage in mortgages:
                if mortgage.get('PropertyID') == property_id:
                    mortgage_for_property = mortgage
                    break
        
        # Generate the report using the correct function name and parameters
        report_path = generate_property_report(
            property_data=target_property,
            mortgage_data=mortgage_for_property,
            output_dir=output_dir,
            report_type="full",  
            auto_open=True
        )
        
        print(f"[SUCCESS] Property report generated at: {report_path}")
        
        return jsonify({
            'status': 'success',
            'message': f'Report generated successfully',
            'file_path': str(report_path)
        })
        
    except Exception as e:
        # Log the error
        import traceback
        traceback.print_exc()
        
        # Return error response
        return jsonify({
            'status': 'error',
            'message': f'Error generating report: {str(e)}'
        }), 500

# Replace the gauge endpoint in server_endpoints.py to match property endpoint pattern:

@app.route('/generate_gauge_report', methods=['POST', 'OPTIONS'])
def handle_gauge_report_generation():
    """
    Handle POST requests to generate gauge reports.
    
    Expects JSON with a gaugeId field.
    Returns JSON response with status and message.
    """
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        # Get the request data
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No JSON data provided'}), 400
            
        gauge_id = data.get('gaugeId')
        
        if not gauge_id:
            return jsonify({'status': 'error', 'message': 'Gauge ID is required'}), 400
        
        print(f"[DEBUG] Received gauge report request for: {gauge_id}")
        
        # Use ProjectPaths like property endpoint does
        try:
            paths = ProjectPaths(__file__)
            data_dir = paths.input_dir
            output_dir = paths.results_dir
            print(f"[DEBUG] ProjectPaths succeeded - data_dir: {data_dir}, output_dir: {output_dir}")
            
            # Check if the gauge file actually exists at this path
            gauge_file_test = data_dir / 'flood_gauge_portfolio.json'
            if not gauge_file_test.exists():
                print(f"[DEBUG] ProjectPaths gave wrong path, file doesn't exist at {gauge_file_test}")
                raise Exception("ProjectPaths returned incorrect path")
                
        except Exception as e:
            # Fallback to relative paths from project root
            print(f"[DEBUG] ProjectPaths failed ({e}), using fallback")
            # Since server is in root, and input is in root/input
            project_root = Path(__file__).parent  # This is the physrisk directory
            data_dir = project_root / 'input'
            output_dir = project_root / 'reports'
            print(f"[DEBUG] Fallback paths - data_dir: {data_dir}, output_dir: {output_dir}")

        gauge_file = data_dir / 'flood_gauge_portfolio.json'
        
        # Debug output
        print(f"[DEBUG] Gauge file path: {gauge_file}")
        print(f"[DEBUG] Gauge file exists: {gauge_file.exists()}")
        print(f"[DEBUG] Looking for gauge ID: {gauge_id}")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Load gauge data
        if not gauge_file.exists():
            return jsonify({'status': 'error', 'message': f'Gauge file not found at: {gauge_file}'}), 404
        
        with open(gauge_file, 'r') as f:
            gauge_data = json.load(f)
        
        # Find the specific gauge
        target_gauge = None
        
        # Handle different gauge file formats (same pattern as property)
        if isinstance(gauge_data, dict):
            if 'floodGauges' in gauge_data:
                gauges = gauge_data['floodGauges']
            elif 'flood_gauges' in gauge_data:
                gauges = gauge_data['flood_gauges']
            else:
                gauges = [gauge_data]
        elif isinstance(gauge_data, list):
            gauges = gauge_data
        else:
            gauges = []
        
        # Find the specific gauge
        for gauge in gauges:
            gauge_header_id = gauge.get('FloodGauge', {}).get('Header', {}).get('GaugeID')
            if gauge_header_id == gauge_id:
                target_gauge = gauge
                break
        
        if target_gauge is None:
            return jsonify({
                'status': 'error', 
                'message': f'Gauge with ID {gauge_id} not found'
            }), 404
        
        # Generate the report using the correct function name and parameters
        report_path = generate_gauge_report(
            gauge_data=target_gauge,
            timeseries_data=None,  # Could be added later
            output_dir=output_dir,
            report_type="basic",  
            auto_open=True
        )
        
        print(f"[SUCCESS] Gauge report generated at: {report_path}")
        
        return jsonify({
            'status': 'success',
            'message': f'Report generated successfully',
            'file_path': str(report_path)
        })
        
    except Exception as e:
        # Log the error
        import traceback
        traceback.print_exc()
        
        # Return error response
        return jsonify({
            'status': 'error',
            'message': f'Error generating report: {str(e)}'
        }), 500





@app.route('/list_gauges', methods=['GET', 'OPTIONS'])
def list_available_gauges():
    """
    GET endpoint to list all available gauges.
    
    Returns JSON response with list of available gauge IDs and names.
    """
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
        
    try:
        print(f"[STATUS] Received request to list available gauges")
        
        # Use ProjectPaths like other endpoints
        try:
            paths = ProjectPaths(__file__)
            data_dir = paths.input_dir
        except Exception as e:
            # Fallback to relative paths from project root
            print(f"[STATUS] ProjectPaths failed ({e}), using fallback")
            server_dir = Path(__file__).parent
            data_dir = server_dir / 'input'

        gauge_portfolio_file = data_dir / 'flood_gauge_portfolio.json'
        
        print(f"[STATUS] Checking gauge portfolio file: {gauge_portfolio_file}")
        
        if not gauge_portfolio_file.exists():
            return jsonify({
                'status': 'error', 
                'message': f'Gauge portfolio file not found at: {gauge_portfolio_file}'
            }), 404
        
        # Debug: Test get_available_gauges function
        try:
            available_gauges = get_available_gauges(gauge_portfolio_file)
            print(f"[DEBUG] get_available_gauges returned {len(available_gauges)} gauges")
            print(f"[DEBUG] First 5 gauges: {available_gauges[:5]}")
        except Exception as e:
            print(f"[DEBUG] get_available_gauges failed: {e}")
                
        # Also get gauge details for more helpful response
        with open(gauge_portfolio_file) as f:
            gauge_data = json.load(f)
        
        gauges_info = []
        # Fix: Use correct key from JSON structure
        gauges = gauge_data.get('floodGauges', gauge_data.get('flood_gauges', []))
        
        for gauge in gauges:
            gauge_header = gauge.get('FloodGauge', {}).get('Header', {})
            gauge_info = gauge.get('FloodGauge', {}).get('SensorDetails', {}).get('GaugeInformation', {})
            
            gauges_info.append({
                'gaugeId': gauge_header.get('GaugeID'),
                'name': gauge_header.get('GaugeName'),
                'type': gauge_info.get('GaugeType'),
                'owner': gauge_info.get('GaugeOwner'),
                'status': gauge_info.get('OperationalStatus')
            })
        
        print(f"[SUCCESS] Found {len(gauges_info)} available gauges")
        
        return jsonify({
            'status': 'success',
            'message': f'Found {len(gauges_info)} available gauges',
            'count': len(gauges_info),
            'gauges': gauges_info
        })
        
    except Exception as e:
        # Log the error
        import traceback
        traceback.print_exc()
        
        # Return error response
        return jsonify({
            'status': 'error',
            'message': f'Error listing gauges: {str(e)}'
        }), 500


def extract_gauge_timeseries(timeseries_data, gauge_id, gauge_metadata):
    """
    Extract time series data for specific gauge.
    Handles the ID mismatch between portfolio and timeseries data.
    
    Note: This function is kept for future use when timeseries integration is added.
    """
    gauge_name = gauge_metadata.get('Header', {}).get('GaugeName', '')
    gauge_timeseries = []
    
    print(f"DEBUG: Looking for timeseries data for gauge_id='{gauge_id}', gauge_name='{gauge_name}'")
    
    for time_record in timeseries_data:
        if isinstance(time_record, dict) and 'readings' in time_record:
            for reading in time_record['readings']:
                # Check multiple ways to match the gauge
                reading_gauge_id = reading.get('gaugeId', '')
                reading_name = reading.get('name', '')
                
                if (reading_gauge_id == gauge_id or 
                    reading_name == gauge_name or
                    reading_name == gauge_id):
                    
                    # Found a match - add this reading with timestamp info
                    gauge_timeseries.append({
                        'timestamp': time_record.get('timestamp'),
                        'hour': time_record.get('hour'),
                        **reading
                    })
                    break  # Found match for this time record, move to next
    
    print(f"DEBUG: Found {len(gauge_timeseries)} matching time series readings")
    return gauge_timeseries if gauge_timeseries else None


if __name__ == '__main__':
    # Run the Flask app when executed directly
    print("[STARTUP] Starting MKM Research Labs Report Server...")
    print("[STARTUP] CORS enabled for multiple origins")
    print("[STARTUP] Server will run on http://127.0.0.1:5001")
    app.run(debug=True, port=5001, host='127.0.0.1')