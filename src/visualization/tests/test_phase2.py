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
Test script for Phase 2 of the visualization refactoring.

This script tests the core infrastructure modules: DataLoader, MapBuilder,
and the main TCEventVisualization coordinator.
"""

import sys
from pathlib import Path

# Fix the Python path to find project modules
current_file = Path(__file__).resolve()
# tests/test_phase2.py -> tests -> visualization -> src -> physrisk
project_root = current_file.parent.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import modules
from src.utilities.project_paths import ProjectPaths

# Now import the visualization modules
from src.visualization.core import TCEventVisualization, DataLoader, MapBuilder


def test_data_loader_only():
    """Test the DataLoader module independently."""
    print("=" * 60)
    print("TESTING: DataLoader Module")
    print("=" * 60)
    
    # Test with your actual input directory
    input_dir = project_root / "input"
    
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        print("Please ensure your input directory exists with JSON files")
        return False
    
    try:
        # Initialize data loader
        data_loader = DataLoader(input_dir)
        
        # Test loading individual files
        test_files = [
            "single_tceventts.json",
            "flood_gauge_portfolio.json", 
            "property_portfolio.json",
            "mortgage_portfolio.json",
            "flood_risk_report.json"
        ]
        
        print(f"\nTesting individual file loading:")
        for filename in test_files:
            data = data_loader._load_json(filename)
            if data:
                print(f"✅ {filename}: Loaded successfully")
            else:
                print(f"⚠️  {filename}: Not found or invalid")
        
        # Test full data loading if TC file exists
        tc_file = input_dir / "single_tceventts.json"
        if tc_file.exists():
            print(f"\nTesting full data loading pipeline:")
            loaded_data = data_loader.load_all_data(
                ts_filename="single_tceventts.json",
                gauge_filename="flood_gauge_portfolio.json",
                property_filename="property_portfolio.json", 
                mortgage_filename="mortgage_portfolio.json",
                flood_risk_filename="flood_risk_report.json"
            )
            
            print(f"\nData loading results:")
            print(f"✅ TC Data: {'Loaded' if loaded_data.tc_data else 'Missing'}")
            print(f"✅ Gauge Data: {'Loaded' if loaded_data.gauge_data else 'Missing'}")
            print(f"✅ Property Data: {'Loaded' if loaded_data.property_data else 'Missing'}")
            print(f"✅ Mortgage Data: {'Loaded' if loaded_data.mortgage_data else 'Missing'}")
            print(f"✅ Flood Risk Data: {'Loaded' if loaded_data.flood_risk_data else 'Missing'}")
            
            return True
        else:
            print(f"⚠️  TC file not found: {tc_file}")
            print("Cannot test full pipeline without TC data")
            return False
            
    except Exception as e:
        print(f"❌ DataLoader test failed: {e}")
        return False


def test_map_builder_only():
    """Test the MapBuilder module independently."""
    print("\n" + "=" * 60)
    print("TESTING: MapBuilder Module")
    print("=" * 60)
    
    try:
        # Test map builder with sample data
        map_builder = MapBuilder()
        
        # Create sample TC data for testing
        sample_tc_data = {
            "timeseries": [
                {
                    "EventTimeseries": {
                        "Dimensions": {"lat": 51.5, "lon": -0.1},
                        "Header": {"time": "2024-01-01T00:00:00Z"}
                    }
                },
                {
                    "EventTimeseries": {
                        "Dimensions": {"lat": 51.6, "lon": -0.2},
                        "Header": {"time": "2024-01-01T01:00:00Z"}
                    }
                },
                {
                    "EventTimeseries": {
                        "Dimensions": {"lat": 51.7, "lon": -0.3},
                        "Header": {"time": "2024-01-01T02:00:00Z"}
                    }
                }
            ]
        }
        
        print("Creating test map with sample TC data...")
        base_map = map_builder.create_base_map(sample_tc_data)
        
        if base_map:
            print("✅ MapBuilder: Base map created successfully")
            
            # Test saving the map
            output_dir = project_root / "results"
            output_dir.mkdir(exist_ok=True)
            
            test_output = output_dir / "test_map_builder.html"
            result = map_builder.finalize_map(base_map, test_output)
            
            if result:
                print(f"✅ MapBuilder: Test map saved to {result}")
                return True
            else:
                print("❌ MapBuilder: Failed to save test map")
                return False
        else:
            print("❌ MapBuilder: Failed to create base map")
            return False
            
    except Exception as e:
        print(f"❌ MapBuilder test failed: {e}")
        return False


def test_visualizer_simple():
    """Test the TCEventVisualization with minimal data."""
    print("\n" + "=" * 60)
    print("TESTING: TCEventVisualization (Simple Test)")
    print("=" * 60)
    
    try:
        # Setup directories
        input_dir = project_root / "input"
        output_dir = project_root / "results"
        output_dir.mkdir(exist_ok=True)
        
        # Create visualizer
        viz = TCEventVisualization(input_dir=input_dir, output_dir=output_dir)
        
        # Test with just TC data
        tc_file = "single_tceventts.json"
        if (input_dir / tc_file).exists():
            print(f"Testing simple map creation with {tc_file}...")
            
            result = viz.create_test_map(tc_file, "phase2_test_simple.html")
            
            if result:
                print(f"✅ Simple test map created: {result}")
                return True
            else:
                print("❌ Failed to create simple test map")
                return False
        else:
            print(f"⚠️  TC file not found: {input_dir / tc_file}")
            print("Cannot test without TC data")
            return False
            
    except Exception as e:
        print(f"❌ Simple visualizer test failed: {e}")
        return False


def test_visualizer_full():
    """Test the full TCEventVisualization pipeline."""
    print("\n" + "=" * 60)
    print("TESTING: TCEventVisualization (Full Pipeline)")
    print("=" * 60)
    
    try:
        # Setup directories
        input_dir = project_root / "input"
        output_dir = project_root / "results"
        output_dir.mkdir(exist_ok=True)
        
        # Create visualizer
        viz = TCEventVisualization(input_dir=input_dir, output_dir=output_dir)
        
        # Test file validation first
        filenames = {
            'ts_filename': "single_tceventts.json",
            'gauge_filename': "flood_gauge_portfolio.json",
            'property_filename': "property_portfolio.json",
            'mortgage_filename': "mortgage_portfolio.json",
            'flood_risk_filename': "flood_risk_report.json"
        }
        
        print("Validating input files...")
        files_valid = viz.validate_input_files(**filenames)
        
        if not files_valid:
            print("⚠️  Some input files are missing. Testing with available files...")
        
        # Test full pipeline
        print("Testing full visualization pipeline...")
        result = viz.create_event_map(
            **filenames,
            output_filename="phase2_test_full.html"
        )
        
        if result:
            print(f"✅ Full pipeline test completed: {result}")
            print("Note: Layers and interactivity are placeholders (Phases 3-4)")
            return True
        else:
            print("❌ Full pipeline test failed")
            return False
            
    except Exception as e:
        print(f"❌ Full visualizer test failed: {e}")
        return False


def test_utilities():
    """Test that utility modules can be imported and used."""
    print("\n" + "=" * 60)
    print("TESTING: Utility Modules")
    print("=" * 60)
    
    try:
        from visualization.utils import (
            DataFormatter, ColorSchemes, RiskAssessor, DataExtractor
        )
        
        # Test a few utility functions
        print("Testing utility functions...")
        
        # Test formatter
        formatted_currency = DataFormatter.format_currency(123456.789)
        print(f"✅ Currency formatting: {formatted_currency}")
        
        # Test color schemes
        risk_color = ColorSchemes.get_flood_risk_color("High")
        print(f"✅ Risk color mapping: High -> {risk_color}")
        
        # Test risk assessor
        risk_level = RiskAssessor.assess_flood_risk_level(1.5)
        print(f"✅ Risk assessment: 1.5m depth -> {risk_level}")
        
        print("✅ All utility modules working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Utility module test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 2 tests."""
    print("🧪 PHASE 2 TESTING SUITE")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print(f"Input directory: {project_root / 'input'}")
    print(f"Output directory: {project_root / 'results'}")
    
    # Run all tests
    tests = [
        ("Utility Modules", test_utilities),
        ("DataLoader", test_data_loader_only),
        ("MapBuilder", test_map_builder_only),
        ("Visualizer (Simple)", test_visualizer_simple),
        ("Visualizer (Full)", test_visualizer_full)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"💥 {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nResult: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 All tests passed! Phase 2 is working correctly.")
    elif passed_count > 0:
        print("⚠️  Some tests passed. Check failures above.")
    else:
        print("💥 All tests failed. Check your setup and file paths.")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)