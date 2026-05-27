# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.typhoon.wind_field.radial — symmetric profile and
outer-decay length calibration.
"""

import pytest

from models.typhoon.wind_field import (
    calibrate_outer_decay_length,
    symmetric_profile,
)


class TestCalibrateOuterDecayLength:

    def test_anchors_v_sym_at_r_outer_to_reference(self):
        v_max = 45.0
        r_max = 30.0
        r_outer = 150.0
        v_ref = 17.5
        p = 1.5
        L = calibrate_outer_decay_length(v_max, r_max, r_outer, v_ref, p)
        v_at_outer = symmetric_profile(
            r_km=r_outer, r_max_km=r_max, v_max_ms=v_max,
            alpha_eye=0.4, outer_decay_length_km=L, outer_shape_p=p,
        )
        assert v_at_outer == pytest.approx(v_ref, rel=1e-6)

    def test_fallback_when_v_max_below_reference(self):
        # Storm at or below gale-force at its eyewall — calibration undefined.
        L = calibrate_outer_decay_length(
            v_max_ms=15.0, r_max_km=30.0, r_outer_km=150.0,
            v_outer_ref_ms=17.5, outer_shape_p=1.5,
        )
        # Fallback to R_outer - R_max = 120.
        assert L == pytest.approx(120.0, abs=1e-9)

    def test_fallback_when_geometry_invalid(self):
        # R_max >= R_outer — defensive guard returns 1.0 km.
        L = calibrate_outer_decay_length(
            v_max_ms=40.0, r_max_km=150.0, r_outer_km=100.0,
            v_outer_ref_ms=17.5, outer_shape_p=1.5,
        )
        assert L == 1.0


class TestSymmetricProfile:

    def test_value_at_center_is_alpha_eye_times_v_max(self):
        v = symmetric_profile(
            r_km=0.0, r_max_km=30.0, v_max_ms=40.0,
            alpha_eye=0.4, outer_decay_length_km=100.0, outer_shape_p=1.5,
        )
        assert v == pytest.approx(0.4 * 40.0, abs=1e-9)

    def test_value_at_r_max_is_v_max(self):
        # Inner-core ramp continuous with outer-decay envelope at r = R_max.
        v = symmetric_profile(
            r_km=30.0, r_max_km=30.0, v_max_ms=40.0,
            alpha_eye=0.4, outer_decay_length_km=100.0, outer_shape_p=1.5,
        )
        assert v == pytest.approx(40.0, abs=1e-9)

    def test_inner_core_is_linear_ramp(self):
        # At r = R_max / 2, value should be (alpha_eye + (1-alpha_eye)/2) * V_max.
        v = symmetric_profile(
            r_km=15.0, r_max_km=30.0, v_max_ms=40.0,
            alpha_eye=0.4, outer_decay_length_km=100.0, outer_shape_p=1.5,
        )
        expected = (0.4 + 0.5 * 0.6) * 40.0
        assert v == pytest.approx(expected, abs=1e-9)

    def test_outer_decays_below_v_max(self):
        v = symmetric_profile(
            r_km=300.0, r_max_km=30.0, v_max_ms=40.0,
            alpha_eye=0.4, outer_decay_length_km=100.0, outer_shape_p=1.5,
        )
        assert v < 40.0
        assert v > 0.0

    def test_doubling_v_max_doubles_v_sym_at_fixed_geometry(self):
        # Profile is multiplicatively linear in V_max for fixed (r, R_max, L, p).
        v1 = symmetric_profile(
            r_km=80.0, r_max_km=30.0, v_max_ms=40.0,
            alpha_eye=0.4, outer_decay_length_km=100.0, outer_shape_p=1.5,
        )
        v2 = symmetric_profile(
            r_km=80.0, r_max_km=30.0, v_max_ms=80.0,
            alpha_eye=0.4, outer_decay_length_km=100.0, outer_shape_p=1.5,
        )
        assert v2 == pytest.approx(2.0 * v1, abs=1e-9)
