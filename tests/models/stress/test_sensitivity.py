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

"""Tests for models.stress.sensitivity — FloodPoly threshold what-if diagnostics."""
import math

from models.stress.sensitivity import (
    flood_probability,
    flood_probability_distribution,
    flood_probability_slope,
    threshold_sensitivity,
)


class TestFloodProbability:
    def test_probability_in_unit_interval(self):
        for h in (-1.0, 0.0, 1.0):
            assert 0.0 <= flood_probability(h, 0.0) <= 1.0

    def test_monotone_increasing_in_water_margin(self):
        assert flood_probability(-0.1, 0.0) < flood_probability(0.0, 0.0) < flood_probability(0.1, 0.0)

    def test_extreme_margin_clamped_not_overflowing(self):
        # Very large |h| would overflow exp without the clamp; must stay finite.
        assert flood_probability(100.0, 0.0) <= 1.0
        assert flood_probability(-100.0, 0.0) >= 0.0


class TestFloodProbabilitySlope:
    def test_slope_peaks_in_transition_band(self):
        # Steepest near the threshold (h=0), collapsing in the saturated tail.
        near = flood_probability_slope(0.0, 0.0)
        far = flood_probability_slope(0.4, 0.0)
        assert near > far
        assert far >= 0.0

    def test_slope_sign_matches_probability_rise(self):
        assert flood_probability_slope(0.0, 0.0) > 0.0


class TestThresholdSensitivity:
    def test_base_factor_reproduces_base_probability(self):
        out = threshold_sensitivity(6.0, 6.0, 167, [1.0])
        assert math.isclose(out["rows"][0]["prob"], out["base_prob"])
        assert math.isclose(out["rows"][0]["prob_change"], 0.0, abs_tol=1e-12)

    def test_higher_threshold_lowers_flood_probability(self):
        out = threshold_sensitivity(6.0, 6.0, 167, [0.95, 1.0, 1.05])
        probs = [r["prob"] for r in out["rows"]]
        assert probs[0] > probs[1] > probs[2]

    def test_reports_severe_level_and_slope(self):
        out = threshold_sensitivity(6.0, 6.0, 167, [1.1])
        row = out["rows"][0]
        assert math.isclose(row["severe_level"], 6.6)
        assert "slope_dP_dh" in row


class TestFloodProbabilityDistribution:
    def test_median_row_is_zero_move(self):
        out = flood_probability_distribution(
            6.0, 6.0, 167, {"p05": 0.95, "p50": 1.0, "p95": 1.05})
        med = [r for r in out["rows"] if r["percentile"] == "p50"][0]
        assert math.isclose(med["prob"], out["median_prob"])
        assert math.isclose(med["prob_minus_median"], 0.0, abs_tol=1e-12)

    def test_band_straddles_median(self):
        out = flood_probability_distribution(
            6.0, 6.0, 167, {"p05": 0.95, "p50": 1.0, "p95": 1.05})
        lo = [r for r in out["rows"] if r["percentile"] == "p05"][0]
        hi = [r for r in out["rows"] if r["percentile"] == "p95"][0]
        assert lo["prob_minus_median"] > 0.0  # lower threshold -> more likely
        assert hi["prob_minus_median"] < 0.0

    def test_defaults_median_factor_to_one_when_absent(self):
        out = flood_probability_distribution(6.0, 6.0, 167, {"p95": 1.05})
        assert math.isclose(out["median_prob"], flood_probability(0.0, out["log_time"]))
