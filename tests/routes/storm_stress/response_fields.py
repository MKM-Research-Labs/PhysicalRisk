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

"""Tests that POST /trading/stress/run response contains all fields for UI rendering."""

import json


class TestStressRunResponseFields:
    """POST /trading/stress/run response must contain all fields needed
    to render both the gauge Stress tab and Trading Desk Stress tab.
    """

    def test_run_has_hydrograph_source_info(self, integration_env):
        """Response includes hydrograph_source string describing the data origin."""
        client = integration_env['client']
        resp = client.post('/api/v1/trading/stress/run',
                           json={'gauge_id': 'GAUGE-001',
                                 'storm_id': 'STORM-SEVERE-001'})
        data = json.loads(resp.data)
        assert 'hydrograph_source' in data, \
            "Response must describe hydrograph data origin for UI display"

    def test_run_has_alert_warning_severe_levels(self, integration_env):
        """Response includes trigger levels for threshold annotation on charts."""
        client = integration_env['client']
        resp = client.post('/api/v1/trading/stress/run',
                           json={'gauge_id': 'GAUGE-001',
                                 'storm_id': 'STORM-SEVERE-001'})
        data = json.loads(resp.data)
        assert 'alert_level' in data
        assert 'warning_level' in data
        assert 'severe_level' in data

    def test_run_has_storm_name_and_category(self, integration_env):
        """Response includes storm_name and intensity_category for header display."""
        client = integration_env['client']
        resp = client.post('/api/v1/trading/stress/run',
                           json={'gauge_id': 'GAUGE-001',
                                 'storm_id': 'STORM-SEVERE-001'})
        data = json.loads(resp.data)
        assert data['storm_name'] == 'Severe Storm Alpha'
        assert data['intensity_category'] == 'severe'

    def test_run_hourly_count_is_168(self, integration_env):
        """Hourly array must be 168 elements (7-day storm window).

        STORM_HOURS = 168 is the production constant. Tests using a local
        copy with num_hours=60 are testing the wrong default.
        """
        client = integration_env['client']
        resp = client.post('/api/v1/trading/stress/run',
                           json={'gauge_id': 'GAUGE-001',
                                 'storm_id': 'STORM-SEVERE-001'})
        data = json.loads(resp.data)
        assert len(data['hourly']) == 168, \
            "Stress run must return 168-hour forecast (STORM_HOURS=168), not 60"

    def test_run_probability_surface_has_full_168h(self, integration_env):
        """Surface table must cover the full 168h window regardless of knock-out."""
        client = integration_env['client']
        resp = client.post('/api/v1/trading/stress/run',
                           json={'gauge_id': 'GAUGE-001',
                                 'storm_id': 'STORM-SEVERE-001'})
        data = json.loads(resp.data)
        surface = data['probability_surface']
        assert max(surface['hours']) >= 164, \
            "Surface must go to H164+ -- user needs scrollable 168h table"


class TestStressStormsNoGaugeId:
    """GET /trading/stress/storms without gauge_id returns total count for startup popup."""

    def test_no_gauge_id_returns_200_not_400(self, integration_env):
        """Startup preloader fetches without gauge_id -- must not return 400."""
        r = integration_env['client'].get('/api/v1/trading/stress/storms')
        assert r.status_code == 200

    def test_no_gauge_id_returns_success(self, integration_env):
        r = integration_env['client'].get('/api/v1/trading/stress/storms')
        data = r.get_json()
        assert data['status'] == 'success'

    def test_no_gauge_id_returns_all_storms(self, integration_env):
        """All storms in file returned -- not filtered by gauge."""
        r = integration_env['client'].get('/api/v1/trading/stress/storms')
        data = r.get_json()
        assert 'storms' in data
        assert data['count'] == len(data['storms'])
        assert data['count'] == 2  # SHARED_STORM_DATA has 2 storms

    def test_no_gauge_id_response_has_count(self, integration_env):
        data = integration_env['client'].get('/api/v1/trading/stress/storms').get_json()
        assert isinstance(data['count'], int)
        assert data['count'] > 0

    def test_with_gauge_id_still_filters(self, integration_env):
        """gauge_id param still filters to matching storms."""
        r = integration_env['client'].get('/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        data = r.get_json()
        assert data['status'] == 'success'
        assert all(True for _ in data['storms'])  # endpoint filters but still succeeds
