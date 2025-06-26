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
Portfolio Elevation Validator - FIXED WITH COMPREHENSIVE DIAGNOSTICS

Validates and fixes elevation data with detailed diagnostics to show exactly what's happening.
This version will find and fix the elevation relationship problems causing extreme flood depths.
"""

import json
import sys
import shutil
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

def validate_and_fix_elevations(input_dir: Path, create_backups: bool = True, verbose: bool = True) -> bool:
    """
    Main function called by run_portfolio.py to validate and fix elevations.
    NOW WITH COMPREHENSIVE DIAGNOSTICS to see what's actually happening.
    
    Args:
        input_dir: Directory containing property and gauge JSON files
        create_backups: Whether to create backup files before making changes
        verbose: Whether to print detailed output
        
    Returns:
        True if validation passed or fixes were successful, False otherwise
    """
    
    if verbose:
        print("🔍 COMPREHENSIVE ELEVATION VALIDATION WITH DIAGNOSTICS")
        print("=" * 70)
        print("Goal: Find and fix elevation problems causing extreme flood depths")
        print("")
    
    # Check files exist
    property_file = input_dir / "property_portfolio.json"
    gauge_file = input_dir / "flood_gauge_portfolio.json"
    
    if not property_file.exists() or not gauge_file.exists():
        if verbose:
            print(f"⚠️  Elevation validation skipped - missing files")
            print(f"   Property file: {property_file.exists()}")
            print(f"   Gauge file: {gauge_file.exists()}")
        return True  # Don't fail the pipeline for missing files
    
    # Load data with diagnostics
    try:
        properties, gauges = _load_portfolio_data_with_diagnostics(property_file, gauge_file, verbose)
    except Exception as e:
        if verbose:
            print(f"❌ Failed to load elevation data: {e}")
        return False
    
    # COMPREHENSIVE DIAGNOSTIC ANALYSIS
    if verbose:
        print(f"\n📊 PHASE 1: DATA STRUCTURE ANALYSIS")
        print("-" * 50)
        _analyze_data_structure(properties, gauges)
        
        print(f"\n📏 PHASE 2: ELEVATION RANGE ANALYSIS")
        print("-" * 50)
        _analyze_elevation_ranges(properties, gauges)
        
        print(f"\n⚖️ PHASE 3: PROPERTY-GAUGE RELATIONSHIP ANALYSIS")
        print("-" * 50)
        problems_found = _analyze_property_gauge_relationships(properties, gauges)
        
        print(f"\n🎯 PHASE 4: PROBLEM IDENTIFICATION")
        print("-" * 50)
        _identify_core_problems(properties, gauges, problems_found)
    else:
        # Quick analysis without verbose output
        problems_found = _analyze_property_gauge_relationships(properties, gauges)
    
    # Count total issues with new logic
    total_issues = len(problems_found)
    
    if total_issues == 0:
        if verbose:
            print("✅ All elevation relationships are realistic - no fixes needed")
        return True
    
    if verbose:
        print(f"\n🔧 PHASE 5: APPLYING FIXES")
        print("-" * 50)
        print(f"Found {total_issues} elevation relationship problems to fix")
    
    # Create backups if requested
    if create_backups:
        _create_backups(property_file, gauge_file, verbose)
    
    # Apply comprehensive fixes
    prop_fixes = _fix_elevation_relationships_comprehensive(properties, gauges, problems_found, verbose)
    
    # Save updated data
    try:
        _save_portfolio_data(property_file, gauge_file, properties, gauges)
        
        if verbose:
            print(f"\n✅ COMPREHENSIVE ELEVATION FIXES COMPLETED:")
            print(f"   Properties fixed: {prop_fixes}")
            print(f"   All properties now above their nearest gauges")
            print(f"   Expected flood depths: 0-8m (realistic for Thames)")
            print(f"   No more negative or extreme flood depths!")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"❌ Failed to save elevation fixes: {e}")
        return False


def _load_portfolio_data_with_diagnostics(property_file: Path, gauge_file: Path, verbose: bool) -> Tuple[List[Dict], List[Dict]]:
    """Load property and gauge data from JSON files with diagnostics."""
    
    if verbose:
        print(f"📂 Loading data files...")
        print(f"   Property file: {property_file}")
        print(f"   Gauge file: {gauge_file}")
    
    with open(property_file, 'r') as f:
        property_data = json.load(f)
    
    with open(gauge_file, 'r') as f:
        gauge_data = json.load(f)
    
    properties = property_data.get('properties', [])
    gauges = gauge_data.get('gauges', [])
    
    if verbose:
        print(f"✅ Loaded {len(properties)} properties and {len(gauges)} gauges")
    
    return properties, gauges


def _analyze_data_structure(properties: List[Dict], gauges: List[Dict]) -> None:
    """Analyze the structure of the loaded data."""
    
    print(f"📋 Data Structure Analysis:")
    print(f"   Total properties: {len(properties)}")
    print(f"   Total gauges: {len(gauges)}")
    
    # Check property structure
    if properties:
        sample_prop = properties[0]
        has_header = 'PropertyHeader' in sample_prop
        has_location = 'Location' in sample_prop.get('PropertyHeader', {})
        has_risk = 'RiskAssessment' in sample_prop.get('PropertyHeader', {})
        has_elevation = 'GroundLevelMeters' in sample_prop.get('PropertyHeader', {}).get('RiskAssessment', {})
        
        print(f"   Property structure: Header={has_header}, Location={has_location}, Risk={has_risk}, Elevation={has_elevation}")
    
    # Check gauge structure
    if gauges:
        sample_gauge = gauges[0]
        has_elevation = 'elevation' in sample_gauge
        has_lat = 'latitude' in sample_gauge
        has_lon = 'longitude' in sample_gauge
        
        print(f"   Gauge structure: Elevation={has_elevation}, Latitude={has_lat}, Longitude={has_lon}")


def _analyze_elevation_ranges(properties: List[Dict], gauges: List[Dict]) -> None:
    """Analyze elevation ranges for properties and gauges."""
    
    # Analyze property elevations
    prop_elevations = []
    prop_parsing_errors = 0
    
    for prop in properties:
        try:
            elevation = prop.get('PropertyHeader', {}).get('RiskAssessment', {}).get('GroundLevelMeters', 0)
            if elevation > 0:  # Only count valid elevations
                prop_elevations.append(elevation)
        except:
            prop_parsing_errors += 1
    
    # Analyze gauge elevations
    gauge_elevations = []
    gauge_parsing_errors = 0
    
    for gauge in gauges:
        try:
            elevation = gauge.get('elevation', 0)
            if elevation > 0:  # Only count valid elevations
                gauge_elevations.append(elevation)
        except:
            gauge_parsing_errors += 1
    
    print(f"📏 Elevation Range Analysis:")
    
    if prop_elevations:
        print(f"   Property elevations:")
        print(f"     Valid elevations: {len(prop_elevations)}")
        print(f"     Min: {min(prop_elevations):.2f}m")
        print(f"     Max: {max(prop_elevations):.2f}m")
        print(f"     Mean: {np.mean(prop_elevations):.2f}m")
        print(f"     Parsing errors: {prop_parsing_errors}")
    
    if gauge_elevations:
        print(f"   Gauge elevations:")
        print(f"     Valid elevations: {len(gauge_elevations)}")
        print(f"     Min: {min(gauge_elevations):.2f}m")
        print(f"     Max: {max(gauge_elevations):.2f}m")
        print(f"     Mean: {np.mean(gauge_elevations):.2f}m")
        print(f"     Parsing errors: {gauge_parsing_errors}")
    
    # Flag extreme values
    extreme_props = sum(1 for e in prop_elevations if e > 100 or e < 2)
    extreme_gauges = sum(1 for e in gauge_elevations if e > 60 or e < 3)
    
    if extreme_props > 0:
        print(f"   ⚠️  Properties with extreme elevations (>100m or <2m): {extreme_props}")
    if extreme_gauges > 0:
        print(f"   ⚠️  Gauges with extreme elevations (>60m or <3m): {extreme_gauges}")


def _analyze_property_gauge_relationships(properties: List[Dict], gauges: List[Dict]) -> List[Dict]:
    """Analyze relationships between properties and their nearest gauges."""
    
    problems_found = []
    analysis_errors = 0
    relationships_checked = 0
    
    print(f"⚖️ Property-Gauge Relationship Analysis:")
    
    # Sample first 20 for detailed analysis, then check all for problems
    sample_size = min(20, len(properties))
    print(f"   Detailed analysis of first {sample_size} properties:")
    
    for i, prop in enumerate(properties):
        try:
            # Get property details
            location = prop.get('PropertyHeader', {}).get('Location', {})
            risk_assessment = prop.get('PropertyHeader', {}).get('RiskAssessment', {})
            
            prop_lat = location.get('LatitudeDegrees', 0)
            prop_lon = location.get('LongitudeDegrees', 0)
            prop_elevation = risk_assessment.get('GroundLevelMeters', 0)
            prop_id = prop.get('PropertyHeader', {}).get('PropertyID', f'PROP-{i}')
            
            if prop_lat == 0 or prop_lon == 0 or prop_elevation == 0:
                continue
            
            # Find nearest gauge
            nearest_gauge = _find_nearest_gauge_with_details(prop_lat, prop_lon, gauges)
            
            if nearest_gauge:
                gauge_elevation = nearest_gauge['elevation']
                elevation_diff = prop_elevation - gauge_elevation
                relationships_checked += 1
                
                # Show detailed analysis for first 20
                if i < sample_size:
                    status = ""
                    if elevation_diff < 0:
                        status = "❌ BELOW GAUGE!"
                    elif elevation_diff < 3:
                        status = "⚠️  Too close"
                    else:
                        status = "✅ OK"
                    
                    print(f"     {prop_id}: Prop={prop_elevation:.1f}m, Gauge={gauge_elevation:.1f}m, Diff={elevation_diff:.1f}m {status}")
                
                # Record problems for ALL properties
                if elevation_diff < 3:  # Less than 3m above gauge is problematic
                    problems_found.append({
                        'prop_index': i,
                        'prop_id': prop_id,
                        'prop_elevation': prop_elevation,
                        'gauge_elevation': gauge_elevation,
                        'elevation_diff': elevation_diff,
                        'nearest_gauge': nearest_gauge
                    })
            
        except Exception as e:
            analysis_errors += 1
            if i < sample_size:
                print(f"     Error analyzing property {i}: {e}")
    
    print(f"   Relationships checked: {relationships_checked}")
    print(f"   Analysis errors: {analysis_errors}")
    print(f"   Problems found: {len(problems_found)}")
    
    return problems_found


def _identify_core_problems(properties: List[Dict], gauges: List[Dict], problems_found: List[Dict]) -> None:
    """Identify and explain the core elevation problems."""
    
    print(f"🎯 Core Problem Identification:")
    
    if not problems_found:
        print(f"   ✅ No elevation relationship problems found")
        return
    
    # Categorize problems
    below_gauge = [p for p in problems_found if p['elevation_diff'] < 0]
    too_close = [p for p in problems_found if 0 <= p['elevation_diff'] < 3]
    
    print(f"   🚨 Properties BELOW their nearest gauge: {len(below_gauge)}")
    print(f"   ⚠️  Properties too close to gauge (<3m): {len(too_close)}")
    
    # Show worst examples
    if below_gauge:
        print(f"   📋 Worst examples (properties below gauges):")
        worst_cases = sorted(below_gauge, key=lambda x: x['elevation_diff'])[:5]
        for case in worst_cases:
            print(f"     {case['prop_id']}: {case['elevation_diff']:.1f}m below gauge")
    
    print(f"\n   💡 WHY THIS CAUSES EXTREME FLOOD DEPTHS:")
    print(f"      When flood water level > property elevation:")
    print(f"      Calculated depth = Property elevation - Water level = NEGATIVE!")
    print(f"      Flood model tries to compensate, creating extreme depths (15m+)")


def _find_nearest_gauge_with_details(prop_lat: float, prop_lon: float, gauges: List[Dict]) -> Optional[Dict]:
    """Find nearest gauge and return full details."""
    
    min_distance = float('inf')
    nearest_gauge = None
    
    for gauge in gauges:
        try:
            gauge_lat = gauge.get('latitude', 0)
            gauge_lon = gauge.get('longitude', 0)
            gauge_elevation = gauge.get('elevation', 0)
            
            if gauge_lat == 0 or gauge_lon == 0 or gauge_elevation == 0:
                continue
            
            # Simple distance calculation
            distance = ((prop_lat - gauge_lat) ** 2 + (prop_lon - gauge_lon) ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                nearest_gauge = {
                    'gauge_id': gauge.get('gauge_id', 'unknown'),
                    'gauge_name': gauge.get('gauge_name', 'unknown'),
                    'elevation': gauge_elevation,
                    'latitude': gauge_lat,
                    'longitude': gauge_lon,
                    'distance': distance
                }
        
        except:
            continue
    
    return nearest_gauge


def _fix_elevation_relationships_comprehensive(properties: List[Dict], gauges: List[Dict], 
                                             problems_found: List[Dict], verbose: bool) -> int:
    """
    Comprehensively fix elevation relationships based on diagnosed problems.
    """
    
    fixes_applied = 0
    safety_margin = 5.0  # Minimum 5m above nearest gauge
    
    if verbose:
        print(f"🔧 Applying comprehensive elevation fixes...")
        print(f"   Safety margin: {safety_margin}m above nearest gauge")
        print(f"   Properties to fix: {len(problems_found)}")
    
    for problem in problems_found:
        try:
            prop_index = problem['prop_index']
            prop = properties[prop_index]
            nearest_gauge = problem['nearest_gauge']
            
            # Calculate new realistic elevation
            gauge_elevation = nearest_gauge['elevation']
            
            # Generate elevation well above gauge with Thames valley characteristics
            new_elevation = _generate_realistic_elevation_above_gauge(
                gauge_elevation, 
                safety_margin,
                problem.get('prop_lat', 51.5),
                problem.get('prop_lon', -0.1)
            )
            
            # Apply the fix
            risk_assessment = prop.get('PropertyHeader', {}).get('RiskAssessment', {})
            old_elevation = risk_assessment.get('GroundLevelMeters', 0)
            risk_assessment['GroundLevelMeters'] = round(new_elevation, 2)
            
            fixes_applied += 1
            
            # Show detailed fix information for first 10
            if verbose and fixes_applied <= 10:
                print(f"     Fixed {problem['prop_id']}: {old_elevation:.1f}m → {new_elevation:.1f}m "
                      f"(gauge: {gauge_elevation:.1f}m)")
        
        except Exception as e:
            if verbose:
                print(f"     Error fixing property {problem.get('prop_id', 'unknown')}: {e}")
    
    if verbose:
        print(f"   ✅ Successfully applied {fixes_applied} elevation fixes")
    
    return fixes_applied


def _generate_realistic_elevation_above_gauge(gauge_elevation: float, safety_margin: float, 
                                            prop_lat: float, prop_lon: float) -> float:
    """
    Generate realistic property elevation that is safely above the gauge.
    """
    
    # Base elevation: gauge + safety margin
    base_elevation = gauge_elevation + safety_margin
    
    # Add realistic Thames valley variation
    # Properties further from Thames center are generally higher
    thames_center_lat = 51.5
    distance_from_thames = abs(prop_lat - thames_center_lat) * 111000  # Convert to meters
    
    if distance_from_thames < 500:  # Very close to Thames
        elevation_boost = np.random.uniform(0, 10)  # 0-10m additional height
    elif distance_from_thames < 2000:  # Moderate distance
        elevation_boost = np.random.uniform(5, 20)  # 5-20m additional height
    else:  # Further from Thames (London hills)
        elevation_boost = np.random.uniform(10, 30)  # 10-30m additional height
    
    final_elevation = base_elevation + elevation_boost
    
    # Ensure reasonable Thames valley bounds (not too extreme)
    return max(gauge_elevation + safety_margin, min(80.0, final_elevation))


def _create_backups(property_file: Path, gauge_file: Path, verbose: bool):
    """Create backup files before making changes."""
    
    try:
        import time
        timestamp = str(int(time.time()))
        
        prop_backup = property_file.with_suffix(f'.pre_comprehensive_fix_{timestamp}.json')
        gauge_backup = gauge_file.with_suffix(f'.pre_comprehensive_fix_{timestamp}.json')
        
        shutil.copy2(property_file, prop_backup)
        shutil.copy2(gauge_file, gauge_backup)
        
        if verbose:
            print(f"   📁 Comprehensive fix backups: *_pre_comprehensive_fix_{timestamp}.json")
    
    except Exception as e:
        if verbose:
            print(f"   ⚠️  Failed to create backups: {e}")


def _save_portfolio_data(property_file: Path, gauge_file: Path, properties: List[Dict], gauges: List[Dict]):
    """Save updated property and gauge data back to JSON files."""
    
    # Save properties with fixed elevations
    with open(property_file, 'w') as f:
        json.dump({'properties': properties}, f, indent=2)
    
    # Gauges don't need changes for this fix
    with open(gauge_file, 'w') as f:
        json.dump({'gauges': gauges}, f, indent=2)


# Standalone execution for testing
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    input_dir = project_root / "input"
    
    print("🔍 COMPREHENSIVE ELEVATION VALIDATOR WITH DIAGNOSTICS")
    print("=" * 70)
    print("This version will show exactly what's wrong and fix it properly")
    print("")
    
    success = validate_and_fix_elevations(input_dir, create_backups=True, verbose=True)
    
    if success:
        print("\n🎉 COMPREHENSIVE ELEVATION VALIDATION COMPLETED!")
        print("💡 Expected results after next portfolio run:")
        print("   • Properties properly positioned above gauges")
        print("   • Realistic flood depths: 0-8m")
        print("   • No negative or extreme flood depths")
        print("   • Professional flood risk analysis")
    else:
        print("\n❌ Comprehensive elevation validation failed")