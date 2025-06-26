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

import json
import datetime
import os
import sys
import math
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
import numpy as np

# Fix the Python path to find project modules
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent  # Go up 3 levels: portfolio -> src -> root

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import modules
try:
    from utilities.project_paths import ProjectPaths
    from utilities.elevation import get_elevation
    from cdm.flood_gauge_cdm import FloodGaugeCDM
    
    # Use ProjectPaths if available
    paths = ProjectPaths(__file__)
    paths.setup_import_paths()
    input_dir = paths.input_dir
    
except ImportError as e:
    print(f"Warning: Could not import project modules: {e}")
    print("Using fallback paths...")
    
    # Fallback to manual path construction
    input_dir = project_root / 'input'
    
    # Mock the missing modules for testing
    class FloodGaugeCDM:
        def validate_gauge(self, gauge): return []
        def create_gauge_mapping(self, gauge): return {}
    
    def get_elevation(lat, lon): return 10.0  # Default elevation

# Ensure input directory exists
input_dir.mkdir(parents=True, exist_ok=True)

params = {
    "simulation_hours": 60,
    "time_step": 1,
    "flood_wave_speed": 1.5,  # Gauges per hour
    "peak_flood_height_ratio": 2.5,  # Ratio of peak height to flood alert level
    "initial_flood_height_ratio": 1.5,  # Ratio of initial height to flood alert level
    "recession_rate": 0.02,  # How quickly flood recedes (meters per hour)
    "simulation_start_date": datetime.datetime.now()
}

def load_gauge_portfolio(json_file_path: str = None, 
                         validate: bool = True) -> Dict[str, List[Dict]]:
    """
    Load the gauge portfolio from a JSON file and validate using CDM.
    
    Args:
        json_file_path: Path to the JSON file containing gauge portfolio data
        validate: Whether to validate the loaded data against the CDM schema
        
    Returns:
        Dictionary containing the gauge portfolio data
    """
    # If no path specified, use the input_dir
    if json_file_path is None:
        json_file_path = input_dir / 'flood_gauge_portfolio.json'
    else:
        # Convert relative paths to absolute paths based on project root
        json_file_path = Path(json_file_path)
        if not json_file_path.is_absolute():
            if str(json_file_path).startswith('input/'):
                # Handle 'input/filename.json' format
                json_file_path = project_root / json_file_path
            else:
                # Handle just 'filename.json' format
                json_file_path = input_dir / json_file_path
    
    print(f"Looking for gauge portfolio at: {json_file_path}")
    print(f"File exists: {json_file_path.exists()}")
    
    try:
        with open(json_file_path, 'r') as f:
            gauge_portfolio = json.load(f)
        
        gauge_count = len(gauge_portfolio.get('flood_gauges', []))
        print(f"✓ Loaded gauge portfolio from {json_file_path} with {gauge_count} gauges.")
        
        # Validate against CDM if requested
        if validate:
            try:
                cdm = FloodGaugeCDM()
                validation_errors = []
                
                for i, gauge in enumerate(gauge_portfolio.get('flood_gauges', [])):
                    errors = cdm.validate_gauge(gauge)
                    if errors:
                        gauge_id = gauge.get('FloodGauge', {}).get('Header', {}).get('GaugeID', f"Gauge #{i+1}")
                        validation_errors.append(f"Validation errors for {gauge_id}: {errors}")
                
                if validation_errors:
                    print("WARNING: Some gauges failed validation:")
                    for error in validation_errors:
                        print(f"  - {error}")
                    print("Proceeding with simulation despite validation errors.")
                else:
                    print("✓ All gauges successfully validated against CDM schema.")
            except Exception as e:
                print(f"Warning: CDM validation failed: {e}")
        
        return gauge_portfolio
    
    except FileNotFoundError:
        print(f"✗ ERROR: Could not find gauge portfolio file at {json_file_path}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Project root: {project_root}")
        print(f"Input directory: {input_dir}")
        
        # List available files for debugging
        if input_dir.exists():
            files = list(input_dir.glob("*.json"))
            print(f"Available JSON files in input directory: {files}")
        else:
            print(f"Input directory {input_dir} does not exist!")
            
        raise FileNotFoundError(f"Could not find gauge portfolio file at {json_file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in gauge portfolio file at {json_file_path}")
    except Exception as e:
        raise Exception(f"Error loading gauge portfolio: {str(e)}")


