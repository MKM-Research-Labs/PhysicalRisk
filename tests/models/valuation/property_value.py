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
Tests for models.valuation.property_value — factor tables and valuation.

Covers: get_age_band, get_proximity_zone, apply_valuation_factors,
and all exported factor tables (structure, keys, ranges).
"""

import pytest

from models.valuation.property_value import (
    AGE_BAND_FACTORS,
    BASE_AREA_RANGES,
    BASE_PRICE_PER_SQM,
    CONDITION_FACTORS,
    EPC_FACTORS,
    FLOOD_RISK_FACTORS,
    MAX_PROPERTY_VALUE,
    MIN_PROPERTY_VALUE,
    PROXIMITY_ZONES,
    RENTAL_YIELD_RATES,
    RENT_PER_SQM,
    apply_valuation_factors,
    get_age_band,
    get_proximity_zone,
)


# ===========================================================================
# Factor table structure sanity checks
# ===========================================================================

class TestFactorTables:

    def test_base_area_ranges_all_positive(self):
        for k, (lo, hi) in BASE_AREA_RANGES.items():
            assert lo > 0, f"{k}: lo must be positive"
            assert hi > lo, f"{k}: hi must exceed lo"

    def test_base_price_per_sqm_all_positive(self):
        for k, (lo, hi) in BASE_PRICE_PER_SQM.items():
            assert lo > 0
            assert hi > lo

    def test_age_band_factors_within_reasonable_bounds(self):
        for k, (lo, hi) in AGE_BAND_FACTORS.items():
            assert lo > 0, f"{k}: must be positive"
            assert hi >= lo, f"{k}: hi >= lo"

    def test_condition_factors_ordered_by_severity(self):
        # Excellent should have higher min than Poor
        excellent_lo = CONDITION_FACTORS['Excellent'][0]
        poor_hi = CONDITION_FACTORS['Poor'][1]
        assert excellent_lo > poor_hi

    def test_flood_risk_factors_decrease_with_risk(self):
        # Very Low should have higher min factor than Very High
        very_low_lo = FLOOD_RISK_FACTORS['Very Low'][0]
        very_high_hi = FLOOD_RISK_FACTORS['Very High'][1]
        assert very_low_lo > very_high_hi

    def test_epc_factors_a_highest(self):
        a_lo = EPC_FACTORS['A'][0]
        g_hi = EPC_FACTORS['G'][1]
        assert a_lo > g_hi

    def test_proximity_zones_have_range_key(self):
        for zone, data in PROXIMITY_ZONES.items():
            assert 'range' in data

    def test_rental_yield_rates_all_present(self):
        expected_types = {'Flat', 'Mid-terrace', 'End-terrace',
                          'Semi-detached', 'Detached', 'Bungalow'}
        assert set(RENTAL_YIELD_RATES.keys()) == expected_types

    def test_rent_per_sqm_all_present(self):
        expected_types = {'Flat', 'Mid-terrace', 'End-terrace',
                          'Semi-detached', 'Detached', 'Bungalow'}
        assert set(RENT_PER_SQM.keys()) == expected_types

    def test_min_max_value_bounds(self):
        assert MIN_PROPERTY_VALUE == 150_000
        assert MAX_PROPERTY_VALUE == 5_000_000


# ===========================================================================
# get_age_band
# ===========================================================================

class TestGetAgeBand:

    def test_new_build(self):
        assert get_age_band(2020, current_year=2025) == 'new_build'

    def test_exactly_9_years_is_new_build(self):
        assert get_age_band(2016, current_year=2025) == 'new_build'

    def test_10_years_is_modern(self):
        assert get_age_band(2015, current_year=2025) == 'modern'

    def test_modern(self):
        assert get_age_band(2005, current_year=2025) == 'modern'

    def test_exactly_24_years_is_modern(self):
        assert get_age_band(2001, current_year=2025) == 'modern'

    def test_25_years_is_established(self):
        assert get_age_band(2000, current_year=2025) == 'established'

    def test_established(self):
        assert get_age_band(1985, current_year=2025) == 'established'

    def test_exactly_49_years_is_established(self):
        assert get_age_band(1976, current_year=2025) == 'established'

    def test_50_years_is_period(self):
        assert get_age_band(1975, current_year=2025) == 'period'

    def test_period(self):
        assert get_age_band(1950, current_year=2025) == 'period'

    def test_exactly_99_years_is_period(self):
        assert get_age_band(1926, current_year=2025) == 'period'

    def test_100_years_is_heritage(self):
        assert get_age_band(1925, current_year=2025) == 'heritage'

    def test_heritage_old(self):
        assert get_age_band(1800, current_year=2025) == 'heritage'

    def test_default_current_year(self):
        # Default year is 2025; just checks it doesn't crash
        result = get_age_band(2020)
        assert result in AGE_BAND_FACTORS


# ===========================================================================
# get_proximity_zone
# ===========================================================================

class TestGetProximityZone:

    def test_close_low_risk_very_low(self):
        assert get_proximity_zone(100, 'Very Low') == 'close_low_risk'

    def test_close_low_risk_low(self):
        assert get_proximity_zone(150, 'Low') == 'close_low_risk'

    def test_close_high_risk_medium(self):
        assert get_proximity_zone(100, 'Medium') == 'close_high_risk'

    def test_close_high_risk_high(self):
        assert get_proximity_zone(50, 'High') == 'close_high_risk'

    def test_close_high_risk_very_high(self):
        assert get_proximity_zone(10, 'Very High') == 'close_high_risk'

    def test_medium_zone(self):
        assert get_proximity_zone(300, 'Very Low') == 'medium'

    def test_medium_zone_upper_bound(self):
        assert get_proximity_zone(499, 'Very High') == 'medium'

    def test_far_zone(self):
        assert get_proximity_zone(600, 'Medium') == 'far'

    def test_exactly_200m_is_medium_zone(self):
        assert get_proximity_zone(200, 'Low') == 'medium'

    def test_exactly_500m_is_far(self):
        assert get_proximity_zone(500, 'Low') == 'far'


# ===========================================================================
# apply_valuation_factors
# ===========================================================================

class TestApplyValuationFactors:

    def _call(self, **kwargs):
        defaults = dict(
            area=100.0,
            price_per_sqm=8000.0,
            value_factor=1.0,
            age_factor=1.0,
            condition_factor=1.0,
            flood_risk_factor=1.0,
            epc_factor=1.0,
            proximity_factor=1.0,
            noise_factor=1.0,
        )
        defaults.update(kwargs)
        return apply_valuation_factors(**defaults)

    def test_basic_calculation(self):
        # 100 * 8000 * 1.0 * ... = 800,000
        result = self._call()
        assert result == 800_000.0

    def test_all_factors_applied(self):
        result = self._call(
            area=100.0,
            price_per_sqm=8000.0,
            value_factor=1.0,
            age_factor=0.9,
            condition_factor=1.05,
            flood_risk_factor=0.95,
            epc_factor=1.02,
            proximity_factor=1.0,
        )
        expected = 100 * 8000 * 1.0 * 0.9 * 1.05 * 0.95 * 1.02 * 1.0 * 1.0
        assert abs(result - round(expected, 2)) < 0.01

    def test_clamped_to_min(self):
        # Tiny area + very low price → below MIN_PROPERTY_VALUE
        result = self._call(area=1.0, price_per_sqm=100.0)
        assert result == MIN_PROPERTY_VALUE

    def test_clamped_to_max(self):
        # Large area + high price → above MAX_PROPERTY_VALUE
        result = self._call(area=1000.0, price_per_sqm=15000.0)
        assert result == MAX_PROPERTY_VALUE

    def test_noise_factor_applied(self):
        result1 = self._call(noise_factor=1.0)
        result2 = self._call(noise_factor=1.1)
        assert result2 > result1

    def test_returns_float(self):
        result = self._call()
        assert isinstance(result, float)

    def test_flood_risk_discount_reduces_value(self):
        no_risk = self._call(flood_risk_factor=1.0)
        with_risk = self._call(flood_risk_factor=0.80)
        assert with_risk < no_risk
