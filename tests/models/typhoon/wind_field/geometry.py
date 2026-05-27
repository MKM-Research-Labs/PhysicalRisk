# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.typhoon.wind_field.geometry — Haversine distance and
compass bearing between storm center and evaluation point.
"""

import math

import pytest

from models.typhoon.transitions.position import EARTH_RADIUS_KM
from models.typhoon.wind_field import bearing_deg, haversine_distance_km


# Neutral test coordinates — see tests/models/typhoon/conftest.py.
LON, LAT = 5.0, 5.0


class TestHaversineDistance:

    def test_zero_for_coincident_points(self):
        assert haversine_distance_km(LON, LAT, LON, LAT) == pytest.approx(0.0, abs=1e-9)

    def test_one_degree_latitude_is_pi_R_over_180(self):
        # Exact analytical: pi * R / 180 ~ 111.195 km per degree along a meridian.
        d = haversine_distance_km(LON, LAT, LON, LAT + 1.0)
        expected = math.pi * EARTH_RADIUS_KM / 180.0
        assert d == pytest.approx(expected, abs=1e-3)

    def test_symmetric(self):
        d_ab = haversine_distance_km(LON, LAT, LON + 1.5, LAT + 1.5)
        d_ba = haversine_distance_km(LON + 1.5, LAT + 1.5, LON, LAT)
        assert d_ab == pytest.approx(d_ba, abs=1e-9)


class TestBearing:

    def test_due_east_is_90(self):
        # Small lon step at the same latitude is approximately due east.
        b = bearing_deg(LON, LAT, LON + 0.01, LAT)
        assert b == pytest.approx(90.0, abs=0.01)

    def test_due_north_is_0(self):
        b = bearing_deg(LON, LAT, LON, LAT + 0.01)
        assert b == pytest.approx(0.0, abs=0.01)

    def test_due_west_is_270(self):
        b = bearing_deg(LON, LAT, LON - 0.01, LAT)
        assert b == pytest.approx(270.0, abs=0.01)

    def test_due_south_is_180(self):
        b = bearing_deg(LON, LAT, LON, LAT - 0.01)
        assert b == pytest.approx(180.0, abs=0.01)

    def test_in_range(self):
        b = bearing_deg(LON, LAT, LON - 0.3, LAT + 0.3)
        assert 0.0 <= b < 360.0
