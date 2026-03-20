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

"""storm_id consistency: list IDs must be accepted by /trading/stress/run."""

import json
from unittest.mock import MagicMock, patch


class TestStormIdConsistency:

    @patch('routes.trading.stress.scenario._get_predictor')
    def test_storm_from_list_is_runnable(self, mock_pred, integration_env):
        pred = MagicMock()
        pred.predict.return_value = 0.3
        pred._load_summary.return_value = {'gauges': []}
        mock_pred.return_value = pred

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

    @patch('routes.trading.stress.scenario._get_predictor')
    def test_worst_storm_auto_selection_is_runnable(self, mock_pred, integration_env):
        pred = MagicMock()
        pred.predict.return_value = 0.4
        pred._load_summary.return_value = {'gauges': []}
        mock_pred.return_value = pred

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

    @patch('routes.trading.stress.scenario._get_predictor')
    def test_storm_id_exact_match_required(self, mock_pred, integration_env):
        pred = MagicMock()
        pred.predict.return_value = 0.3
        pred._load_summary.return_value = {'gauges': []}
        mock_pred.return_value = pred

        client = integration_env['client']

        resp = client.post('/api/v1/trading/stress/run',
                           json={'gauge_id': 'GAUGE-001', 'storm_id': 'STORM-SEVERE-001'})
        assert resp.status_code == 200

        resp = client.post('/api/v1/trading/stress/run',
                           json={'gauge_id': 'GAUGE-001', 'storm_id': 'STORM-SEVERE'})
        assert resp.status_code == 404, "Partial storm_id must not match"
