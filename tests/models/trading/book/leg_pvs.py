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
