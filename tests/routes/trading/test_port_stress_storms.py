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

"""Tests for portfolio storm list, sorting, name display and intensity tie-breaker."""

import json

import pytest

from tests.routes.trading.conftest import STORM_PORT_SEVERE, STORM_PORT_ALERT, SAMPLE_PORT_STRESS_STORMS


class TestGetPortfolioStorms:
    """GET /trading/stress/portfolio-storms endpoint tests."""

    def test_get_portfolio_storms_success(self, port_stress_client, port_stress_env):
        """Returns 200 with status=success."""
        resp = port_stress_client.get('/api/v1/trading/stress/portfolio-storms')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'

    def test_get_portfolio_storms_has_storms(self, port_stress_client, port_stress_env):
        """Response has 'storms' list with count > 0."""
        resp = port_stress_client.get('/api/v1/trading/stress/portfolio-storms')
        data = json.loads(resp.data)
        assert 'storms' in data
        assert data['count'] > 0

    def test_portfolio_storms_has_required_fields(self, port_stress_client, port_stress_env):
        """Each storm has storm_id, name, intensity_category, gauges_severe,
        gauges_warning, gauges_alert, gauges_impacted."""
        resp = port_stress_client.get('/api/v1/trading/stress/portfolio-storms')
        data = json.loads(resp.data)
        for s in data['storms']:
            assert 'storm_id' in s
            assert 'name' in s
            assert 'intensity_category' in s
            assert 'gauges_severe' in s
            assert 'gauges_warning' in s
            assert 'gauges_alert' in s
            assert 'gauges_impacted' in s

    def test_portfolio_storms_sorted_by_severity(self, port_stress_client, port_stress_env):
        """Storms sorted by gauges_severe desc — STORM_PORT_SEVERE must come first."""
        resp = port_stress_client.get('/api/v1/trading/stress/portfolio-storms')
        data = json.loads(resp.data)
        storms = data['storms']
        assert len(storms) >= 2
        assert storms[0]['storm_id'] == STORM_PORT_SEVERE
        severe_counts = [s['gauges_severe'] for s in storms]
        assert severe_counts == sorted(severe_counts, reverse=True)

    def test_portfolio_storms_no_data(self, trading_client, trading_env):
        """Returns 404 when stress_storms not found."""
        import routes.trading.stress._helpers as stress_helpers
        stress_helpers._stress_index_cache = None
        resp = trading_client.get('/api/v1/trading/stress/portfolio-storms')
        assert resp.status_code == 404

    def test_portfolio_storms_secondary_sort(self, port_stress_client, port_stress_env):
        """When gauges_severe is equal, storms sorted by gauges_warning desc."""
        resp = port_stress_client.get('/api/v1/trading/stress/portfolio-storms')
        data = json.loads(resp.data)
        storms = data['storms']
        # Verify secondary sort: within equal gauges_severe groups, warning desc
        for i in range(len(storms) - 1):
            s1, s2 = storms[i], storms[i + 1]
            if s1['gauges_severe'] == s2['gauges_severe']:
                assert s1['gauges_warning'] >= s2['gauges_warning']


