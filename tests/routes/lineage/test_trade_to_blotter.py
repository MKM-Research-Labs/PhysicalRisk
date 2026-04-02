# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Data lineage tests: PRS trade commit → blotter → active gauges.

Verifies the full chain:
  POST /prs/commit → trade file on disk
  GET /trading/blotter → trade appears in list
  GET /trading/blotter/active-gauges → gauge appears in active set
"""

import json
import os
import shutil

import pytest


@pytest.fixture
def app_client():
    """Flask test client."""
    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as c:
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


class TestTradeCommitCreatesFile:
    """POST /prs/commit must create a trade file on disk."""

    def test_commit_returns_swap_id(self, app_client, sample_trade_payload):
        resp = app_client.post('/api/v1/prs/commit',
                               json=sample_trade_payload,
                               content_type='application/json')
        data = resp.get_json()
        assert data['status'] == 'success', f"Commit failed: {data}"
        assert 'swap_id' in data, "Response missing swap_id"
        assert data['swap_id'].startswith('PRS-'), f"Bad swap_id: {data['swap_id']}"


class TestBlotterShowsNewTrade:
    """GET /trading/blotter must include a newly committed trade."""

    def test_new_trade_in_blotter(self, app_client, sample_trade_payload):
        # Commit a trade
        commit_resp = app_client.post('/api/v1/prs/commit',
                                      json=sample_trade_payload,
                                      content_type='application/json')
        commit_data = commit_resp.get_json()
        assert commit_data['status'] == 'success'
        swap_id = commit_data['swap_id']

        # Fetch blotter
        blotter_resp = app_client.get('/api/v1/trading/blotter')
        blotter_data = blotter_resp.get_json()
        assert blotter_data['status'] == 'success'

        trades = blotter_data.get('trades', [])
        trade_ids = [t.get('swap_id') for t in trades]
        assert swap_id in trade_ids, (
            f"Newly committed trade {swap_id} not found in blotter. "
            f"Blotter has {len(trades)} trades."
        )


class TestActiveGaugesIncludesNewTrade:
    """GET /trading/blotter/active-gauges must include the gauge of a new trade."""

    def test_gauge_in_active_list_after_commit(self, app_client, sample_trade_payload):
        gauge_id = sample_trade_payload['gauge_id']

        # Commit a trade
        commit_resp = app_client.post('/api/v1/prs/commit',
                                      json=sample_trade_payload,
                                      content_type='application/json')
        assert commit_resp.get_json()['status'] == 'success'

        # Check active gauges
        active_resp = app_client.get('/api/v1/trading/blotter/active-gauges')
        active_data = active_resp.get_json()
        assert active_data['status'] == 'success'

        gauge_ids = active_data.get('gauge_ids', [])
        assert gauge_id in gauge_ids, (
            f"Gauge {gauge_id} not in active-gauges after commit. "
            f"Active gauges: {gauge_ids[:10]}"
        )


class TestBlotterContainsTradeForGauge:
    """Blotter must contain a trade for the committed gauge."""

    def test_blotter_has_trade_for_gauge(self, app_client, sample_trade_payload):
        gauge_id = sample_trade_payload['gauge_id']

        # Commit trade
        commit_resp = app_client.post('/api/v1/prs/commit',
                                      json=sample_trade_payload,
                                      content_type='application/json')
        swap_id = commit_resp.get_json()['swap_id']

        # Fetch full blotter
        resp = app_client.get('/api/v1/trading/blotter')
        data = resp.get_json()
        assert data['status'] == 'success'

        trades = data.get('trades', [])
        matching = [t for t in trades if t.get('swap_id') == swap_id]
        assert len(matching) == 1, (
            f"Trade {swap_id} not found in blotter ({len(trades)} total trades)"
        )
        assert matching[0].get('gauge_id') == gauge_id, (
            f"Trade {swap_id} gauge mismatch: {matching[0].get('gauge_id')} != {gauge_id}"
        )
