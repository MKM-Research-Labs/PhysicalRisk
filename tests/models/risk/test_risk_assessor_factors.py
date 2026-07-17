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

"""
Tests for models.risk.risk_assessor — RiskAssessor class (factors).

Covers VaR, gauge reliability, distance decay, insurance premium,
and recommendation generation.
"""

import pytest

from models.risk.risk_assessor.assessor import RiskAssessor


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
