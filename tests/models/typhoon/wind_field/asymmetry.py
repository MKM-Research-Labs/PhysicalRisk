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

"""Tests for models.typhoon.wind_field.asymmetry — motion-linked asymmetry
factor, epsilon scaling, and phi phase offset.
"""

import pytest

from models.typhoon.wind_field import (
    asymmetry_factor,
    compute_epsilon,
    compute_phi_deg,
)


class TestEpsilon:

    def test_zero_translation_gives_zero(self):
        eps = compute_epsilon(
            translation_speed_kmh=0.0, v_max_ms=40.0,
            eps_max=0.3, c_eps=0.6, eta_ms=1.0,
        )
        assert eps == pytest.approx(0.0, abs=1e-9)

    def test_capped_at_eps_max(self):
        eps = compute_epsilon(
            translation_speed_kmh=400.0, v_max_ms=20.0,
            eps_max=0.3, c_eps=0.6, eta_ms=1.0,
        )
        assert eps == 0.3

    def test_typical_storm(self):
        # 20 km/h ~= 5.56 m/s. With V=40 and eta=1, eps = 0.6 * 5.56 / 41 ~ 0.081.
        eps = compute_epsilon(
            translation_speed_kmh=20.0, v_max_ms=40.0,
            eps_max=0.3, c_eps=0.6, eta_ms=1.0,
        )
        assert eps == pytest.approx(0.6 * (20.0 / 3.6) / 41.0, abs=1e-9)


class TestPhi:

    def test_motion_plus_offset_wraps(self):
        # 270 + 90 = 360 = 0.
        assert compute_phi_deg(270.0, 90.0) == 0.0

    def test_wrapping_handled(self):
        assert compute_phi_deg(350.0, 30.0) == 20.0


class TestAsymmetryFactor:

    def test_neutral_when_eps_zero(self):
        assert asymmetry_factor(0.0, 0.0, 0.0) == 1.0

    def test_enhancement_along_phi(self):
        # theta = phi -> cos(0) = 1 -> max enhancement.
        assert asymmetry_factor(45.0, 45.0, 0.2) == pytest.approx(1.2, abs=1e-9)

    def test_suppression_opposite_phi(self):
        # theta - phi = 180 -> cos = -1 -> max suppression.
        assert asymmetry_factor(225.0, 45.0, 0.2) == pytest.approx(0.8, abs=1e-9)
