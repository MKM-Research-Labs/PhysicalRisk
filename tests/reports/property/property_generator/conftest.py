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

"""Shared fixtures and helpers for property_generator tests."""

from pathlib import Path
from typing import Any, Dict

import pytest


def _minimal_property(property_id: str = "PROP-001") -> Dict[str, Any]:
    """Minimal CDM-shaped property dict."""
    return {
        "PropertyHeader": {
            "Header": {"PropertyID": property_id},
            "Location": {"LatitudeDegrees": 51.5, "LongitudeDegrees": -0.1},
            "Valuation": {"PropertyValue": 400_000},
            "RiskAssessment": {"OverallFloodRisk": "Medium"},
            "Attributes": {
                "PropertyType": "Residential",
                "NumberOfBedrooms": 3,
                "FloorArea": 90.0,
            },
            "Construction": {
                "YearBuilt": 1990,
                "ConstructionType": "Brick",
            },
            "FloodProtection": {
                "HasFloodBarrier": False,
            },
            "History": {"FloodEvents": []},
            "Transactions": {"SaleHistory": []},
        }
    }


def _full_property(property_id: str = "PROP-FULL") -> Dict[str, Any]:
    """Richer property dict."""
    base = _minimal_property(property_id)
    base["PropertyHeader"].update({
        "FinancialDetails": {
            "PurchasePrice": 380_000,
            "CurrentValue": 430_000,
        },
        "CurrentStatus": {"OccupancyStatus": "Owner-occupied"},
    })
    return base


def _minimal_mortgage(property_id: str = "PROP-001") -> Dict[str, Any]:
    return {
        "Mortgage": {
            "Header": {"MortgageID": "MORT-001", "PropertyID": property_id},
            "FinancialTerms": {
                "OriginalLoan": 300_000,
                "InterestRate": 3.5,
                "TermYears": 25,
            },
            "CurrentStatus": {"OutstandingBalance": 280_000},
            "BorrowerProfile": {"CreditScore": 720},
            "RegulatoryStatus": {"LTVRatio": 0.65},
        }
    }


def _make_generator(tmp_path: Path):
    from reports.property.property_generator import PropertyReportGenerator
    return PropertyReportGenerator(output_dir=tmp_path)


@pytest.fixture
def output_dir(tmp_path) -> Path:
    d = tmp_path / "prop_out"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def prop_data() -> Dict[str, Any]:
    return _minimal_property()


@pytest.fixture
def full_prop_data() -> Dict[str, Any]:
    return _full_property()


@pytest.fixture
def mort_data() -> Dict[str, Any]:
    return _minimal_mortgage()