def generate_gauge_floodts_json(output_file: str = None, 
                               input_portfolio_file: str = None,
                               cdm_validation: bool = True,
                               simulation_params: Dict[str, Any] = None) -> None:
    """
    Generate the gauge_floodts.json file with a simulated flood event.
    FIXED VERSION: Creates correct structure for _load_gauge_readings()
    
    Args:
        output_file: Path to output JSON file (if None, uses input_dir/gauge_floodts.json)
        input_portfolio_file: Path to the input gauge portfolio JSON file
        cdm_validation: Whether to validate the gauge data using CDM
        simulation_params: Dictionary of simulation parameters (optional)
    """
    print("=" * 60)
    print("FLOOD SIMULATION GENERATOR (FIXED VERSION)")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print(f"Current file: {current_file}")
    print(f"Input directory: {input_dir}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Set default output file
    if output_file is None:
        output_file = input_dir / 'gauge_floodts.json'
    else:
        output_file = Path(output_file)
        if not output_file.is_absolute():
            output_file = input_dir / output_file
    
    try:
        # Load gauge portfolio from file with CDM validation
        gauge_portfolio = load_gauge_portfolio(input_portfolio_file, validate=cdm_validation)
        
        # Get simulation parameters
        if simulation_params is None:
            simulation_params = params
        
        simulation_hours = simulation_params.get('simulation_hours', 72)
        start_time = simulation_params.get('simulation_start_date', datetime.datetime.now())
        
        gauges = gauge_portfolio.get('flood_gauges', [])
        print(f"Generating simulation for {len(gauges)} gauges over {simulation_hours} hours...")
        
        # FIXED: Create the correct structure that _load_gauge_readings() expects
        time_series_data = []
        
        for hour in range(simulation_hours):
            # Create timestamp for this hour
            current_time = start_time + datetime.timedelta(hours=hour)
            timestamp = current_time.isoformat()
            
            # Create readings array for this timestep
            readings = []
            
            for i, gauge in enumerate(gauges):
                try:
                    gauge_header = gauge['FloodGauge']['Header']
                    gauge_stage = gauge['FloodGauge']['FloodStage']['UK']
                    
                    gauge_id = gauge_header['GaugeID']
                    
                    # Get flood levels from the gauge data
                    alert_level = gauge_stage['FloodAlert']
                    warning_level = gauge_stage['FloodWarning'] 
                    severe_level = gauge_stage['SevereFloodWarning']
                    
                    # Generate realistic water level based on flood simulation
                    base_level = alert_level - 1.0  # Start below alert level
                    
                    # Create a flood wave that peaks around hour 24-36
                    peak_hour = 30 + (i * 2)  # Stagger peaks for different gauges
                    
                    if hour < peak_hour - 12:
                        # Rising phase
                        progress = hour / (peak_hour - 12)
                        amplitude = 0.5 + (progress * 1.5)
                    elif hour < peak_hour + 12:
                        # Peak phase
                        progress = abs(hour - peak_hour) / 12
                        amplitude = 2.0 - (progress * 0.5)
                    else:
                        # Recession phase
                        progress = (hour - peak_hour - 12) / (simulation_hours - peak_hour - 12)
                        amplitude = 1.5 * (1 - progress)
                    
                    # Add some random variation
                    variation = math.sin((hour + i) * 0.3) * 0.2
                    water_level = base_level + amplitude + variation
                    
                    # Determine alert status based on water level
                    if water_level >= severe_level:
                        alert_status = "Severe Flood Warning"
                    elif water_level >= warning_level:
                        alert_status = "Flood Warning"
                    elif water_level >= alert_level:
                        alert_status = "Flood Alert"
                    else:
                        alert_status = "Normal"
                    
                    # FIXED: Create reading with correct field names and structure
                    reading = {
                        'gaugeId': gauge_id,  # FIXED: Changed from 'gauge_id' to 'gaugeId'
                        'timestamp': timestamp,  # FIXED: Added timestamp
                        'waterLevel': round(water_level, 2),  # FIXED: Changed from 'water_level' to 'waterLevel'
                        'alertLevel': alert_level,  # FIXED: Added alertLevel
                        'warningLevel': warning_level,  # FIXED: Added warningLevel  
                        'severeLevel': severe_level,  # FIXED: Added severeLevel
                        'alertStatus': alert_status  # FIXED: Added alertStatus
                    }
                    
                    readings.append(reading)
                    
                except Exception as e:
                    print(f"Error processing gauge {i}: {e}")
                    continue
            
            # FIXED: Wrap readings in the expected structure
            timestep_data = {
                'readings': readings
            }
            time_series_data.append(timestep_data)
        
        # Write to JSON file
        print(f"Writing output to: {output_file}")
        with open(output_file, 'w') as f:
            json.dump(time_series_data, f, indent=2)
        
        # Verify the file was created correctly
        if output_file.exists():
            file_size = output_file.stat().st_size
            print(f"✓ Successfully created {output_file} ({file_size} bytes)")
            
            # Quick verification
            with open(output_file, 'r') as f:
                test_data = json.load(f)
            
            if test_data and len(test_data) > 0:
                print(f"✓ Verification successful: {len(test_data)} timesteps generated")
                if 'readings' in test_data[0] and len(test_data[0]['readings']) > 0:
                    sample_reading = test_data[0]['readings'][0]
                    print(f"✓ Sample reading structure: {list(sample_reading.keys())}")
                    print(f"✓ Sample data: gaugeId={sample_reading.get('gaugeId')}, waterLevel={sample_reading.get('waterLevel')}, status={sample_reading.get('alertStatus')}")
                    
                    # Count total readings across all timesteps
                    total_readings = sum(len(timestep.get('readings', [])) for timestep in test_data)
                    print(f"✓ Total readings generated: {total_readings}")
                else:
                    print("⚠ Warning: Timesteps have no readings")
            else:
                print("✗ Verification failed: No data in output file")
        else:
            print("✗ Error: Output file was not created")
            
    except Exception as e:
        print(f"✗ SIMULATION FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Generate the JSON file with corrected paths
    generate_gauge_floodts_json()