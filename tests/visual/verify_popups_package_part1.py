#!/usr/bin/env python3

# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Verification script for the popups package structure — part 1.

Covers: test_package_structure, test_imports, test_class_instantiation.
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
        status = "\u2713" if exists else "\u2717"
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
        print("\u2713 import visualization")
        tests.append(True)
    except ImportError as e:
        print(f"\u2717 import visualization - {e}")
        tests.append(False)

    # Test 2: Import popups subpackage
    try:
        import visualization.popups
        print("\u2713 import visualization.popups")
        tests.append(True)
    except ImportError as e:
        print(f"\u2717 import visualization.popups - {e}")
        tests.append(False)

    # Test 3: Import from popups
    try:
        from visualization.popups import PopupBuilder
        print("\u2713 from visualization.popups import PopupBuilder")
        tests.append(True)
    except ImportError as e:
        print(f"\u2717 from visualization.popups import PopupBuilder - {e}")
        tests.append(False)

    # Test 4: Import PropertyPopupBuilder
    try:
        from visualization.popups import PropertyPopupBuilder
        print("\u2713 from visualization.popups import PropertyPopupBuilder")
        tests.append(True)
    except ImportError as e:
        print(f"\u2717 from visualization.popups import PropertyPopupBuilder - {e}")
        tests.append(False)

    # Test 5: Import GaugePopupBuilder
    try:
        from visualization.popups import GaugePopupBuilder
        print("\u2713 from visualization.popups import GaugePopupBuilder")
        tests.append(True)
    except ImportError as e:
        print(f"\u2717 from visualization.popups import GaugePopupBuilder - {e}")
        tests.append(False)

    # Test 6: Import all at once
    try:
        from visualization.popups import GaugePopupBuilder, PopupBuilder, PropertyPopupBuilder
        print("\u2713 from visualization.popups import PopupBuilder, PropertyPopupBuilder, GaugePopupBuilder")
        tests.append(True)
    except ImportError as e:
        print(f"\u2717 Multiple import - {e}")
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
        print("\u2713 PopupBuilder() instantiated")
        tests.append(True)
    except Exception as e:
        print(f"\u2717 PopupBuilder() - {e}")
        tests.append(False)

    try:
        from visualization.popups import PropertyPopupBuilder
        builder = PropertyPopupBuilder()
        print("\u2713 PropertyPopupBuilder() instantiated")
        tests.append(True)
    except Exception as e:
        print(f"\u2717 PropertyPopupBuilder() - {e}")
        tests.append(False)

    try:
        from visualization.popups import GaugePopupBuilder
        builder = GaugePopupBuilder()
        print("\u2713 GaugePopupBuilder() instantiated")
        tests.append(True)
    except Exception as e:
        print(f"\u2717 GaugePopupBuilder() - {e}")
        tests.append(False)

    return all(tests)
