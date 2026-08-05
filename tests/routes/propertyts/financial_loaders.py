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

"""Unit tests for routes/propertyts/financial_loaders.py degradation paths.

The loaders swallow seam-read failures and log a warning so the financial
endpoints still respond. These branches are exercised by calling the loader
helpers directly with the ``database`` seam monkeypatched — the file fixtures
used by the endpoint tests never make a read raise.
"""

import database
from routes.propertyts import financial_loaders as fl


def _raise(*_a, **_k):
    raise RuntimeError("seam read failed")


class TestLoadPropValues:

    def test_load_raises_returns_empty(self, monkeypatch):
        """Lines 75-76: get_property_portfolio raising → {} and a warning."""
        monkeypatch.setattr(database, "get_property_portfolio", _raise)
        assert fl._load_prop_values() == {}

    def test_none_portfolio_returns_empty(self, monkeypatch):
        """`or {}` guard: a None portfolio yields no values."""
        monkeypatch.setattr(database, "get_property_portfolio", lambda *a, **k: None)
        assert fl._load_prop_values() == {}


class TestLoadGaugeElevations:

    def test_gauge_portfolio_raises_falls_through(self, monkeypatch):
        """Lines 176-177: gauge portfolio read raising is swallowed; the
        hazard-curve source still populates elevations."""
        monkeypatch.setattr(database, "get_gauge_portfolio", _raise)
        monkeypatch.setattr(database, "get_gauge_hazard_curves",
                            lambda *a, **k: {"hazard_curves": {
                                "GAUGE-001": {"elevation_m": 4.2}}})
        result = fl._load_gauge_elevations()
        assert result == {"GAUGE-001": 4.2}

    def test_both_sources_raise_returns_empty(self, monkeypatch):
        monkeypatch.setattr(database, "get_gauge_portfolio", _raise)
        monkeypatch.setattr(database, "get_gauge_hazard_curves", _raise)
        assert fl._load_gauge_elevations() == {}


class TestLoadPropertyDetails:

    def _no_gauge_sources(self, monkeypatch):
        monkeypatch.setattr(database, "get_gauge_portfolio", lambda *a, **k: {})
        monkeypatch.setattr(database, "get_gauge_hazard_curves", lambda *a, **k: {})

    def test_property_without_id_skipped(self, monkeypatch):
        """Line 207: a property whose Header has no PropertyID is skipped."""
        self._no_gauge_sources(monkeypatch)
        monkeypatch.setattr(database, "get_property_portfolio", lambda *a, **k: {
            "properties": [
                {"PropertyHeader": {"Header": {}}},  # no PropertyID → skipped
                {"PropertyHeader": {
                    "Header": {"PropertyID": "PROP-001"},
                    "Location": {"BuildingNumber": "1", "StreetName": "High St"},
                    "Valuation": {"PropertyValue": 250000},
                    "Construction": {"FloorLevelMeters": 0.3},
                    "RiskAssessment": {"GroundLevelMeters": 5.0,
                                       "RiverDistanceMeters": 800,
                                       "EAFloodZone": "Zone 2"},
                    "ReferenceGauges": [],
                }},
            ]
        })
        details = fl._load_property_details()
        assert list(details.keys()) == ["PROP-001"]
        assert details["PROP-001"]["river_distance_km"] == 0.8

    def test_reference_gauge_elevation_resolved(self, monkeypatch):
        """A property's first reference gauge supplies the gauge elevation."""
        monkeypatch.setattr(database, "get_gauge_portfolio", lambda *a, **k: {
            "flood_gauges": [{"FloodGauge": {
                "Header": {"GaugeID": "GAUGE-001"},
                "Location": {"GaugeElevation": 3.0},
            }}]
        })
        monkeypatch.setattr(database, "get_gauge_hazard_curves", lambda *a, **k: {})
        monkeypatch.setattr(database, "get_property_portfolio", lambda *a, **k: {
            "properties": [{"PropertyHeader": {
                "Header": {"PropertyID": "PROP-001"},
                "Location": {},
                "Valuation": {"PropertyValue": 100000},
                "Construction": {"FloorLevelMeters": 0.0},
                "RiskAssessment": {"GroundLevelMeters": 3.0},
                "ReferenceGauges": ["GAUGE-001"],
            }}]
        })
        details = fl._load_property_details()
        assert "PROP-001" in details
        assert "elevation_m" in details["PROP-001"]

    def test_property_portfolio_raises_returns_empty(self, monkeypatch):
        """Lines 243-244: property-details read raising → {} and a warning."""
        self._no_gauge_sources(monkeypatch)
        monkeypatch.setattr(database, "get_property_portfolio", _raise)
        assert fl._load_property_details() == {}
