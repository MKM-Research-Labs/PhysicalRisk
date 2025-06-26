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
Gauge report generation integration - Fixed version.
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
        print(f"[STATUS] Starting gauge report generation for: {gauge_id}")
        
        # Step 1: Validate input files
        print(f"[STATUS] Validating gauge file: {gauge_file}")
        if not gauge_file.exists():
            print(f"[ERROR] Gauge file not found: {gauge_file}")
            return None
        
        # Step 2: Load gauge data
        print(f"[STATUS] Loading gauge data from file...")
        with open(gauge_file) as f:
            gauge_data = json.load(f)
        
        print(f"[STATUS] Successfully loaded gauge data")
        
        # Step 3: Find the specific gauge - Handle both possible JSON structures
        print(f"[STATUS] Searching for gauge ID: {gauge_id}")
        gauges = gauge_data.get('floodGauges', gauge_data.get('flood_gauges', []))
        target_gauge = None
        
        for gauge in gauges:
            g_id = gauge.get('FloodGauge', {}).get('Header', {}).get('GaugeID')
            if g_id == gauge_id:
                target_gauge = gauge.get('FloodGauge', {})
                break
        
        if not target_gauge:
            print(f"[ERROR] Gauge {gauge_id} not found in data")
            # Debug: Show available gauges
            available_ids = [g.get('FloodGauge', {}).get('Header', {}).get('GaugeID') for g in gauges]
            print(f"[DEBUG] Available gauge IDs: {available_ids}")
            return None
        
        print(f"[STATUS] Found gauge data for: {gauge_id}")
        
        # Step 4: Prepare output directory
        print(f"[STATUS] Creating output directory: {output_dir}")
        output_dir.mkdir(exist_ok=True)
        
        # Step 5: Generate report content
        print(f"[STATUS] Generating report content...")
        report_file = output_dir / f"gauge_report_{gauge_id}.txt"
        
        print(f"[STATUS] Writing report to: {report_file}")
        with open(report_file, 'w') as f:
            f.write(f"FLOOD GAUGE REPORT\n")
            f.write(f"==================\n\n")
            f.write(f"Report Generated: {Path(__file__).name}\n")
            f.write(f"Gauge ID: {gauge_id}\n")
            
            # Gauge header information
            header = target_gauge.get('Header', {})
            f.write(f"Gauge Name: {header.get('GaugeName', 'Unknown')}\n")
            f.write(f"Created Date: {header.get('createdDate', 'Unknown')}\n")
            f.write(f"Last Modified: {header.get('lastModifiedDate', 'Unknown')}\n")
            
            # Gauge details
            gauge_info = target_gauge.get('SensorDetails', {}).get('GaugeInformation', {})
            f.write(f"\nGAUGE INFORMATION:\n")
            f.write(f"Type: {gauge_info.get('GaugeType', 'Unknown')}\n")
            f.write(f"Owner: {gauge_info.get('GaugeOwner', 'Unknown')}\n")
            f.write(f"Status: {gauge_info.get('OperationalStatus', 'Unknown')}\n")
            f.write(f"Installation Date: {gauge_info.get('InstallationDate', 'N/A')}\n")
            f.write(f"Location: {gauge_info.get('GaugeLatitude', 'N/A')}°N, {gauge_info.get('GaugeLongitude', 'N/A')}°E\n")
            f.write(f"Datum: {gauge_info.get('GaugeDatum', 'N/A')}\n")
            
            # Flood thresholds
            flood_stage = target_gauge.get('FloodStage', {}).get('UK', {})
            f.write(f"\nFLOOD THRESHOLDS (UK):\n")
            f.write(f"Alert Level: {flood_stage.get('FloodAlert', 'N/A')} m\n")
            f.write(f"Warning Level: {flood_stage.get('FloodWarning', 'N/A')} m\n")
            f.write(f"Severe Warning: {flood_stage.get('SevereFloodWarning', 'N/A')} m\n")
            
            # Historical data
            stats = target_gauge.get('SensorStats', {})
            f.write(f"\nHISTORICAL DATA:\n")
            f.write(f"Historical High Level: {stats.get('HistoricalHighLevel', 'N/A')} m\n")
            f.write(f"High Date: {stats.get('HistoricalHighDate', 'N/A')}\n")
            f.write(f"Historical Low Level: {stats.get('HistoricalLowLevel', 'N/A')} m\n")
            f.write(f"Low Date: {stats.get('HistoricalLowDate', 'N/A')}\n")
            f.write(f"Average Level: {stats.get('AverageLevel', 'N/A')} m\n")
            
            # Sensor specifications
            sensor_specs = target_gauge.get('SensorDetails', {}).get('SensorSpecifications', {})
            f.write(f"\nSENSOR SPECIFICATIONS:\n")
            f.write(f"Manufacturer: {sensor_specs.get('Manufacturer', 'N/A')}\n")
            f.write(f"Model: {sensor_specs.get('Model', 'N/A')}\n")
            f.write(f"Accuracy: {sensor_specs.get('Accuracy', 'N/A')}\n")
            f.write(f"Range: {sensor_specs.get('Range', 'N/A')}\n")
            f.write(f"Resolution: {sensor_specs.get('Resolution', 'N/A')}\n")
            
            f.write(f"\n--- Report Creation Complete ---\n")
            f.write(f"This report was successfully generated by the gauge report integration system.\n")
            f.write(f"Report file: {report_file.name}\n")
        
        print(f"[SUCCESS] Gauge report successfully created at: {report_file}")
        print(f"[STATUS] Report generation completed successfully")
        return report_file
        
    except Exception as e:
        print(f"[ERROR] Failed to generate gauge report: {e}")
        import traceback
        traceback.print_exc()
        return None


