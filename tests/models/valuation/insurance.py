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
Tests for models.valuation.insurance — factor tables and premium calculation.

Covers: get_age_premium_band, get_area_premium_factor_range,
apply_insurance_factors, and table structure checks.
"""

import pytest

from models.valuation.insurance import (
    AGE_PREMIUM_FACTORS,
    AREA_PREMIUM_BANDS,
    BASE_RATE_RANGE,
    CONSTRUCTION_TYPE_FACTORS,
    FLOOD_RISK_PREMIUM_FACTORS,
    MAX_PREMIUM,
    MIN_PREMIUM,
    PROPERTY_TYPE_PREMIUM_FACTORS,
    apply_insurance_factors,
    get_age_premium_band,
    get_area_premium_factor_range,
)


# ===========================================================================
# Factor table structure sanity checks
# ===========================================================================

class TestInsuranceFactorTables:

    def test_property_type_factors_present(self):
        expected = {'Flat', 'Mid-terrace', 'End-terrace',
                    'Semi-detached', 'Detached', 'Bungalow'}
        assert set(PROPERTY_TYPE_PREMIUM_FACTORS.keys()) == expected

    def test_flood_risk_factors_present(self):
        expected = {'Very Low', 'Low', 'Medium', 'High', 'Very High'}
        assert set(FLOOD_RISK_PREMIUM_FACTORS.keys()) == expected

    def test_flood_risk_factors_increase_with_risk(self):
        very_low_lo = FLOOD_RISK_PREMIUM_FACTORS['Very Low'][0]
        very_high_hi = FLOOD_RISK_PREMIUM_FACTORS['Very High'][1]
        assert very_high_hi > very_low_lo

    def test_age_premium_factors_all_positive(self):
        for band, (lo, hi) in AGE_PREMIUM_FACTORS.items():
            assert lo > 0, f"{band}: lo must be positive"
            assert hi >= lo, f"{band}: hi >= lo"

    def test_construction_type_factors_present(self):
        assert 'Brick' in CONSTRUCTION_TYPE_FACTORS
        assert 'Timber Frame' in CONSTRUCTION_TYPE_FACTORS

    def test_area_bands_are_sorted(self):
        thresholds = [t for t, _ in AREA_PREMIUM_BANDS if t != float('inf')]
        assert thresholds == sorted(thresholds)

    def test_base_rate_range(self):
        lo, hi = BASE_RATE_RANGE
        assert lo > 0
        assert hi > lo

    def test_min_max_premium_bounds(self):
        assert MIN_PREMIUM == 200
        assert MAX_PREMIUM == 20_000


# ===========================================================================
# get_age_premium_band
# ===========================================================================

class TestGetAgePremiumBand:

    def test_new_build(self):
        assert get_age_premium_band(2020, current_year=2025) == 'new_build'

    def test_exactly_9_years_new_build(self):
        assert get_age_premium_band(2016, current_year=2025) == 'new_build'

    def test_10_years_is_modern(self):
        assert get_age_premium_band(2015, current_year=2025) == 'modern'

    def test_modern(self):
        assert get_age_premium_band(2000, current_year=2025) == 'modern'

    def test_exactly_29_years_modern(self):
        assert get_age_premium_band(1996, current_year=2025) == 'modern'

    def test_30_years_is_established(self):
        assert get_age_premium_band(1995, current_year=2025) == 'established'

    def test_established(self):
        assert get_age_premium_band(1960, current_year=2025) == 'established'

    def test_exactly_99_years_established(self):
        assert get_age_premium_band(1926, current_year=2025) == 'established'

    def test_100_years_is_heritage(self):
        assert get_age_premium_band(1925, current_year=2025) == 'heritage'

    def test_heritage_old(self):
        assert get_age_premium_band(1850, current_year=2025) == 'heritage'

    def test_default_current_year(self):
        result = get_age_premium_band(2020)
        assert result in AGE_PREMIUM_FACTORS


# ===========================================================================
# get_area_premium_factor_range
# ===========================================================================

class TestGetAreaPremiumFactorRange:

    def test_small_area_first_band(self):
        lo, hi = get_area_premium_factor_range(30)
        assert (lo, hi) == AREA_PREMIUM_BANDS[0][1]

    def test_just_below_50_first_band(self):
        lo, hi = get_area_premium_factor_range(49.9)
        assert (lo, hi) == AREA_PREMIUM_BANDS[0][1]

    def test_exactly_50_second_band(self):
        lo, hi = get_area_premium_factor_range(50)
        assert (lo, hi) == AREA_PREMIUM_BANDS[1][1]

    def test_medium_area_second_band(self):
        lo, hi = get_area_premium_factor_range(80)
        assert (lo, hi) == AREA_PREMIUM_BANDS[1][1]

    def test_just_below_100_second_band(self):
        lo, hi = get_area_premium_factor_range(99.9)
        assert (lo, hi) == AREA_PREMIUM_BANDS[1][1]

    def test_exactly_100_third_band(self):
        lo, hi = get_area_premium_factor_range(100)
        assert (lo, hi) == AREA_PREMIUM_BANDS[2][1]

    def test_large_area_fourth_band(self):
        lo, hi = get_area_premium_factor_range(300)
        assert (lo, hi) == AREA_PREMIUM_BANDS[3][1]

    def test_returns_tuple(self):
        result = get_area_premium_factor_range(75)
        assert isinstance(result, tuple)
        assert len(result) == 2


# ===========================================================================
# apply_insurance_factors
# ===========================================================================

class TestApplyInsuranceFactors:

    def _call(self, **kwargs):
        defaults = dict(
            property_value=500_000.0,
            base_rate_per_1000=2.5,
            type_factor=1.0,
            flood_factor=1.0,
            age_factor=1.0,
            construction_factor=1.0,
            area_factor=1.0,
        )
        defaults.update(kwargs)
        return apply_insurance_factors(**defaults)

    def test_basic_calculation(self):
        # 500_000 / 1000 * 2.5 = 1250
        result = self._call()
        assert result == 1250.0

    def test_all_factors_applied(self):
        result = self._call(
            type_factor=1.2,
            flood_factor=1.5,
            age_factor=1.1,
            construction_factor=0.95,
            area_factor=1.05,
        )
        base = (500_000 / 1000) * 2.5
        expected = base * 1.2 * 1.5 * 1.1 * 0.95 * 1.05
        assert abs(result - round(expected, 2)) < 0.01

    def test_clamped_to_min(self):
        result = self._call(property_value=1000.0, base_rate_per_1000=0.1)
        assert result == MIN_PREMIUM

    def test_clamped_to_max(self):
        result = self._call(
            property_value=5_000_000.0,
            base_rate_per_1000=4.0,
            flood_factor=4.0,
        )
        assert result == MAX_PREMIUM

    def test_security_factor_reduces_premium(self):
        without = self._call()
        with_security = self._call(security_factor=0.9)
        assert with_security < without

    def test_claims_factor_increases_premium(self):
        base = self._call()
        with_claims = self._call(claims_factor=1.5)
        assert with_claims > base

    def test_contents_premium_added(self):
        base = self._call()
        with_contents = self._call(contents_premium=500.0)
        assert with_contents == base + 500.0

    def test_returns_float(self):
        result = self._call()
        assert isinstance(result, float)

    def test_high_flood_risk_increases_premium(self):
        low_flood = self._call(flood_factor=1.0)
        high_flood = self._call(flood_factor=3.0)
        assert high_flood > low_flood
