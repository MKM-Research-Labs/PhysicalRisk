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

"""Tests for risk_page_06_property_details.py coverage:
- Lines 200-201: exception handler in generate_elements
- Lines 250-253: _categorize_property_values for 2M-5M and Over 5M categories
"""

import pytest

from reports.risk.risk_page_06_property_details import RiskPropertyDetailsPage


class TestCategorizePropertyValues:
    """Cover lines 250-253: the 2M-5M and Over 5M value categories."""

    def test_property_in_2m_to_5m_range(self):
        """A property valued at 3M falls into the 2M-5M category."""
        page = RiskPropertyDetailsPage()
        property_risk = {
            "P1": {
                "property_id": "P1",
                "property_value": 3_000_000,
                "risk_level": "High",
                "value_at_risk": 500_000,
            },
        }
        categories = page._categorize_property_values(property_risk)
        assert categories["\u00a32M-\u00a35M"]["total_count"] == 1
        assert categories["\u00a32M-\u00a35M"]["at_risk_count"] == 1
        assert categories["\u00a32M-\u00a35M"]["total_value_at_risk"] == 500_000

    def test_property_over_5m(self):
        """A property valued at 6M falls into the Over 5M category."""
        page = RiskPropertyDetailsPage()
        property_risk = {
            "P1": {
                "property_id": "P1",
                "property_value": 6_000_000,
                "risk_level": "Medium",
                "value_at_risk": 1_000_000,
            },
        }
        categories = page._categorize_property_values(property_risk)
        assert categories["Over \u00a35M"]["total_count"] == 1
        assert categories["Over \u00a35M"]["at_risk_count"] == 1
        assert categories["Over \u00a35M"]["total_value_at_risk"] == 1_000_000

    def test_mixed_value_categories(self):
        """Multiple properties across different value bands are categorized correctly."""
        page = RiskPropertyDetailsPage()
        property_risk = {
            "P1": {"property_value": 300_000, "risk_level": "Low", "value_at_risk": 0},
            "P2": {"property_value": 750_000, "risk_level": "High", "value_at_risk": 100_000},
            "P3": {"property_value": 1_500_000, "risk_level": "Medium", "value_at_risk": 200_000},
            "P4": {"property_value": 3_500_000, "risk_level": "High", "value_at_risk": 500_000},
            "P5": {"property_value": 7_000_000, "risk_level": "High", "value_at_risk": 2_000_000},
        }
        categories = page._categorize_property_values(property_risk)
        assert categories["Under \u00a3500K"]["total_count"] == 1
        assert categories["\u00a3500K-\u00a31M"]["total_count"] == 1
        assert categories["\u00a31M-\u00a32M"]["total_count"] == 1
        assert categories["\u00a32M-\u00a35M"]["total_count"] == 1
        assert categories["Over \u00a35M"]["total_count"] == 1

    def test_low_risk_property_not_counted_as_at_risk(self):
        """Properties with risk_level 'Low' are not counted as at-risk."""
        page = RiskPropertyDetailsPage()
        property_risk = {
            "P1": {
                "property_value": 4_000_000,
                "risk_level": "Low",
                "value_at_risk": 0,
            },
        }
        categories = page._categorize_property_values(property_risk)
        assert categories["\u00a32M-\u00a35M"]["total_count"] == 1
        assert categories["\u00a32M-\u00a35M"]["at_risk_count"] == 0


class TestGenerateElementsExceptionHandler:
    """Cover lines 200-201: exception handler appends error paragraph."""

    def test_error_in_generate_elements(self):
        """When generate_elements encounters an error, it appends an error paragraph."""
        page = RiskPropertyDetailsPage()
        # Pass data that will trigger a TypeError in _analyze_property_values
        # because property_risk values are not dicts
        bad_flood_data = {
            "property_risk": "not-a-dict",  # .values() will yield characters
        }
        elements = page.generate_elements(bad_flood_data)
        # Should have at least one element (the error paragraph)
        assert len(elements) >= 1
        # The last element should contain the error message text
        # (Paragraph objects store text in their .text attribute)
        error_el = elements[-1]
        assert "Error generating property details" in error_el.text

    def test_error_with_none_property_risk(self):
        """When property_risk is None, generate_elements handles the error."""
        page = RiskPropertyDetailsPage()
        bad_flood_data = {"property_risk": None}
        elements = page.generate_elements(bad_flood_data)
        assert len(elements) >= 1
        error_el = elements[-1]
        assert "Error generating property details" in error_el.text
