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
Tests for models.stress.flood_poly -- the flood polynomial, MKM-FPO-001 v2.0.

This file was named ``flood_poly.py`` until v2.0, so pytest never collected it and
its v1.0 assertions were never run. The benchmark (tools/wolfram_oracle/floodpoly)
checks the arithmetic to 1e-14; these pin the model's documented behaviour.
"""

import math

import pytest

from config.models import (
    flood_poly_coeffs,
    flood_poly_envelope,
    flood_poly_fit,
    flood_poly_level_floor,
    flood_poly_storm_hours,
    flood_poly_terms,
)
from models.stress.flood_poly import (
    client_params,
    envelope_slope,
    envelope_t,
    kernel,
    kernel_dh,
    kernel_dt,
    model_card,
    p_flood_poly,
    p_flood_series,
    p_flood_simple,
    p_from_features,
    slope_from_features,
)

SEVERE = 6.58
H_FLOOR = math.log(flood_poly_level_floor)


class TestPFloodPoly:

    def test_returns_a_probability(self):
        p = p_flood_poly(water_level=5.0, hour=48, severe_level=SEVERE)
        assert isinstance(p, float) and 0.0 <= p <= 1.0

    @pytest.mark.parametrize("severe", [0.0, -1.0])
    def test_no_severe_level_returns_zero(self, severe):
        assert p_flood_poly(water_level=5.0, hour=48, severe_level=severe) == 0.0

    @pytest.mark.parametrize("hour", [0, 24, 84, 167])
    def test_at_or_above_severe_a_flood_has_happened(self, hour):
        assert p_flood_poly(SEVERE, hour, SEVERE) == 1.0
        assert p_flood_poly(10.0, hour, SEVERE) == 1.0

    @pytest.mark.parametrize("hour", range(168))
    def test_rising_water_never_lowers_p(self, hour):
        """v1.0 fell as the level rose early in a storm; v2.0 is fitted monotone, held
        hours included."""
        levels = [SEVERE * k / 2000 for k in range(1, 2001)]
        ps = [p_flood_poly(w, hour, SEVERE) for w in levels]
        assert all(b >= a - 1e-12 for a, b in zip(ps, ps[1:]))

    def test_below_the_floor_p_holds_its_value_there_and_is_negligible(self):
        for hour in range(168):
            at_floor = p_flood_poly(SEVERE * flood_poly_level_floor, hour, SEVERE)
            assert p_flood_poly(0.1, hour, SEVERE) == at_floor
            assert at_floor < 0.01

    def test_at_a_fixed_level_p_falls_as_the_storm_goes_on(self):
        """A level reached late in a storm is less likely to go on to severe."""
        early, late = p_flood_poly(5.0, 48, SEVERE), p_flood_poly(5.0, 120, SEVERE)
        assert early > 0.9 > 0.05 > late


class TestFeatures:

    def test_kernel_is_the_sum_over_the_configured_terms(self):
        h, t = -0.3, -1.2
        expected = sum(c * h ** i * t ** j
                       for (i, j), c in zip(flood_poly_terms, flood_poly_coeffs))
        assert kernel(h, t) == pytest.approx(expected, rel=1e-15)

    def test_kernel_dh_matches_a_central_difference(self):
        h, t, d = -0.4, -0.8, 1e-6
        numeric = (kernel(h + d, t) - kernel(h - d, t)) / (2 * d)
        assert kernel_dh(h, t) == pytest.approx(numeric, rel=1e-7)

    def test_the_slope_is_zero_at_severe_and_below_the_floor(self):
        assert slope_from_features(0.0, -1.0) == 0.0
        assert slope_from_features(H_FLOOR - 0.1, -1.0) == 0.0

    def test_the_slope_is_positive_between_the_floor_and_severe(self):
        for h in (H_FLOOR + 0.01, -0.8, -0.3, -0.01):
            for t in (-5.0, -2.0, -0.5, 0.0):
                assert slope_from_features(h, t) >= 0.0

    def test_kernel_dt_matches_a_central_difference(self):
        h, t, d = -0.4, -0.8, 1e-6
        numeric = (kernel(h, t + d) - kernel(h, t - d)) / (2 * d)
        assert kernel_dt(h, t) == pytest.approx(numeric, rel=1e-7)

    def test_p_from_features_clamps_h_at_the_floor(self):
        assert p_from_features(H_FLOOR - 3.0, -1.0) == p_from_features(H_FLOOR, -1.0)


class TestEnvelope:
    """Earlier than any storm reached a level, the hour is held where one did."""

    def test_the_knots_are_the_configured_hours(self):
        for ratio, hour in flood_poly_envelope[1:]:     # the first is where holding starts
            assert envelope_t(math.log(ratio)) == pytest.approx(math.log((hour + 1) / flood_poly_storm_hours))

    def test_below_the_first_knot_every_hour_is_supported(self):
        assert envelope_t(math.log(flood_poly_envelope[0][0]) - 0.01) == -math.inf
        assert envelope_slope(math.log(flood_poly_envelope[0][0]) - 0.01) == 0.0

    def test_beyond_the_last_knot_the_envelope_holds_its_end(self):
        end = math.log((flood_poly_envelope[-1][1] + 1) / flood_poly_storm_hours)
        assert envelope_t(0.5) == pytest.approx(end)
        assert envelope_slope(0.5) == 0.0

    @pytest.mark.parametrize("ratio", [0.4, 0.6, 0.9])
    def test_an_hour_before_the_envelope_is_priced_at_it(self, ratio):
        held = math.exp(envelope_t(math.log(ratio))) * flood_poly_storm_hours - 1
        assert p_flood_poly(ratio * SEVERE, 0, SEVERE) == pytest.approx(
            p_from_features(math.log(ratio), math.log((held + 1) / flood_poly_storm_hours)))
        assert p_flood_poly(ratio * SEVERE, 0, SEVERE) == p_flood_poly(ratio * SEVERE, int(held), SEVERE)

    def test_after_the_envelope_the_hour_is_not_held(self):
        assert p_flood_poly(0.6 * SEVERE, 48, SEVERE) != p_flood_poly(0.6 * SEVERE, 60, SEVERE)

    def test_held_slope_matches_a_central_difference_at_a_fixed_hour(self):
        t, d = math.log(1 / flood_poly_storm_hours), 1e-6
        for h in (math.log(0.52), math.log(0.83)):        # off the knots, where it kinks
            numeric = (p_from_features(h + d, t) - p_from_features(h - d, t)) / (2 * d)
            assert slope_from_features(h, t) == pytest.approx(numeric, rel=1e-5)


class TestPFloodSimple:
    """A proximity ratio, not a probability: min(1, w/s)."""

    def test_ratio(self):
        assert p_flood_simple(3.29, SEVERE) == pytest.approx(0.5)

    @pytest.mark.parametrize("w", [SEVERE, 10.0])
    def test_capped_at_one(self, w):
        assert p_flood_simple(w, SEVERE) == 1.0

    @pytest.mark.parametrize("severe", [0.0, -1.0])
    def test_no_severe_level_returns_zero(self, severe):
        assert p_flood_simple(5.0, severe) == 0.0


class TestPFloodSeries:

    def test_hour_is_the_position_in_the_hydrograph(self):
        levels = [3.0, 4.0, 5.0, 6.0, 7.0]
        assert p_flood_series(levels, SEVERE) == [
            p_flood_poly(w, h, SEVERE) for h, w in enumerate(levels)]

    def test_empty(self):
        assert p_flood_series([], SEVERE) == []


class TestModelCard:

    def test_identifies_v2(self):
        card = model_card()
        assert card["model_id"] == flood_poly_fit["model_id"] == "flood-poly-v2"
        assert card["version"] == "2.0.0"

    def test_carries_every_coefficient_by_term(self):
        card = model_card()
        assert card["num_parameters"] == len(flood_poly_terms) == 10
        assert card["coefficients"]["h^1 t^0"] == flood_poly_coeffs[0]

    def test_says_what_it_was_fitted_to_and_how_well(self):
        card = model_card()
        assert card["fitted_to"] == flood_poly_fit["fitted_to"]
        assert set(card["fit_quality"]) >= {"near_mae", "near_bias", "below_mae"}
        assert card["storm_hours"] == flood_poly_storm_hours == 168


class TestClientParams:
    """What the port-stress screen evaluates; it must be the live model."""

    def test_serves_the_configured_model(self):
        params = client_params()
        assert params["coeffs"] == list(flood_poly_coeffs)
        assert params["terms"] == [list(t) for t in flood_poly_terms]
        assert params["level_floor"] == flood_poly_level_floor
        assert params["storm_hours"] == flood_poly_storm_hours
        assert params["envelope"] == [list(k) for k in flood_poly_envelope]
