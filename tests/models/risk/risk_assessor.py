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
Tests for models.risk.risk_assessor — RiskAssessor class.

Covers every classmethod branch: flood risk levels, LTV bands,
mortgage risk assessment, combined scoring, vulnerability, VaR,
gauge reliability, distance decay, insurance premium, and recommendations.
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
# assess_mortgage_risk
# ===========================================================================

class TestMortgageRisk:

    def test_high_flood_overrides(self):
        r = RiskAssessor.assess_mortgage_risk("High", 500_000, 400_000, 0.5)
        assert "High Risk" in r and "flood" in r.lower()

    def test_very_high_flood_overrides(self):
        r = RiskAssessor.assess_mortgage_risk("Very High", 500_000, 400_000, 0.3)
        assert "High Risk" in r

    def test_negative_value_critical(self):
        # abs(-50000) / 400000 = 12.5% > 10%
        r = RiskAssessor.assess_mortgage_risk("Low", -50_000, 400_000, 0.5)
        assert "Critical Risk" in r

    def test_negative_value_high(self):
        # abs(-22000) / 400000 = 5.5% > 5%
        r = RiskAssessor.assess_mortgage_risk("Low", -22_000, 400_000, 0.5)
        assert "High Risk" in r

    def test_negative_value_moderate(self):
        # abs(-9000) / 400000 = 2.25% > 2%
        r = RiskAssessor.assess_mortgage_risk("Low", -9_000, 400_000, 0.5)
        assert "Moderate Risk" in r

    def test_high_ltv_medium_flood(self):
        r = RiskAssessor.assess_mortgage_risk("Medium", 500_000, 400_000, 0.85)
        assert "High Risk" in r

    def test_elevated_ltv_medium_flood(self):
        r = RiskAssessor.assess_mortgage_risk("Medium", 500_000, 400_000, 0.72)
        assert "Moderate Risk" in r

    def test_medium_flood_default(self):
        r = RiskAssessor.assess_mortgage_risk("Medium", 500_000, 400_000, 0.5)
        assert "Moderate Risk" in r

    def test_low_flood_risk(self):
        r = RiskAssessor.assess_mortgage_risk("Low", 500_000, 400_000, 0.5)
        assert "Low Risk" in r

    def test_minimal_risk(self):
        r = RiskAssessor.assess_mortgage_risk("Very Low", 500_000, 400_000, 0.4)
        assert "Minimal" in r

    def test_none_ltv_no_crash(self):
        r = RiskAssessor.assess_mortgage_risk("Low", 500_000, 400_000, None)
        assert isinstance(r, str)


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


# ===========================================================================
# calculate_value_at_risk
# ===========================================================================

class TestValueAtRisk:

    def test_zero_property_value(self):
        assert RiskAssessor.calculate_value_at_risk(0, "High") == 0.0

    def test_negative_property_value(self):
        assert RiskAssessor.calculate_value_at_risk(-100_000, "High") == 0.0

    def test_risk_level_percentages(self):
        cases = [
            ("Very Low", 0.01), ("Low", 0.05), ("Medium", 0.15),
            ("High", 0.35), ("Very High", 0.60), ("Unknown", 0.10),
        ]
        for level, pct in cases:
            var = RiskAssessor.calculate_value_at_risk(1_000_000, level)
            assert var == pytest.approx(1_000_000 * pct), f"Failed for {level}"

    def test_depth_over_2m(self):
        var = RiskAssessor.calculate_value_at_risk(1_000_000, "Very Low", flood_depth=2.5)
        assert var == pytest.approx(800_000)

    def test_depth_1_to_2m(self):
        var = RiskAssessor.calculate_value_at_risk(1_000_000, "Very Low", flood_depth=1.5)
        assert var == pytest.approx(500_000)

    def test_depth_half_to_1m(self):
        var = RiskAssessor.calculate_value_at_risk(1_000_000, "Very Low", flood_depth=0.75)
        assert var == pytest.approx(250_000)

    def test_depth_under_half_m(self):
        var = RiskAssessor.calculate_value_at_risk(1_000_000, "Very Low", flood_depth=0.1)
        assert var == pytest.approx(100_000)

    def test_base_pct_wins_when_higher_than_depth_factor(self):
        # High risk (35%) beats depth factor for 0.5-1m (25%)
        var = RiskAssessor.calculate_value_at_risk(1_000_000, "High", flood_depth=0.75)
        assert var == pytest.approx(350_000)

    def test_zero_depth_uses_base_pct(self):
        var = RiskAssessor.calculate_value_at_risk(1_000_000, "Medium", flood_depth=0)
        assert var == pytest.approx(150_000)