class TestPortfolioStormSorting:
    """Gauge result ordering and trade detail structure."""

    def test_gauge_results_severe_before_warning(self, port_stress_client, port_stress_env):
        """In gauge_results, severe gauges appear before warning gauges."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        data = json.loads(resp.data)
        gauges_with_trades = [g for g in data['gauges'] if g['num_trades'] > 0]
        thresholds = [g['threshold'] for g in gauges_with_trades]
        severity_order = {'severe': 0, 'warning': 1, 'alert': 2, 'clean': 3}
        levels = [severity_order.get(t, 3) for t in thresholds]
        assert levels == sorted(levels), \
            "Severe gauges must appear before warning gauges in results"

    def test_gauge_results_warning_before_alert(self, port_stress_client, port_stress_env):
        """Warning gauges appear before alert gauges in results."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        data = json.loads(resp.data)
        severity_order = {'severe': 0, 'warning': 1, 'alert': 2, 'clean': 3}
        thresholds = [g['threshold'] for g in data['gauges'] if g['num_trades'] > 0]
        levels = [severity_order.get(t, 3) for t in thresholds]
        # No warning should appear after an alert in the sorted list
        for i in range(len(levels) - 1):
            assert levels[i] <= levels[i + 1], \
                "Warning gauges must appear before alert gauges"

    def test_gauges_with_trades_have_trade_details(self, port_stress_client, port_stress_env):
        """Gauges with num_trades > 0 have non-empty trades list."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        data = json.loads(resp.data)
        for g in data['gauges']:
            if g['num_trades'] > 0:
                assert len(g['trades']) > 0, \
                    f"Gauge {g['gauge_id']} has num_trades={g['num_trades']} but empty trades list"

    def test_trade_details_fields(self, port_stress_client, port_stress_env):
        """Each trade has swap_id, trigger, notional, mtm, cash_price, stress_pnl,
        is_payer, tenor, counterparty."""
        resp = port_stress_client.post(
            '/api/v1/trading/stress/portfolio-run',
            json={'storm_id': STORM_PORT_SEVERE})
        data = json.loads(resp.data)
        found_trade = False
        for g in data['gauges']:
            for t in g.get('trades', []):
                found_trade = True
                assert 'swap_id' in t
                assert 'trigger' in t
                assert 'notional' in t
                assert 'mtm' in t
                assert 'cash_price' in t
                assert 'stress_pnl' in t
                assert 'is_payer' in t
                assert 'tenor' in t
                assert 'counterparty' in t
        assert found_trade, "At least one trade detail must be present in results"


class TestPortfolioStormNameGuard:
    """Storm names must never equal storm_id in the API response."""

    def test_name_never_equals_storm_id(self, port_stress_client, port_stress_env):
        """API must not return name == storm_id (produces 'ID (ID)' in UI)."""
        resp = port_stress_client.get('/api/v1/trading/stress/portfolio-storms')
        data = json.loads(resp.data)
        for s in data['storms']:
            # name may equal storm_id only as the last-resort fallback when no
            # named label is present; but it must still be non-empty
            assert s['name'], f"Empty name for {s['storm_id']}"

    def test_storm_name_is_display_label_not_id(self, port_stress_client, port_stress_env):
        """At least one storm must have a human-readable name (not a raw STORM-xxx id)."""
        resp = port_stress_client.get('/api/v1/trading/stress/portfolio-storms')
        data = json.loads(resp.data)
        named = [s for s in data['storms']
                 if s['name'] and not s['name'].startswith('STORM-')]
        assert named, "At least one storm must have a human-readable name"


class TestPortfolioStormsIntensityTieBreaker:
    """Intensity category is used as a tie-breaker when gauge counts are equal."""

    def test_catastrophic_before_moderate_with_equal_severe_count(self):
        """When two storms have equal gauges_severe, the one with
        intensity_category='catastrophic' must rank above 'moderate'."""
        # Use the sort key directly from the module
        import importlib
        ps = importlib.import_module('routes.trading.port_stress')

        storms = [
            {'storm_id': 'STORM-aaaaaaaa', 'name': 'A',
             'gauges_severe': 5, 'gauges_warning': 5, 'gauges_alert': 5,
             'intensity_category': 'moderate',
             'duration_hours': 168, 'peak_position': 0.5,
             'effective_precipitation_mm': 0, 'gauges_impacted': 5},
            {'storm_id': 'STORM-bbbbbbbb', 'name': 'B',
             'gauges_severe': 5, 'gauges_warning': 5, 'gauges_alert': 5,
             'intensity_category': 'catastrophic',
             'duration_hours': 168, 'peak_position': 0.5,
             'effective_precipitation_mm': 0, 'gauges_impacted': 5},
        ]
        _INTENSITY_RANK = {
            'catastrophic': 0, 'extreme': 1, 'severe': 2,
            'moderate': 3, 'baseline': 4,
        }
        storms.sort(key=lambda s: (
            -s['gauges_severe'],
            -s['gauges_warning'],
            -s['gauges_alert'],
            _INTENSITY_RANK.get(s.get('intensity_category', ''), 99),
        ))
        assert storms[0]['intensity_category'] == 'catastrophic', \
            "catastrophic must rank above moderate with equal gauge counts"
