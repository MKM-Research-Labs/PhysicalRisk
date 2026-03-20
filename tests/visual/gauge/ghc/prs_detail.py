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

"""Detailed regression tests for PRS Pricing tab (ghc_prs.py) JS generation.

Protects against regressions in analytical pricer, maturity convention,
yield curve integration, and trade commit workflow.
"""

import pytest


@pytest.fixture(scope='module')
def prs_js():
    """Get PRS pricing tab JS once for all tests."""
    from visual.interactivity.gauge.gaugehc import ghc_prs
    return ghc_prs.get_js()


class TestPRSTabRenders:
    """Basic rendering checks."""

    def test_prs_tab_renders(self, prs_js):
        """ghc_prs.get_js() returns valid JS."""
        assert len(prs_js) > 1000

    def test_prs_yield_curve_fetch(self, prs_js):
        """Fetches yield curve from /api/v1/trading/yield-curve."""
        assert '/api/v1/trading/yield-curve' in prs_js


class TestMaturityConvention:
    """Maturity date calculation functions."""

    def test_compute_maturity_date(self, prs_js):
        """computeMaturityDate function exists."""
        assert 'computeMaturityDate' in prs_js

    def test_last_friday_of_month(self, prs_js):
        """lastFridayOfMonth function exists."""
        assert 'lastFridayOfMonth' in prs_js

    def test_current_roll_date(self, prs_js):
        """currentRollDate function exists."""
        assert 'currentRollDate' in prs_js

    def test_maturity_popup(self, prs_js):
        """showMaturityPopup function exists."""
        assert 'showMaturityPopup' in prs_js


class TestAnalyticalPricer:
    """Cashflow and survival interpolation functions."""

    def test_cashflow_computation(self, prs_js):
        """computePRSCashflows function exists."""
        assert 'computePRSCashflows' in prs_js

    def test_survival_interpolation(self, prs_js):
        """interpolateSurvival function exists."""
        assert 'interpolateSurvival' in prs_js

    def test_yield_rate_interpolation(self, prs_js):
        """interpolateYieldRate function exists."""
        assert 'interpolateYieldRate' in prs_js


class TestPRSControls:
    """PRS pricer control panel must have all inputs."""

    def test_controls_function(self, prs_js):
        """buildPRSControls function exists."""
        assert 'buildPRSControls' in prs_js

    def test_direction_toggle(self, prs_js):
        """Payer/Receiver direction selector present."""
        assert 'payer' in prs_js.lower()
        assert 'receiver' in prs_js.lower()
        assert 'prs-direction' in prs_js

    def test_counterparty_dropdown(self, prs_js):
        """Counterparty selector present."""
        assert 'prs-counterparty' in prs_js

    def test_trigger_selector(self, prs_js):
        """Trigger level selector present."""
        assert 'prs-trigger' in prs_js

    def test_notional_input(self, prs_js):
        """Notional input field present."""
        assert 'prs-notional' in prs_js

    def test_maturity_selector(self, prs_js):
        """Maturity/tenor selector present."""
        assert 'prs-maturity' in prs_js


class TestTradeCommit:
    """Trade commit workflow."""

    def test_commit_endpoint(self, prs_js):
        """Posts to /api/v1/prs/commit."""
        assert '/api/v1/prs/commit' in prs_js

    def test_payer_flag_in_commit(self, prs_js):
        """Commit payload includes payer flag."""
        assert 'isPayer' in prs_js