# ===========================================================================
# assess_gauge_reliability
# ===========================================================================

class TestGaugeReliability:

    def test_fully_operational(self):
        r = RiskAssessor.assess_gauge_reliability("Fully operational")
        assert r['reliability_score'] == 95
        assert r['category'] == "Highly Reliable"

    def test_maintenance_required(self):
        r = RiskAssessor.assess_gauge_reliability("Maintenance required")
        assert r['reliability_score'] == 70
        assert r['category'] == "Reliable"

    def test_temporarily_offline(self):
        r = RiskAssessor.assess_gauge_reliability("Temporarily offline")
        assert r['reliability_score'] == 30
        assert r['category'] == "Low Reliability"

    def test_decommissioned(self):
        r = RiskAssessor.assess_gauge_reliability("Decommissioned")
        assert r['reliability_score'] == 0
        assert r['category'] == "Unreliable"

    def test_unknown_status(self):
        r = RiskAssessor.assess_gauge_reliability("Unknown")
        assert r['reliability_score'] == 50
        assert r['category'] == "Moderately Reliable"

    def test_realtime_no_adjustment(self):
        base = RiskAssessor.assess_gauge_reliability("Fully operational")
        rt = RiskAssessor.assess_gauge_reliability("Fully operational", data_frequency="real-time")
        assert rt['reliability_score'] == base['reliability_score']

    def test_hourly_minus_5(self):
        r = RiskAssessor.assess_gauge_reliability("Fully operational", data_frequency="hourly")
        assert r['reliability_score'] == 90

    def test_daily_minus_15(self):
        r = RiskAssessor.assess_gauge_reliability("Fully operational", data_frequency="daily")
        assert r['reliability_score'] == 80

    def test_weekly_minus_30(self):
        r = RiskAssessor.assess_gauge_reliability("Fully operational", data_frequency="weekly")
        assert r['reliability_score'] == 65

    def test_monthly_minus_50(self):
        r = RiskAssessor.assess_gauge_reliability("Maintenance required", data_frequency="monthly")
        assert r['reliability_score'] == 20
        assert r['category'] == "Unreliable"

    def test_score_clamped_at_zero(self):
        r = RiskAssessor.assess_gauge_reliability("Decommissioned", data_frequency="monthly")
        assert r['reliability_score'] == 0

    def test_result_keys(self):
        r = RiskAssessor.assess_gauge_reliability("Unknown")
        assert 'reliability_score' in r
        assert 'category' in r
        assert 'operational_status' in r


# ===========================================================================
# calculate_distance_risk_factor
# ===========================================================================

