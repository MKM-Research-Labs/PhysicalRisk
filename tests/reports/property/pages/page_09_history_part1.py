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

"""Tests for reports.property.property_page_09_history — HistoryPage."""

import pytest
from db_helpers import tmp_catchment
from reportlab.platypus import Paragraph, Table

import database
from tests.reports.property.pages.conftest import _make_mortgage, _make_property


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

    def test_build_flood_history_no_hd_file(self, tmp_path):
        prop = {"PropertyHeader": {"ReferenceGauges": ["GAUGE-MISSING"]}}
        with tmp_catchment(tmp_path, "thames"):
            result = self._page()._build_flood_history(prop)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("No historical" in t or "historical" in t.lower() for t in texts)

    def test_build_flood_history_with_flood_data(self, tmp_path):
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
        prop = {
            "PropertyHeader": {
                "ReferenceGauges": ["GAUGE-001"],
                "RiskAssessment": {"GroundLevelMeters": 4.0},
                "Construction": {"FloorLevelMeters": 0.5},
            }
        }
        with tmp_catchment(tmp_path, "thames"):
            database.save_gauge_history("thames", "GAUGE-001", hd_data)
            result = self._page()._build_flood_history(prop)
        assert isinstance(result, list)
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1

    def test_build_flood_history_no_flood_days(self, tmp_path):
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
        prop = {"PropertyHeader": {"ReferenceGauges": ["GAUGE-001"]}}
        with tmp_catchment(tmp_path, "thames"):
            database.save_gauge_history("thames", "GAUGE-001", hd_data)
            result = self._page()._build_flood_history(prop)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("No flood events" in t for t in texts)

    def test_build_flood_history_bad_json(self, tmp_path, monkeypatch):
        def _boom(*a, **k):
            raise ValueError("corrupt gauge history record")
        monkeypatch.setattr(database, "get_gauge_history", _boom)
        prop = {"PropertyHeader": {"ReferenceGauges": ["GAUGE-001"]}}
        with tmp_catchment(tmp_path, "thames"):
            result = self._page()._build_flood_history(prop)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Error" in t or "error" in t.lower() for t in texts)
