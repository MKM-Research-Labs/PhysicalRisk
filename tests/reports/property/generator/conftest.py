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

"""Shared fixtures and helpers for PropertyReportGenerator tests."""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Data builders
# ---------------------------------------------------------------------------

def minimal_property(property_id: str = "PROP-001") -> Dict[str, Any]:
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


def full_property(property_id: str = "PROP-FULL") -> Dict[str, Any]:
    """Richer property dict with extra financial/status fields."""
    base = minimal_property(property_id)
    base["PropertyHeader"].update({
        "FinancialDetails": {
            "PurchasePrice": 380_000,
            "CurrentValue": 430_000,
        },
        "CurrentStatus": {"OccupancyStatus": "Owner-occupied"},
    })
    return base


def minimal_mortgage(property_id: str = "PROP-001") -> Dict[str, Any]:
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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def prop_data() -> Dict[str, Any]:
    return minimal_property()


@pytest.fixture
def full_prop_data() -> Dict[str, Any]:
    return full_property()


@pytest.fixture
def mort_data() -> Dict[str, Any]:
    return minimal_mortgage()


# ---------------------------------------------------------------------------
# Generator factory helpers
# ---------------------------------------------------------------------------

def make_generator(tmp_path: Path):
    from reports.property.property_generator import PropertyReportGenerator
    return PropertyReportGenerator(output_dir=tmp_path)


def mock_generator(tmp_path: Path):
    """Return (mock, fake_pdf_path) for convenience-function tests."""
    fake_pdf = tmp_path / "prop_report.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4 fake")
    mock = MagicMock()
    mock.generate_property_only_report.return_value = fake_pdf
    mock.generate_mortgage_focused_report.return_value = fake_pdf
    mock.generate_risk_focused_report.return_value = fake_pdf
    mock.generate_report.return_value = fake_pdf
    return mock, fake_pdf
