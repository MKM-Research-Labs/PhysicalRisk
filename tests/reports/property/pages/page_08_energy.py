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

"""Tests for reports.property.property_page_08_energy — EnergyPage."""


class TestEnergyPage:

    def _page(self):
        from reports.property.property_page_08_energy import EnergyPage
        return EnergyPage()

    def test_returns_list(self):
        page = self._page()
        result = page.generate_elements({})
        assert isinstance(result, list)
        assert len(result) > 0

    def test_no_energy_data_fallback_message(self):
        page = self._page()
        from reportlab.platypus import Paragraph
        result = page.generate_elements({})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No energy performance data" in t for t in texts)

    def test_with_ratings_data(self):
        page = self._page()
        data = {
            "EnergyPerformance": {
                "Ratings": {"EPCRating": "B", "SAP": 75},
            }
        }
        result = page.generate_elements(data)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_with_ratings_includes_table(self):
        page = self._page()
        from reportlab.platypus import Table
        data = {
            "EnergyPerformance": {
                "Ratings": {"EPCRating": "C"},
            }
        }
        result = page.generate_elements(data)
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1

    def test_with_energy_usage(self):
        page = self._page()
        data = {
            "EnergyPerformance": {
                "Ratings": {},
                "EnergyUsage": {
                    "AnnualEnergyKwh": 5000,
                    "GridElectricityKwh": 3000,
                    "GasUsageKwh": 2000,
                    "AnnualCarbonKgCO2e": 1200,
                    "AnnualEnergyBill": 1500,
                },
            }
        }
        result = page.generate_elements(data)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_with_building_fabric(self):
        page = self._page()
        data = {
            "EnergyPerformance": {
                "Ratings": {},
                "BuildingFabric": {
                    "LoftInsulationMm": 270,
                    "ThermalBridgeScore": 0.05,
                    "AirTightnessScore": 7.0,
                    "HeatingSystem": "Gas boiler",
                    "WaterHeating": "Immersion",
                    "GlazingType": "Double",
                },
            }
        }
        result = page.generate_elements(data)
        assert isinstance(result, list)

    def test_energy_intensity_calculation(self):
        """Exercises energy intensity branch when area is known."""
        page = self._page()
        data = {
            "PropertyHeader": {
                "PropertyAttributes": {"PropertyAreaSqm": 100.0}
            },
            "EnergyPerformance": {
                "Ratings": {"EPCRating": "D"},
                "EnergyUsage": {"AnnualEnergyKwh": 15000},
            }
        }
        result = page.generate_elements(data)
        from reportlab.platypus import Table
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1

    def test_analyze_epc_rating_all_bands(self):
        page = self._page()
        for rating, expected_word in [
            ("A", "Excellent"), ("B", "Good"), ("C", "Fairly"),
            ("D", "Average"), ("E", "Below"), ("F", "Poor"), ("G", "Very poor"),
        ]:
            result = page._analyze_epc_rating(rating)
            assert expected_word in result

    def test_analyze_epc_rating_unknown(self):
        page = self._page()
        result = page._analyze_epc_rating("Z")
        assert "Unknown" in result

    def test_analyze_epc_rating_case_insensitive(self):
        page = self._page()
        assert "Excellent" in page._analyze_epc_rating("a")

    def test_full_data_no_crash(self):
        """Full data set exercises all branches without exception."""
        page = self._page()
        data = {
            "PropertyHeader": {
                "PropertyAttributes": {"PropertyAreaSqm": 120.0}
            },
            "EnergyPerformance": {
                "Ratings": {"EPCRating": "B", "SAP": 80},
                "EnergyUsage": {
                    "AnnualEnergyKwh": 10000,
                    "GridElectricityKwh": 5000,
                    "GasUsageKwh": 5000,
                    "SolarGenerationKwh": 1000,
                    "AnnualCarbonKgCO2e": 2400,
                    "AnnualEnergyBill": 2000,
                },
                "BuildingFabric": {
                    "LoftInsulationMm": 300,
                    "ThermalBridgeScore": 0.03,
                    "AirTightnessScore": 5.0,
                    "HeatingSystem": "Heat pump",
                    "WaterHeating": "Solar",
                    "GlazingType": "Triple",
                },
            }
        }
        result = page.generate_elements(data)
        assert isinstance(result, list)
        assert len(result) > 2
