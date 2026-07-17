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
