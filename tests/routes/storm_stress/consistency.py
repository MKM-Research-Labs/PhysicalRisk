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

"""storm_id consistency: list IDs must be accepted by /trading/stress/run."""

import json


class TestStormIdConsistency:

    def test_storm_from_list_is_runnable(self, integration_env):
        client = integration_env['client']
        resp = client.get('/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert len(data['storms']) > 0

        for storm in data['storms']:
            run_resp = client.post(
                '/api/v1/trading/stress/run',
                json={'gauge_id': 'GAUGE-001', 'storm_id': storm['storm_id']}
            )
            run_data = json.loads(run_resp.data)
            assert run_resp.status_code == 200, \
                f"Storm {storm['storm_id']} returned {run_resp.status_code}: " \
                f"{run_data.get('message')}"
            assert run_data['status'] == 'success'

    def test_worst_storm_auto_selection_is_runnable(self, integration_env):
        client = integration_env['client']
        resp = client.get('/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        worst_storm = json.loads(resp.data)['storms'][0]

        run_resp = client.post(
            '/api/v1/trading/stress/run',
            json={'gauge_id': 'GAUGE-001', 'storm_id': worst_storm['storm_id']}
        )
        assert run_resp.status_code == 200, "Auto-selected storm must run without error"


class TestStressRunInputFields:

    def test_storm_list_has_all_run_inputs(self, integration_env):
        client = integration_env['client']
        resp = client.get('/api/v1/trading/stress/storms?gauge_id=GAUGE-001')
        data = json.loads(resp.data)
        assert data['gauge_id'] == 'GAUGE-001'
        for s in data['storms']:
            assert 'storm_id' in s

    def test_storm_id_exact_match_required(self, integration_env):
        client = integration_env['client']

        resp = client.post('/api/v1/trading/stress/run',
                           json={'gauge_id': 'GAUGE-001', 'storm_id': 'STORM-SEVERE-001'})
        assert resp.status_code == 200

        resp = client.post('/api/v1/trading/stress/run',
                           json={'gauge_id': 'GAUGE-001', 'storm_id': 'STORM-SEVERE'})
        assert resp.status_code == 404, "Partial storm_id must not match"
