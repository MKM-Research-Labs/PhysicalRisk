# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage tests for scalar_depth_damage edge cases."""

from models.floodrisk.depth_damage import scalar_depth_damage


class TestScalarDepthDamageFallback:
    """Defensive return-0.0 path and control-point boundary behaviour."""

    def test_just_below_first_positive_depth(self):
        d = scalar_depth_damage(0.001)
        assert 0.0 < d < 0.05

    def test_at_each_control_point(self):
        from config.damage import DEPTH_POINTS
        for dp in DEPTH_POINTS:
            val = scalar_depth_damage(dp)
            assert 0.0 <= val <= 1.0
