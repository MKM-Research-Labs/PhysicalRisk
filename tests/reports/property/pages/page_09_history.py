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

"""Tests for reports.property.property_page_09_history — HistoryPage."""

import pytest
from reportlab.platypus import Paragraph, Table


def _make_property():
    return {
        "PropertyHeader": {
            "PropertyID": "PROP-001",
            "Address": "1 Test Street",
            "RiskAssessment": {
                "OverallFloodRisk": "Medium",
                "EAFloodZone": "Zone 2",
                "FloodZoneType": "River",
                "ClimateChangeFloodRisk": "High",
                "FloodInsuranceAvailable": True,
                "FloodInsurancePremiumIndicative": 1200,
            },
            "Construction": {
                "ConstructionMethod": "Traditional Brick",
                "FoundationType": "Strip",
                "RoofType": "Pitched",
                "WallMaterial": "Brick",
                "FloorType": "Solid concrete",
                "NumberOfFloors": 2,
                "BasementPresent": False,
                "FloodAdaptations": ["Flood barriers"],
            },
            "Valuation": {
                "PropertyValue": 750_000,
                "PurchasePrice": 600_000,
                "PurchaseDate": "2015-06-01",
                "RentalYield": 0.045,
                "FloodRiskDiscount": 0.05,
            },
            "Protection": {
                "BuildingsInsuranceProvider": "Aviva",
                "BuildingsInsuranceCover": 800_000,
                "BuildingsInsurancePremium": 1_200,
                "ContentsInsuranceProvider": "Direct Line",
                "ContentsInsurancePremium": 400,
                "FloodInsuranceFlag": True,
                "SecuritySystem": "Alarm + CCTV",
                "SmokeCO2Detectors": True,
            },
            "PropertyAttributes": {
                "PropertyAreaSqm": 120,
                "PropertyType": "Semi-detached",
                "ConstructionYear": 1990,
            },
        },
        "Location": {
            "Latitude": 51.5,
            "Longitude": -0.1,
            "Elevation": 5.0,
            "DistanceToRiver": 150,
        },
        "FloodHistory": {
            "FloodEvents": [
                {"EventDate": "2014-02-10", "FloodDepth": 0.3, "FloodType": "Surface"},
            ],
            "PreviousFloodClaims": 1,
        },
        "TransactionHistory": {
            "Transactions": [
                {"TransactionDate": "2015-06-01", "TransactionType": "Purchase",
                 "TransactionPrice": 600_000, "TransactionStatus": "Completed"},
                {"TransactionDate": "2010-03-01", "TransactionType": "Sale",
                 "TransactionPrice": 480_000, "TransactionStatus": "Completed"},
            ]
        },
    }


def _make_mortgage():
    return {
        "Mortgage": {
            "Header": {"MortgageID": "MORT-001"},
            "CurrentStatus": {
                "CurrentLTV": 0.65,
                "CurrentBalance": 400_000,
                "InArrearsFlag": False,
                "MissedPayments12M": 0,
                "MonthsInArrears": 0,
                "ArrearsAmount": 0,
            },
            "FinancialDetails": {
                "MonthlyPayment": 2_000,
                "InterestRate": 0.035,
                "RemainingTerm": 18,
                "OriginalBalance": 450_000,
                "ProductType": "Fixed",
                "ProductEndDate": "2028-01-01",
            },
            "BorrowerDetails": {
                "BorrowerAge": 42,
                "EmploymentStatus": "Employed",
                "AnnualIncome": 90_000,
                "CreditScore": 750,
            },
        }
    }


