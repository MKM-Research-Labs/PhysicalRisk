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

"""Tests for models.typhoon.wind_field.sensitivity — wind-field what-if diagnostics."""
import math

from models.typhoon.wind_field.sensitivity import (
    intensity_sensitivity,
    local_peak_wind,
    peak_wind_distribution,
    track_offset_sensitivity,
)

# Representative Cat-3-ish anchor storm.
VMAX, RMAX, ROUTER = 50.0, 30.0, 250.0


class TestLocalPeakWind:
    def test_eyewall_is_peak_of_the_ramp(self):
        # Inner core ramps from alpha_eye*Vmax at centre up to Vmax at R_max.
        centre = local_peak_wind(0.0, VMAX, RMAX, ROUTER)
        eyewall = local_peak_wind(RMAX, VMAX, RMAX, ROUTER)
        assert centre < eyewall
        assert math.isclose(eyewall, VMAX, rel_tol=1e-6)

    def test_outer_field_decays_below_peak(self):
        assert local_peak_wind(120.0, VMAX, RMAX, ROUTER) < VMAX


class TestIntensitySensitivity:
    def test_base_factor_reproduces_base_wind(self):
        out = intensity_sensitivity(60.0, VMAX, RMAX, ROUTER, [1.0])
        assert math.isclose(out["rows"][0]["wind"], out["base_wind"])
        assert math.isclose(out["rows"][0]["wind_rel_to_base"], 1.0)

    def test_stronger_storm_raises_local_wind(self):
        out = intensity_sensitivity(60.0, VMAX, RMAX, ROUTER, [0.8, 1.0, 1.2])
        winds = [r["wind"] for r in out["rows"]]
        assert winds[0] < winds[1] < winds[2]

    def test_nan_relative_when_base_wind_zero(self):
        # A degenerate zero-intensity storm gives no wind, so relatives are nan.
        out = intensity_sensitivity(60.0, 0.0, RMAX, ROUTER, [1.0, 2.0])
        assert out["base_wind"] == 0.0
        assert math.isnan(out["rows"][0]["wind_rel_to_base"])


class TestTrackOffsetSensitivity:
    def test_gradient_steeper_on_eyewall_ramp_than_outer_field(self):
        out = track_offset_sensitivity(
            RMAX, VMAX, RMAX, ROUTER, [15.0, 120.0])
        ramp = [r for r in out["rows"] if r["offset_km"] == 15.0][0]
        outer = [r for r in out["rows"] if r["offset_km"] == 120.0][0]
        assert ramp["gradient_ms_per_km"] > abs(outer["gradient_ms_per_km"])

    def test_offset_near_zero_uses_clamped_difference(self):
        # offset 0 must not probe negative radius; span is clamped at 0.
        out = track_offset_sensitivity(RMAX, VMAX, RMAX, ROUTER, [0.0])
        assert math.isfinite(out["rows"][0]["gradient_ms_per_km"])

    def test_wind_change_recorded_against_base(self):
        out = track_offset_sensitivity(RMAX, VMAX, RMAX, ROUTER, [RMAX])
        assert math.isclose(out["rows"][0]["wind_change"], 0.0, abs_tol=1e-9)


class TestPeakWindDistribution:
    def test_median_row_is_zero_move(self):
        out = peak_wind_distribution(
            VMAX, RMAX, ROUTER, {"p05": 10.0, "p50": 45.0, "p95": 90.0})
        med = [r for r in out["rows"] if r["percentile"] == "p50"][0]
        assert math.isclose(med["wind"], out["median_wind"])
        assert math.isclose(med["wind_minus_median"], 0.0, abs_tol=1e-9)

    def test_farther_pass_gives_lower_wind(self):
        out = peak_wind_distribution(
            VMAX, RMAX, ROUTER, {"p50": 45.0, "p95": 120.0})
        far = [r for r in out["rows"] if r["percentile"] == "p95"][0]
        assert far["wind_minus_median"] < 0.0

    def test_nan_median_when_p50_absent(self):
        out = peak_wind_distribution(VMAX, RMAX, ROUTER, {"p95": 90.0})
        assert math.isnan(out["median_wind"])
        assert math.isnan(out["rows"][0]["wind_minus_median"])
