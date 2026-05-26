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

"""
Tests for models.risk.risk_assessor — RiskAssessor class (core).

Covers flood risk levels, LTV bands, mortgage risk assessment,
combined scoring, and property vulnerability.
"""

import pytest

from models.risk.risk_assessor.assessor import RiskAssessor


# ===========================================================================
# assess_flood_risk_level
# ===========================================================================

class TestFloodRiskLevel:

    def test_none_returns_unknown(self):
        assert RiskAssessor.assess_flood_risk_level(None) == "Unknown"

    def test_negative_returns_unknown(self):
        assert RiskAssessor.assess_flood_risk_level(-1.0) == "Unknown"

    def test_zero_is_very_low(self):
        assert RiskAssessor.assess_flood_risk_level(0.0) == "Very Low"

    def test_below_low_threshold(self):
        assert RiskAssessor.assess_flood_risk_level(0.05) == "Low"

    def test_at_low_threshold(self):
        assert RiskAssessor.assess_flood_risk_level(0.1) == "Low"

    def test_medium_range(self):
        assert RiskAssessor.assess_flood_risk_level(0.3) == "Medium"

    def test_at_medium_threshold(self):
        assert RiskAssessor.assess_flood_risk_level(0.5) == "Medium"

    def test_high_range(self):
        assert RiskAssessor.assess_flood_risk_level(0.75) == "High"

    def test_at_high_threshold(self):
        assert RiskAssessor.assess_flood_risk_level(1.0) == "High"

    def test_very_high(self):
        assert RiskAssessor.assess_flood_risk_level(2.5) == "Very High"

    def test_monotone_with_depth(self):
        depths = [0.0, 0.05, 0.3, 0.75, 2.5]
        levels = [RiskAssessor.assess_flood_risk_level(d) for d in depths]
        order = ["Very Low", "Low", "Medium", "High", "Very High"]
        assert levels == order


# ===========================================================================
# assess_ltv_risk_level
# ===========================================================================

class TestLTVRiskLevel:

    def test_none_returns_unknown(self):
        assert RiskAssessor.assess_ltv_risk_level(None) == "Unknown"

    def test_low_ltv(self):
        assert RiskAssessor.assess_ltv_risk_level(0.5) == "Low"

    def test_at_low_boundary(self):
        assert RiskAssessor.assess_ltv_risk_level(0.6) == "Low"

    def test_moderate_ltv(self):
        assert RiskAssessor.assess_ltv_risk_level(0.7) == "Moderate"

    def test_at_moderate_boundary(self):
        assert RiskAssessor.assess_ltv_risk_level(0.8) == "Moderate"

    def test_high_ltv(self):
        assert RiskAssessor.assess_ltv_risk_level(0.88) == "High"

    def test_at_high_boundary(self):
        assert RiskAssessor.assess_ltv_risk_level(0.95) == "High"

    def test_critical_ltv(self):
        assert RiskAssessor.assess_ltv_risk_level(0.98) == "Critical"

    def test_normalises_percentage_input(self):
        # 70 / 100 = 0.70 → Moderate
        assert RiskAssessor.assess_ltv_risk_level(70) == "Moderate"

    def test_normalises_95_pct(self):
        assert RiskAssessor.assess_ltv_risk_level(95) == "High"


# ===========================================================================
# calculate_combined_risk_score
# ===========================================================================

