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

"""Tests for stress test endpoints -- gauges list and storms list."""

import json

import pytest

from .conftest import STORM_SEVERE


class TestGetStressGauges:
    """GET /trading/stress/gauges endpoint tests."""

    def test_get_gauges_returns_list(self, stress_client, stress_env):
        """Returns gauge list with trade counts."""
        resp = stress_client.get('/api/v1/trading/stress/gauges')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert 'gauges' in data
        assert data['count'] > 0

    def test_get_gauges_has_required_fields(self, stress_client, stress_env):
        """Each gauge has gauge_id, gauge_name, lon, lat, trade_count."""
        resp = stress_client.get('/api/v1/trading/stress/gauges')
        data = json.loads(resp.data)
        for g in data['gauges']:
            assert 'gauge_id' in g
            assert 'gauge_name' in g
            assert 'lon' in g
            assert 'lat' in g
            assert 'trade_count' in g

    def test_get_gauges_sorted_by_longitude(self, stress_client, stress_env):
        """Gauges sorted west to east (ascending longitude)."""
        resp = stress_client.get('/api/v1/trading/stress/gauges')
        data = json.loads(resp.data)
        lons = [g['lon'] for g in data['gauges']]
        assert lons == sorted(lons)

    def test_get_gauges_has_trade_counts(self, stress_client, stress_env):
        """Gauges with trades show non-zero trade_count."""
        resp = stress_client.get('/api/v1/trading/stress/gauges')
        data = json.loads(resp.data)
        # At least one gauge should have trades (from conftest fixtures)
        counts = [g['trade_count'] for g in data['gauges']]
        assert sum(counts) > 0


class TestGetStorms:
    """GET /trading/stress/storms endpoint tests."""

    def test_get_storms_no_gauge_id_returns_all_storms(self, stress_client, stress_env):
        """Missing gauge_id returns total count (used by startup preloader)."""
        resp = stress_client.get('/api/v1/trading/stress/storms')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'success'
        assert 'storms' in data
        assert isinstance(data['count'], int)

    def test_get_storms_returns_list(self, stress_client, stress_env):
        """Returns storm list for specified gauge."""
        resp = stress_client.get(
            '/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert len(data['storms']) == 2
        assert data['gauge_id'] == 'GAUGE-001'

    def test_get_storms_has_peak_level(self, stress_client, stress_env):
        """Each storm has peak_level_m."""
        resp = stress_client.get(
            '/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        data = json.loads(resp.data)
        for s in data['storms']:
            assert 'peak_level_m' in s
            assert s['peak_level_m'] > 0

    def test_get_storms_has_storm_fields(self, stress_client, stress_env):
        """Storms have required identification fields."""
        resp = stress_client.get(
            '/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        data = json.loads(resp.data)
        for s in data['storms']:
            assert 'storm_id' in s
            assert 'name' in s
            assert 'duration_hours' in s
            assert 'base_level_m' in s
            assert 'level_change_m' in s

    def test_get_storms_sorted_by_peak(self, stress_client, stress_env):
        """Storms sorted by peak level descending (worst first)."""
        resp = stress_client.get(
            '/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        data = json.loads(resp.data)
        peaks = [s['peak_level_m'] for s in data['storms']]
        assert peaks == sorted(peaks, reverse=True)

    def test_get_storms_no_data(self, trading_client, trading_env):
        """Returns 404 when stress_storms not found."""
        import routes.trading.stress._helpers as stress_helpers
        stress_helpers._stress_index_cache = None
        resp = trading_client.get(
            '/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        assert resp.status_code == 404

    def test_get_storms_no_matching_gauge(self, stress_client, stress_env):
        """Returns empty list for gauge with no storms."""
        resp = stress_client.get(
            '/api/v1/trading/stress/storms?gauge_id=GAUGE-999')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['storms'] == []

    def test_response_includes_total_storms(self, stress_client, stress_env):
        """Response must include total_storms (full catalogue count)."""
        resp = stress_client.get(
            '/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        data = json.loads(resp.data)
        assert 'total_storms' in data
        assert isinstance(data['total_storms'], int)
        assert data['total_storms'] >= len(data['storms'])
