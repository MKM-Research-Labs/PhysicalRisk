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

"""Tests for reports.property.property_page_04_construction — ConstructionPage."""

from reportlab.platypus import Paragraph, Table


def _make_property(construction_type="brick", foundation="strip", height=8.0,
                   floor_level=None, site_height=None, year=2000):
    return {
        "PropertyHeader": {
            "Construction": {
                "ConstructionType": construction_type,
                "FoundationType": foundation,
                "FloorType": "Solid concrete",
                "PropertyHeight": height,
                "FloorLevelMeters": floor_level,
                "SiteHeight": site_height,
                "BasementPresent": False,
                "ConstructionYear": year,
            },
        }
    }


class TestConstructionPageBasics:

    def _page(self):
        from reports.property.property_page_04_construction import ConstructionPage
        return ConstructionPage()

    def test_returns_list_with_data(self):
        result = self._page().generate_elements(_make_property())
        assert isinstance(result, list) and len(result) > 0

    def test_no_construction_data_returns_message(self):
        result = self._page().generate_elements({"PropertyHeader": {}})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("No construction" in t for t in texts)

    def test_empty_property_does_not_crash(self):
        assert isinstance(self._page().generate_elements({}), list)

    def test_has_section_header(self):
        result = self._page().generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Construction" in t for t in texts)

    def test_has_table(self):
        result = self._page().generate_elements(_make_property())
        assert any(isinstance(e, Table) for e in result)

    def test_construction_year_shown(self):
        result = self._page().generate_elements(_make_property(year=1985))
        assert isinstance(result, list)

    def test_no_construction_year(self):
        prop = _make_property()
        del prop["PropertyHeader"]["Construction"]["ConstructionYear"]
        assert isinstance(self._page().generate_elements(prop), list)

    def test_floor_level_shown(self):
        result = self._page().generate_elements(_make_property(floor_level=2.5))
        assert isinstance(result, list)

    def test_site_height_shown(self):
        result = self._page().generate_elements(_make_property(site_height=12.0))
        assert isinstance(result, list)


class TestConstructionTypeAnalysis:

    def _page(self):
        from reports.property.property_page_04_construction import ConstructionPage
        return ConstructionPage()

    def test_timber_construction(self):
        result = self._page().generate_elements(_make_property(construction_type="timber frame"))
        assert isinstance(result, list)

    def test_steel_construction(self):
        result = self._page().generate_elements(_make_property(construction_type="steel frame"))
        assert isinstance(result, list)

    def test_concrete_construction(self):
        result = self._page().generate_elements(_make_property(construction_type="reinforced concrete"))
        assert isinstance(result, list)

    def test_brick_construction(self):
        result = self._page().generate_elements(_make_property(construction_type="brick"))
        assert isinstance(result, list)

    def test_masonry_construction(self):
        result = self._page().generate_elements(_make_property(construction_type="masonry"))
        assert isinstance(result, list)

    def test_unknown_construction_type(self):
        result = self._page().generate_elements(_make_property(construction_type="glass"))
        assert isinstance(result, list)

    def test_empty_construction_type(self):
        result = self._page().generate_elements(_make_property(construction_type=""))
        assert isinstance(result, list)


class TestFoundationTypeAnalysis:

    def _page(self):
        from reports.property.property_page_04_construction import ConstructionPage
        return ConstructionPage()

    def test_raft_foundation(self):
        result = self._page().generate_elements(_make_property(foundation="raft"))
        assert isinstance(result, list)

    def test_pile_foundation(self):
        result = self._page().generate_elements(_make_property(foundation="pile"))
        assert isinstance(result, list)

    def test_strip_foundation(self):
        result = self._page().generate_elements(_make_property(foundation="strip"))
        assert isinstance(result, list)

    def test_pad_foundation(self):
        result = self._page().generate_elements(_make_property(foundation="pad footing"))
        assert isinstance(result, list)

    def test_unknown_foundation(self):
        result = self._page().generate_elements(_make_property(foundation="unknown type"))
        assert isinstance(result, list)


class TestHeightClassification:

    def _page(self):
        from reports.property.property_page_04_construction import ConstructionPage
        return ConstructionPage()

    def test_tall_structure_over_15m(self):
        result = self._page().generate_elements(_make_property(height=16.0))
        assert isinstance(result, list)

    def test_medium_height_10_to_15m(self):
        result = self._page().generate_elements(_make_property(height=12.0))
        assert isinstance(result, list)

    def test_standard_height_under_10m(self):
        result = self._page().generate_elements(_make_property(height=8.0))
        assert isinstance(result, list)

    def test_no_height_skips_classification(self):
        prop = _make_property()
        del prop["PropertyHeader"]["Construction"]["PropertyHeight"]
        result = self._page().generate_elements(prop)
        assert isinstance(result, list)