class TestDistanceRiskFactor:

    def test_none_returns_default(self):
        assert RiskAssessor.calculate_distance_risk_factor(None) == 0.5

    def test_negative_returns_default(self):
        assert RiskAssessor.calculate_distance_risk_factor(-1.0) == 0.5

    def test_at_zero_is_max(self):
        assert RiskAssessor.calculate_distance_risk_factor(0.0) == 1.0

    def test_very_close(self):
        assert RiskAssessor.calculate_distance_risk_factor(0.05) == 1.0

    def test_close_band(self):
        assert RiskAssessor.calculate_distance_risk_factor(0.3) == 0.8

    def test_near_band(self):
        assert RiskAssessor.calculate_distance_risk_factor(0.7) == 0.6

    def test_medium_band(self):
        assert RiskAssessor.calculate_distance_risk_factor(1.5) == 0.4

    def test_far_band(self):
        assert RiskAssessor.calculate_distance_risk_factor(3.0) == 0.2

    def test_very_far(self):
        assert RiskAssessor.calculate_distance_risk_factor(10.0) == 0.1

    def test_monotone_decrease(self):
        distances = [0.0, 0.3, 0.7, 1.5, 3.0, 10.0]
        factors = [RiskAssessor.calculate_distance_risk_factor(d) for d in distances]
        assert all(factors[i] >= factors[i + 1] for i in range(len(factors) - 1))


# ===========================================================================
# calculate_insurance_premium_factor
# ===========================================================================

class TestInsurancePremiumFactor:

    def test_base_rates_by_level(self):
        cases = [
            ("Very Low", 0.001), ("Low", 0.002), ("Medium", 0.005),
            ("High", 0.015), ("Very High", 0.035),
        ]
        for level, rate in cases:
            result = RiskAssessor.calculate_insurance_premium_factor(level, 500_000)
            assert result == pytest.approx(rate), f"Failed for {level}"

    def test_unknown_level_uses_default(self):
        result = RiskAssessor.calculate_insurance_premium_factor("Unknown", 500_000)
        assert result == pytest.approx(0.005)

    def test_depth_increases_premium(self):
        no_depth = RiskAssessor.calculate_insurance_premium_factor("Medium", 500_000)
        with_depth = RiskAssessor.calculate_insurance_premium_factor("Medium", 500_000, flood_depth=1.0)
        assert with_depth > no_depth

    def test_zero_depth_no_effect(self):
        base = RiskAssessor.calculate_insurance_premium_factor("Medium", 500_000)
        zero = RiskAssessor.calculate_insurance_premium_factor("Medium", 500_000, flood_depth=0)
        assert base == zero

    def test_capped_at_10_pct(self):
        result = RiskAssessor.calculate_insurance_premium_factor("Very High", 500_000, flood_depth=100.0)
        assert result == pytest.approx(0.10)

    def test_depth_multiplier_formula(self):
        rate = RiskAssessor.calculate_insurance_premium_factor("Medium", 500_000, flood_depth=2.0)
        expected = min(0.005 * (1 + 2.0 * 0.5), 0.10)
        assert rate == pytest.approx(expected)


# ===========================================================================
# _generate_recommendations
# ===========================================================================

class TestGenerateRecommendations:

    def test_high_risk_four_or_more(self):
        recs = RiskAssessor._generate_recommendations(0.5, "High")
        assert len(recs) >= 4

    def test_high_risk_mentions_flood_insurance(self):
        recs = RiskAssessor._generate_recommendations(0.5, "High")
        assert any("flood insurance" in r.lower() for r in recs)

    def test_deep_flood_extra_items(self):
        shallow = RiskAssessor._generate_recommendations(0.5, "High")
        deep = RiskAssessor._generate_recommendations(1.5, "High")
        assert len(deep) > len(shallow)

    def test_medium_risk(self):
        recs = RiskAssessor._generate_recommendations(0.3, "Medium")
        assert len(recs) >= 3

    def test_low_risk(self):
        recs = RiskAssessor._generate_recommendations(0.05, "Low")
        assert len(recs) >= 2

    def test_very_low_risk(self):
        recs = RiskAssessor._generate_recommendations(0.0, "Very Low")
        assert len(recs) >= 1

    def test_all_items_are_strings(self):
        for level in ["High", "Medium", "Low", "Very Low"]:
            recs = RiskAssessor._generate_recommendations(0.5, level)
            assert all(isinstance(r, str) for r in recs)
