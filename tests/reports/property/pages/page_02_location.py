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

"""Tests for reports.property.property_page_02_location — LocationPage."""

from reportlab.platypus import Paragraph, Table


def _make_property(density=None, extra_location=None):
    location = {
        "BuildingNumber": "42",
        "StreetName": "Test Road",
        "TownCity": "London",
        "County": "Greater London",
        "Postcode": "SW1A 1AA",
        "LatitudeDegrees": 51.5,
        "LongitudeDegrees": -0.1,
        "BritishNationalGrid": "TQ300800",
        "What3Words": "filled.count.soap",
        "USRN": "12345678",
        "Country": "England",
        "Region": "London",
        "LocalAuthority": "Westminster",
        "ElectoralWard": "St James's",
        "ParliamentaryConstituency": "Cities of London",
        "UrbanRuralClassification": "Urban",
    }
    if density is not None:
        location["LocalDensityHectare"] = density
    if extra_location:
        location.update(extra_location)
    return {"PropertyHeader": {"Location": location}}


class TestLocationPage:

    def _page(self):
        from reports.property.property_page_02_location import LocationPage
        return LocationPage()

    def test_returns_list(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        assert isinstance(result, list)
        assert len(result) > 0

    def test_empty_property_does_not_crash(self):
        page = self._page()
        result = page.generate_elements({})
        assert isinstance(result, list)

    def test_has_section_header(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Location Details" in t for t in texts)

    def test_has_tables(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        assert any(isinstance(e, Table) for e in result)

    def test_address_subsection_header(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Primary Address" in t for t in texts)

    def test_geographic_subsection_header(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Geographic Information" in t for t in texts)

    def test_administrative_subsection_header(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Administrative Areas" in t for t in texts)

    def test_area_classification_subsection_header(self):
        page = self._page()
        result = page.generate_elements(_make_property(density=150))
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Area Classification" in t for t in texts)

    def test_density_very_high(self):
        page = self._page()
        result = page.generate_elements(_make_property(density=250))
        assert isinstance(result, list)

    def test_density_high(self):
        page = self._page()
        result = page.generate_elements(_make_property(density=150))
        assert isinstance(result, list)

    def test_density_medium(self):
        page = self._page()
        result = page.generate_elements(_make_property(density=75))
        assert isinstance(result, list)

    def test_density_low_medium(self):
        page = self._page()
        result = page.generate_elements(_make_property(density=30))
        assert isinstance(result, list)

    def test_density_low(self):
        page = self._page()
        result = page.generate_elements(_make_property(density=10))
        assert isinstance(result, list)

    def test_no_coordinates_skips_geo_rows(self):
        """Missing lat/lon means coordinates rows are omitted — no crash."""
        page = self._page()
        data = {"PropertyHeader": {"Location": {"TownCity": "London"}}}
        result = page.generate_elements(data)
        assert isinstance(result, list)

    def test_with_mortgage_data_does_not_crash(self):
        page = self._page()
        mortgage = {"RLoan": {"Header": {"RLoanID": "MORT-001"}}}
        result = page.generate_elements(_make_property(), mortgage)
        assert isinstance(result, list)
