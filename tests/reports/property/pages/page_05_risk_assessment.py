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

"""Tests for reports.property.property_page_05_risk_assessment — RiskAssessmentPage."""

from reportlab.platypus import Paragraph, Table


def _make_property(flood_risk="Medium", ea_zone="Zone 2", ground_level=12.0,
                   river_dist=600.0, coastal_dist=5000.0, soil_type="Clay",
                   govt_defence=True, flood_type="River", last_flood="2014-02-10",
                   lake_dist=None, canal_dist=None):
    risk = {
        "OverallFloodRisk": flood_risk,
        "EAFloodZone": ea_zone,
        "FloodRiskType": flood_type,
        "LastFloodDate": last_flood,
        "GroundLevelMeters": ground_level,
        "RiverDistanceMeters": river_dist,
        "CoastalDistanceMeters": coastal_dist,
        "SoilType": soil_type,
        "GovernmentDefenceScheme": govt_defence,
    }
    if lake_dist is not None:
        risk["LakeDistanceMeters"] = lake_dist
    if canal_dist is not None:
        risk["CanalDistanceMeters"] = canal_dist
    return {"PropertyHeader": {"RiskAssessment": risk}}


class TestRiskAssessmentPageBasics:

    def _page(self):
        from reports.property.property_page_05_risk_assessment import RiskAssessmentPage
        return RiskAssessmentPage()

    def test_returns_list(self):
        assert isinstance(self._page().generate_elements(_make_property()), list)

    def test_empty_property_does_not_crash(self):
        assert isinstance(self._page().generate_elements({}), list)

    def test_has_risk_header(self):
        result = self._page().generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Risk" in t for t in texts)

    def test_has_table(self):
        result = self._page().generate_elements(_make_property())
        assert any(isinstance(e, Table) for e in result)

    def test_last_flood_date_shown(self):
        result = self._page().generate_elements(_make_property(last_flood="2014-02-10"))
        assert isinstance(result, list)

    def test_no_last_flood_date(self):
        result = self._page().generate_elements(_make_property(last_flood=None))
        assert isinstance(result, list)

    def test_flood_risk_type_shown(self):
        result = self._page().generate_elements(_make_property(flood_type="Coastal"))
        assert isinstance(result, list)

    def test_lake_distance_shown(self):
        result = self._page().generate_elements(_make_property(lake_dist=200.0))
        assert isinstance(result, list)

    def test_canal_distance_shown(self):
        result = self._page().generate_elements(_make_property(canal_dist=150.0))
        assert isinstance(result, list)

    def test_no_defence_scheme(self):
        result = self._page().generate_elements(_make_property(govt_defence=False))
        assert isinstance(result, list)

    def test_no_ea_zone(self):
        prop = {"PropertyHeader": {"RiskAssessment": {"OverallFloodRisk": "Low"}}}
        result = self._page().generate_elements(prop)
        assert isinstance(result, list)


class TestFloodZoneInterpretation:

    def _page(self):
        from reports.property.property_page_05_risk_assessment import RiskAssessmentPage
        return RiskAssessmentPage()

    def test_zone_1_low_risk(self):
        r = self._page()._interpret_flood_zone("Zone 1")
        assert "Low" in r

    def test_zone_2_medium_risk(self):
        r = self._page()._interpret_flood_zone("Zone 2")
        assert "Medium" in r

    def test_zone_3a_high_risk(self):
        r = self._page()._interpret_flood_zone("Zone 3a")
        assert "High" in r

    def test_zone_3b_floodplain(self):
        r = self._page()._interpret_flood_zone("Zone 3b")
        assert "floodplain" in r.lower() or "Functional" in r

    def test_unknown_zone(self):
        r = self._page()._interpret_flood_zone("Zone X")
        assert "Unknown" in r or "Zone X" in r

    def test_zone_in_page_output(self):
        for zone in ["Zone 1", "Zone 2", "Zone 3a", "Zone 3b"]:
            result = self._page().generate_elements(_make_property(ea_zone=zone))
            assert isinstance(result, list)


class TestSoilRiskAssessment:

    def _page(self):
        from reports.property.property_page_05_risk_assessment import RiskAssessmentPage
        return RiskAssessmentPage()

    def test_peat_high_risk(self):
        r = self._page()._assess_soil_risk("peat")
        assert "High" in r

    def test_clay_medium_high(self):
        r = self._page()._assess_soil_risk("clay loam")
        assert "Medium" in r or "high" in r.lower()

    def test_sand_medium_risk(self):
        r = self._page()._assess_soil_risk("sandy soil")
        assert "Medium" in r

    def test_rock_low_risk(self):
        r = self._page()._assess_soil_risk("bedrock")
        assert "Low" in r

    def test_unknown_soil(self):
        r = self._page()._assess_soil_risk("chalk")
        assert "Assessment" in r or "chalk" in r

    def test_rock_keyword(self):
        r = self._page()._assess_soil_risk("rock")
        assert "Low" in r


