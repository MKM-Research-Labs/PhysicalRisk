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
Integration test for popup modules with layer modules.

This script tests how the popup modules integrate with the existing layer modules
from the visualization refactoring.
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
from src.visualization.core import DataLoader, MapBuilder

# Import the popup modules
from src.visualization.popups import PropertyPopupBuilder, GaugePopupBuilder

# Try to import layer modules (may not exist yet)
try:
    from src.visualization.layers import PropertyLayer, GaugeLayer
    LAYERS_AVAILABLE = True
except ImportError:
    print("⚠️  Layer modules not available - testing popups in isolation")
    LAYERS_AVAILABLE = False


def test_popup_with_real_data():
    """Test popup creation with real project data."""
    print("=" * 60)
    print("TESTING: Popups with Real Data")
    print("=" * 60)
    
    try:
        # Load real data
        input_dir = project_root / "input"
        data_loader = DataLoader(input_dir)
        
        # Load all data
        loaded_data = data_loader.load_all_data(
            ts_filename="single_tceventts.json",
            gauge_filename="flood_gauge_portfolio.json",
            property_filename="property_portfolio.json",
            mortgage_filename="mortgage_portfolio.json",
            flood_risk_filename="flood_risk_report.json"
        )
        
        print(f"Data loaded successfully:")
        print(f"  - TC data: {'✅' if loaded_data.tc_data else '❌'}")
        print(f"  - Gauge data: {'✅' if loaded_data.gauge_data else '❌'}")
        print(f"  - Property data: {'✅' if loaded_data.property_data else '❌'}")
        print(f"  - Mortgage data: {'✅' if loaded_data.mortgage_data else '❌'}")
        print(f"  - Flood risk data: {'✅' if loaded_data.flood_risk_data else '❌'}")
        
        # Test property popup with real data
        if loaded_data.property_data:
            success = test_property_popup_with_real_data(loaded_data)
            if not success:
                return False
        
        # Test gauge popup with real data
        if loaded_data.gauge_data:
            success = test_gauge_popup_with_real_data(loaded_data)
            if not success:
                return False
        
        print("✅ Popup tests with real data passed")
        return True
        
    except Exception as e:
        print(f"❌ Real data popup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_property_popup_with_real_data(loaded_data):
    """Test property popup creation with real property data."""
    print("\nTesting property popup with real data...")
    
    try:
        prop_builder = PropertyPopupBuilder()
        
        # Get the first property from real data
        properties = loaded_data.property_data.get('properties', [])
        if not properties:
            print("⚠️  No properties in real data")
            return True
        
        # Test with first property
        first_property = properties[0]
        property_header = first_property.get('PropertyHeader', {}).get('Header', {})
        property_id = property_header.get('PropertyID', 'UNKNOWN')
        
        print(f"Testing with property: {property_id}")
        
        # Extract location info (using the same logic as the original visualization.py)
        location = first_property.get('PropertyHeader', {}).get('Location', {})
        lat = location.get('LatitudeDegrees')
        lon = location.get('LongitudeDegrees')
        
        if lat is None or lon is None:
            print(f"⚠️  Property {property_id} has no valid coordinates")
            return True
        
        # Create address dictionary
        address = {
            'building_number': location.get('BuildingNumber', ''),
            'street_name': location.get('StreetName', ''),
            'town_city': location.get('TownCity', ''),
            'post_code': location.get('Postcode', '')
        }
        
        # Check for mortgage data
        mortgage_lookup = {}
        if loaded_data.mortgage_data:
            mortgages = loaded_data.mortgage_data.get('mortgages', [])
            for mortgage in mortgages:
                mort_data = mortgage.get('Mortgage', {})
                mort_header = mort_data.get('Header', {})
                prop_id = mort_header.get('PropertyID')
                if prop_id:
                    mortgage_lookup[prop_id] = mort_data
        
        has_mortgage = property_id in mortgage_lookup
        mortgage_info = mortgage_lookup.get(property_id) if has_mortgage else None
        
        # Check for flood risk data
        flood_info = None
        if loaded_data.flood_risk_data:
            property_risk = loaded_data.flood_risk_data.get('property_risk', {})
            flood_info = property_risk.get(property_id)
        
        # Check for mortgage risk data
        mortgage_risk_info = None
        if loaded_data.flood_risk_data and has_mortgage:
            mortgage_risk = loaded_data.flood_risk_data.get('mortgage_risk', {})
            # Try to find by mortgage ID or property ID
            if mortgage_info:
                mort_id = mortgage_info.get('Header', {}).get('MortgageID')
                if mort_id and mort_id in mortgage_risk:
                    mortgage_risk_info = mortgage_risk[mort_id]
                elif property_id in mortgage_risk:
                    mortgage_risk_info = mortgage_risk[property_id]
        
        # Get construction year for age factor calculation
        construction_year = first_property.get('PropertyHeader', {}).get('PropertyAttributes', {}).get('ConstructionYear', 2000)
        property_age_factor = "Unknown"
        if construction_year and isinstance(construction_year, int):
            age = 2025 - construction_year
            if age > 100:
                property_age_factor = "High (Pre-1925)"
            elif age > 50:
                property_age_factor = "Medium (1925-1975)"
            else:
                property_age_factor = "Low (Post-1975)"
        
        # Create the popup
        popup = prop_builder.build_property_popup(
            prop=first_property,
            property_id=property_id,
            address=address,
            coordinates=f"{lat:.4f}°N, {lon:.4f}°E",
            flood_risk="Medium",  # Default since we may not have this in the data structure
            thames_proximity="Close",
            ground_elevation=2.5,
            elevation_estimated=False,
            property_value=750000,  # Default value
            construction_year=construction_year,
            property_age_factor=property_age_factor,
            has_mortgage=has_mortgage,
            mortgage_info=mortgage_info,
            flood_info=flood_info,
            mortgage_risk_info=mortgage_risk_info
        )
        
        # Verify popup was created
        assert popup is not None
        print(f"✅ Property popup created successfully for {property_id}")
        
        # Test that popup contains expected content
        popup_content = popup._template.render()
        assert property_id in popup_content
        assert "Property Analysis" in popup_content
        
        if has_mortgage:
            assert "MORTGAGE DETAILS" in popup_content
            print(f"✅ Mortgage information included in popup")
        
        if flood_info:
            assert "Detailed Flood Risk Information" in popup_content
            print(f"✅ Flood risk information included in popup")
        
        if mortgage_risk_info:
            assert "MORTGAGE RISK ANALYSIS" in popup_content
            print(f"✅ Mortgage risk analysis included in popup")
        
        return True
        
    except Exception as e:
        print(f"❌ Property popup test with real data failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gauge_popup_with_real_data(loaded_data):
    """Test gauge popup creation with real gauge data."""
    print("\nTesting gauge popup with real data...")
    
    try:
        gauge_builder = GaugePopupBuilder()
        
        # Get gauges from real data
        gauges = loaded_data.gauge_data.get('floodGauges', loaded_data.gauge_data.get('flood_gauges', []))
        if not gauges:
            print("⚠️  No gauges in real data")
            return True
        
        # Test with first gauge
        first_gauge = gauges[0]
        gauge_info = first_gauge.get('FloodGauge', {})
        gauge_header = gauge_info.get('Header', {})
        gauge_id = gauge_header.get('GaugeID', 'UNKNOWN')
        
        print(f"Testing with gauge: {gauge_id}")
        
        # Get coordinates
        gauge_details = gauge_info.get('SensorDetails', {}).get('GaugeInformation', {})
        lat = gauge_details.get('GaugeLatitude')
        lon = gauge_details.get('GaugeLongitude')
        
        if lat is None or lon is None:
            print(f"⚠️  Gauge {gauge_id} has no valid coordinates")
            return True
        
        # Check for flood risk data
        flood_info = None
        if loaded_data.flood_risk_data:
            gauge_data = loaded_data.flood_risk_data.get('gauge_data', {})
            flood_info = gauge_data.get(gauge_id)
        
        # Create the popup
        popup = gauge_builder.build_gauge_popup(
            gauge_id=gauge_id,
            lat=lat,
            lon=lon,
            info=gauge_info,
            flood_info=flood_info
        )
        
        # Verify popup was created
        assert popup is not None
        print(f"✅ Gauge popup created successfully for {gauge_id}")
        
        # Test that popup contains expected content
        popup_content = popup._template.render()
        assert gauge_id in popup_content
        assert "Flood Gauge Analysis" in popup_content
        assert "Equipment Details" in popup_content
        
        if flood_info:
            assert "Flood Risk Data" in popup_content
            print(f"✅ Flood risk data included in gauge popup")
        
        return True
        
    except Exception as e:
        print(f"❌ Gauge popup test with real data failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_popup_performance():
    """Test popup creation performance with multiple items."""
    print("\n" + "=" * 60)
    print("TESTING: Popup Performance")
    print("=" * 60)
    
    try:
        import time
        
        # Load real data
        input_dir = project_root / "input"
        data_loader = DataLoader(input_dir)
        
        loaded_data = data_loader.load_all_data(
            ts_filename="single_tceventts.json",
            gauge_filename="flood_gauge_portfolio.json",
            property_filename="property_portfolio.json",
            mortgage_filename="mortgage_portfolio.json",
            flood_risk_filename="flood_risk_report.json"
        )
        
        # Test property popup performance
        if loaded_data.property_data:
            properties = loaded_data.property_data.get('properties', [])
            if properties:
                print(f"Testing property popup performance with {len(properties)} properties...")
                
                prop_builder = PropertyPopupBuilder()
                start_time = time.time()
                
                successful_popups = 0
                for i, prop in enumerate(properties):
                    try:
                        prop_header = prop.get('PropertyHeader', {}).get('Header', {})
                        property_id = prop_header.get('PropertyID', f'PROP-{i}')
                        
                        location = prop.get('PropertyHeader', {}).get('Location', {})
                        lat = location.get('LatitudeDegrees')
                        lon = location.get('LongitudeDegrees')
                        
                        if lat is not None and lon is not None:
                            # Create simple popup (without full data lookup for performance)
                            address = {
                                'building_number': location.get('BuildingNumber', ''),
                                'street_name': location.get('StreetName', ''),
                                'town_city': location.get('TownCity', ''),
                                'post_code': location.get('Postcode', '')
                            }
                            
                            popup = prop_builder.build_property_popup(
                                prop=prop,
                                property_id=property_id,
                                address=address,
                                coordinates=f"{lat:.4f}°N, {lon:.4f}°E",
                                flood_risk="Medium",
                                thames_proximity="Close",
                                ground_elevation=2.5,
                                elevation_estimated=False,
                                property_value=500000,
                                construction_year=2000,
                                property_age_factor="Low (Post-1975)",
                                has_mortgage=False
                            )
                            successful_popups += 1
                        
                        # Test every 10th property to avoid too much output
                        if i % 10 == 0:
                            print(f"  Processed {i+1}/{len(properties)} properties...")
                            
                    except Exception as e:
                        print(f"  ⚠️  Failed to create popup for property {i}: {e}")
                        continue
                
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"✅ Property popup performance test completed:")
                print(f"   - Processed: {successful_popups}/{len(properties)} properties")
                print(f"   - Duration: {duration:.2f} seconds")
                print(f"   - Rate: {successful_popups/duration:.1f} popups/second")
        
        # Test gauge popup performance
        if loaded_data.gauge_data:
            gauges = loaded_data.gauge_data.get('floodGauges', loaded_data.gauge_data.get('flood_gauges', []))
            if gauges:
                print(f"\nTesting gauge popup performance with {len(gauges)} gauges...")
                
                gauge_builder = GaugePopupBuilder()
                start_time = time.time()
                
                successful_popups = 0
                for i, gauge in enumerate(gauges):
                    try:
                        gauge_info = gauge.get('FloodGauge', {})
                        gauge_header = gauge_info.get('Header', {})
                        gauge_id = gauge_header.get('GaugeID', f'GAUGE-{i}')
                        
                        gauge_details = gauge_info.get('SensorDetails', {}).get('GaugeInformation', {})
                        lat = gauge_details.get('GaugeLatitude')
                        lon = gauge_details.get('GaugeLongitude')
                        
                        if lat is not None and lon is not None:
                            popup = gauge_builder.build_gauge_popup(
                                gauge_id=gauge_id,
                                lat=lat,
                                lon=lon,
                                info=gauge_info
                            )
                            successful_popups += 1
                            
                    except Exception as e:
                        print(f"  ⚠️  Failed to create popup for gauge {i}: {e}")
                        continue
                
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"✅ Gauge popup performance test completed:")
                print(f"   - Processed: {successful_popups}/{len(gauges)} gauges")
                print(f"   - Duration: {duration:.2f} seconds")
                print(f"   - Rate: {successful_popups/duration:.1f} popups/second")
        
        print("✅ Popup performance tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Popup performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_popup_layer_integration():
    """Test integration between popups and layers (if available)."""
    print("\n" + "=" * 60)
    print("TESTING: Popup-Layer Integration")
    print("=" * 60)
    
    if not LAYERS_AVAILABLE:
        print("⚠️  Layer modules not available - skipping integration test")
        return True
    
    try:
        # Load real data
        input_dir = project_root / "input"
        data_loader = DataLoader(input_dir)
        
        loaded_data = data_loader.load_all_data(
            ts_filename="single_tceventts.json",
            gauge_filename="flood_gauge_portfolio.json",
            property_filename="property_portfolio.json",
            mortgage_filename="mortgage_portfolio.json",
            flood_risk_filename="flood_risk_report.json"
        )
        
        # Create base map
        map_builder = MapBuilder()
        base_map = map_builder.create_base_map(loaded_data.tc_data)
        
        # Test property layer with popup integration
        if loaded_data.property_data:
            print("Testing property layer with popup integration...")
            
            property_layer = PropertyLayer()
            
            # Override the popup creation method to use our popup builder
            prop_builder = PropertyPopupBuilder()
            property_layer.popup_builder = prop_builder
            
            # Add to map (this should use the integrated popup builder)
            property_group = property_layer.add_to_map(base_map, loaded_data)
            print("✅ Property layer integrated with popup builder")
        
        # Test gauge layer with popup integration
        if loaded_data.gauge_data:
            print("Testing gauge layer with popup integration...")
            
            gauge_layer = GaugeLayer()
            
            # Override the popup creation method to use our popup builder
            gauge_builder = GaugePopupBuilder()
            gauge_layer.popup_builder = gauge_builder
            
            # Add to map (this should use the integrated popup builder)
            gauge_group = gauge_layer.add_to_map(base_map, loaded_data)
            print("✅ Gauge layer integrated with popup builder")
        
        # Save test map
        output_dir = project_root / "results"
        output_dir.mkdir(exist_ok=True)
        test_output = output_dir / "test_popup_layer_integration.html"
        result = map_builder.finalize_map(base_map, test_output)
        
        if result:
            print(f"✅ Integrated popup-layer map saved: {result}")
            return True
        else:
            print("❌ Failed to save integrated map")
            return False
        
    except Exception as e:
        print(f"❌ Popup-layer integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all popup-layer integration tests."""
    print("🧪 POPUP-LAYER INTEGRATION TESTING SUITE")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print(f"Layers available: {'✅' if LAYERS_AVAILABLE else '❌'}")
    
    # Run all tests
    tests = [
        ("Popups with Real Data", test_popup_with_real_data),
        ("Popup Performance", test_popup_performance),
        ("Popup-Layer Integration", test_popup_layer_integration)
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
    print("POPUP-LAYER INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nResult: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 All popup-layer integration tests passed!")
        print("✅ Popup modules are ready for full integration")
    elif passed_count > 0:
        print("⚠️  Some popup-layer integration tests passed. Check failures above.")
        print("🔧 Debug failed integrations before proceeding")
    else:
        print("💥 All popup-layer integration tests failed.")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)