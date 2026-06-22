#!/usr/bin/env python

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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""
Master Test Runner: All CDM to JSON Mapping Tests

Runs all CDM validation tests for:
- Gauge portfolio
- Property portfolio
- Mortgage portfolio

Usage:
    python tests/port/run_all_cdm_tests.py
    python tests/port/run_all_cdm_tests.py --quiet
    python tests/port/run_all_cdm_tests.py --catchment rhine
"""

import argparse
import sys
from dataclasses import dataclass
from typing import List, Optional

from config import config


@dataclass
class TestResult:
    """Result from a single test suite."""
    name: str
    passed: bool
    fields_missing: int
    fields_type_invalid: int
    fields_value_invalid: int
    error: Optional[str] = None


def run_all_tests(verbose: bool = True, catchment: Optional[str] = None) -> List[TestResult]:
    """
    Run all CDM mapping tests.

    Args:
        verbose: Show detailed output
        catchment: Override catchment (defaults to config.CATCHMENT)

    Returns:
        List of TestResult objects
    """
    results = []

    # Set catchment if provided (internal scoped setter; still validates + raises
    # ValueError for an unknown catchment — the public setter was removed in WP2.4).
    if catchment:
        try:
            config._set_catchment(catchment)
        except ValueError as e:
            print(f"❌ Error setting catchment: {e}")
            return results

    print("\n" + "#" * 70)
    print("# MKM RESEARCH LABS - CDM TO JSON MAPPING TEST SUITE")
    print("#" * 70)
    print(f"\nCatchment: {config.CATCHMENT}")
    print(f"Input directory: {config.get_input_dir()}")

    # Test 1: Gauge CDM
    print("\n" + "=" * 70)
    print("RUNNING: Gauge CDM Mapping Tests")
    print("=" * 70)
    try:
        from tests.port.test_gauge_cdm_mapping import run_gauge_cdm_test
        summary = run_gauge_cdm_test(verbose=verbose)
        results.append(TestResult(
            name="Gauge CDM",
            passed=(summary.fields_missing == 0 and
                   summary.fields_type_invalid == 0 and
                   summary.fields_value_invalid == 0),
            fields_missing=summary.fields_missing,
            fields_type_invalid=summary.fields_type_invalid,
            fields_value_invalid=summary.fields_value_invalid
        ))
    except FileNotFoundError as e:
        print(f"⚠️  Skipped: {e}")
        results.append(TestResult(
            name="Gauge CDM",
            passed=False,
            fields_missing=0,
            fields_type_invalid=0,
            fields_value_invalid=0,
            error=f"File not found: {e}"
        ))
    except Exception as e:
        print(f"❌ Error: {e}")
        results.append(TestResult(
            name="Gauge CDM",
            passed=False,
            fields_missing=0,
            fields_type_invalid=0,
            fields_value_invalid=0,
            error=str(e)
        ))

    # Test 2: Property CDM
    print("\n" + "=" * 70)
    print("RUNNING: Property CDM Mapping Tests")
    print("=" * 70)
    try:
        from tests.port.test_property_cdm_mapping import run_property_cdm_test
        summary = run_property_cdm_test(verbose=verbose)
        results.append(TestResult(
            name="Property CDM",
            passed=(summary.fields_missing == 0 and
                   summary.fields_type_invalid == 0 and
                   summary.fields_value_invalid == 0),
            fields_missing=summary.fields_missing,
            fields_type_invalid=summary.fields_type_invalid,
            fields_value_invalid=summary.fields_value_invalid
        ))
    except FileNotFoundError as e:
        print(f"⚠️  Skipped: {e}")
        results.append(TestResult(
            name="Property CDM",
            passed=False,
            fields_missing=0,
            fields_type_invalid=0,
            fields_value_invalid=0,
            error=f"File not found: {e}"
        ))
    except Exception as e:
        print(f"❌ Error: {e}")
        results.append(TestResult(
            name="Property CDM",
            passed=False,
            fields_missing=0,
            fields_type_invalid=0,
            fields_value_invalid=0,
            error=str(e)
        ))

    # Test 3: Mortgage CDM
    print("\n" + "=" * 70)
    print("RUNNING: Mortgage CDM Mapping Tests")
    print("=" * 70)
    try:
        from tests.port.test_mortgage_cdm_mapping import run_mortgage_cdm_test
        summary = run_mortgage_cdm_test(verbose=verbose)
        results.append(TestResult(
            name="Mortgage CDM",
            passed=(summary.fields_missing == 0 and
                   summary.fields_type_invalid == 0 and
                   summary.fields_value_invalid == 0),
            fields_missing=summary.fields_missing,
            fields_type_invalid=summary.fields_type_invalid,
            fields_value_invalid=summary.fields_value_invalid
        ))
    except FileNotFoundError as e:
        print(f"⚠️  Skipped: {e}")
        results.append(TestResult(
            name="Mortgage CDM",
            passed=False,
            fields_missing=0,
            fields_type_invalid=0,
            fields_value_invalid=0,
            error=f"File not found: {e}"
        ))
    except Exception as e:
        print(f"❌ Error: {e}")
        results.append(TestResult(
            name="Mortgage CDM",
            passed=False,
            fields_missing=0,
            fields_type_invalid=0,
            fields_value_invalid=0,
            error=str(e)
        ))

    return results


def print_final_summary(results: List[TestResult]):
    """Print final summary of all tests."""
    print("\n" + "#" * 70)
    print("# FINAL SUMMARY")
    print("#" * 70)

    total_passed = sum(1 for r in results if r.passed)
    total_tests = len(results)

    print(f"\n{'Test Suite':<20} {'Status':<10} {'Missing':<10} {'Type Err':<10} {'Value Err':<10}")
    print("-" * 70)

    for result in results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        if result.error:
            status = "⚠️  SKIP"
        print(f"{result.name:<20} {status:<10} {result.fields_missing:<10} {result.fields_type_invalid:<10} {result.fields_value_invalid:<10}")
        if result.error:
            print(f"   └─ {result.error}")

    print("-" * 70)
    print(f"\nTotal: {total_passed}/{total_tests} test suites passed")

    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run all CDM to JSON mapping tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python tests/port/run_all_cdm_tests.py
    python tests/port/run_all_cdm_tests.py --quiet
    python tests/port/run_all_cdm_tests.py --catchment thames
        """
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output (only show failures and summary)"
    )
    parser.add_argument(
        "--catchment", "-c",
        type=str,
        default=None,
        help="Catchment to test (defaults to config.CATCHMENT)"
    )

    args = parser.parse_args()

    results = run_all_tests(verbose=not args.quiet, catchment=args.catchment)
    exit_code = print_final_summary(results)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
