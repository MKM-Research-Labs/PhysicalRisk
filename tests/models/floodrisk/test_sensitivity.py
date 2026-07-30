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

"""Tests for models.floodrisk.sensitivity — depth-damage what-if diagnostics."""
import math

from models.floodrisk.sensitivity import (
    damage_distribution,
    damage_elasticity,
    depth_bias_sensitivity,
    depth_damage_sensitivity,
    poly_damage,
    poly_damage_slope,
)


class TestPolyDamage:
    def test_zero_and_negative_depth_is_no_damage(self):
        assert poly_damage(0.0) == 0.0
        assert poly_damage(-1.0) == 0.0

    def test_matches_piecewise_anchor_at_one_metre(self):
        # DAMAGE_POINTS has 0.40 at DEPTH_POINTS 1.0 m; the polynomial reproduces it.
        assert abs(poly_damage(1.0) - 0.40) < 0.01

    def test_clamped_into_unit_interval(self):
        assert 0.0 <= poly_damage(50.0) <= 1.0
        assert poly_damage(50.0) == 1.0  # deep water saturates on the clamp


class TestPolyDamageSlope:
    def test_zero_depth_slope_is_zero(self):
        assert poly_damage_slope(0.0) == 0.0

    def test_positive_and_decreasing_on_the_concave_body(self):
        # Concave curve: marginal damage per metre falls as depth rises.
        assert poly_damage_slope(0.25) > poly_damage_slope(1.0) > 0.0


class TestDamageElasticity:
    def test_zero_where_no_damage(self):
        assert damage_elasticity(0.0) == 0.0

    def test_below_one_and_attenuating(self):
        # Elasticity < 1 everywhere on the concave curve, and falls with depth.
        e_shallow = damage_elasticity(0.25)
        e_deep = damage_elasticity(2.0)
        assert e_shallow < 1.0
        assert e_deep < e_shallow

    def test_matches_definition(self):
        d = 0.8
        assert math.isclose(
            damage_elasticity(d), d * poly_damage_slope(d) / poly_damage(d))


class TestDepthDamageSensitivity:
    def test_base_row_reproduces_base_damage(self):
        out = depth_damage_sensitivity(1.0, [1.0])
        row = out["rows"][0]
        assert math.isclose(row["damage"], out["base_damage"])
        assert math.isclose(row["damage_rel_to_base"], 1.0)

    def test_shallower_reduces_damage(self):
        out = depth_damage_sensitivity(1.0, [0.5, 1.0, 1.5])
        damages = [r["damage"] for r in out["rows"]]
        assert damages[0] < damages[1] < damages[2]

    def test_nan_relative_when_base_is_dry(self):
        out = depth_damage_sensitivity(0.0, [2.0])
        assert math.isnan(out["rows"][0]["damage_rel_to_base"])


class TestDepthBiasSensitivity:
    def test_negative_bias_can_flip_property_dry(self):
        out = depth_bias_sensitivity(0.2, [-0.5, 0.0, 0.5])
        rows = {r["bias_m"]: r for r in out["rows"]}
        assert rows[-0.5]["flooded"] is False
        assert rows[-0.5]["damage"] == 0.0
        assert rows[0.5]["flooded"] is True
        assert rows[0.5]["damage_change"] > 0.0

    def test_base_damage_recorded(self):
        out = depth_bias_sensitivity(1.0, [0.0])
        assert math.isclose(out["rows"][0]["damage"], out["base_damage"])


class TestDamageDistribution:
    def test_median_row_is_base(self):
        out = damage_distribution(1.0, {"p05": 0.6, "p50": 1.0, "p95": 1.4})
        med = [r for r in out["rows"] if r["percentile"] == "p50"][0]
        assert math.isclose(med["damage"], out["median_damage"])
        assert math.isnan(med["passthrough"])

    def test_passthrough_below_one_on_concave_curve(self):
        out = damage_distribution(1.0, {"p50": 1.0, "p95": 1.4})
        hi = [r for r in out["rows"] if r["percentile"] == "p95"][0]
        assert 0.0 < hi["passthrough"] < 1.0

    def test_defaults_median_factor_to_one_when_absent(self):
        out = damage_distribution(1.0, {"p95": 1.4})
        assert math.isclose(out["median_damage"], poly_damage(1.0))

    def test_nan_when_median_damage_is_zero(self):
        out = damage_distribution(0.0, {"p50": 1.0, "p95": 2.0})
        for r in out["rows"]:
            assert math.isnan(r["damage_rel_to_median"])
