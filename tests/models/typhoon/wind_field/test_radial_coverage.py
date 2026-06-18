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

"""Coverage tests for the symmetric radial wind profile's defensive guards:
degenerate R_max, negative radius clamp, zero decay length and the
non-positive neg_ln calibration fallback."""

import pytest

from models.typhoon.wind_field import radial


class TestRadialCoverage:
    def test_zero_r_max_returns_zero(self):
        assert radial.symmetric_profile(
            r_km=10.0, r_max_km=0.0, v_max_ms=50.0, alpha_eye=0.4,
            outer_decay_length_km=20.0, outer_shape_p=1.5) == 0.0  # line 111

    def test_negative_radius_clamped_to_centre(self):
        # r_km < 0 clamps to 0 -> inner-core floor = alpha_eye * v_max.
        v = radial.symmetric_profile(
            r_km=-5.0, r_max_km=30.0, v_max_ms=50.0, alpha_eye=0.4,
            outer_decay_length_km=20.0, outer_shape_p=1.5)  # line 113
        assert v == pytest.approx(0.4 * 50.0)

    def test_zero_decay_length_returns_v_max(self):
        # At/after R_max with a degenerate (<=0) decay length -> flat at V_max.
        v = radial.symmetric_profile(
            r_km=40.0, r_max_km=30.0, v_max_ms=50.0, alpha_eye=0.4,
            outer_decay_length_km=0.0, outer_shape_p=1.5)  # lines 120-121
        assert v == 50.0

    def test_calibrate_returns_delta_r_when_neg_ln_non_positive(self, monkeypatch):
        # neg_ln = -log(ratio) is positive in normal operation; force the
        # defensive guard at line 81 by making log() return 0.
        monkeypatch.setattr(radial.math, "log", lambda _x: 0.0)
        L = radial.calibrate_outer_decay_length(
            v_max_ms=45.0, r_max_km=30.0, r_outer_km=150.0,
            v_outer_ref_ms=17.5, outer_shape_p=1.5)
        assert L == pytest.approx(120.0)  # delta_r = 150 - 30
