#!/usr/bin/env python3

# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Verification script for the popups package structure.

This script verifies that the package is properly structured and can be imported.
"""

import sys
from pathlib import Path

# Add the outputs directory to Python path for testing
outputs_dir = Path(__file__).parent
if str(outputs_dir) not in sys.path:
    sys.path.insert(0, str(outputs_dir))


def test_package_structure():
    """Verify package structure exists."""
    print("=" * 60)
    print("VERIFYING PACKAGE STRUCTURE")
    print("=" * 60)

    viz_dir = outputs_dir / "visualization"
    popups_dir = viz_dir / "popups"

    required_files = [
        viz_dir / "__init__.py",
        popups_dir / "__init__.py",
        popups_dir / "popup_builder.py",
        popups_dir / "property_popup.py",
        popups_dir / "gauge_popup.py",
        popups_dir / "README.md",
        popups_dir / "CLEANUP_SUMMARY.md"
    ]

    all_exist = True
    for file in required_files:
        exists = file.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {file.relative_to(outputs_dir)}")
        if not exists:
            all_exist = False

    return all_exist


def test_imports():
    """Verify package can be imported."""
    print("\n" + "=" * 60)
    print("TESTING IMPORTS")
    print("=" * 60)

    tests = []

    # Test 1: Import package
    try:
        import visualization
        print("✓ import visualization")
        tests.append(True)
    except ImportError as e:
        print(f"✗ import visualization - {e}")
        tests.append(False)

    # Test 2: Import popups subpackage
    try:
        import visualization.popups
        print("✓ import visualization.popups")
        tests.append(True)
    except ImportError as e:
        print(f"✗ import visualization.popups - {e}")
        tests.append(False)

    # Test 3: Import from popups
    try:
        from visualization.popups import PopupBuilder
        print("✓ from visualization.popups import PopupBuilder")
        tests.append(True)
    except ImportError as e:
        print(f"✗ from visualization.popups import PopupBuilder - {e}")
        tests.append(False)

    # Test 4: Import PropertyPopupBuilder
    try:
        from visualization.popups import PropertyPopupBuilder
        print("✓ from visualization.popups import PropertyPopupBuilder")
        tests.append(True)
    except ImportError as e:
        print(f"✗ from visualization.popups import PropertyPopupBuilder - {e}")
        tests.append(False)

    # Test 5: Import GaugePopupBuilder
    try:
        from visualization.popups import GaugePopupBuilder
        print("✓ from visualization.popups import GaugePopupBuilder")
        tests.append(True)
    except ImportError as e:
        print(f"✗ from visualization.popups import GaugePopupBuilder - {e}")
        tests.append(False)

    # Test 6: Import all at once
    try:
        from visualization.popups import GaugePopupBuilder, PopupBuilder, PropertyPopupBuilder
        print("✓ from visualization.popups import PopupBuilder, PropertyPopupBuilder, GaugePopupBuilder")
        tests.append(True)
    except ImportError as e:
        print(f"✗ Multiple import - {e}")
        tests.append(False)

    return all(tests)


def test_class_instantiation():
    """Verify classes can be instantiated."""
    print("\n" + "=" * 60)
    print("TESTING CLASS INSTANTIATION")
    print("=" * 60)

    tests = []

    try:
        from visualization.popups import PopupBuilder
        builder = PopupBuilder()
        print("✓ PopupBuilder() instantiated")
        tests.append(True)
    except Exception as e:
        print(f"✗ PopupBuilder() - {e}")
        tests.append(False)

    try:
        from visualization.popups import PropertyPopupBuilder
        builder = PropertyPopupBuilder()
        print("✓ PropertyPopupBuilder() instantiated")
        tests.append(True)
    except Exception as e:
        print(f"✗ PropertyPopupBuilder() - {e}")
        tests.append(False)

    try:
        from visualization.popups import GaugePopupBuilder
        builder = GaugePopupBuilder()
        print("✓ GaugePopupBuilder() instantiated")
        tests.append(True)
    except Exception as e:
        print(f"✗ GaugePopupBuilder() - {e}")
        tests.append(False)

    return all(tests)


def test_inheritance():
    """Verify inheritance structure."""
    print("\n" + "=" * 60)
    print("TESTING INHERITANCE")
    print("=" * 60)

    try:
        from visualization.popups import GaugePopupBuilder, PopupBuilder, PropertyPopupBuilder

        prop_builder = PropertyPopupBuilder()
        gauge_builder = GaugePopupBuilder()

        # Test PropertyPopupBuilder inherits from PopupBuilder
        is_subclass = isinstance(prop_builder, PopupBuilder)
        status = "✓" if is_subclass else "✗"
        print(f"{status} PropertyPopupBuilder inherits from PopupBuilder: {is_subclass}")

        # Test GaugePopupBuilder inherits from PopupBuilder
        is_subclass = isinstance(gauge_builder, PopupBuilder)
        status = "✓" if is_subclass else "✗"
        print(f"{status} GaugePopupBuilder inherits from PopupBuilder: {is_subclass}")

        # Test they have base class methods
        has_methods = all([
            hasattr(prop_builder, 'create_section'),
            hasattr(prop_builder, 'create_header'),
            hasattr(prop_builder, 'format_currency'),
            hasattr(gauge_builder, 'create_section'),
            hasattr(gauge_builder, 'create_header'),
            hasattr(gauge_builder, 'safe_format_float')
        ])
        status = "✓" if has_methods else "✗"
        print(f"{status} Builders have base class methods: {has_methods}")

        return True
    except Exception as e:
        print(f"✗ Inheritance test failed - {e}")
        return False


def test_no_path_manipulation():
    """Verify no path manipulation in source files."""
    print("\n" + "=" * 60)
    print("VERIFYING NO PATH MANIPULATION")
    print("=" * 60)

    popups_dir = outputs_dir / "visualization" / "popups"
    source_files = [
        popups_dir / "popup_builder.py",
        popups_dir / "property_popup.py",
        popups_dir / "gauge_popup.py"
    ]

    forbidden_patterns = [
        "sys.path.insert",
        "sys.path.append",
        "os.path.join",
        "__file__",
        "Path(__file__)",
        "parent.parent",
    ]

    all_clean = True
    for file in source_files:
        content = file.read_text()
        found_issues = []

        for pattern in forbidden_patterns:
            if pattern in content:
                found_issues.append(pattern)

        if found_issues:
            print(f"✗ {file.name} - Found: {', '.join(found_issues)}")
            all_clean = False
        else:
            print(f"✓ {file.name} - No path manipulation")

    return all_clean


def test_relative_imports():
    """Verify relative imports are used correctly."""
    print("\n" + "=" * 60)
    print("VERIFYING RELATIVE IMPORTS")
    print("=" * 60)

    popups_dir = outputs_dir / "visualization" / "popups"

    # Check property_popup.py
    prop_file = popups_dir / "property_popup.py"
    content = prop_file.read_text()

    has_relative = "from .popup_builder import PopupBuilder" in content
    status = "✓" if has_relative else "✗"
    print(f"{status} property_popup.py uses relative import: {has_relative}")

    # Check gauge_popup.py
    gauge_file = popups_dir / "gauge_popup.py"
    content = gauge_file.read_text()

    has_relative = "from .popup_builder import PopupBuilder" in content
    status = "✓" if has_relative else "✗"
    print(f"{status} gauge_popup.py uses relative import: {has_relative}")

    # Check __init__.py
    init_file = popups_dir / "__init__.py"
    content = init_file.read_text()

    has_all_imports = all([
        "from .popup_builder import PopupBuilder" in content,
        "from .property_popup import PropertyPopupBuilder" in content,
        "from .gauge_popup import GaugePopupBuilder" in content
    ])
    status = "✓" if has_all_imports else "✗"
    print(f"{status} __init__.py uses relative imports: {has_all_imports}")

    return has_relative and has_all_imports


def main():
    """Run all verification tests."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "POPUPS PACKAGE VERIFICATION SUITE" + " " * 14 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    results = {
        "Package Structure": test_package_structure(),
        "Imports": test_imports(),
        "Class Instantiation": test_class_instantiation(),
        "Inheritance": test_inheritance(),
        "No Path Manipulation": test_no_path_manipulation(),
        "Relative Imports": test_relative_imports()
    }

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} {test_name}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED - Package is properly structured!")
    else:
        print("✗ SOME TESTS FAILED - Review issues above")
    print("=" * 60)
    print()

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
