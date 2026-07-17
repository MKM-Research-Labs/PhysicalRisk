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

"""
Data lineage tests: PRS trade commit → blotter → active gauges.

Uses monkeypatch + tmp_path to isolate from production data.
Follows the same pattern as tests/routes/test_prs_basic.py.
"""

import pytest


@pytest.fixture
def isolated_client(lineage_app):
    """Authenticated Flask test client whose PRS writes are isolated to a scratch
    catchment input dir (see ``isolated_input_dir`` / ``lineage_app`` in conftest)."""
    from fixtures_admin import AuthenticatedTestClient

    lineage_app.test_client_class = AuthenticatedTestClient
    with lineage_app.test_client() as c:
        yield c


@pytest.fixture
def sample_trade_payload():
    """Minimal valid PRS trade commit payload."""
    return {
        'gauge_id': 'GAUGE-ef7f75ec',
        'gauge_name': 'Thames Caversham Bridge',
        'trigger': 'severe',
        'direction': 'pay',
        'notional': 5000000,
        'spread_bps': 300.0,
        'tenor': 3,
        'counterparty_id': 'CTPY-001',
        'counterparty_name': 'Test Counterparty',
    }


class TestTradeCommitPersists:
    """POST /prs/commit must persist the trade through the database seam."""

    def test_commit_returns_swap_id(self, isolated_client, sample_trade_payload):
        resp = isolated_client.post('/api/v1/prs/commit',
                                    json=sample_trade_payload,
                                    content_type='application/json')
        data = resp.get_json()
        assert data['status'] == 'success', f"Commit failed: {data}"
        assert data['swap_id'].startswith('PRS-')

    def test_commit_persists_via_seam(self, isolated_client, sample_trade_payload):
        import database
        from config import config

        resp = isolated_client.post('/api/v1/prs/commit',
                                    json=sample_trade_payload,
                                    content_type='application/json')
        swap_id = resp.get_json()['swap_id']

        trade = database.get_prs_trade(config.catchment_id, swap_id)
        assert trade is not None, f"Committed trade {swap_id} not retrievable via seam"
        assert trade['PhysicalSwap']['Header']['SwapID'] == swap_id


class TestBlotterShowsNewTrade:
    """GET /trading/blotter must include a newly committed trade."""

    def test_new_trade_in_blotter(self, isolated_client, sample_trade_payload):
        commit_data = isolated_client.post(
            '/api/v1/prs/commit',
            json=sample_trade_payload,
            content_type='application/json'
        ).get_json()
        swap_id = commit_data['swap_id']

        blotter = isolated_client.get('/api/v1/trading/blotter').get_json()
        assert blotter['status'] == 'success'
        trade_ids = [t.get('swap_id') for t in blotter.get('trades', [])]
        assert swap_id in trade_ids, (
            f"Trade {swap_id} not in blotter ({len(trade_ids)} trades)"
        )


class TestActiveGaugesIncludesNewTrade:
    """GET /trading/blotter/active-gauges must include the new trade's gauge."""

    def test_gauge_in_active_list(self, isolated_client, sample_trade_payload):
        gauge_id = sample_trade_payload['gauge_id']

        isolated_client.post('/api/v1/prs/commit',
                             json=sample_trade_payload,
                             content_type='application/json')

        active = isolated_client.get(
            '/api/v1/trading/blotter/active-gauges'
        ).get_json()
        assert active['status'] == 'success'
        assert gauge_id in active.get('gauge_ids', []), (
            f"{gauge_id} not in active gauges after commit"
        )
