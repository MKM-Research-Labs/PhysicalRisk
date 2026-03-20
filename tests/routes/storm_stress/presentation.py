# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests that gauge Stress tab, Trading Desk Stress tab, and Historical tab are consistent."""

import pytest


class TestPresentationConsistency:
    """Both the gauge Stress tab and Trading Desk Stress tab consume the same
    /trading/stress/storms endpoint.  The JS must access the same field names.
    """

    @pytest.fixture(scope='class')
    def ghc_stress_js(self):
        from visual.interactivity.gauge.gaugehc import ghc_stress
        return ghc_stress.get_js()

    @pytest.fixture(scope='class')
    def td_stress_js(self):
        from visual.interactivity.trading import stress
        return stress.get_js()

    @pytest.fixture(scope='class')
    def hist_js(self):
        from visual.interactivity.gauge.gaugehc import ghc_historical
        return ghc_historical.get_js()

    REQUIRED_FIELDS = [
        'storm_id', 'name', 'intensity_category',
        'gauges_severe', 'effective_precipitation_mm',
    ]

    def test_gauge_stress_tab_uses_all_required_fields(self, ghc_stress_js):
        """Gauge Stress tab storm dropdown uses all required storm fields."""
        for field in self.REQUIRED_FIELDS:
            assert field in ghc_stress_js, \
                f"Gauge Stress tab missing field '{field}'"

    def test_trading_stress_tab_uses_all_required_fields(self, td_stress_js):
        """Trading Desk Stress tab storm dropdown uses all required storm fields."""
        for field in self.REQUIRED_FIELDS:
            assert field in td_stress_js, \
                f"Trading Desk Stress tab missing field '{field}'"

    def test_historical_tab_uses_all_required_fields(self, hist_js):
        """Historical tab storm list uses all required storm fields."""
        for field in self.REQUIRED_FIELDS:
            assert field in hist_js, \
                f"Historical tab storm list missing field '{field}'"

    def test_all_three_use_same_storms_endpoint(self, ghc_stress_js,
                                                 td_stress_js, hist_js):
        """All three tabs must fetch from /trading/stress/storms."""
        for js, name in [(ghc_stress_js, 'Gauge Stress'),
                         (td_stress_js, 'Trading Desk Stress'),
                         (hist_js, 'Historical')]:
            assert '/trading/stress/storms' in js, \
                f"{name} tab must use /trading/stress/storms endpoint"

    def test_peak_level_m_in_trading_stress_label(self, td_stress_js):
        """Trading Desk storm dropdown includes peak_level_m in the label.

        This is a deliberate difference — the TD label shows peak level for
        trading context, while gauge tab shows storm_id.
        """
        assert 'peak_level_m' in td_stress_js, \
            "Trading Desk storm label must show peak_level_m"

    def test_gauge_stress_auto_selects_worst_case(self, ghc_stress_js):
        """Gauge Stress tab auto-selects storms[0] (worst case)."""
        assert 'storms[0]' in ghc_stress_js or 'storms.length > 0' in ghc_stress_js, \
            "Gauge Stress tab must auto-select first storm (worst case)"

    def test_trading_stress_auto_selects_worst_case(self, td_stress_js):
        """Trading Desk Stress tab also auto-selects worst case storm."""
        assert 'withTrades' in td_stress_js or \
               'storms.length' in td_stress_js, \
            "Trading Desk Stress tab must auto-select worst case storm"
