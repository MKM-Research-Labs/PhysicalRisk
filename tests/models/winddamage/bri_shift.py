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

"""Tests for models.winddamage.bri_shift — BRI-driven v_50 shift."""

import math

import pytest

from config.bri import (
    BRI_COMPOSITE_BETA_MS,
    BRI_COMPOSITE_REFERENCE,
    BRI_WIND_ALPHA_MS,
    BRI_WIND_REFERENCE,
    WIND_V50_SHIFT_MAX_MS,
)
from models.winddamage.bri_shift import bri_v50_shift


class TestBriV50Shift:

    def test_at_references_shift_is_zero(self):
        # ln(1) = 0 in both terms.
        s = bri_v50_shift(BRI_WIND_REFERENCE, BRI_COMPOSITE_REFERENCE)
        assert s == pytest.approx(0.0, abs=1e-12)

    def test_above_reference_gives_positive_shift(self):
        # Hardening: curve translates right, less damage at same gust.
        s = bri_v50_shift(0.80, 0.70)
        assert s > 0.0

    def test_below_reference_gives_negative_shift(self):
        # More vulnerable than baseline: curve translates left.
        s = bri_v50_shift(0.20, 0.20)
        assert s < 0.0

    def test_monotonic_in_wind_score(self):
        # Holding composite at reference, larger wind score gives larger shift.
        a = bri_v50_shift(0.30, BRI_COMPOSITE_REFERENCE)
        b = bri_v50_shift(0.60, BRI_COMPOSITE_REFERENCE)
        c = bri_v50_shift(0.90, BRI_COMPOSITE_REFERENCE)
        assert a < b < c

    def test_monotonic_in_composite_score(self):
        a = bri_v50_shift(BRI_WIND_REFERENCE, 0.30)
        b = bri_v50_shift(BRI_WIND_REFERENCE, 0.60)
        c = bri_v50_shift(BRI_WIND_REFERENCE, 0.90)
        assert a < b < c

    def test_shift_capped_above(self):
        # An almost-1.0 wind score with composite also high blows past the cap.
        s = bri_v50_shift(0.999, 0.999)
        assert s <= WIND_V50_SHIFT_MAX_MS

    def test_shift_capped_below(self):
        # Tiny scores produce a large negative log-shift; cap kicks in.
        s = bri_v50_shift(1e-12, 1e-12)
        assert s >= -WIND_V50_SHIFT_MAX_MS

    def test_zero_score_is_clamped_not_undefined(self):
        # ln(0) is undefined; the implementation must floor and still
        # return a finite value at the cap.
        s = bri_v50_shift(0.0, 0.0)
        assert math.isfinite(s)
        assert s == pytest.approx(-WIND_V50_SHIFT_MAX_MS, abs=1e-9)

    def test_analytical_value_at_2x_reference(self):
        # Wind score doubles (composite at reference) => shift = alpha * ln(2).
        s = bri_v50_shift(2 * BRI_WIND_REFERENCE, BRI_COMPOSITE_REFERENCE)
        expected = BRI_WIND_ALPHA_MS * math.log(2.0)
        assert s == pytest.approx(expected, abs=1e-9)

    def test_composite_alone_moves_the_shift(self):
        s = bri_v50_shift(BRI_WIND_REFERENCE, 2 * BRI_COMPOSITE_REFERENCE)
        expected = BRI_COMPOSITE_BETA_MS * math.log(2.0)
        assert s == pytest.approx(expected, abs=1e-9)
