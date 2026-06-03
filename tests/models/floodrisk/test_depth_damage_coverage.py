# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage tests for scalar_depth_damage edge cases plus bri_stilt and
bri_depth_damage."""

from models.floodrisk.depth_damage import (
    bri_depth_damage,
    bri_stilt,
    scalar_depth_damage,
)


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


class TestBriStilt:
    """Signed depth offset from BRI scores, clamped to ±BRI_STILT_MAX_M."""

    def test_high_scores_positive_stilt(self):
        # Scores above reference → hardened → positive stilt.
        assert bri_stilt(0.95, 0.95) > 0

    def test_low_scores_negative_stilt(self):
        # Scores below reference → vulnerable → negative stilt.
        assert bri_stilt(0.05, 0.05) < 0

    def test_clamped_to_max(self):
        from config.damage import BRI_STILT_MAX_M
        # Extreme high scores still clamp at +max.
        s = bri_stilt(1.0, 1.0)
        assert s <= BRI_STILT_MAX_M
        # Extreme low scores clamp at -max (zero handled by _LN_FLOOR).
        s_lo = bri_stilt(0.0, 0.0)
        assert s_lo >= -BRI_STILT_MAX_M


class TestBriDepthDamage:
    """Damage ratio with floor level + BRI stilt applied."""

    def test_effective_depth_zero_returns_zero(self):
        # Floor level above depth → effective ≤ 0 → 0.0.
        assert bri_depth_damage(0.2, 1.0, 0.5, 0.5) == 0.0

    def test_deep_flood_returns_positive_ratio(self):
        d = bri_depth_damage(3.0, 0.3, 0.5, 0.5)
        assert 0.0 < d <= 1.0

    def test_ratio_clamped_to_one(self):
        # Very deep flood → polynomial saturates → clamp at 1.0.
        d = bri_depth_damage(50.0, 0.0, 0.5, 0.5)
        assert d == 1.0
