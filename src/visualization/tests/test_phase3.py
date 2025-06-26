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
Test script for Phase 3 of the visualization refactoring.

This script tests the layer modules: StormLayer, GaugeLayer, PropertyLayer, and MortgageLayer.
"""

import sys
from pathlib import Path

# Fix the Python path to find project modules
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import modules
from src.utilities.project_paths import ProjectPaths

# Import the core modules
from src.visualization.core import TCEventVisualization, DataLoader, MapBuilder

# Import the layer modules
from src.visualization.layers import StormLayer, GaugeLayer, PropertyLayer, MortgageLayer


def test_layer_imports():
    """Test that all layer modules can be imported."""
    print("=" * 60)
    print("TESTING: Layer Module Imports")
    print("=" * 60)
    
    try:
        # Test individual layer imports
        storm = StormLayer()
        print(f"✅ StormLayer imported and created: {storm.layer_name}")
        
        gauge = GaugeLayer()
        print(f"✅ GaugeLayer imported and created: {gauge.layer_name}")
        
        property_layer = PropertyLayer()
        print(f"✅ PropertyLayer imported and created: {property_layer.layer_name}")
        
        mortgage = MortgageLayer()
        print(f"✅ MortgageLayer imported and created: {mortgage.layer_name}")
        
        print("✅ All layer modules imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Layer import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_storm_layer():
    """Test the StormLayer module with real data."""
    print("\n" + "=" * 60)
    print("TESTING: Storm Layer")
    print("=" * 60)
    
    try:
        # Load data
        input_dir = project_root / "input"
        data_loader = DataLoader(input_dir)
        
        # Load TC data
        tc_data = data_loader._load_json("single_tceventts.json")
        if not tc_data:
            print("⚠️  No TC data available for storm layer test")
            return False
        
        # Create map builder and base map
        map_builder = MapBuilder()
        base_map = map_builder.create_base_map(tc_data)
        
        # Create and test storm layer
        storm_layer = StormLayer()
        storm_group = storm_layer.add_to_map(base_map, tc_data)
        
        # Test configuration
        storm_layer.configure(show_storm_size=True, show_time_markers=True, marker_interval=4)
        
        # Test statistics
        storm_data = storm_layer._extract_storm_data(tc_data)
        stats = storm_layer.get_storm_statistics(storm_data)
        
        print(f"✅ Storm layer statistics:")
        print(f"   - Total points: {stats.get('total_points', 0)}")
        print(f"   - Duration: {stats.get('duration_hours', 0)} hours")
        print(f"   - Max wind speed: {stats.get('max_wind_speed', 0):.1f} m/s")
        print(f"   - Track length: {stats.get('track_length_km', 0):.1f} km")
        
        # Save test map
        output_dir = project_root / "results"
        output_dir.mkdir(exist_ok=True)
        test_output = output_dir / "test_storm_layer.html"
        result = map_builder.finalize_map(base_map, test_output)
        
        if result:
            print(f"✅ Storm layer test map saved: {result}")
            return True
        else:
            print("❌ Failed to save storm layer test map")
            return False
            
    except Exception as e:
        print(f"❌ Storm layer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gauge_layer():
    """Test the GaugeLayer module with real data."""
    print("\n" + "=" * 60)
    print("TESTING: Gauge Layer")
    print("=" * 60)
    
    try:
        # Load data
        input_dir = project_root / "input"
        data_loader = DataLoader(input_dir)
        
        # Load all required data
        loaded_data = data_loader.load_all_data(
            ts_filename="single_tceventts.json",
            gauge_filename="flood_gauge_portfolio.json",
            property_filename="property_portfolio.json",
            mortgage_filename="mortgage_portfolio.json",
            flood_risk_filename="flood_risk_report.json"
        )
        
        if not loaded_data.gauge_data:
            print("⚠️  No gauge data available for gauge layer test")
            return False
        
        # Create base map
        map_builder = MapBuilder()
        base_map = map_builder.create_base_map(loaded_data.tc_data)
        
        # Create and test mortgage layer
        mortgage_layer = MortgageLayer()
        mortgage_group = mortgage_layer.add_to_map(base_map, loaded_data)
        
        # Test configuration
        mortgage_layer.configure(show_risk_circles=True, show_ltv_indicators=True)
        
        # Test statistics
        mortgage_locations = mortgage_layer._extract_mortgage_locations(loaded_data)
        stats = mortgage_layer.get_mortgage_statistics(mortgage_locations)
        
        print(f"✅ Mortgage layer statistics:")
        print(f"   - Total mortgages: {stats.get('total_mortgages', 0)}")
        print(f"   - Average loan amount: £{stats.get('avg_loan_amount', 0):,.2f}")
        print(f"   - Total loan value: £{stats.get('total_loan_value', 0):,.2f}")
        print(f"   - High LTV count: {stats.get('high_ltv_count', 0)}")
        print(f"   - Risk distribution: {stats.get('risk_distribution', {})}")
        
        # Save test map
        output_dir = project_root / "results"
        test_output = output_dir / "test_mortgage_layer.html"
        result = map_builder.finalize_map(base_map, test_output)
        
        if result:
            print(f"✅ Mortgage layer test map saved: {result}")
            return True
        else:
            print("❌ Failed to save mortgage layer test map")
            return False
            
    except Exception as e:
        print(f"❌ Mortgage layer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integrated_layers():
    """Test all layers together in an integrated visualization."""
    print("\n" + "=" * 60)
    print("TESTING: Integrated Layer Visualization")
    print("=" * 60)
    
    try:
        # Load data
        input_dir = project_root / "input"
        data_loader = DataLoader(input_dir)
        
        # Load all required data
        loaded_data = data_loader.load_all_data(
            ts_filename="single_tceventts.json",
            gauge_filename="flood_gauge_portfolio.json",
            property_filename="property_portfolio.json",
            mortgage_filename="mortgage_portfolio.json",
            flood_risk_filename="flood_risk_report.json"
        )
        
        if not loaded_data.tc_data:
            print("⚠️  No TC data available for integrated test")
            return False
        
        # Create base map
        map_builder = MapBuilder()
        base_map = map_builder.create_base_map(loaded_data.tc_data)
        
        # Create all layers
        storm_layer = StormLayer()
        gauge_layer = GaugeLayer()
        property_layer = PropertyLayer()
        mortgage_layer = MortgageLayer()
        
        # Add all layers to map
        layer_results = {}
        
        print("Adding layers to integrated map...")
        
        # Add storm layer
        try:
            storm_group = storm_layer.add_to_map(base_map, loaded_data.tc_data)
            layer_results['Storm'] = True
            print("✅ Storm layer added")
        except Exception as e:
            print(f"❌ Storm layer failed: {e}")
            layer_results['Storm'] = False
        
        # Add gauge layer
        if loaded_data.gauge_data:
            try:
                gauge_group = gauge_layer.add_to_map(base_map, loaded_data)
                layer_results['Gauges'] = True
                print("✅ Gauge layer added")
            except Exception as e:
                print(f"❌ Gauge layer failed: {e}")
                layer_results['Gauges'] = False
        else:
            layer_results['Gauges'] = False
            print("⚠️  Gauge layer skipped (no data)")
        
        # Add property layer
        if loaded_data.property_data:
            try:
                property_group = property_layer.add_to_map(base_map, loaded_data)
                layer_results['Properties'] = True
                print("✅ Property layer added")
            except Exception as e:
                print(f"❌ Property layer failed: {e}")
                layer_results['Properties'] = False
        else:
            layer_results['Properties'] = False
            print("⚠️  Property layer skipped (no data)")
        
        # Add mortgage layer
        if loaded_data.mortgage_data and loaded_data.property_data:
            try:
                mortgage_group = mortgage_layer.add_to_map(base_map, loaded_data)
                layer_results['Mortgages'] = True
                print("✅ Mortgage layer added")
            except Exception as e:
                print(f"❌ Mortgage layer failed: {e}")
                layer_results['Mortgages'] = False
        else:
            layer_results['Mortgages'] = False
            print("⚠️  Mortgage layer skipped (insufficient data)")
        
        # Save integrated map
        output_dir = project_root / "results"
        test_output = output_dir / "test_integrated_layers.html"
        result = map_builder.finalize_map(base_map, test_output)
        
        # Print summary
        successful_layers = sum(layer_results.values())
        total_layers = len(layer_results)
        
        print(f"\n✅ Integrated test results:")
        print(f"   - Layers added: {successful_layers}/{total_layers}")
        for layer_name, success in layer_results.items():
            status = "✅" if success else "❌"
            print(f"   - {status} {layer_name}")
        
        if result:
            print(f"✅ Integrated layer map saved: {result}")
            return successful_layers > 0  # Success if at least one layer works
        else:
            print("❌ Failed to save integrated layer map")
            return False
            
    except Exception as e:
        print(f"❌ Integrated layer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_layer_configuration():
    """Test layer configuration options."""
    print("\n" + "=" * 60)
    print("TESTING: Layer Configuration")
    print("=" * 60)
    
    try:
        # Test all layer configurations
        storm_layer = StormLayer()
        storm_layer.configure(
            show_storm_size=False,
            show_time_markers=True,
            marker_interval=12,
            color_scheme="pressure"
        )
        print("✅ Storm layer configuration test passed")
        
        gauge_layer = GaugeLayer()
        gauge_layer.configure(
            show_status_colors=True,
            show_flood_thresholds=False
        )
        print("✅ Gauge layer configuration test passed")
        
        property_layer = PropertyLayer()
        property_layer.configure(
            show_risk_colors=False,
            show_mortgage_status=True,
            risk_based_sizing=True
        )
        print("✅ Property layer configuration test passed")
        
        mortgage_layer = MortgageLayer()
        mortgage_layer.configure(
            show_risk_circles=True,
            show_ltv_indicators=False,
            circle_opacity=0.6,
            max_circle_radius=300
        )
        print("✅ Mortgage layer configuration test passed")
        
        print("✅ All layer configuration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Layer configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_updated_visualizer():
    """Test the updated visualizer with Phase 3 layers."""
    print("\n" + "=" * 60)
    print("TESTING: Updated Visualizer with Layers")
    print("=" * 60)
    
    try:
        # Create visualizer
        input_dir = project_root / "input"
        output_dir = project_root / "results"
        
        viz = TCEventVisualization(input_dir=input_dir, output_dir=output_dir)
        
        # Test creating a full visualization
        print("Creating full visualization with Phase 3 layers...")
        result = viz.create_event_map(
            ts_filename="single_tceventts.json",
            gauge_filename="flood_gauge_portfolio.json",
            property_filename="property_portfolio.json",
            mortgage_filename="mortgage_portfolio.json",
            flood_risk_filename="flood_risk_report.json",
            output_filename="phase3_full_test.html"
        )
        
        if result:
            print(f"✅ Full Phase 3 visualization created: {result}")
            print("Note: This should now include actual layers, not just placeholders")
            return True
        else:
            print("❌ Failed to create full Phase 3 visualization")
            return False
            
    except Exception as e:
        print(f"❌ Updated visualizer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 3 tests."""
    print("🧪 PHASE 3 TESTING SUITE - LAYER MODULES")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print(f"Input directory: {project_root / 'input'}")
    print(f"Output directory: {project_root / 'results'}")
    
    # Run all tests
    tests = [
        ("Layer Imports", test_layer_imports),
        ("Storm Layer", test_storm_layer),
        ("Gauge Layer", test_gauge_layer),
        ("Property Layer", test_property_layer),
        ("Mortgage Layer", test_mortgage_layer),
        ("Integrated Layers", test_integrated_layers),
        ("Layer Configuration", test_layer_configuration),
        ("Updated Visualizer", test_updated_visualizer)
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
    print("PHASE 3 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nResult: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 All Phase 3 tests passed! Layer modules are working correctly.")
        print("✅ Ready for Phase 4: Interactivity modules")
    elif passed_count > 0:
        print("⚠️  Some Phase 3 tests passed. Check failures above.")
        print("🔧 Debug failed layers before proceeding to Phase 4")
    else:
        print("💥 All Phase 3 tests failed. Check your layer implementations.")
    
    return passed_count == total_count




def test_property_layer():
    """Test the PropertyLayer module with real data."""
    print("\n" + "=" * 60)
    print("TESTING: Property Layer")
    print("=" * 60)
    
    try:
        # Load data
        input_dir = project_root / "input"
        data_loader = DataLoader(input_dir)
        
        # Load all required data
        loaded_data = data_loader.load_all_data(
            ts_filename="single_tceventts.json",
            gauge_filename="flood_gauge_portfolio.json",
            property_filename="property_portfolio.json",
            mortgage_filename="mortgage_portfolio.json",
            flood_risk_filename="flood_risk_report.json"
        )
        
        if not loaded_data.property_data:
            print("⚠️  No property data available for property layer test")
            return False
        
        # Create base map
        map_builder = MapBuilder()
        base_map = map_builder.create_base_map(loaded_data.tc_data)
        
        # Create and test property layer
        property_layer = PropertyLayer()
        property_group = property_layer.add_to_map(base_map, loaded_data)
        
        # Test configuration
        property_layer.configure(show_risk_colors=True, show_mortgage_status=True)
        
        # Test statistics
        properties = property_layer._get_properties_list(loaded_data.property_data)
        stats = property_layer.get_property_statistics(properties, loaded_data)
        
        print(f"✅ Property layer statistics:")
        print(f"   - Total properties: {stats.get('total_properties', 0)}")
        print(f"   - Mortgaged properties: {stats.get('mortgaged_properties', 0)}")
        print(f"   - Mortgage percentage: {stats.get('mortgage_percentage', 0):.1f}%")
        print(f"   - Risk distribution: {stats.get('risk_distribution', {})}")
        
        # Save test map
        output_dir = project_root / "results"
        test_output = output_dir / "test_property_layer.html"
        result = map_builder.finalize_map(base_map, test_output)
        
        if result:
            print(f"✅ Property layer test map saved: {result}")
            return True
        else:
            print("❌ Failed to save property layer test map")
            return False
            
    except Exception as e:
        print(f"❌ Property layer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mortgage_layer():
    """Test the MortgageLayer module with real data."""
    print("\n" + "=" * 60)
    print("TESTING: Mortgage Layer")
    print("=" * 60)
    
    try:
        # Load data
        input_dir = project_root / "input"
        data_loader = DataLoader(input_dir)
        
        # Load all required data
        loaded_data = data_loader.load_all_data(
            ts_filename="single_tceventts.json",
            gauge_filename="flood_gauge_portfolio.json",
            property_filename="property_portfolio.json",
            mortgage_filename="mortgage_portfolio.json",
            flood_risk_filename="flood_risk_report.json"
        )
        
        if not loaded_data.mortgage_data or not loaded_data.property_data:
            print("⚠️  Insufficient data for mortgage layer test")
            return False
        
        # Create base map
        map_builder = MapBuilder()
        base_map = map_builder.create_base_map(loaded_data.tc_data)
        
        # Create and test mortgage layer
        mortgage_layer = MortgageLayer()
        mortgage_group = mortgage_layer.add_to_map(base_map, loaded_data)
        
        # Test configuration
        mortgage_layer.configure(show_risk_circles=True, show_ltv_indicators=True)
        
        # Test statistics
        mortgage_locations = mortgage_layer._extract_mortgage_locations(loaded_data)
        stats = mortgage_layer.get_mortgage_statistics(mortgage_locations)
        
        print(f"✅ Mortgage layer statistics:")
        print(f"   - Total mortgages: {stats.get('total_mortgages', 0)}")
        print(f"   - Average loan amount: £{stats.get('avg_loan_amount', 0):,.2f}")
        print(f"   - Total loan value: £{stats.get('total_loan_value', 0):,.2f}")
        print(f"   - High LTV count: {stats.get('high_ltv_count', 0)}")
        print(f"   - Risk distribution: {stats.get('risk_distribution', {})}")
        
        # Save test map
        output_dir = project_root / "results"
        test_output = output_dir / "test_mortgage_layer.html"
        result = map_builder.finalize_map(base_map, test_output)
        
        if result:
            print(f"✅ Mortgage layer test map saved: {result}")
            return True
        else:
            print("❌ Failed to save mortgage layer test map")
            return False
            
    except Exception as e:
        print(f"❌ Mortgage layer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    
    
    
if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

    # Create and test gauge layer
    gauge_layer = GaugeLayer()
    gauge_group = gauge_layer.add_to_map(base_map, loaded_data)

    # Test configuration
    gauge_layer.configure(show_status_colors=True, show_flood_thresholds=True)

    # Test statistics
    gauges = gauge_layer._extract_gauges(loaded_data.gauge_data)
    stats = gauge_layer.get_gauge_statistics(gauges)

    print(f"✅ Gauge layer statistics:")
    print(f"   - Total gauges: {stats.get('total_gauges', 0)}")
    print(f"   - Operational: {stats.get('operational_percentage', 0):.1f}%")
    print(f"   - Status distribution: {stats.get('status_distribution', {})}")

    # Save test map
    output_dir = project_root / "results"
    test_output = output_dir / "test_gauge_layer.html"
    result = map_builder.finalize_map(base_map, test_output)
