# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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
