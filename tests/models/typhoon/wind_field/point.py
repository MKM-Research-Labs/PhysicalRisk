# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.typhoon.wind_field.point — single-point evaluation
that composes geometry, radial profile, asymmetry, and surface reduction.
"""

import pytest

from config.typhoon import WindFieldParams
from models.typhoon.wind_field import (
    PointWind,
    evaluate_point,
    evaluate_point_with_geometry,
)
from tests.models.typhoon.wind_field._helpers import (
    DEFAULT_LAT,
    DEFAULT_LON,
    make_state,
)


# Neutral land masks for tests.
def _open_sea(lon, lat):
    return False


def _all_land(lon, lat):
    return True


@pytest.fixture
def default_params():
    return WindFieldParams()


class TestEvaluatePoint:

    def test_at_storm_center_value_is_alpha_eye_with_sea(self, default_params):
        s = make_state(lon=DEFAULT_LON, lat=DEFAULT_LAT, v=40.0, speed=0.0)
        v = evaluate_point(s, DEFAULT_LON, DEFAULT_LAT, default_params, _open_sea)
        # At r=0: V_sym = alpha_eye * V_max. Asymmetry = 1 (eps=0). Sea: rho=1.
        assert v == pytest.approx(default_params.alpha_eye * 40.0, abs=1e-9)

    def test_doubling_v_max_doubles_evaluation_in_inner_core(self, default_params):
        # Inside R_max the profile is strictly linear in V_max. Outside
        # R_max the outer-decay length depends on V_max so the relationship
        # is no longer linear (a real property of the model, not a bug).
        s1 = make_state(lon=DEFAULT_LON, lat=DEFAULT_LAT, v=40.0, speed=0.0, r_max=35.0)
        s2 = make_state(lon=DEFAULT_LON, lat=DEFAULT_LAT, v=80.0, speed=0.0, r_max=35.0)
        # 0.1 deg east ~= 11 km, well inside R_max=35.
        v1 = evaluate_point(s1, DEFAULT_LON + 0.1, DEFAULT_LAT, default_params, _open_sea)
        v2 = evaluate_point(s2, DEFAULT_LON + 0.1, DEFAULT_LAT, default_params, _open_sea)
        assert v2 == pytest.approx(2.0 * v1, rel=1e-9)

    def test_land_reduction_applied(self, default_params):
        # Same state and point — sea vs land differ by the reduction factor.
        s = make_state(speed=0.0)
        v_sea = evaluate_point(s, DEFAULT_LON + 0.5, DEFAULT_LAT, default_params, _open_sea)
        v_land = evaluate_point(s, DEFAULT_LON + 0.5, DEFAULT_LAT, default_params, _all_land)
        expected = default_params.rho_surf_land / default_params.rho_surf_sea * v_sea
        assert v_land == pytest.approx(expected, rel=1e-6)

    def test_faster_storm_enhances_nh_right_side(self, default_params):
        # Motion = 270 (west); the asymmetry phase offset (+90 in NH) puts
        # the peak enhancement on the north side. Place the eval point
        # north of center and verify a faster storm gives stronger winds
        # there than a slow one.
        slow = make_state(speed=5.0, heading=270.0, v=40.0)
        fast = make_state(speed=50.0, heading=270.0, v=40.0)
        v_slow = evaluate_point(slow, DEFAULT_LON, DEFAULT_LAT + 0.45, default_params, _open_sea)
        v_fast = evaluate_point(fast, DEFAULT_LON, DEFAULT_LAT + 0.45, default_params, _open_sea)
        assert v_fast > v_slow

    def test_geometry_returned_alongside_wind(self, default_params):
        s = make_state(lon=DEFAULT_LON, lat=DEFAULT_LAT)
        result = evaluate_point_with_geometry(
            s, DEFAULT_LON, DEFAULT_LAT + 0.5, default_params, _open_sea,
        )
        assert isinstance(result, PointWind)
        assert result.distance_km > 0.0
        # 0.5 deg north is roughly 55.6 km.
        assert result.distance_km == pytest.approx(55.6, abs=0.5)
        assert result.azimuth_deg == pytest.approx(0.0, abs=0.01)
