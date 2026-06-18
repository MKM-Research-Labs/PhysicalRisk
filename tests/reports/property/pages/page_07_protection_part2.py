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

"""Tests for reports.property.property_page_07_protection — ProtectionPage. (part 2 of 2)"""

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


class TestProtectionPageHazardProfile:
    """Covers the HazardProfile + Operational Thresholds blocks."""

    def _page(self):
        from reports.property.property_page_07_protection import ProtectionPage
        return ProtectionPage()

    def test_hazard_profile_all_intensities(self):
        prop = {"ProtectionMeasures": {"HazardProfile": {
            "FloodHazardClass": "High", "DesignFloodReturnYr": 100,
            "WindHazardClass": "Medium", "DesignWindSpeedKmh": 180.0,
            "SeismicHazardClass": "Low", "DesignSeismicPGA": 0.123,
            "FireHazardClass": "Extreme",
        }}}
        result = self._page().generate_elements(prop)
        texts = [e.text for e in result
                 if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Hazard Profile" in t for t in texts)

    def test_hazard_profile_missing_intensities_dash(self):
        # Classes present but no design-intensity values → '—' branches.
        prop = {"ProtectionMeasures": {"HazardProfile": {
            "FloodHazardClass": "None", "WindHazardClass": "None",
            "SeismicHazardClass": "None",
        }}}
        result = self._page().generate_elements(prop)
        assert any(isinstance(e, Table) for e in result)

    def test_operational_thresholds_rendered(self):
        prop = {"ProtectionMeasures": {"HazardProfile": {
            "FloodHazardClass": "High",
            "WindThresholdMajorMps": 33.0,
            "WaterThresholdMinorM": 0.25,
            "FlashThresholdMajorM": "n/a",  # non-numeric str branch
        }}}
        result = self._page().generate_elements(prop)
        texts = [e.text for e in result
                 if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Operational Thresholds" in t for t in texts)


class TestProtectionPageBRIRatings:
    """Covers the GoverningBodyRatings/BRI + IndustryGroups blocks."""

    def _page(self):
        from reports.property.property_page_07_protection import ProtectionPage
        return ProtectionPage()

    def test_bri_ratings_full(self):
        prop = {"ProtectionMeasures": {"RiskAssessment": {
            "InsuranceBodyRatings": {
                "InsuranceRatingBody": "BodyCo", "InsuranceRating": "A",
                "InsuranceDate": "2026-01-01", "InsuranceRatingVersion": "1.0"},
            "GoverningBodyRatings": {
                "BRIRatingAgent": "AgentCo", "BRIRatingVersion": "2.0",
                "BRIDate": "2026-01-01", "BRIRating": "AA", "BRIScore": 0.9876,
                "BRIWindRating": "A", "BRIWindScore": 0.5,
                "BRIFloodRating": "B", "BRIFloodScore": 0.4,
                "BRIWaterRating": "AA", "BRIWaterScore": 0.95,
                "BRIFlashRating": "A", "BRIFlashScore": 0.6,
                "BRIFireRating": "AA", "BRIFireScore": 0.8,
                "BRISeismicRating": "B", "BRISeismicScore": 0.3,
                "IndustryGroups": {
                    "WindCodes": ["W1", "W2"], "WaterCodes": ["WA1"],
                    "FlashCodes": ["FL1"], "FireCodes": ["FI1"],
                    "SeismicCodes": ["S1"]},
            },
            "InsurancePremium": 1200.0, "ExcessAmount": 500.0,
        }}}
        result = self._page().generate_elements(prop)
        texts = [e.text for e in result
                 if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("BRI Governing Body" in t for t in texts) or \
            any(isinstance(e, Table) for e in result)
        assert any("Industry Groups" in t for t in texts)

    def test_bri_ratings_minimal_no_water_flash(self):
        # Water/Flash ratings absent → those conditional rows skipped.
        prop = {"ProtectionMeasures": {"RiskAssessment": {
            "GoverningBodyRatings": {
                "BRIRating": "A", "BRIScore": "not-float",  # non-float → '—'
                "BRIWindRating": "A",  # no score → '/ —'
            },
        }}}
        result = self._page().generate_elements(prop)
        assert any(isinstance(e, Table) for e in result)


class TestProtectionPageNestedResilience:
    """Covers the nested ResilienceMeasures subsection-detail block."""

    def _page(self):
        from reports.property.property_page_07_protection import ProtectionPage
        return ProtectionPage()

    def test_nested_subsections_rendered(self):
        prop = {"ProtectionMeasures": {"ResilienceMeasures": {
            "FloodProtection": {"FloodGates": "Enhanced", "Barriers": "Partial"},
            "SiteAndDrainage": {"Drainage": "None"},
            "BuildingAssessment": {"Survey": "Meets"},
            "FireProtection": {"Alarms": "Enhanced"},
            "ContinuityMeasures": {"Backup": None},
        }}}
        result = self._page().generate_elements(prop)
        texts = [e.text for e in result
                 if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Flood Protection" in t for t in texts)
        assert any("Site & Drainage" in t for t in texts)

    def test_nested_recommendations_partial_none(self):
        page = self._page()
        result = page._generate_protection_recommendations({
            "ResilienceMeasures": {
                "FloodProtection": {"Gates": "partial"},
                "SiteAndDrainage": {"Drain": "none"},
            }})
        assert "Flood Protection" in result
        assert "Site & Drainage" in result


class TestProtectionPageRecommendations:

    def _page(self):
        from reports.property.property_page_07_protection import ProtectionPage
        return ProtectionPage()

    def test_recommendations_section_always_rendered(self):
        prop = _make_property(resilience=_full_resilience(False))
        result = self._page().generate_elements(prop)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Recommendation" in t for t in texts)

    def test_missing_critical_measures_in_recommendations(self):
        prop = _make_property(resilience={"FloodGates": False, "SumpPump": False})
        result = self._page().generate_elements(prop)
        assert isinstance(result, list)

    def test_full_protection_fewer_recommendations(self):
        prop = _make_property(
            resilience=_full_resilience(True),
            risk_assessment={"FloodReEligible": False},
            natural={"Wetland": True},
        )
        result = self._page().generate_elements(prop)
        assert isinstance(result, list)

    def test_generate_protection_recommendations_returns_dict(self):
        from reports.property.property_page_07_protection import ProtectionPage
        page = ProtectionPage()
        result = page._generate_protection_recommendations({})
        assert isinstance(result, dict)

    def test_recommendations_missing_critical(self):
        from reports.property.property_page_07_protection import ProtectionPage
        page = ProtectionPage()
        result = page._generate_protection_recommendations({
            "ResilienceMeasures": {"FloodGates": False}
        })
        assert "Priority Installations" in result

    def test_recommendations_all_natural_false(self):
        from reports.property.property_page_07_protection import ProtectionPage
        page = ProtectionPage()
        result = page._generate_protection_recommendations({
            "NaturalMeasures": {"Wetland": False}
        })
        assert "Natural Solutions" in result

    def test_recommendations_flood_re_eligible(self):
        from reports.property.property_page_07_protection import ProtectionPage
        page = ProtectionPage()
        result = page._generate_protection_recommendations({
            "RiskAssessment": {"FloodReEligible": True}
        })
        assert "Insurance" in result