def validate_gauge_exists(gauge_id: str, gauge_file: Path) -> bool:
    """
    Validate that a gauge exists in the portfolio file.
    
    Args:
        gauge_id: ID of the gauge to validate
        gauge_file: Path to gauge portfolio JSON file
        
    Returns:
        True if gauge exists, False otherwise
    """
    try:
        print(f"[STATUS] Validating gauge existence: {gauge_id}")
        
        if not gauge_file.exists():
            print(f"[ERROR] Gauge file not found: {gauge_file}")
            return False
            
        with open(gauge_file) as f:
            gauge_data = json.load(f)
        
        # Handle both possible JSON structure keys
        gauges = gauge_data.get('floodGauges', gauge_data.get('flood_gauges', []))
        
        for gauge in gauges:
            g_id = gauge.get('FloodGauge', {}).get('Header', {}).get('GaugeID')
            if g_id == gauge_id:
                print(f"[SUCCESS] Gauge {gauge_id} found in portfolio")
                return True
        
        print(f"[WARNING] Gauge {gauge_id} not found in portfolio")
        return False
        
    except Exception as e:
        print(f"[ERROR] Error validating gauge: {e}")
        return False


def get_available_gauges(gauge_file: Path) -> list:
    """
    Get list of available gauge IDs from the portfolio file.
    
    Args:
        gauge_file: Path to gauge portfolio JSON file
        
    Returns:
        List of available gauge IDs
    """
    try:
        print(f"[STATUS] Retrieving available gauges from: {gauge_file}")
        
        if not gauge_file.exists():
            print(f"[ERROR] Gauge file not found: {gauge_file}")
            return []
            
        with open(gauge_file) as f:
            gauge_data = json.load(f)
        
        # Handle both possible JSON structure keys
        gauges = gauge_data.get('floodGauges', gauge_data.get('flood_gauges', []))
        gauge_ids = []
        
        for gauge in gauges:
            g_id = gauge.get('FloodGauge', {}).get('Header', {}).get('GaugeID')
            if g_id:
                gauge_ids.append(g_id)
        
        print(f"[SUCCESS] Found {len(gauge_ids)} available gauges")
        return gauge_ids
        
    except Exception as e:
        print(f"[ERROR] Error retrieving gauge list: {e}")
        return []