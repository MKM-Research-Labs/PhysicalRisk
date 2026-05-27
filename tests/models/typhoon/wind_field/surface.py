# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.typhoon.wind_field.surface — land / sea reduction."""

from models.typhoon.wind_field import surface_factor


class TestSurfaceFactor:

    def test_sea_uses_rho_surf_sea(self):
        assert surface_factor(is_land=False, rho_surf_sea=1.0, rho_surf_land=0.8) == 1.0

    def test_land_uses_rho_surf_land(self):
        assert surface_factor(is_land=True, rho_surf_sea=1.0, rho_surf_land=0.8) == 0.8
