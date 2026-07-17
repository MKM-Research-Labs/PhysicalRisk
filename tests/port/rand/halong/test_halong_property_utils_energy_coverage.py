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
