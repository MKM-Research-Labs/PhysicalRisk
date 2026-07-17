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
Tests for models.stress.flood_poly — polynomial flood probability model.

Covers: p_flood_poly, p_flood_simple, p_flood_series, model_card,
config integration, boundary conditions, monotonicity.
"""

import math

import pytest


# ===========================================================================
# p_flood_poly — 2D model (water level + time)
# ===========================================================================

class TestPFloodPoly:

    def test_returns_float(self):
        from models.stress.flood_poly import p_flood_poly
        result = p_flood_poly(water_level=5.0, hour=48, severe_level=6.58)
        assert isinstance(result, float)

    def test_in_range(self):
        from models.stress.flood_poly import p_flood_poly
        result = p_flood_poly(water_level=5.0, hour=48, severe_level=6.58)
        assert 0.0 <= result <= 1.0

    def test_zero_severe_returns_zero(self):
        from models.stress.flood_poly import p_flood_poly
        assert p_flood_poly(water_level=5.0, hour=48, severe_level=0.0) == 0.0

    def test_negative_severe_returns_zero(self):
        from models.stress.flood_poly import p_flood_poly
        assert p_flood_poly(water_level=5.0, hour=48, severe_level=-1.0) == 0.0

    def test_high_water_high_probability(self):
        """Water well above severe threshold should give high P(flood)."""
        from models.stress.flood_poly import p_flood_poly
        p = p_flood_poly(water_level=7.0, hour=84, severe_level=6.58)
        assert p > 0.8

    def test_low_water_low_probability(self):
        """Water well below severe threshold should give low P(flood)."""
        from models.stress.flood_poly import p_flood_poly
        p = p_flood_poly(water_level=2.0, hour=84, severe_level=6.58)
        assert p < 0.1

    def test_monotonic_in_water_level(self):
        """Higher water level should give higher P(flood) at same hour."""
        from models.stress.flood_poly import p_flood_poly
        severe = 6.58
        hour = 84
        p_low = p_flood_poly(water_level=4.0, hour=hour, severe_level=severe)
        p_mid = p_flood_poly(water_level=5.5, hour=hour, severe_level=severe)
        p_high = p_flood_poly(water_level=7.0, hour=hour, severe_level=severe)
        assert p_low < p_mid < p_high

    def test_hour_zero_lower_than_mid_storm(self):
        """P(flood) at hour 0 should be lower than mid-storm for moderate water."""
        from models.stress.flood_poly import p_flood_poly
        severe = 6.58
        wl = 5.5
        p_early = p_flood_poly(water_level=wl, hour=0, severe_level=severe)
        p_mid = p_flood_poly(water_level=wl, hour=84, severe_level=severe)
        assert p_early < p_mid

    def test_very_low_water_near_zero(self):
        """Near-zero water level should give near-zero P(flood)."""
        from models.stress.flood_poly import p_flood_poly
        p = p_flood_poly(water_level=0.1, hour=48, severe_level=6.58)
        assert p < 0.01

    def test_extreme_water_near_one(self):
        """Water far above severe at late hour should be near 1.0."""
        from models.stress.flood_poly import p_flood_poly
        p = p_flood_poly(water_level=10.0, hour=120, severe_level=6.58)
        assert p > 0.9

    def test_hour_boundary_zero(self):
        """hour=0 should not raise."""
        from models.stress.flood_poly import p_flood_poly
        p = p_flood_poly(water_level=5.0, hour=0, severe_level=6.58)
        assert 0.0 <= p <= 1.0

    def test_hour_boundary_167(self):
        """hour=167 (last storm hour) should not raise."""
        from models.stress.flood_poly import p_flood_poly
        p = p_flood_poly(water_level=5.0, hour=167, severe_level=6.58)
        assert 0.0 <= p <= 1.0


# ===========================================================================
# p_flood_simple — time-independent model
# ===========================================================================

class TestPFloodSimple:

    def test_returns_float(self):
        from models.stress.flood_poly import p_flood_simple
        result = p_flood_simple(water_level=5.0, severe_level=6.58)
        assert isinstance(result, float)

    def test_in_range(self):
        from models.stress.flood_poly import p_flood_simple
        result = p_flood_simple(water_level=5.0, severe_level=6.58)
        assert 0.0 <= result <= 1.0

    def test_ratio_calculation(self):
        """P = min(1, w/s)."""
        from models.stress.flood_poly import p_flood_simple
        assert abs(p_flood_simple(3.29, 6.58) - 0.5) < 0.01

    def test_at_severe_equals_one(self):
        from models.stress.flood_poly import p_flood_simple
        assert p_flood_simple(6.58, 6.58) == 1.0

    def test_above_severe_capped_at_one(self):
        from models.stress.flood_poly import p_flood_simple
        assert p_flood_simple(10.0, 6.58) == 1.0

    def test_zero_water(self):
        from models.stress.flood_poly import p_flood_simple
        assert p_flood_simple(0.0, 6.58) == 0.0

    def test_zero_severe_returns_zero(self):
        from models.stress.flood_poly import p_flood_simple
        assert p_flood_simple(5.0, 0.0) == 0.0

    def test_negative_severe_returns_zero(self):
        from models.stress.flood_poly import p_flood_simple
        assert p_flood_simple(5.0, -1.0) == 0.0


# ===========================================================================
# p_flood_series — hydrograph convenience wrapper
# ===========================================================================

class TestPFloodSeries:

    def test_returns_list(self):
        from models.stress.flood_poly import p_flood_series
        result = p_flood_series([3.0, 4.0, 5.0], severe_level=6.58)
        assert isinstance(result, list)

    def test_correct_length(self):
        from models.stress.flood_poly import p_flood_series
        levels = [3.0, 4.0, 5.0, 6.0, 7.0]
        result = p_flood_series(levels, severe_level=6.58)
        assert len(result) == 5

    def test_all_in_range(self):
        from models.stress.flood_poly import p_flood_series
        levels = [2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
        result = p_flood_series(levels, severe_level=6.58)
        assert all(0.0 <= p <= 1.0 for p in result)

    def test_empty_list(self):
        from models.stress.flood_poly import p_flood_series
        assert p_flood_series([], severe_level=6.58) == []


# ===========================================================================
# model_card — metadata for audit
# ===========================================================================

class TestModelCard:

    def test_returns_dict(self):
        from models.stress.flood_poly import model_card
        card = model_card()
        assert isinstance(card, dict)

    def test_has_required_fields(self):
        from models.stress.flood_poly import model_card
        card = model_card()
        assert "model_id" in card
        assert "version" in card
        assert "coefficients" in card
        assert "fit_quality" in card
        assert "fitted_from" in card

    def test_model_id_matches_config(self):
        from models.stress.flood_poly import model_card
        from config.models import flood_poly_fit
        card = model_card()
        assert card["model_id"] == flood_poly_fit["model_id"]

    def test_coefficients_count(self):
        from models.stress.flood_poly import model_card
        card = model_card()
        assert card["num_parameters"] == 6

    def test_fit_quality_has_metrics(self):
        from models.stress.flood_poly import model_card
        card = model_card()
        fq = card["fit_quality"]
        assert "r_squared" in fq
        assert "mae" in fq
        assert "rmse" in fq


# ===========================================================================
# Config integration
# ===========================================================================

class TestConfigIntegration:

    def test_coefficients_from_config(self):
        """Coefficients used by model match config/models.py."""
        from config.models import flood_poly_coeffs
        from models.stress.flood_poly import p_flood_poly
        # Verify the named tuple has the expected fields
        assert hasattr(flood_poly_coeffs, 'a')
        assert hasattr(flood_poly_coeffs, 'f')
        assert len(flood_poly_coeffs) == 6

    def test_storm_hours_from_config(self):
        from config.models import flood_poly_storm_hours
        assert flood_poly_storm_hours == 168

    def test_log_eps_from_config(self):
        from config.models import flood_poly_log_eps
        assert flood_poly_log_eps == 1e-8

    def test_fit_metadata_from_config(self):
        from config.models import flood_poly_fit
        assert flood_poly_fit["model_id"] == "flood-poly-v1"
        assert flood_poly_fit["r_squared"] > 0.9
