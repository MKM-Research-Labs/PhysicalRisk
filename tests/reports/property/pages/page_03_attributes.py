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

"""Tests for reports.property.property_page_03_attributes — AttributesPage."""

from reportlab.platypus import Paragraph, Table


def _make_property(construction_year=1990, condition="Good", extra=None):
    attrs = {
        "PropertyType": "Semi-detached",
        "OccupancyType": "Owner-occupied",
        "PropertyCondition": condition,
        "PropertyAreaSqm": 120.0,
        "HeightMeters": 8.5,
        "NumberOfStoreys": 2,
        "TotalRooms": 7,
        "NumberBedrooms": 3,
        "NumberBathrooms": 2,
        "CouncilTaxBand": "D",
        "ParkingType": "Driveway",
        "AccessType": "Road",
        "GardenAreaFront": 20.0,
        "GardenAreaBack": 50.0,
        "HousingAssociation": False,
        "IncomeGenerating": False,
        "PayingBusinessRates": False,
        "RenovationRequired": False,
    }
    if construction_year is not None:
        attrs["ConstructionYear"] = construction_year
    if extra:
        attrs.update(extra)
    return {"PropertyHeader": {"PropertyAttributes": attrs}}


class TestAttributesPage:

    def _page(self):
        from reports.property.property_page_03_attributes import AttributesPage
        return AttributesPage()

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
        assert any("Property Attributes" in t for t in texts)

    def test_has_tables(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        assert any(isinstance(e, Table) for e in result)

    def test_basic_info_subsection(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Basic Property Information" in t for t in texts)

    def test_physical_dimensions_subsection(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Physical Dimensions" in t for t in texts)

    def test_room_composition_subsection(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Room Composition" in t for t in texts)

    def test_building_age_subsection(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Building Age" in t for t in texts)

    def test_age_historic(self):
        """Building older than 100 years → Historic category."""
        page = self._page()
        result = page.generate_elements(_make_property(construction_year=1900))
        assert isinstance(result, list)

    def test_age_mature(self):
        """Building 50–100 years → Mature category."""
        page = self._page()
        result = page.generate_elements(_make_property(construction_year=1960))
        assert isinstance(result, list)

    def test_age_modern(self):
        """Building 25–50 years → Modern category."""
        page = self._page()
        result = page.generate_elements(_make_property(construction_year=1990))
        assert isinstance(result, list)

    def test_age_contemporary(self):
        """Building ≤25 years → Contemporary category."""
        page = self._page()
        result = page.generate_elements(_make_property(construction_year=2010))
        assert isinstance(result, list)

    def test_no_construction_year_skips_age(self):
        page = self._page()
        result = page.generate_elements(_make_property(construction_year=None))
        assert isinstance(result, list)

    def test_condition_poor_recommendation(self):
        page = self._page()
        result = page.generate_elements(_make_property(condition="poor"))
        assert isinstance(result, list)

    def test_condition_fair_recommendation(self):
        page = self._page()
        result = page.generate_elements(_make_property(condition="fair"))
        assert isinstance(result, list)

    def test_condition_good_recommendation(self):
        page = self._page()
        result = page.generate_elements(_make_property(condition="Good"))
        assert isinstance(result, list)

    def test_condition_unknown_falls_back(self):
        page = self._page()
        result = page.generate_elements(_make_property(condition="Excellent"))
        assert isinstance(result, list)

    def test_external_features_subsection(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("External Features" in t for t in texts)

    def test_with_mortgage_data_does_not_crash(self):
        page = self._page()
        mortgage = {"RLoan": {"Header": {"RLoanID": "MORT-001"}}}
        result = page.generate_elements(_make_property(), mortgage)
        assert isinstance(result, list)