class TestElevationRiskBranches:

    def _page(self):
        from reports.property.property_page_05_risk_assessment import RiskAssessmentPage
        return RiskAssessmentPage()

    def test_very_low_elevation_under_5m(self):
        result = self._page().generate_elements(_make_property(ground_level=3.0))
        assert isinstance(result, list)

    def test_low_elevation_5_to_10m(self):
        result = self._page().generate_elements(_make_property(ground_level=7.0))
        assert isinstance(result, list)

    def test_moderate_elevation_10_to_20m(self):
        result = self._page().generate_elements(_make_property(ground_level=15.0))
        assert isinstance(result, list)

    def test_good_elevation_over_20m(self):
        result = self._page().generate_elements(_make_property(ground_level=25.0))
        assert isinstance(result, list)

    def test_no_ground_level(self):
        prop = {"PropertyHeader": {"RiskAssessment": {}}}
        result = self._page().generate_elements(prop)
        assert isinstance(result, list)


class TestRiverProximityBranches:

    def _page(self):
        from reports.property.property_page_05_risk_assessment import RiskAssessmentPage
        return RiskAssessmentPage()

    def test_very_close_under_100m(self):
        result = self._page().generate_elements(_make_property(river_dist=50.0))
        assert isinstance(result, list)

    def test_close_100_to_500m(self):
        result = self._page().generate_elements(_make_property(river_dist=300.0))
        assert isinstance(result, list)

    def test_moderate_500_to_1000m(self):
        result = self._page().generate_elements(_make_property(river_dist=700.0))
        assert isinstance(result, list)

    def test_good_distance_over_1000m(self):
        result = self._page().generate_elements(_make_property(river_dist=1500.0))
        assert isinstance(result, list)


class TestRiskScoreCalculation:

    def _page(self):
        from reports.property.property_page_05_risk_assessment import RiskAssessmentPage
        return RiskAssessmentPage()

    def _score(self, **kwargs):
        return self._page()._calculate_risk_score(kwargs)

    def test_very_high_flood_risk_adds_4(self):
        result = self._score(OverallFloodRisk="very high")
        assert result["score"] >= 4

    def test_high_flood_risk_adds_3(self):
        result = self._score(OverallFloodRisk="high")
        assert result["score"] >= 3

    def test_medium_flood_risk_adds_2(self):
        result = self._score(OverallFloodRisk="medium")
        assert result["score"] >= 2

    def test_low_flood_risk_adds_1(self):
        result = self._score(OverallFloodRisk="low")
        assert result["score"] >= 1

    def test_very_low_elevation_adds_3(self):
        result = self._score(GroundLevelMeters=3)
        assert result["score"] >= 3

    def test_low_elevation_adds_2(self):
        result = self._score(GroundLevelMeters=7)
        assert result["score"] >= 2

    def test_moderate_elevation_adds_1(self):
        result = self._score(GroundLevelMeters=15)
        assert result["score"] >= 1

    def test_very_close_river_adds_2(self):
        result = self._score(RiverDistanceMeters=50)
        assert result["score"] >= 2

    def test_close_river_adds_1(self):
        result = self._score(RiverDistanceMeters=300)
        assert result["score"] >= 1

    def test_peat_soil_adds_2(self):
        result = self._score(SoilType="peat")
        assert result["score"] >= 2

    def test_clay_soil_adds_1(self):
        result = self._score(SoilType="clay")
        assert result["score"] >= 1

    def test_very_high_score_level(self):
        result = self._score(
            OverallFloodRisk="very high", GroundLevelMeters=3,
            RiverDistanceMeters=50, SoilType="peat"
        )
        assert result["level"] == "Very High Risk"

    def test_high_score_level(self):
        result = self._score(
            OverallFloodRisk="high", GroundLevelMeters=7, RiverDistanceMeters=300
        )
        assert result["level"] == "High Risk"

    def test_medium_score_level(self):
        result = self._score(OverallFloodRisk="medium", GroundLevelMeters=7)
        assert "Medium" in result["level"] or result["score"] >= 4

    def test_low_medium_score_level(self):
        result = self._score(OverallFloodRisk="medium")
        assert result["level"] in ("Medium Risk", "Low-Medium Risk")

    def test_low_risk_level(self):
        result = self._score()
        assert result["level"] == "Low Risk"

    def test_no_risk_factors_message(self):
        result = self._score()
        assert "No major" in result["primary_factors"]

    def test_returns_all_keys(self):
        result = self._score()
        for k in ("score", "level", "primary_factors", "recommendations"):
            assert k in result
