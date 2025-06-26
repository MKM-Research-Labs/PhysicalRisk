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
Tropical Cyclone Event Time Series Portfolio Generator.

This module generates synthetic tropical cyclone event time series data
based on the TCEventTSCDM schema with an oscillating path.
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import numpy as np
import sys


# Fix the Python path to find project modules
current_file = Path(__file__).resolve()
# Navigate up to find project root (assuming we're in src/portfolio or similar)
project_root = current_file.parent.parent

# Add project root to Python's path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import modules using absolute imports
from utilities.project_paths import ProjectPaths

paths = ProjectPaths(__file__)
paths.setup_import_paths()

# Import CDM models
from cdm.tc_event_ts_cdm import TCEventTSCDM

class TCEventTSPortfolioGenerator:
    """Generates synthetic tropical cyclone event time series data."""
    
    def __init__(self, output_dir: Union[str, Path]):
        """
        Initialize the TC Event Time Series Portfolio Generator.
        
        Args:
            output_dir: Directory to save generated files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tc_event_ts_cdm = TCEventTSCDM()
        
    def generate(self, tc_events_data: Union[Dict, int] = None, num_steps: int = 100) -> Dict:
        """
        Generate synthetic tropical cyclone event time series data
        based on TCEventTSCDM schema with oscillating path.
    
        Args:
            tc_events_data: Dictionary containing TC events data from TCEventPortfolioGenerator
                            or number of TC events to generate
            num_steps: Number of time steps to generate
        
        Returns:
            Dictionary containing generated data and file path
        """
        # Check if this is a count instead of data
        if isinstance(tc_events_data, int):
            # Generate some mock TC event data
            count = tc_events_data
            tc_events = []
            tc_event_ids = []
        
            for i in range(count):
                event_id = f"TC-EVENT-{str(uuid.uuid4())[:8]}"
                tc_events.append({
                    "event_id": event_id,
                    "name": f"Cyclone {chr(65 + i)}",  # A, B, C, etc.
                    "type": "Tropical Cyclone"
                })
                tc_event_ids.append(event_id)
            
            # Save to file
            output_path = self.output_dir / "tc_events.json"
            with open(output_path, 'w') as f:
                json.dump({"tc_events": tc_events}, f, indent=2)
            
            print(f"Generated {count} TC events, saved to: {output_path}")
        
            return {
                "data": {
                    "tc_events": tc_events,
                    "tc_event_ids": tc_event_ids
                },
                "file_path": output_path
            }
    
        # Original functionality for generating time series
        print("Generating TC event time series data with oscillating path...")
    
        # Check if TC events are available
        if not tc_events_data or "tc_event_ids" not in tc_events_data:
            raise ValueError("TC events must be generated before time series")
                
        # Take the first TC event for time series
        tc_event_id = tc_events_data["tc_event_ids"][0]
    
        # Generate time series with oscillating path
        ts_data = self._generate_oscillating_timeseries(tc_event_id, num_steps)
    
        # Save to JSON file
        output_path = self.output_dir / "single_tceventts.json"
        with open(output_path, 'w') as f:
            json.dump(ts_data, f, indent=2)
            
        print(f"TC event time series data saved to: {output_path}")
    
        return {
            "data": ts_data,
            "file_path": output_path
        }
    def _generate_tc_events(self, count: int = 2) -> Dict:
        """Generate synthetic tropical cyclone events."""
        print(f"Generating {count} TC events...")
    
        tc_events = []
        tc_event_ids = []
    
        for i in range(count):
            # Generate a unique ID for the event
            event_id = f"TC-EVENT-{str(uuid.uuid4())[:8]}"
            tc_event_ids.append(event_id)
        
            # Create a simple TC event structure
            tc_event = {
                "event_id": event_id,
                "name": f"Cyclone {chr(65 + i)}",  # A, B, C, etc.
                "type": "Tropical Cyclone",
                "start_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
                "end_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
            }
        
            tc_events.append(tc_event)
    
        # Save to JSON file
        output_path = self.output_dir / "tc_events.json"
        with open(output_path, 'w') as f:
            json.dump({"tc_events": tc_events}, f, indent=2)
        
        print(f"TC events data saved to: {output_path}")
    
        return {
            "data": {
                "tc_events": tc_events,
                "tc_event_ids": tc_event_ids
            },
            "file_path": output_path
        }

    def _generate_tc_event_timeseries(self, tc_events_data: Dict, num_steps: int = 100) -> Dict:
        """
        Generate synthetic tropical cyclone event time series data
        based on TCEventTSCDM schema with oscillating path.
    
        Args:
            tc_events_data: Dictionary containing TC events data
            num_steps: Number of time steps to generate
        
        Returns:
            Dictionary containing generated data and file path
        """
        print("Generating TC event time series data with oscillating path...")
    
        # Check if TC events are available
        if not tc_events_data or "tc_event_ids" not in tc_events_data:
            raise ValueError("TC events must be generated before time series")
            
        # Take the first TC event for time series
        tc_event_id = tc_events_data["tc_event_ids"][0]
    
        # Generate time series with oscillating path
        ts_data = self._generate_oscillating_timeseries(tc_event_id, num_steps)
    
        # Save to JSON file - without v1 suffix as requested
        output_path = self.output_dir / "single_tceventts.json"
        with open(output_path, 'w') as f:
            json.dump(ts_data, f, indent=2)
        
        print(f"TC event time series data saved to: {output_path}")
    
        return {
            "data": ts_data,
            "file_path": output_path
        }
    
    def _generate_oscillating_timeseries(self, tc_event_id: str, num_steps: int) -> Dict:
        """Generate a TC event timeseries with an oscillating path."""
        # Define start and end points for the TC event path
        start_point = {"name": "Clifton Suspension Bridge", "lat": 51.455017, "lon": -2.628114}
        end_point = {"name": "Margate", "lat": 51.38132, "lon": 1.38617}
        
        # Generate path coordinates with oscillation
        t = np.linspace(0, 1, num_steps)
        
        # Add oscillation using sine waves (similar to TCEvent_event_v1.py)
        variation_lat = 0.08 * np.sin(3 * np.pi * t)  
        variation_lon = 0.12 * np.sin(2 * np.pi * t)
        
        # Calculate path with variations
        lat_steps = start_point["lat"] + (end_point["lat"] - start_point["lat"]) * t + variation_lat
        lon_steps = start_point["lon"] + (end_point["lon"] - start_point["lon"]) * t + variation_lon
        
        # Generate time series entries
        timeseries_entries = []
        for i in range(num_steps):
            # Generate a single time step
            ts_entry = self._generate_single_timestep(tc_event_id, i, num_steps, lat_steps[i], lon_steps[i])
            timeseries_entries.append(ts_entry)
        
        # Create the complete time series data
        return {
            "event_id": tc_event_id,
            "description": f"Time series data for TC Event {tc_event_id} from {start_point['name']} to {end_point['name']}",
            "timeseries": timeseries_entries
        }
    
    def _generate_single_timestep(self, tc_event_id: str, index: int, num_steps: int, lat: float, lon: float) -> Dict:
        """Generate a single time step for the time series."""
        # Access the schema
        schema = self.tc_event_ts_cdm.schema
        
        # Build time series entry recursively based on schema
        ts_entry = self._build_section(schema, index, num_steps, lat, lon, None, tc_event_id)
        
        # Ensure specific fields are set correctly
        if "EventTimeseries" in ts_entry:
            # Update coordinates to follow the path
            if "Dimensions" in ts_entry["EventTimeseries"]:
                ts_entry["EventTimeseries"]["Dimensions"]["lat"] = lat
                ts_entry["EventTimeseries"]["Dimensions"]["lon"] = lon
            
            # Set event_id and time correctly
            if "Header" in ts_entry["EventTimeseries"]:
                ts_entry["EventTimeseries"]["Header"]["event_id"] = tc_event_id
                ts_entry["EventTimeseries"]["Header"]["time"] = (datetime.now() - timedelta(days=5) + timedelta(hours=index/2)).strftime("%Y-%m-%dT%H:%M:%SZ")
                ts_entry["EventTimeseries"]["Header"]["lead_time"] = index
        
        return ts_entry
    
    def _build_section(self, section_schema: Dict, index: int, num_steps: int, lat: float, lon: float, parent_name: str = None, tc_event_id: str = None) -> Dict:
        """Recursively build a section of time series data."""
        section_data = {}
        for field_name, field_def in section_schema.items():
            if isinstance(field_def, dict) and not field_def.get("type"):
                # This is a nested section
                section_data[field_name] = self._build_section(field_def, index, num_steps, lat, lon, field_name, tc_event_id)
            else:
                # This is a field
                value = self._generate_value(field_def, index, num_steps, field_name, parent_name, lat, lon, tc_event_id)
                if value is not None:
                    section_data[field_name] = value
        return section_data
    
    def _generate_value(self, field_def, index, num_steps, field_name=None, parent_name=None, lat=None, lon=None, tc_event_id=None):
        """Generate a value for a field based on its definition with oscillation patterns."""
        progress = index / num_steps  # Used for simulating progression through storm lifecycle
        
        if isinstance(field_def, dict):
            if "type" in field_def:
                field_type = field_def["type"]
                
                if field_type == "menu" or field_type == "enum":
                    options = field_def.get("options", field_def.get("values", []))
                    if options:
                        return options[index % len(options)]
                elif field_type == "boolean":
                    return index % 3 == 0
                elif field_type == "decimal":
                    # Special handling based on field name and parent context
                    if parent_name == "SurfaceNearSurface":
                        if field_name and "t2m" in field_name:
                            return 298 - (index * 0.2 / num_steps)
                        elif field_name and "sp" in field_name:
                            # Pressure oscillates with the storm lifecycle
                            return 95000 + 3000 * np.sin(np.pi * progress)
                        elif field_name and "msl" in field_name:
                            # Decreasing pressure as storm intensifies, then increasing
                            return 95000 - 4000 * np.sin(np.pi * progress)
                        elif field_name and "tcwv" in field_name:
                            return 40 + 10 * np.sin(2 * np.pi * progress)
                        elif field_name and ("u" in field_name or "v" in field_name):
                            # Wind speed increases then decreases with oscillations
                            return 15 + 20 * np.sin(np.pi * progress) + 5 * np.sin(4 * np.pi * progress)
                        elif field_name and "tp" in field_name:
                            # Precipitation with multiple oscillation patterns
                            return 0.05 + 0.1 * np.sin(np.pi * progress) * (1 + 0.3 * np.sin(4 * np.pi * progress))
                        else:
                            return 0.01 + 0.03 * np.sin(2 * np.pi * progress)
                            
                    elif parent_name and "hPa" in parent_name:
                        if field_name and ("u" in field_name or "v" in field_name):
                            return 20 + 15 * np.sin(np.pi * progress + 0.2)
                        elif field_name and "t" in field_name:
                            level = int(''.join(filter(str.isdigit, field_name)))
                            return 298 - (level/10) - 2 * np.sin(np.pi * progress)
                        elif field_name and "z" in field_name:
                            level = int(''.join(filter(str.isdigit, field_name)))
                            return level * 10 + 200 * np.sin(0.5 * np.pi * progress)
                        elif field_name and "r" in field_name:
                            return 70 + 20 * np.sin(3 * np.pi * progress)
                            
                    elif parent_name == "Dimensions":
                        if field_name and "mrr" in field_name:
                            # Radius of maximum winds varies with oscillation - smaller size
                            return 30 - 10 * np.sin(np.pi * progress)
                        elif field_name and "lat" in field_name and lat is not None:
                            return lat
                        elif field_name and "lon" in field_name and lon is not None:
                            return lon
                            
                    elif parent_name == "CycloneParameters":
                        if field_name and "direction" in field_name:
                            # Direction shifts as the storm moves
                            return 45 + 30 * np.sin(2 * np.pi * progress)
                        elif field_name and "storm_size" in field_name:
                            # Reduced storm size with oscillation
                            return 120 + 20 * np.sin(2 * np.pi * progress)
                        elif field_name and "intensity_change" in field_name:
                            # Intensity changes with multiple oscillations
                            return 5 * np.sin(2 * np.pi * progress) + 2 * np.sin(5 * np.pi * progress)
                        elif field_name and "pressure_change" in field_name:
                            # Pressure changes with oscillation
                            return -3 * np.sin(2 * np.pi * progress) - np.sin(4 * np.pi * progress)
                            
                    return 10.0 + 5.0 * np.sin(2 * np.pi * progress)
                    
                elif field_type == "integer":
                    if field_name and "lead_time" in field_name:
                        return index
                    return 10 + (index % 20)
                    
                elif field_type == "datetime":
                    # Start 5 days ago and progress hourly
                    return (datetime.now() - timedelta(days=5) + timedelta(hours=index/2)).strftime("%Y-%m-%dT%H:%M:%SZ")
                    
                elif field_type == "text":
                    if field_name and "event_id" in field_name:
                        return tc_event_id
                    return f"Text-{index}"
                    
        # Default fallback
        return f"Value-{index}"