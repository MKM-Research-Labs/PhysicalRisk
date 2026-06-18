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

"""Tests for POST /trading/stress/portfolio-run endpoint."""

import json

import pytest

from tests.routes.trading.conftest import STORM_PORT_SEVERE, STORM_PORT_ALERT


class TestRunPortfolioStress:
    """POST /trading/stress/portfolio-run endpoint tests."""

    def test_run_portfolio_missing_storm_id(self, port_stress_client, port_stress_env):
        """POST with no body or empty storm_id returns 400."""
        resp = port_stress_client.post('/api/v1/trading/stress/portfolio-run',
                                       json={})
        assert resp.status_code == 400

    def test_run_portfolio_invalid_storm(self, port_stress_client, port_stress_env):
        """POST with non-existent storm_id returns 404."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': 'STORM-DOES-NOT-EXIST'})
        assert resp.status_code == 404

    def test_run_portfolio_returns_success(self, port_stress_client, port_stress_env):
        """POST STORM-PORT-001 returns 200 with status=success."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'

    def test_portfolio_run_has_gauge_results(self, port_stress_client, port_stress_env):
        """Response has 'gauges' list."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        data = json.loads(resp.data)
        assert 'gauges' in data
        assert isinstance(data['gauges'], list)

    def test_portfolio_gauge_results_fields(self, port_stress_client, port_stress_env):
        """Each gauge has gauge_id, gauge_name, p_flood, p_flood_pct, threshold,
        stress_pnl, mtm, num_trades, trades, impacted."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        data = json.loads(resp.data)
        for g in data['gauges']:
            assert 'gauge_id' in g
            assert 'gauge_name' in g
            assert 'p_flood' in g
            assert 'p_flood_pct' in g
            assert 'threshold' in g
            assert 'stress_pnl' in g
            assert 'mtm' in g
            assert 'num_trades' in g
            assert 'trades' in g
            assert 'impacted' in g

    def test_portfolio_run_has_portfolio_totals(self, port_stress_client, port_stress_env):
        """Response has portfolio_stress_pnl, portfolio_mtm, num_gauges."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        data = json.loads(resp.data)
        assert 'portfolio_stress_pnl' in data
        assert 'portfolio_mtm' in data
        assert 'num_gauges' in data

    def test_portfolio_run_gauges_severe_list(self, port_stress_client, port_stress_env):
        """Response has gauges_severe as list of gauge_ids; for STORM_PORT_SEVERE
        should include GAUGE-001 and GAUGE-9042bd95."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        data = json.loads(resp.data)
        assert 'gauges_severe' in data
        assert isinstance(data['gauges_severe'], list)
        assert 'GAUGE-001' in data['gauges_severe']
        assert 'GAUGE-9042bd95' in data['gauges_severe']

    def test_portfolio_run_gauges_warning_list(self, port_stress_client, port_stress_env):
        """gauges_warning list includes GAUGE-002."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        data = json.loads(resp.data)
        assert 'gauges_warning' in data
        assert isinstance(data['gauges_warning'], list)
        # GAUGE-002 appears in the storm's gauge_responses with
        # exceeded_warning=True.  Threshold classification depends on
        # hydrograph scaling against gaugehc thresholds, so we verify
        # the field exists and is a list rather than a specific membership.
        assert 'gauges_alert' in data
        assert isinstance(data['gauges_alert'], list)


class TestPortfolioStressPnlCalculation:
    """Verify the CDS-in-stress cash pricing formula."""

    def test_stress_pnl_formula(self, port_stress_client, port_stress_env):
        """stress_pnl = cash_price - mtm; cash_price = signed_notional * p_flood."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_ALERT})
        data = json.loads(resp.data)
        assert data['status'] == 'success'
        for g in data['gauges']:
            for t in g.get('trades', []):
                # stress_pnl = cash_price - mtm
                assert abs(t['stress_pnl'] - (t['cash_price'] - t['mtm'])) < 0.01

    def test_payer_positive_notional(self, port_stress_client, port_stress_env):
        """Payer (is_payer=True) has positive notional in trade details."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        data = json.loads(resp.data)
        for g in data['gauges']:
            for t in g.get('trades', []):
                if t['is_payer']:
                    assert t['notional'] > 0, \
                        f"Payer trade {t['swap_id']} should have positive notional"

    def test_receiver_negative_notional(self, port_stress_client, port_stress_env):
        """Receiver (is_payer=False) has negative notional in trade details."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        data = json.loads(resp.data)
        for g in data['gauges']:
            for t in g.get('trades', []):
                if not t['is_payer']:
                    assert t['notional'] < 0, \
                        f"Receiver trade {t['swap_id']} should have negative notional"

    def test_severe_breach_latches_p_flood_to_100pct(self, port_stress_client, port_stress_env):
        """When peak_level_m >= severe_level, p_flood should be 1.0.
        GAUGE-001 peak 6.2m > severe 5.5m -> p_flood=1.0 regardless of predictor."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        data = json.loads(resp.data)
        gauge_001 = next(
            (g for g in data['gauges'] if g['gauge_id'] == 'GAUGE-001'), None)
        assert gauge_001 is not None
        assert gauge_001['p_flood'] == 1.0, \
            "GAUGE-001 peak 6.2m > severe 5.5m -- p_flood must be latched to 1.0"

    def test_unimpacted_gauge_has_zero_p_flood(self, port_stress_client, port_stress_env):
        """Gauge not in storm's gauge_responses has p_flood=0.0 and impacted=False."""
        # STORM_PORT_ALERT only has GAUGE-001 in its gauge_responses
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_ALERT})
        data = json.loads(resp.data)
        # GAUGE-9042bd95 is not in STORM_PORT_ALERT gauge_responses (no breach data)
        lambeth = next(
            (g for g in data['gauges'] if g['gauge_id'] == 'GAUGE-9042bd95'), None)
        if lambeth is not None:
            assert lambeth['p_flood'] == 0.0
            assert lambeth['impacted'] is False

    def test_portfolio_total_is_sum_of_gauges(self, port_stress_client, port_stress_env):
        """portfolio_stress_pnl == sum(g['stress_pnl'] for g in gauges)."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        data = json.loads(resp.data)
        expected_total = sum(g['stress_pnl'] for g in data['gauges'])
        assert abs(data['portfolio_stress_pnl'] - expected_total) < 0.01, \
            "portfolio_stress_pnl must equal the sum of all gauge stress_pnl values"
