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

"""Tests for models.floodrisk.depth_damage — scalar_depth_damage."""

import pytest

from models.floodrisk.depth_damage import (
    DAMAGE_POINTS,
    DEPTH_POINTS,
    scalar_depth_damage,
)


class TestScalarDepthDamage:

    def test_zero_depth_returns_zero(self):
        assert scalar_depth_damage(0.0) == 0.0

    def test_negative_depth_returns_zero(self):
        assert scalar_depth_damage(-1.0) == 0.0
        assert scalar_depth_damage(-100.0) == 0.0

    def test_max_depth_returns_one(self):
        assert scalar_depth_damage(DEPTH_POINTS[-1]) == pytest.approx(1.0)

    def test_above_max_depth_returns_one(self):
        assert scalar_depth_damage(100.0) == pytest.approx(1.0)

    def test_small_depth_returns_small_damage(self):
        d = scalar_depth_damage(0.05)
        assert d == pytest.approx(DAMAGE_POINTS[1], abs=1e-9)

    def test_half_meter_damage(self):
        # 0.5m is a control point
        d = scalar_depth_damage(0.5)
        assert d == pytest.approx(DAMAGE_POINTS[2], abs=1e-6)

    def test_one_meter_damage(self):
        d = scalar_depth_damage(1.0)
        assert d == pytest.approx(DAMAGE_POINTS[3], abs=1e-6)

    def test_monotonically_increasing(self):
        depths = [0.01, 0.1, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0]
        damages = [scalar_depth_damage(d) for d in depths]
        assert all(damages[i] <= damages[i + 1] for i in range(len(damages) - 1))

    def test_returns_float(self):
        assert isinstance(scalar_depth_damage(0.75), float)

    def test_between_control_points_interpolated(self):
        # Between 0.5m (0.25) and 1.0m (0.40): midpoint should be ~0.325
        d = scalar_depth_damage(0.75)
        assert 0.25 < d < 0.40

    def test_damage_between_0_and_1(self):
        for depth in [0.01, 0.25, 0.5, 1.0, 2.5, 4.9]:
            assert 0 <= scalar_depth_damage(depth) <= 1.0