class TestCombinedRiskScore:

    def test_basic_returns_float(self):
        score = RiskAssessor.calculate_combined_risk_score("Low", 0.5)
        assert isinstance(score, float)
        assert 0 < score <= 10

    def test_very_high_flood_capped(self):
        score = RiskAssessor.calculate_combined_risk_score(
            "Very High", 0.99, property_age=120, construction_type="timber")
        assert score == 10.0

    def test_high_ltv_multiplier(self):
        low = RiskAssessor.calculate_combined_risk_score("Medium", 0.5)
        high = RiskAssessor.calculate_combined_risk_score("Medium", 0.97)
        assert high > low

    def test_ltv_80_to_95_multiplier(self):
        base = RiskAssessor.calculate_combined_risk_score("Low", 0.5)
        mid = RiskAssessor.calculate_combined_risk_score("Low", 0.85)
        assert mid > base

    def test_ltv_60_to_80_multiplier(self):
        base = RiskAssessor.calculate_combined_risk_score("Low", 0.4)
        mid = RiskAssessor.calculate_combined_risk_score("Low", 0.7)
        assert mid > base

    def test_age_over_100(self):
        young = RiskAssessor.calculate_combined_risk_score("Medium", 0.7)
        old = RiskAssessor.calculate_combined_risk_score("Medium", 0.7, property_age=120)
        assert old > young

    def test_age_50_to_100(self):
        young = RiskAssessor.calculate_combined_risk_score("Medium", 0.7, property_age=10)
        mid_age = RiskAssessor.calculate_combined_risk_score("Medium", 0.7, property_age=75)
        assert mid_age > young

    def test_construction_timber_higher(self):
        brick = RiskAssessor.calculate_combined_risk_score("Medium", 0.7, construction_type="brick")
        timber = RiskAssessor.calculate_combined_risk_score("Medium", 0.7, construction_type="timber")
        assert timber > brick

    def test_construction_wood_equals_timber(self):
        timber = RiskAssessor.calculate_combined_risk_score("Medium", 0.7, construction_type="timber")
        wood = RiskAssessor.calculate_combined_risk_score("Medium", 0.7, construction_type="wood")
        assert timber == wood

    def test_construction_concrete_lower(self):
        brick = RiskAssessor.calculate_combined_risk_score("Medium", 0.7, construction_type="brick")
        concrete = RiskAssessor.calculate_combined_risk_score("Medium", 0.7, construction_type="concrete")
        assert concrete < brick

    def test_construction_steel_lowest(self):
        concrete = RiskAssessor.calculate_combined_risk_score("Medium", 0.7, construction_type="concrete")
        steel = RiskAssessor.calculate_combined_risk_score("Medium", 0.7, construction_type="steel")
        assert steel < concrete

    def test_unknown_construction_type(self):
        score = RiskAssessor.calculate_combined_risk_score("Medium", 0.7, construction_type="glass")
        assert 0 < score <= 10

    def test_unknown_flood_level(self):
        score = RiskAssessor.calculate_combined_risk_score("Unknown", 0.5)
        assert 0 < score <= 10

    def test_very_low_flood_lowest_score(self):
        vl = RiskAssessor.calculate_combined_risk_score("Very Low", 0.3)
        vh = RiskAssessor.calculate_combined_risk_score("Very High", 0.3)
        assert vl < vh

    def test_none_ltv_no_multiplier(self):
        score = RiskAssessor.calculate_combined_risk_score("Medium", None)
        assert 0 < score <= 10


# ===========================================================================
# assess_property_vulnerability
# ===========================================================================

class TestPropertyVulnerability:

    def test_none_elevation_returns_unknown(self):
        r = RiskAssessor.assess_property_vulnerability(None, 5.0)
        assert r['risk_level'] == 'Unknown'
        assert r['flood_depth'] is None
        assert 'Insufficient' in r['recommendations'][0]

    def test_none_flood_level_returns_unknown(self):
        r = RiskAssessor.assess_property_vulnerability(5.0, None)
        assert r['risk_level'] == 'Unknown'

    def test_no_flood(self):
        r = RiskAssessor.assess_property_vulnerability(10.0, 5.0)
        assert r['flood_depth'] == 0.0
        assert r['vulnerability_score'] == 0

    def test_flooded_depth_computed(self):
        r = RiskAssessor.assess_property_vulnerability(5.0, 6.0)
        assert r['flood_depth'] == pytest.approx(1.0)
        assert r['vulnerability_score'] > 0

    def test_close_to_water_increases_score(self):
        far = RiskAssessor.assess_property_vulnerability(5.0, 6.0, distance_to_water=2.0)
        near = RiskAssessor.assess_property_vulnerability(5.0, 6.0, distance_to_water=0.5)
        assert near['vulnerability_score'] > far['vulnerability_score']

    def test_score_capped_at_100(self):
        r = RiskAssessor.assess_property_vulnerability(0.0, 10.0, distance_to_water=0.1)
        assert r['vulnerability_score'] <= 100

    def test_high_risk_recommendations_present(self):
        r = RiskAssessor.assess_property_vulnerability(5.0, 7.5)
        assert any("flood" in rec.lower() for rec in r['recommendations'])

    def test_result_dict_keys(self):
        r = RiskAssessor.assess_property_vulnerability(5.0, 6.0)
        assert set(r.keys()) == {'flood_depth', 'risk_level', 'vulnerability_score', 'recommendations'}
