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
Unit tests for hazard curve builder: GEVFitter, GaugeResponseModel, HazardCurveBuilder.
"""

import numpy as np

from models.hazard import (
    GaugeHazardCurve,
    GaugeResponse,
    GaugeResponseModel,
    GEVFitter,
    HazardCurveBuilder,
    TermStructurePoint,
    compute_term_structure,
)

# =============================================================================
# GEVFitter
# =============================================================================

class TestGEVFitter:

    def test_fit_returns_three_floats(self):
        np.random.seed(42)
        data = np.random.gumbel(loc=2.0, scale=0.5, size=200)
        fitter = GEVFitter(force_gumbel=False)
        shape, loc, scale = fitter.fit(data)
        assert isinstance(shape, float)
        assert isinstance(loc, float)
        assert isinstance(scale, float)

    def test_force_gumbel_sets_shape_zero(self):
        np.random.seed(42)
        data = np.random.gumbel(loc=2.0, scale=0.5, size=200)
        fitter = GEVFitter(force_gumbel=True)
        shape, loc, scale = fitter.fit(data)
        assert shape == 0.0

    def test_exceedance_probability_in_range(self):
        fitter = GEVFitter()
        prob = fitter.exceedance_probability(3.0, shape=0.0, loc=2.0, scale=0.5)
        assert 0.0 <= prob <= 1.0

    def test_higher_threshold_lower_probability(self):
        fitter = GEVFitter()
        p_low = fitter.exceedance_probability(2.0, shape=0.0, loc=2.0, scale=0.5)
        p_high = fitter.exceedance_probability(4.0, shape=0.0, loc=2.0, scale=0.5)
        assert p_high < p_low

    def test_return_level_increases_with_period(self):
        fitter = GEVFitter()
        rl_10 = fitter.return_level(10, shape=0.0, loc=2.0, scale=0.5)
        rl_100 = fitter.return_level(100, shape=0.0, loc=2.0, scale=0.5)
        assert rl_100 > rl_10


# =============================================================================
# GaugeResponseModel
# =============================================================================

class TestGaugeResponseModel:

    def test_compute_response_returns_gauge_response(self, synthetic_flat_gauges, synthetic_storm_dicts):
        model = GaugeResponseModel(synthetic_flat_gauges)
        gauge_id = synthetic_flat_gauges[0]["gauge_id"]
        storm = synthetic_storm_dicts[0]
        response = model.compute_response(gauge_id, storm)
        assert isinstance(response, GaugeResponse)
        assert response.gauge_id == gauge_id
        assert response.peak_level_m >= 0

    def test_compute_all_responses_returns_dict(self, synthetic_flat_gauges, synthetic_storm_dicts):
        model = GaugeResponseModel(synthetic_flat_gauges)
        responses = model.compute_all_responses(synthetic_storm_dicts[:10])
        assert isinstance(responses, dict)
        assert len(responses) == len(synthetic_flat_gauges)
        for gauge_id, resp_list in responses.items():
            assert len(resp_list) == 10

    def test_response_threshold_flags(self, synthetic_flat_gauges, synthetic_storm_dicts):
        model = GaugeResponseModel(synthetic_flat_gauges)
        gauge_id = synthetic_flat_gauges[0]["gauge_id"]
        storm = synthetic_storm_dicts[0]
        response = model.compute_response(gauge_id, storm)
        # If exceeded_warning, must also have exceeded_alert
        if response.exceeded_warning:
            assert response.exceeded_alert
        if response.exceeded_severe:
            assert response.exceeded_warning


# =============================================================================
# compute_term_structure
# =============================================================================

class TestTermStructure:

    def test_returns_correct_length(self):
        ts = compute_term_structure(0.05, max_years=5)
        assert len(ts) == 5

    def test_returns_term_structure_points(self):
        ts = compute_term_structure(0.05)
        for point in ts:
            assert isinstance(point, TermStructurePoint)

    def test_cumulative_prob_increasing(self):
        ts = compute_term_structure(0.05, max_years=5)
        probs = [p.cumulative_default_prob for p in ts]
        for i in range(1, len(probs)):
            assert probs[i] >= probs[i - 1]

    def test_survival_prob_decreasing(self):
        ts = compute_term_structure(0.05, max_years=5)
        survivals = [p.survival_prob for p in ts]
        for i in range(1, len(survivals)):
            assert survivals[i] <= survivals[i - 1]

    def test_probabilities_sum_to_one(self):
        ts = compute_term_structure(0.05)
        for point in ts:
            assert abs(point.survival_prob + point.prob_at_least_one - 1.0) < 1e-10


# =============================================================================
# HazardCurveBuilder (integration)
# =============================================================================

class TestHazardCurveBuilder:

    def test_build_returns_dict_of_curves(self, synthetic_flat_gauges, synthetic_storm_dicts):
        builder = HazardCurveBuilder(
            gauges=synthetic_flat_gauges,
            storms=synthetic_storm_dicts,
            verbose=False,
        )
        curves, responses = builder.build()
        assert isinstance(curves, dict)
        assert len(curves) == len(synthetic_flat_gauges)
        assert isinstance(responses, dict)
        assert len(responses) == len(synthetic_flat_gauges)

    def test_each_curve_is_gauge_hazard_curve(self, synthetic_flat_gauges, synthetic_storm_dicts):
        builder = HazardCurveBuilder(
            gauges=synthetic_flat_gauges,
            storms=synthetic_storm_dicts,
            verbose=False,
        )
        curves, _ = builder.build()
        for gauge_id, curve in curves.items():
            assert isinstance(curve, GaugeHazardCurve)
            assert curve.gauge_id == gauge_id

    def test_annual_flood_probabilities_in_range(self, synthetic_flat_gauges, synthetic_storm_dicts):
        builder = HazardCurveBuilder(
            gauges=synthetic_flat_gauges,
            storms=synthetic_storm_dicts,
            verbose=False,
        )
        curves, _ = builder.build()
        for curve in curves.values():
            assert 0.0 <= curve.annual_flood_prob_alert <= 1.0
            assert 0.0 <= curve.annual_flood_prob_warning <= 1.0
            assert 0.0 <= curve.annual_flood_prob_severe <= 1.0
