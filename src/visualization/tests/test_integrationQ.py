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
Quick integration test runner for the refactored visualization system.

This is a simpler test that focuses on verifying the basic integration
between your refactored modules without requiring extensive test data.
"""

import sys
from pathlib import Path

# Add project root to path
# From src/visualization/tests/ we need to go up 3 levels to reach project root
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported successfully."""
    print("🔍 Testing module imports...")
    
    try:
        # Test core imports
        from src.visualization.core.visualizer import TCEventVisualization
        from src.visualization.core.data_loader import DataLoader
        from src.visualization.core.map_builder import MapBuilder
        print("  ✅ Core modules imported successfully")
        
        # Test layer imports
        from src.visualization.layers.storm_layer import StormLayer
        from src.visualization.layers.gauge_layer import GaugeLayer
        from src.visualization.layers.property_layer import PropertyLayer
        from src.visualization.layers.mortgage_layer import MortgageLayer
        print("  ✅ Layer modules imported successfully")
        
        # Test popup imports
        from src.visualization.popups.property_popup import PropertyPopupBuilder
        from src.visualization.popups.gauge_popup import GaugePopupBuilder
        print("  ✅ Popup modules imported successfully")
        
        # Test interactivity imports
        from src.visualization.interactivity.context_menus import ContextMenuHandler
        from src.visualization.interactivity.backend_handler import BackendHandler
        print("  ✅ Interactivity modules imported successfully")
        
        # Test utility imports
        from src.visualization.utils.data_extractors import PropertyDataExtractor
        from src.visualization.utils.risk_assessors import RiskAssessor
        from src.visualization.utils.formatters import DataFormatter
        print("  ✅ Utility modules imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False

def test_module_instantiation():
    """Test that all modules can be instantiated."""
    print("\n🏗️  Testing module instantiation...")
    
    try:
        # Import modules
        from src.visualization.core.visualizer import TCEventVisualization
        from src.visualization.core.data_loader import DataLoader
        from src.visualization.core.map_builder import MapBuilder
        from src.visualization.layers.storm_layer import StormLayer
        from src.visualization.layers.gauge_layer import GaugeLayer
        from src.visualization.layers.property_layer import PropertyLayer
        from src.visualization.layers.mortgage_layer import MortgageLayer
        from src.visualization.popups.property_popup import PropertyPopupBuilder
        from src.visualization.popups.gauge_popup import GaugePopupBuilder
        from src.visualization.interactivity.context_menus import ContextMenuHandler
        from src.visualization.interactivity.backend_handler import BackendHandler
        from src.visualization.utils.data_extractors import PropertyDataExtractor
        from src.visualization.utils.risk_assessors import RiskAssessor
        from src.visualization.utils.formatters import DataFormatter
        
        # Test instantiation
        visualizer = TCEventVisualization()
        data_loader = DataLoader()
        map_builder = MapBuilder()
        print("  ✅ Core modules instantiated successfully")
        
        storm_layer = StormLayer()
        gauge_layer = GaugeLayer()
        property_layer = PropertyLayer()
        mortgage_layer = MortgageLayer()
        print("  ✅ Layer modules instantiated successfully")
        
        property_popup = PropertyPopupBuilder()
        gauge_popup = GaugePopupBuilder()
        print("  ✅ Popup modules instantiated successfully")
        
        context_handler = ContextMenuHandler()
        backend_handler = BackendHandler()
        print("  ✅ Interactivity modules instantiated successfully")
        
        extractor = PropertyDataExtractor()
        risk_assessor = RiskAssessor()
        formatter = DataFormatter()
        print("  ✅ Utility modules instantiated successfully")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Instantiation failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality of key modules."""
    print("\n⚙️  Testing basic functionality...")
    
    try:
        from src.visualization.interactivity.backend_handler import BackendHandler
        from src.visualization.interactivity.context_menus import ContextMenuHandler
        from src.visualization.utils.formatters import DataFormatter
        from src.visualization.utils.risk_assessors import RiskAssessor
        
        # Test backend handler
        backend = BackendHandler()
        js_code = backend.get_backend_js()
        assert isinstance(js_code, str) and len(js_code) > 0
        assert "generateReport" in js_code
        print("  ✅ Backend handler functionality works")
        
        # Test context menu handler
        context = ContextMenuHandler()
        menu_js = context.get_base_context_menu_js()
        assert isinstance(menu_js, str) and len(menu_js) > 0
        assert "createContextMenu" in menu_js
        print("  ✅ Context menu handler functionality works")
        
        # Test formatter
        formatter = DataFormatter()
        formatted = formatter.format_currency(500000)
        assert isinstance(formatted, str)
        assert "£" in formatted
        print("  ✅ Data formatter functionality works")
        
        # Test risk assessor
        risk_assessor = RiskAssessor()
        color = risk_assessor.get_risk_color("High")
        assert isinstance(color, str)
        print("  ✅ Risk assessor functionality works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Functionality test failed: {e}")
        return False

def test_module_communication():
    """Test that modules can communicate with each other."""
    print("\n🔗 Testing module communication...")
    
    try:
        from src.visualization.core.visualizer import TCEventVisualization
        from src.visualization.interactivity.backend_handler import BackendHandler
        from src.visualization.interactivity.context_menus import ContextMenuHandler
        
        # Test that visualizer can use interactivity modules
        visualizer = TCEventVisualization()
        
        # Create mock folium map for testing
        from unittest.mock import Mock
        mock_map = Mock()
        mock_map.get_root.return_value.html.add_child = Mock()
        
        # Test backend handler integration
        backend = BackendHandler()
        backend.add_to_map(mock_map)  # Should not raise exception
        print("  ✅ Backend handler integrates with map")
        
        # Test context menu integration
        context = ContextMenuHandler()
        context.add_to_map(mock_map)  # Should not raise exception
        print("  ✅ Context menu handler integrates with map")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Module communication test failed: {e}")
        return False

def test_configuration():
    """Test module configuration capabilities."""
    print("\n⚙️  Testing module configuration...")
    
    try:
        from src.visualization.interactivity.backend_handler import BackendHandler
        from src.visualization.interactivity.context_menus import ContextMenuHandler
        
        # Test backend handler configuration
        backend = BackendHandler()
        original_url = backend.server_url
        
        backend.configure(server_url="http://test.example.com:8080")
        assert backend.server_url == "http://test.example.com:8080"
        
        stats = backend.get_statistics()
        assert isinstance(stats, dict)
        assert "server_url" in stats
        print("  ✅ Backend handler configuration works")
        
        # Test context menu configuration
        context = ContextMenuHandler()
        custom_items = [{"id": "test", "label": "Test", "action": "testAction"}]
        context.configure(property_menu_items=custom_items)
        
        stats = context.get_statistics()
        assert isinstance(stats, dict)
        assert "property_menu_items" in stats
        print("  ✅ Context menu configuration works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False

def test_with_existing_data():
    """Test with existing data files if they exist."""
    print("\n📁 Testing with existing data files...")
    
    try:
        from src.visualization.core.visualizer import TCEventVisualization
        
        # Check if standard data files exist
        current_dir = Path.cwd()
        possible_input_dirs = [
            current_dir / "input",
            current_dir / "data",
            current_dir / "test_data",
            current_dir.parent / "input",
            current_dir.parent / "data"
        ]
        
        input_dir = None
        for dir_path in possible_input_dirs:
            if dir_path.exists():
                input_dir = dir_path
                break
        
        if not input_dir:
            print("  ⚠️  No existing data directories found - skipping data file test")
            return True
        
        print(f"  📂 Found input directory: {input_dir}")
        
        # Look for common data files
        common_files = [
            "single_tceventts.json",
            "flood_gauge_portfolio.json", 
            "property_portfolio.json",
            "mortgage_portfolio.json",
            "flood_risk_report.json"
        ]
        
        existing_files = []
        for filename in common_files:
            if (input_dir / filename).exists():
                existing_files.append(filename)
        
        if not existing_files:
            print("  ⚠️  No standard data files found - skipping data loading test")
            return True
        
        print(f"  📄 Found data files: {existing_files}")
        
        # Test with existing files
        visualizer = TCEventVisualization(str(input_dir))
        
        # Try to load any TC event file
        tc_files = list(input_dir.glob("*tc*.json"))
        if tc_files:
            tc_file = tc_files[0]
            print(f"  🌪️  Testing with TC file: {tc_file.name}")
            
            # Attempt to load just the TC data
            try:
                import json
                with open(tc_file) as f:
                    tc_data = json.load(f)
                    
                if 'timeseries' in tc_data and len(tc_data['timeseries']) > 0:
                    print("  ✅ TC data structure looks valid")
                else:
                    print("  ⚠️  TC data structure may be incomplete")
                    
            except Exception as e:
                print(f"  ⚠️  Could not validate TC data: {e}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Existing data test failed: {e}")
        return False

def run_quick_tests():
    """Run all quick integration tests."""
    print("🚀 Quick Integration Test Suite for Refactored Visualization System")
    print("=" * 70)
    
    tests = [
        ("Module Imports", test_imports),
        ("Module Instantiation", test_module_instantiation), 
        ("Basic Functionality", test_basic_functionality),
        ("Module Communication", test_module_communication),
        ("Configuration", test_configuration),
        ("Existing Data Files", test_with_existing_data)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your refactored system is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the output above for details.")
        return False

def check_file_structure():
    """Check if the expected file structure exists."""
    print("\n📂 Checking project file structure...")
    
    expected_structure = {
        "src/visualization/": [
            "__init__.py",
            "core/",
            "layers/", 
            "popups/",
            "interactivity/",
            "utils/",
            "tests/"
        ],
        "src/visualization/core/": [
            "__init__.py",
            "visualizer.py",
            "data_loader.py",
            "map_builder.py"
        ],
        "src/visualization/layers/": [
            "__init__.py",
            "storm_layer.py",
            "gauge_layer.py", 
            "property_layer.py",
            "mortgage_layer.py"
        ],
        "src/visualization/popups/": [
            "__init__.py",
            "property_popup.py",
            "gauge_popup.py",
            "popup_builder.py"
        ],
        "src/visualization/interactivity/": [
            "__init__.py",
            "context_menus.py",
            "backend_handler.py",
            "notifications.py"
        ],
        "src/visualization/utils/": [
            "__init__.py",
            "data_extractors.py",
            "risk_assessors.py", 
            "formatters.py",
            "color_schemes.py"
        ]
    }
    
    current_dir = Path.cwd()
    missing_files = []
    
    for directory, files in expected_structure.items():
        dir_path = current_dir / directory
        
        if not dir_path.exists():
            missing_files.append(f"Directory: {directory}")
            continue
            
        for file in files:
            file_path = dir_path / file
            if not file_path.exists():
                missing_files.append(f"File: {directory}{file}")
    
    if missing_files:
        print("  ⚠️  Missing files/directories:")
        for missing in missing_files[:10]:  # Show first 10
            print(f"    - {missing}")
        if len(missing_files) > 10:
            print(f"    ... and {len(missing_files) - 10} more")
        return False
    else:
        print("  ✅ All expected files and directories found")
        return True

if __name__ == "__main__":
    print("Starting quick integration tests...\n")
    
    # First check file structure
    structure_ok = check_file_structure()
    
    if structure_ok:
        # Run the tests
        success = run_quick_tests()
        
        if success:
            print("\n🎊 INTEGRATION TEST SUCCESS!")
            print("Your refactored visualization system is ready to use.")
            print("\nNext steps:")
            print("1. Try running the main visualization script")
            print("2. Test with your actual data files")
            print("3. Verify the HTML output renders correctly")
        else:
            print("\n🔧 INTEGRATION TEST ISSUES DETECTED")
            print("Please address the failed tests before proceeding.")
        
        sys.exit(0 if success else 1)
    else:
        print("\n❌ FILE STRUCTURE INCOMPLETE")
        print("Please ensure all modules have been properly created.")
        sys.exit(1)