class TestHistoryPage:

    def _page(self):
        from reports.property.property_page_09_history import HistoryPage
        return HistoryPage()

    def test_returns_list(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        assert isinstance(result, list)
        assert len(result) > 0

    def test_empty_property_does_not_crash(self):
        page = self._page()
        result = page.generate_elements({})
        assert isinstance(result, list)

    def test_has_history_header(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("History" in t or "Flood" in t for t in texts)

    def test_with_mortgage_data(self):
        page = self._page()
        result = page.generate_elements(_make_property(), _make_mortgage())
        assert isinstance(result, list)

    def test_no_flood_history(self):
        page = self._page()
        prop = _make_property()
        del prop["FloodHistory"]
        result = page.generate_elements(prop)
        assert isinstance(result, list)

    def test_empty_flood_events(self):
        page = self._page()
        prop = _make_property()
        prop["FloodHistory"]["FloodEvents"] = []
        result = page.generate_elements(prop)
        assert isinstance(result, list)

    def test_with_environmental_issues(self):
        page = self._page()
        prop = _make_property()
        prop["History"] = {
            "EnvironmentalIssues": {"AirQuality": "Moderate", "NoiseLevel": "Medium"},
        }
        result = page.generate_elements(prop)
        assert isinstance(result, list)
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1

    def test_with_fire_incidents(self):
        page = self._page()
        prop = _make_property()
        prop["History"] = {
            "FireIncidents": {"LastFireDate": "2010-05-01", "Cause": "Electrical"},
        }
        result = page.generate_elements(prop)
        assert isinstance(result, list)

    def test_with_ground_conditions(self):
        page = self._page()
        prop = _make_property()
        prop["History"] = {
            "GroundConditions": {"SubsidenceStatus": "Minor movement", "SoilType": "Clay"},
        }
        result = page.generate_elements(prop)
        assert isinstance(result, list)

    def test_assess_historical_risks_high_env(self):
        page = self._page()
        history = {"EnvironmentalIssues": {"AirQuality": "very high pollution"}}
        result = page._assess_historical_risks(history)
        assert "Environmental Risk" in result
        assert "High" in result["Environmental Risk"]

    def test_assess_historical_risks_moderate_env(self):
        page = self._page()
        history = {"EnvironmentalIssues": {"AirQuality": "moderate levels"}}
        result = page._assess_historical_risks(history)
        assert "Medium" in result["Environmental Risk"]

    def test_assess_historical_risks_low_env(self):
        page = self._page()
        history = {"EnvironmentalIssues": {"AirQuality": "good"}}
        result = page._assess_historical_risks(history)
        assert "Low" in result["Environmental Risk"]

    def test_assess_historical_risks_severe_flood(self):
        page = self._page()
        history = {"FloodEvents": {"FloodDamageSeverity": "severe flooding"}}
        result = page._assess_historical_risks(history)
        assert "Historical Flood Risk" in result
        assert "High" in result["Historical Flood Risk"]

    def test_assess_historical_risks_moderate_flood(self):
        page = self._page()
        history = {"FloodEvents": {"FloodDamageSeverity": "moderate damage"}}
        result = page._assess_historical_risks(history)
        assert "Medium" in result["Historical Flood Risk"]

    def test_assess_historical_risks_no_flood_damage(self):
        page = self._page()
        history = {"FloodEvents": {"FloodDamageSeverity": "no damage reported"}}
        result = page._assess_historical_risks(history)
        assert "Low" in result["Historical Flood Risk"]

    def test_assess_historical_risks_active_subsidence(self):
        page = self._page()
        history = {"GroundConditions": {"SubsidenceStatus": "major active movement"}}
        result = page._assess_historical_risks(history)
        assert "Ground Stability Risk" in result
        assert "High" in result["Ground Stability Risk"]

    def test_assess_historical_risks_minor_subsidence(self):
        page = self._page()
        history = {"GroundConditions": {"SubsidenceStatus": "minor ground shift"}}
        result = page._assess_historical_risks(history)
        assert "Medium" in result["Ground Stability Risk"]

    def test_assess_historical_risks_stable_ground(self):
        page = self._page()
        history = {"GroundConditions": {"SubsidenceStatus": "stable"}}
        result = page._assess_historical_risks(history)
        assert "Low" in result["Ground Stability Risk"]

    def test_build_flood_history_no_reference_gauges(self):
        page = self._page()
        prop = {"PropertyHeader": {}}
        result = page._build_flood_history(prop)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("No reference gauges" in t for t in texts)

    def test_build_flood_history_no_hd_file(self, tmp_path, monkeypatch):
        from config import config
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: tmp_path)
        page = self._page()
        prop = {"PropertyHeader": {"ReferenceGauges": ["GAUGE-MISSING"]}}
        result = page._build_flood_history(prop)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("No historical" in t or "historical" in t.lower() for t in texts)

    def test_build_flood_history_with_flood_data(self, tmp_path, monkeypatch):
        import json
        from config import config
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: tmp_path)
        hd_data = {
            "gauge_metadata": {
                "flood_stages": {"FloodWarning": 2.0},
                "elevation": 3.0,
            },
            "years_included": 10,
            "daily_observations": [
                {"date": "2020-01-15", "level_meters": 2.5},
                {"date": "2020-01-16", "level_meters": 2.8},
                {"date": "2020-06-01", "level_meters": 3.0},
            ],
        }
        hd_file = tmp_path / "gauge_GAUGE-001_hd.json"
        hd_file.write_text(json.dumps(hd_data))
        prop = {
            "PropertyHeader": {
                "ReferenceGauges": ["GAUGE-001"],
                "RiskAssessment": {"GroundLevelMeters": 4.0},
                "Construction": {"FloorLevelMeters": 0.5},
            }
        }
        page = self._page()
        result = page._build_flood_history(prop)
        assert isinstance(result, list)
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1

    def test_build_flood_history_no_flood_days(self, tmp_path, monkeypatch):
        import json
        from config import config
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: tmp_path)
        hd_data = {
            "gauge_metadata": {
                "flood_stages": {"FloodWarning": 10.0},
                "elevation": 0.0,
            },
            "years_included": 20,
            "daily_observations": [
                {"date": "2020-01-15", "level_meters": 1.0},
            ],
        }
        hd_file = tmp_path / "gauge_GAUGE-001_hd.json"
        hd_file.write_text(json.dumps(hd_data))
        prop = {"PropertyHeader": {"ReferenceGauges": ["GAUGE-001"]}}
        page = self._page()
        result = page._build_flood_history(prop)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("No flood events" in t for t in texts)

    def test_build_flood_history_bad_json(self, tmp_path, monkeypatch):
        from config import config
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: tmp_path)
        hd_file = tmp_path / "gauge_GAUGE-001_hd.json"
        hd_file.write_text("NOT VALID JSON {{{")
        prop = {"PropertyHeader": {"ReferenceGauges": ["GAUGE-001"]}}
        page = self._page()
        result = page._build_flood_history(prop)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Error" in t or "error" in t.lower() for t in texts)
