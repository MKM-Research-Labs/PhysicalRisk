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
Test script for Phase 4 of the visualization refactoring.

This script tests the popup modules: PopupBuilder, PropertyPopupBuilder, and GaugePopupBuilder.
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

# Import the popup modules
from src.visualization.popups import PopupBuilder, PropertyPopupBuilder, GaugePopupBuilder


def test_popup_imports():
    """Test that all popup modules can be imported."""
    print("=" * 60)
    print("TESTING: Popup Module Imports")
    print("=" * 60)
    
    try:
        # Test individual popup imports
        base_builder = PopupBuilder()
        print(f"✅ PopupBuilder imported and created")
        
        property_builder = PropertyPopupBuilder()
        print(f"✅ PropertyPopupBuilder imported and created")
        
        gauge_builder = GaugePopupBuilder()
        print(f"✅ GaugePopupBuilder imported and created")
        
        print("✅ All popup modules imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Popup import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_popup_builder_base():
    """Test the base PopupBuilder functionality."""
    print("\n" + "=" * 60)
    print("TESTING: Base PopupBuilder")
    print("=" * 60)
    
    try:
        builder = PopupBuilder()
        
        # Test formatting methods
        print("Testing formatting methods...")
        
        # Test safe_format_float
        assert builder.safe_format_float(3.14159, 2) == "3.14"
        assert builder.safe_format_float(None) == "N/A"
        assert builder.safe_format_float("invalid") == "invalid"
        print("✅ safe_format_float working correctly")
        
        # Test format_currency
        assert builder.format_currency(1000000) == "£1,000,000.00"
        assert builder.format_currency(None) == "Not available"
        assert builder.format_currency("invalid") == "invalid"
        print("✅ format_currency working correctly")
        
        # Test format_percentage
        assert builder.format_percentage(0.85) == "85.0%"
        assert builder.format_percentage(85) == "85.0%"
        assert builder.format_percentage(None) == "N/A"
        print("✅ format_percentage working correctly")
        
        # Test risk color mapping
        assert builder.get_risk_color('High') == 'red'
        assert builder.get_risk_color('Low') == 'lightgreen'
        assert builder.get_risk_color('Unknown') == 'blue'
        print("✅ get_risk_color working correctly")
        
        # Test section creation
        section = builder.create_section("Test Section", "<p>Test content</p>")
        assert "Test Section" in section
        assert "Test content" in section
        assert "background-color: #EBF5FB" in section
        print("✅ create_section working correctly")
        
        # Test data row creation - Updated to match the corrected implementation
        row = builder.create_data_row("Test Label", "Test Value")
        assert "Test Label:" in row
        assert "Test Value" in row
        assert "<p>" in row  # Should be paragraph, not table row
        print("✅ create_data_row working correctly")
        
        # Test colored text creation
        colored = builder.create_colored_text("High Risk", "red", bold=True)
        assert "color: red" in colored
        assert "font-weight: bold" in colored
        assert "High Risk" in colored
        print("✅ create_colored_text working correctly")
        
        # Test popup wrapper
        wrapper = builder.create_popup_wrapper("<p>Content</p>", 400, 500)
        assert "font-family: Arial" in wrapper
        assert "width: 400px" in wrapper
        assert "max-height: 500px" in wrapper
        print("✅ create_popup_wrapper working correctly")
        
        print("✅ Base PopupBuilder tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Base PopupBuilder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_property_popup_builder():
    """Test the PropertyPopupBuilder functionality."""
    print("\n" + "=" * 60)
    print("TESTING: PropertyPopupBuilder")
    print("=" * 60)
    
    try:
        builder = PropertyPopupBuilder()
        
        # Create sample data matching the expected structure
        sample_property = {
            'PropertyHeader': {
                'Header': {
                    'PropertyID': 'PROP-test-001',
                    'propertyType': 'Residential',
                    'propertyStatus': 'Active'
                },
                'PropertyAttributes': {
                    'PropertyType': 'Terraced House',
                    'NumberOfStoreys': 2,
                    'ConstructionYear': 1985
                },
                'Construction': {
                    'ConstructionType': 'Brick'
                },
                'Location': {
                    'LatitudeDegrees': 51.5074,
                    'LongitudeDegrees': -0.1278,
                    'BuildingNumber': '123',
                    'StreetName': 'Test Street',
                    'TownCity': 'London',
                    'Postcode': 'SW1A 1AA'
                }
            }
        }
        
        sample_address = {
            'building_number': '123',
            'street_name': 'Test Street',
            'town_city': 'London',
            'post_code': 'SW1A 1AA'
        }
        
        sample_mortgage = {
            'Header': {
                'MortgageID': 'MTG-test-001'
            },
            'FinancialTerms': {
                'OriginalLoan': 500000,
                'OriginalLendingRate': 0.035,
                'TermYears': 25
            },
            'Application': {
                'MortgageProvider': 'Test Bank'
            }
        }
        
        sample_flood_info = {
            'nearest_gauge': 'Thames Test Gauge',
            'distance_to_gauge': 2.5,
            'water_level': 1.2,
            'flood_depth': 0.3,
            'risk_value': 0.25,
            'risk_level': 'Medium',
            'value_at_risk': 125000
        }
        
        sample_mortgage_risk = {
            'MortgageID': 'MTG-test-001',
            'PropertyID': 'PROP-test-001',
            'loan_amount': 500000,
            'interest_rate': 0.035,
            'monthly_payment': 2465.87,
            'annual_payment': 29590.44,
            'credit_spread': 0.005,
            'recovery_haircut': 0.20,
            'mortgage_value': 480000,
            'mortgage_value_at_risk': 96000,
            'flood_risk_level': 'Medium',
            'flood_risk_value': 0.25,
            'flood_depth': 0.3,
            'property_value': 750000
        }
        
        print("Testing property section creation...")
        prop_section = builder.create_property_section(
            sample_property, 'PROP-test-001', sample_address, 
            '51.51°N, -0.13°E', 1985, 'Medium (1925-1975)', 
            750000, True
        )
        assert 'Residential' in prop_section
        assert 'Terraced House' in prop_section
        assert '123 Test Street, London' in prop_section
        assert '£750,000.00' in prop_section
        print("✅ Property section creation working")
        
        print("Testing flood info section creation...")
        flood_section = builder.create_flood_info_section(sample_flood_info)
        assert 'Thames Test Gauge' in flood_section
        assert 'Medium' in flood_section
        assert '£125,000.00' in flood_section
        assert '2.50 km' in flood_section
        print("✅ Flood info section creation working")
        
        print("Testing mortgage section creation...")
        mortgage_section = builder.create_mortgage_section(sample_mortgage, 750000, 'Medium')
        assert 'MTG-test-001' in mortgage_section
        assert 'Test Bank' in mortgage_section
        assert '£500,000.00' in mortgage_section
        assert 'MORTGAGE DETAILS' in mortgage_section
        print("✅ Mortgage section creation working")
        
        print("Testing mortgage risk section creation...")
        risk_section = builder.create_mortgage_risk_section(sample_mortgage_risk)
        assert 'MORTGAGE RISK ANALYSIS' in risk_section
        assert 'MTG-test-001' in risk_section
        assert '£480,000.00' in risk_section  # mortgage_value
        assert 'Medium' in risk_section  # flood_risk_level
        print("✅ Mortgage risk section creation working")
        
        print("Testing complete popup creation...")
        complete_popup = builder.create_complete_popup_content(
            sample_property, 'PROP-test-001', sample_address, 
            '51.51°N, -0.13°E', 'Medium', 'Close', 2.5, False,
            750000, 1985, 'Medium (1925-1975)', True, 
            sample_mortgage, sample_flood_info, sample_mortgage_risk
        )
        
        assert 'Property Analysis' in complete_popup
        assert 'PROP-test-001' in complete_popup
        assert 'font-family: Arial' in complete_popup
        assert 'MORTGAGE DETAILS' in complete_popup
        assert 'MORTGAGE RISK ANALYSIS' in complete_popup
        print("✅ Complete popup creation working")
        
        print("Testing popup builder method...")
        popup_obj = builder.build_property_popup(
            sample_property, 'PROP-test-001', sample_address, 
            '51.51°N, -0.13°E', 'Medium', 'Close', 2.5, False,
            750000, 1985, 'Medium (1925-1975)', True, 
            sample_mortgage, sample_flood_info, sample_mortgage_risk
        )
        assert popup_obj is not None
        print("✅ Popup builder method working")
        
        print("✅ PropertyPopupBuilder tests passed")
        return True
        
    except Exception as e:
        print(f"❌ PropertyPopupBuilder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gauge_popup_builder():
    """Test the GaugePopupBuilder functionality."""
    print("\n" + "=" * 60)
    print("TESTING: GaugePopupBuilder")
    print("=" * 60)
    
    try:
        builder = GaugePopupBuilder()
        
        # Create sample gauge data matching expected structure
        sample_gauge_info = {
            'SensorDetails': {
                'GaugeInformation': {
                    'GaugeOwner': 'Environment Agency',
                    'GaugeType': 'Water Level Gauge',
                    'OperationalStatus': 'Fully operational',
                    'DataSourceType': 'Automatic',
                    'InstallationDate': '2010-03-15',
                    'CertificationStatus': 'Certified'
                },
                'Measurements': {
                    'MeasurementFrequency': 'Every 15 minutes',
                    'MeasurementMethod': 'Pressure sensor',
                    'DataTransmission': 'Telemetry'
                }
            },
            'FloodStage': {
                'UK': {
                    'FloodAlert': 1.5,
                    'FloodWarning': 2.0,
                    'SevereFloodWarning': 2.5
                }
            },
            'SensorStats': {
                'HistoricalHighLevel': 3.2,
                'HistoricalHighDate': '2014-02-07',
                'LastDateLevelExceedLevel3': '2020-12-25',
                'FrequencyExceedLevel3': 5
            }
        }
        
        sample_flood_info = {
            'max_level': 3.5,
            'alert_level': 1.5,
            'warning_level': 2.0,
            'severe_level': 2.5,
            'max_gauge_reading': 3.2
        }
        
        print("Testing status color mapping...")
        assert builder.get_status_color('Fully operational') == '#27AE60'
        assert builder.get_status_color('Maintenance required') == '#F39C12'
        assert builder.get_status_color('Temporarily offline') == '#C0392B'
        print("✅ Status color mapping working")
        
        print("Testing location description...")
        assert 'Central London' in builder.determine_location_description(-0.1)
        assert 'Southeast' in builder.determine_location_description(0.5)
        assert 'East London' in builder.determine_location_description(0.1)
        print("✅ Location description working")
        
        print("Testing equipment details section...")
        equipment_section = builder.create_equipment_details_section(sample_gauge_info)
        assert 'Environment Agency' in equipment_section
        assert 'Water Level Gauge' in equipment_section
        assert 'Fully operational' in equipment_section
        assert 'Equipment Details' in equipment_section
        print("✅ Equipment details section working")
        
        print("Testing measurement approach section...")
        measurement_section = builder.create_measurement_approach_section(sample_gauge_info)
        assert 'Every 15 minutes' in measurement_section
        assert 'Pressure sensor' in measurement_section
        assert 'Telemetry' in measurement_section
        assert 'Measurement Approach' in measurement_section
        print("✅ Measurement approach section working")
        
        print("Testing flood thresholds section...")
        threshold_section = builder.create_flood_thresholds_section(sample_gauge_info)
        assert '1.50 m' in threshold_section
        assert '2.00 m' in threshold_section
        assert '2.50 m' in threshold_section
        assert 'Flood Thresholds' in threshold_section
        print("✅ Flood thresholds section working")
        
        print("Testing historical context section...")
        historical_section = builder.create_historical_context_section(sample_gauge_info)
        assert '3.20 m' in historical_section
        assert '2014-02-07' in historical_section
        assert '5 times' in historical_section
        assert 'Historical Context' in historical_section
        print("✅ Historical context section working")
        
        print("Testing flood risk data section...")
        flood_risk_section = builder.create_flood_risk_data_section(sample_flood_info)
        assert '3.50 m' in flood_risk_section
        assert 'Max Level' in flood_risk_section
        assert 'Flood Risk Data' in flood_risk_section
        print("✅ Flood risk data section working")
        
        print("Testing complete gauge popup creation...")
        # Use coordinates that will map to "East London" (lon > 0 but < 0.3)
        complete_popup = builder.create_complete_gauge_popup_content(
            'GAUGE-test-001', 51.4975, 0.1, sample_gauge_info, sample_flood_info
        )
        assert 'Flood Gauge Analysis' in complete_popup
        assert 'GAUGE-test-001' in complete_popup
        # Updated test - the location should be in the popup content
        assert 'East London' in complete_popup
        assert 'font-family: Arial' in complete_popup
        print("✅ Complete gauge popup creation working")
        
        print("Testing tooltip creation...")
        tooltip = builder.create_gauge_tooltip('Water Level Gauge', 'Fully operational', 1.5)
        assert 'Water Level Gauge' in tooltip
        assert 'Fully operational' in tooltip
        assert '1.50m' in tooltip
        print("✅ Tooltip creation working")
        
        print("Testing popup builder method...")
        popup_obj = builder.build_gauge_popup(
            'GAUGE-test-001', 51.4975, 0.1, sample_gauge_info, sample_flood_info
        )
        assert popup_obj is not None
        print("✅ Popup builder method working")
        
        print("✅ GaugePopupBuilder tests passed")
        return True
        
    except Exception as e:
        print(f"❌ GaugePopupBuilder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_popup_integration():
    """Test integration between popup builders."""
    print("\n" + "=" * 60)
    print("TESTING: Popup Integration")
    print("=" * 60)
    
    try:
        # Test that both builders use the same base functionality
        prop_builder = PropertyPopupBuilder()
        gauge_builder = GaugePopupBuilder()
        
        # Both should format currency the same way
        assert prop_builder.format_currency(1000) == gauge_builder.format_currency(1000)
        print("✅ Currency formatting consistent")
        
        # Both should handle safe float formatting the same way
        assert prop_builder.safe_format_float(3.14159) == gauge_builder.safe_format_float(3.14159)
        print("✅ Float formatting consistent")
        
        # Both should use the same risk color scheme
        assert prop_builder.get_risk_color('High') == gauge_builder.get_risk_color('High')
        print("✅ Risk color scheme consistent")
        
        # Both should create sections with the same structure
        prop_section = prop_builder.create_section("Test", "<p>Content</p>")
        gauge_section = gauge_builder.create_section("Test", "<p>Content</p>")
        assert 'background-color: #EBF5FB' in prop_section
        assert 'background-color: #EBF5FB' in gauge_section
        print("✅ Section creation consistent")
        
        # Test that inheritance is working properly
        assert isinstance(prop_builder, PopupBuilder)
        assert isinstance(gauge_builder, PopupBuilder)
        print("✅ Inheritance working correctly")
        
        print("✅ Popup integration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Popup integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_popup_error_handling():
    """Test error handling in popup builders."""
    print("\n" + "=" * 60)
    print("TESTING: Popup Error Handling")
    print("=" * 60)
    
    try:
        builder = PopupBuilder()
        prop_builder = PropertyPopupBuilder()
        gauge_builder = GaugePopupBuilder()
        
        # Test handling of None/empty data
        print("Testing None/empty data handling...")
        
        # Base builder should handle None values gracefully
        assert builder.safe_format_float(None) == "N/A"
        assert builder.format_currency(None) == "Not available"
        assert builder.format_percentage(None) == "N/A"
        print("✅ Base builder handles None values")
        
        # Property builder should handle empty sections
        empty_flood_section = prop_builder.create_flood_info_section({})
        assert empty_flood_section == ""
        print("✅ Property builder handles empty flood info")
        
        empty_risk_section = prop_builder.create_mortgage_risk_section({})
        assert empty_risk_section == ""
        print("✅ Property builder handles empty mortgage risk")
        
        # Gauge builder should handle empty sections
        empty_flood_data = gauge_builder.create_flood_risk_data_section({})
        assert empty_flood_data == ""
        print("✅ Gauge builder handles empty flood data")
        
        # Test malformed data structures
        print("Testing malformed data handling...")
        
        # Property builder with missing nested data
        incomplete_property = {'PropertyHeader': {}}  # Missing Header
        try:
            section = prop_builder.create_property_section(
                incomplete_property, 'TEST', {}, '', 2000, 'New', 100000, False
            )
            # Should not crash and should contain fallback values
            assert 'Unknown' in section
            print("✅ Property builder handles incomplete data")
        except Exception as e:
            print(f"❌ Property builder failed on incomplete data: {e}")
            return False
        
        # Gauge builder with missing nested data
        incomplete_gauge = {'SensorDetails': {}}  # Missing GaugeInformation
        try:
            section = gauge_builder.create_equipment_details_section(incomplete_gauge)
            # Should not crash and should contain fallback values
            assert 'Unknown' in section
            print("✅ Gauge builder handles incomplete data")
        except Exception as e:
            print(f"❌ Gauge builder failed on incomplete data: {e}")
            return False
        
        print("✅ Popup error handling tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Popup error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all popup tests."""
    print("🧪 POPUP MODULE TESTING SUITE")
    print("=" * 60)
    print(f"Project root: {project_root}")
    
    # Run all tests
    tests = [
        ("Popup Imports", test_popup_imports),
        ("Base PopupBuilder", test_popup_builder_base),
        ("PropertyPopupBuilder", test_property_popup_builder),
        ("GaugePopupBuilder", test_gauge_popup_builder),
        ("Popup Integration", test_popup_integration),
        ("Error Handling", test_popup_error_handling)
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
    print("POPUP TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nResult: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 All popup tests passed! Popup modules are working correctly.")
        print("✅ Popup modules ready for integration with layer modules")
    elif passed_count > 0:
        print("⚠️  Some popup tests passed. Check failures above.")
        print("🔧 Debug failed popup functionality before proceeding")
    else:
        print("💥 All popup tests failed. Check your popup implementations.")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)