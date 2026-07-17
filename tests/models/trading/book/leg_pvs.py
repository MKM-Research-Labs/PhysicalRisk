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

"""Tests for leg PV computation."""

from port.src.book import _compute_leg_pvs


class TestComputeLegPVs:
    """Tests for leg PV computation."""

    def test_positive_hazard_rate(self):
        pvs = _compute_leg_pvs(0.025, 250.0, 5, 10_000_000)
        assert pvs["premium_leg_pv"] > 0
        assert pvs["protection_leg_pv"] > 0
        assert pvs["risky_annuity"] > 0
        assert pvs["risky_annuity"] < 5

    def test_zero_hazard_rate(self):
        pvs = _compute_leg_pvs(0.0, 100.0, 5, 10_000_000)
        assert pvs["premium_leg_pv"] == 0
        assert pvs["protection_leg_pv"] == 0

    def test_higher_spread_means_higher_premium(self):
        pvs_low = _compute_leg_pvs(0.025, 200.0, 5, 10_000_000)
        pvs_high = _compute_leg_pvs(0.025, 300.0, 5, 10_000_000)
        assert pvs_high["premium_leg_pv"] > pvs_low["premium_leg_pv"]
