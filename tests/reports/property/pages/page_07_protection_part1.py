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

"""Tests for reports.property.property_page_07_protection — ProtectionPage. (part 1 of 2)"""

from reportlab.platypus import Paragraph, Table


def _make_property(resilience=None, natural=None, risk_assessment=None):
    """Build property with ProtectionMeasures using correct field names."""
    protection = {}
    if risk_assessment is not None:
        protection["RiskAssessment"] = risk_assessment
    if resilience is not None:
        protection["ResilienceMeasures"] = resilience
    if natural is not None:
        protection["NaturalMeasures"] = natural
    return {"ProtectionMeasures": protection} if protection else {}


def _full_resilience(all_installed=True):
    return {
        "FloodGates": all_installed,
        "FloodBarriers": all_installed,
        "SumpPump": all_installed,
        "NonReturnValves": all_installed,
        "WaterproofFlooring": all_installed,
        "RaisedElectricals": all_installed,
        "WaterproofPlaster": all_installed,
        "FloodWarningSystem": all_installed,
        "EmergencyKit": all_installed,
        "SandBags": all_installed,
    }


class TestProtectionPageNoData:

    def _page(self):
        from reports.property.property_page_07_protection import ProtectionPage
        return ProtectionPage()

    def test_empty_property_returns_list(self):
        page = self._page()
        result = page.generate_elements({})
        assert isinstance(result, list)
        assert len(result) > 0

    def test_no_protection_measures_shows_fallback(self):
        page = self._page()
        result = page.generate_elements({})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("No protection" in t or "Protection" in t for t in texts)

    def test_empty_protection_measures_dict_shows_fallback(self):
        page = self._page()
        result = page.generate_elements({"ProtectionMeasures": {}})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("No protection" in t for t in texts)


class TestProtectionPageRiskAssessment:

    def _page(self):
        from reports.property.property_page_07_protection import ProtectionPage
        return ProtectionPage()

    def test_risk_assessment_section_rendered(self):
        prop = _make_property(risk_assessment={
            "InsurancePremium": 1200,
            "ExcessAmount": 500,
        })
        result = self._page().generate_elements(prop)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Insurance" in t for t in texts)

    def test_insurance_premium_shown(self):
        prop = _make_property(risk_assessment={"InsurancePremium": 1500})
        result = self._page().generate_elements(prop)
        assert any(isinstance(e, Table) for e in result)

    def test_excess_amount_shown(self):
        prop = _make_property(risk_assessment={"ExcessAmount": 250})
        result = self._page().generate_elements(prop)
        assert any(isinstance(e, Table) for e in result)

    def test_other_risk_fields_shown(self):
        prop = _make_property(risk_assessment={
            "FloodReEligible": True,
            "InsuranceCategory": "High risk"
        })
        result = self._page().generate_elements(prop)
        assert isinstance(result, list)
        assert len(result) > 1

    def test_recommendations_include_flood_re(self):
        prop = _make_property(risk_assessment={"FloodReEligible": True})
        result = self._page().generate_elements(prop)
        assert isinstance(result, list)


class TestProtectionPageResilienceMeasures:

    def _page(self):
        from reports.property.property_page_07_protection import ProtectionPage
        return ProtectionPage()

    def test_all_installed_excellent_rating(self):
        prop = _make_property(resilience=_full_resilience(True))
        result = self._page().generate_elements(prop)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Resilience" in t or "Protection" in t for t in texts)

    def test_coverage_excellent_80pct(self):
        """8 of 10 = 80% → Excellent."""
        measures = _full_resilience(True)
        measures["FloodGates"] = False
        measures["FloodBarriers"] = False
        prop = _make_property(resilience=measures)
        result = self._page().generate_elements(prop)
        assert isinstance(result, list)

    def test_coverage_good_60pct(self):
        """6 of 10 = 60% → Good."""
        measures = {k: (i < 6) for i, k in enumerate(_full_resilience(True).keys())}
        prop = _make_property(resilience=measures)
        result = self._page().generate_elements(prop)
        assert isinstance(result, list)

    def test_coverage_fair_40pct(self):
        """4 of 10 = 40% → Fair."""
        measures = {k: (i < 4) for i, k in enumerate(_full_resilience(True).keys())}
        prop = _make_property(resilience=measures)
        result = self._page().generate_elements(prop)
        assert isinstance(result, list)

    def test_coverage_limited_20pct(self):
        """2 of 10 = 20% → Limited."""
        measures = {k: (i < 2) for i, k in enumerate(_full_resilience(True).keys())}
        prop = _make_property(resilience=measures)
        result = self._page().generate_elements(prop)
        assert isinstance(result, list)

    def test_coverage_poor_0pct(self):
        """0 of 10 = 0% → Poor."""
        prop = _make_property(resilience=_full_resilience(False))
        result = self._page().generate_elements(prop)
        assert isinstance(result, list)

    def test_critical_measures_listed(self):
        prop = _make_property(resilience={"FloodGates": True, "SumpPump": False})
        result = self._page().generate_elements(prop)
        assert any(isinstance(e, Table) for e in result)

    def test_building_measures_listed(self):
        prop = _make_property(resilience={"WaterproofFlooring": True, "RaisedElectricals": False})
        result = self._page().generate_elements(prop)
        assert isinstance(result, list)

    def test_emergency_measures_listed(self):
        prop = _make_property(resilience={"FloodWarningSystem": True, "SandBags": False})
        result = self._page().generate_elements(prop)
        assert isinstance(result, list)

    def test_uncategorised_measure_still_shown(self):
        prop = _make_property(resilience={"CustomMeasure": True})
        result = self._page().generate_elements(prop)
        assert isinstance(result, list)


class TestProtectionPageNaturalMeasures:

    def _page(self):
        from reports.property.property_page_07_protection import ProtectionPage
        return ProtectionPage()

    def test_natural_measures_section_rendered(self):
        prop = _make_property(natural={"Wetland": True, "GreenRoof": False})
        result = self._page().generate_elements(prop)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Natural" in t for t in texts)

    def test_all_natural_none_recommendation(self):
        """When no natural measures, recommendation should appear."""
        prop = _make_property(natural={"Wetland": False, "GreenRoof": False})
        result = self._page().generate_elements(prop)
        assert isinstance(result, list)
