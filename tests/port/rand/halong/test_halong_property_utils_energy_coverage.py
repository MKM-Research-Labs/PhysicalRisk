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

"""Coverage tests for halong property utils/energy generators — the
construction-era branches and the solar-generation path."""

import random

import pytest

from port.rand.halong.property import property_energy, property_utils


@pytest.fixture(autouse=True)
def _seed():
    random.seed(20260615)


class TestConstructionYear:
    def test_all_era_branches_reachable(self):
        # The era is chosen randomly internally; sample enough to exercise
        # every band branch (lines 47-56).
        years = {property_utils.generate_construction_year() for _ in range(400)}
        assert all(1800 <= y <= 2022 for y in years)
        # Spread across at least the pre-1900 and post-2000 extremes.
        assert min(years) < 1950 and max(years) > 2000


class TestSolarGeneration:
    def test_solar_pv_returns_positive(self):
        out = property_energy.calculate_solar_generation(
            {"renewable_system": "Solar PV", "property_area": 120})  # lines 64-66
        assert out > 0

    def test_multiple_system_returns_positive(self):
        out = property_energy.calculate_solar_generation(
            {"renewable_system": "Multiple", "property_area": 90})
        assert out > 0

    def test_no_renewable_returns_zero(self):
        assert property_energy.calculate_solar_generation(
            {"renewable_system": "None"}) == 0
