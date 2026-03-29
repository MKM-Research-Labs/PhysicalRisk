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

"""Tests for yield curve, hazard term structure, and reset endpoints."""

import json

import pytest


class TestYieldCurve:
    """GET/POST /trading/yield-curve endpoint tests."""

    def test_get_yield_curve(self, trading_client, trading_env):
        """GET returns yield_curve dict."""
        resp = trading_client.get('/api/v1/trading/yield-curve')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert 'yield_curve' in data

    def test_get_yield_curve_default_shape(self, trading_client, trading_env):
        """Default yield curve has standard tenor points."""
        resp = trading_client.get('/api/v1/trading/yield-curve')
        data = json.loads(resp.data)
        yc = data['yield_curve']
        # Should have some tenor points (keys are string tenors)
        assert len(yc) > 0

    def test_update_yield_curve_single_tenor(self, trading_client, trading_env):
        """POST updates one tenor point."""
        resp = trading_client.post('/api/v1/trading/yield-curve',
                                   json={'tenor': 3, 'rate': 0.05})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert 'yield_curve' in data

    def test_update_yield_curve_invalid_tenor(self, trading_client, trading_env):
        """Tenor outside 1-30 returns 400."""
        resp = trading_client.post('/api/v1/trading/yield-curve',
                                   json={'tenor': 50, 'rate': 0.05})
        assert resp.status_code == 400

    def test_update_yield_curve_no_body(self, trading_client, trading_env):
        """POST without JSON body returns error."""
        resp = trading_client.post('/api/v1/trading/yield-curve',
                                   content_type='application/json')
        assert resp.status_code in (400, 500)


class TestYieldCurveCommit:
    """POST /trading/yield-curve/commit endpoint tests."""

    def test_commit_yield_curve(self, trading_client, trading_env):
        """Commit returns affected_trades and P&L impact fields."""
        resp = trading_client.post('/api/v1/trading/yield-curve/commit',
                                   json={'rates': {'1': 0.04, '3': 0.045}})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert 'affected_trades' in data
        assert 'total_pnl_impact' in data
        assert 'gross_pnl_impact' in data
        assert 'total_fs01' in data

    def test_commit_yield_curve_empty_rates(self, trading_client, trading_env):
        """Empty rates dict returns 400."""
        resp = trading_client.post('/api/v1/trading/yield-curve/commit',
                                   json={'rates': {}})
        assert resp.status_code == 400

    def test_commit_yield_curve_no_body(self, trading_client, trading_env):
        """No JSON body returns error."""
        resp = trading_client.post('/api/v1/trading/yield-curve/commit',
                                   content_type='application/json')
        assert resp.status_code in (400, 500)

    def test_commit_yield_curve_affected_count(self, trading_client,
                                                trading_env):
        """Commit should affect all open trades."""
        resp = trading_client.post(
            '/api/v1/trading/yield-curve/commit',
            json={'rates': {'1': 0.035, '2': 0.04, '3': 0.043,
                            '4': 0.045, '5': 0.04, '6': 0.04}})
        data = json.loads(resp.data)
        assert data['affected_trades'] == 16  # 16 trades in trading_env


class TestYieldCurveReset:
    """POST /trading/yield-curve/reset endpoint tests."""

    def test_reset_yield_curve(self, trading_client, trading_env):
        """Reset returns to default shape."""
        # First change it
        trading_client.post('/api/v1/trading/yield-curve',
                            json={'tenor': 1, 'rate': 0.10})
        # Then reset
        resp = trading_client.post('/api/v1/trading/yield-curve/reset')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert 'yield_curve' in data


class TestHazardTermStructure:
    """GET/POST /trading/hazard-term-structure endpoint tests."""

    def test_get_hazard_term_structure(self, trading_client, trading_env):
        """GET returns per-gauge per-trigger structure."""
        resp = trading_client.get('/api/v1/trading/hazard-term-structure')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert 'hazard_term_structure' in data

    def test_update_hazard_ts_single_point(self, trading_client, trading_env):
        """POST updates one gauge/trigger/tenor point."""
        resp = trading_client.post('/api/v1/trading/hazard-term-structure',
                                   json={'gauge_id': 'GAUGE-001',
                                         'trigger': 'severe',
                                         'tenor': 3, 'rate': 0.005})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'

    def test_update_hazard_ts_missing_gauge(self, trading_client, trading_env):
        """Missing gauge_id returns 400."""
        resp = trading_client.post('/api/v1/trading/hazard-term-structure',
                                   json={'trigger': 'severe',
                                         'tenor': 3, 'rate': 0.005})
        assert resp.status_code == 400

    def test_update_hazard_ts_invalid_tenor(self, trading_client, trading_env):
        """Tenor outside 1-10 returns 400."""
        resp = trading_client.post('/api/v1/trading/hazard-term-structure',
                                   json={'gauge_id': 'GAUGE-001',
                                         'trigger': 'severe',
                                         'tenor': 15, 'rate': 0.005})
        assert resp.status_code == 400


class TestHazardTSCommit:
    """POST /trading/hazard-term-structure/commit endpoint tests."""

    def test_commit_hazard_ts(self, trading_client, trading_env):
        """Commit returns affected_trades for the target gauge."""
        resp = trading_client.post(
            '/api/v1/trading/hazard-term-structure/commit',
            json={'gauge_id': 'GAUGE-001', 'trigger': 'severe',
                  'rates': {'1': 0.004, '2': 0.005, '3': 0.006}})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert 'affected_trades' in data
        assert 'total_pnl_impact' in data
        assert 'gross_pnl_impact' in data

    def test_commit_hazard_ts_only_affects_target_gauge(self, trading_client,
                                                         trading_env):
        """Committing GAUGE-001 only affects its trades (2 trades)."""
        resp = trading_client.post(
            '/api/v1/trading/hazard-term-structure/commit',
            json={'gauge_id': 'GAUGE-001', 'trigger': 'severe',
                  'rates': {'1': 0.004, '3': 0.006, '5': 0.008}})
        data = json.loads(resp.data)
        # GAUGE-001 has 2 trades (PRS-TEST-001, PRS-TEST-002)
        assert data['affected_trades'] == 2

    def test_commit_hazard_ts_missing_gauge(self, trading_client, trading_env):
        """Missing gauge_id returns 400."""
        resp = trading_client.post(
            '/api/v1/trading/hazard-term-structure/commit',
            json={'trigger': 'severe', 'rates': {'1': 0.004}})
        assert resp.status_code == 400

    def test_commit_hazard_ts_missing_rates(self, trading_client, trading_env):
        """Missing rates returns 400."""
        resp = trading_client.post(
            '/api/v1/trading/hazard-term-structure/commit',
            json={'gauge_id': 'GAUGE-001', 'trigger': 'severe'})
        assert resp.status_code == 400


class TestHazardTSReset:
    """POST /trading/hazard-term-structure/reset endpoint tests."""

    def test_reset_hazard_ts_single_gauge(self, trading_client, trading_env):
        """Reset one gauge."""
        resp = trading_client.post(
            '/api/v1/trading/hazard-term-structure/reset',
            json={'gauge_id': 'GAUGE-001'})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert 'GAUGE-001' in data['message']

    def test_reset_hazard_ts_all(self, trading_client, trading_env):
        """Reset all gauges."""
        resp = trading_client.post(
            '/api/v1/trading/hazard-term-structure/reset',
            json={})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert 'all' in data['message']
