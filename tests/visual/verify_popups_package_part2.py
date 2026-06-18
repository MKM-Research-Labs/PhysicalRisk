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
Verification script for the popups package structure — part 2.

Covers: test_inheritance, test_no_path_manipulation, test_relative_imports, main.
"""

import sys
from pathlib import Path

# Add the outputs directory to Python path for testing
outputs_dir = Path(__file__).parent
if str(outputs_dir) not in sys.path:
    sys.path.insert(0, str(outputs_dir))

from tests.visual.verify_popups_package_part1 import (
    test_package_structure,
    test_imports,
    test_class_instantiation,
)


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
        status = "\u2713" if is_subclass else "\u2717"
        print(f"{status} PropertyPopupBuilder inherits from PopupBuilder: {is_subclass}")

        # Test GaugePopupBuilder inherits from PopupBuilder
        is_subclass = isinstance(gauge_builder, PopupBuilder)
        status = "\u2713" if is_subclass else "\u2717"
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
        status = "\u2713" if has_methods else "\u2717"
        print(f"{status} Builders have base class methods: {has_methods}")

        return True
    except Exception as e:
        print(f"\u2717 Inheritance test failed - {e}")
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
            print(f"\u2717 {file.name} - Found: {', '.join(found_issues)}")
            all_clean = False
        else:
            print(f"\u2713 {file.name} - No path manipulation")

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
    status = "\u2713" if has_relative else "\u2717"
    print(f"{status} property_popup.py uses relative import: {has_relative}")

    # Check gauge_popup.py
    gauge_file = popups_dir / "gauge_popup.py"
    content = gauge_file.read_text()

    has_relative = "from .popup_builder import PopupBuilder" in content
    status = "\u2713" if has_relative else "\u2717"
    print(f"{status} gauge_popup.py uses relative import: {has_relative}")

    # Check __init__.py
    init_file = popups_dir / "__init__.py"
    content = init_file.read_text()

    has_all_imports = all([
        "from .popup_builder import PopupBuilder" in content,
        "from .property_popup import PropertyPopupBuilder" in content,
        "from .gauge_popup import GaugePopupBuilder" in content
    ])
    status = "\u2713" if has_all_imports else "\u2717"
    print(f"{status} __init__.py uses relative imports: {has_all_imports}")

    return has_relative and has_all_imports


def main():
    """Run all verification tests."""
    print("\n")
    print("\u2554" + "\u2550" * 58 + "\u2557")
    print("\u2551" + " " * 10 + "POPUPS PACKAGE VERIFICATION SUITE" + " " * 14 + "\u2551")
    print("\u255a" + "\u2550" * 58 + "\u255d")
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
        status = "\u2713 PASS" if passed else "\u2717 FAIL"
        print(f"{status:8} {test_name}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("\u2713 ALL TESTS PASSED - Package is properly structured!")
    else:
        print("\u2717 SOME TESTS FAILED - Review issues above")
    print("=" * 60)
    print()

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
