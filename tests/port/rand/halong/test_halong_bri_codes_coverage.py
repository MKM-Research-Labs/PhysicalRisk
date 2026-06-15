# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage test for water_threshold_for_grade — the no-exposure None cases
and the active-grade threshold pair."""

import pytest

from port.rand.halong.commercial import bri_codes


class TestWaterThresholdForGrade:
    @pytest.mark.parametrize("grade", [None, "N/A"])
    def test_no_exposure_returns_none(self, grade):
        assert bri_codes.water_threshold_for_grade(grade) is None  # lines 165-166

    def test_active_grade_returns_threshold_pair(self):
        out = bri_codes.water_threshold_for_grade("A")  # line 167
        assert out == {"major_m": bri_codes.WATER_MAJOR_M,
                       "minor_m": bri_codes.WATER_MINOR_M}
