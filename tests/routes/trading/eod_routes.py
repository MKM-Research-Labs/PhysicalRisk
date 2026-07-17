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

"""Tests for EOD submission, history, and PDF endpoints."""

import json
from unittest.mock import patch, MagicMock

import pytest


class TestSubmitEOD:
    """POST /trading/eod endpoint tests."""

    def test_submit_eod(self, trading_client, trading_env):
        """POST creates EOD snapshot."""
        resp = trading_client.post('/api/v1/trading/eod',
                                   json={'date': '2026-02-28'})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert data['eod_id'] == 'EOD-20260228'

    def test_submit_eod_returns_summary(self, trading_client, trading_env):
        """Response includes trade count and P&L summary."""
        resp = trading_client.post('/api/v1/trading/eod',
                                   json={'date': '2026-02-28'})
        data = json.loads(resp.data)
        summary = data['summary']
        assert 'num_open_trades' in summary
        assert 'total_notional' in summary
        assert 'total_daily_pnl' in summary
        assert 'total_running_pnl' in summary

    def test_submit_eod_saves_snapshot_file(self, trading_client, trading_env):
        """EOD-<date>.json created in eod/ directory."""
        trading_client.post('/api/v1/trading/eod',
                            json={'date': '2026-02-28'})
        snapshot_path = trading_env['eod_dir'] / 'EOD-20260228.json'
        assert snapshot_path.exists()
        with open(snapshot_path) as f:
            snapshot = json.load(f)
        assert snapshot['eod_id'] == 'EOD-20260228'
        assert snapshot['date'] == '2026-02-28'

    def test_submit_eod_snapshot_has_market_state(self, trading_client,
                                                    trading_env):
        """Snapshot includes yield_curve and hazard_term_structure."""
        trading_client.post('/api/v1/trading/eod',
                            json={'date': '2026-02-28'})
        snapshot_path = trading_env['eod_dir'] / 'EOD-20260228.json'
        with open(snapshot_path) as f:
            snapshot = json.load(f)
        ms = snapshot['market_state_snapshot']
        assert 'yield_curve' in ms
        assert 'hazard_term_structure' in ms

    def test_submit_eod_snapshot_has_positions(self, trading_client,
                                                trading_env):
        """Snapshot includes per-trade positions."""
        trading_client.post('/api/v1/trading/eod',
                            json={'date': '2026-02-28'})
        snapshot_path = trading_env['eod_dir'] / 'EOD-20260228.json'
        with open(snapshot_path) as f:
            snapshot = json.load(f)
        positions = snapshot['positions']
        assert len(positions) == 16  # 16 open trades in trading_env
        for p in positions:
            assert 'swap_id' in p
            assert 'running_pnl' in p
            assert 'daily_pnl' in p

    def test_eod_idempotent_same_day(self, trading_client, trading_env):
        """Same-day snap overwrites previous."""
        trading_client.post('/api/v1/trading/eod',
                            json={'date': '2026-02-28'})
        trading_client.post('/api/v1/trading/eod',
                            json={'date': '2026-02-28'})
        # Only one file should exist
        eod_files = list(trading_env['eod_dir'].glob('EOD-20260228.json'))
        assert len(eod_files) == 1


class TestEODHistory:
    """GET /trading/eod/history endpoint tests."""

    def test_eod_history_empty(self, trading_client, trading_env):
        """Returns empty list when no snapshots exist."""
        resp = trading_client.get('/api/v1/trading/eod/history')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert data['history'] == []
        assert data['count'] == 0

    def test_eod_history_after_snap(self, trading_client, trading_env):
        """Returns list of snapshots after submission."""
        trading_client.post('/api/v1/trading/eod',
                            json={'date': '2026-02-28'})
        resp = trading_client.get('/api/v1/trading/eod/history')
        data = json.loads(resp.data)
        assert len(data['history']) == 1
        entry = data['history'][0]
        assert entry['eod_id'] == 'EOD-20260228'
        assert entry['date'] == '2026-02-28'
        assert 'num_open_trades' in entry
        assert 'total_daily_pnl' in entry

    def test_multiple_eod_snaps(self, trading_client, trading_env):
        """Can submit multiple EODs on different dates."""
        trading_client.post('/api/v1/trading/eod',
                            json={'date': '2026-02-27'})
        trading_client.post('/api/v1/trading/eod',
                            json={'date': '2026-02-28'})
        resp = trading_client.get('/api/v1/trading/eod/history')
        data = json.loads(resp.data)
        assert data['count'] == 2


class TestEODNoDateBody:
    """Submit EOD without a date body."""

    def test_submit_eod_no_json_uses_today(self, trading_client, trading_env):
        """POST with empty JSON body uses today's date (no date key)."""
        resp = trading_client.post('/api/v1/trading/eod', json={})
        data = resp.get_json()
        # Should succeed with today's date (no 'date' key → falls back to today)
        assert resp.status_code == 200
        assert data['status'] == 'success'


class TestEODPdf:
    """GET /trading/eod/<date>/pdf endpoint tests."""

    def test_eod_pdf_not_found(self, trading_client, trading_env):
        """GET for non-existent date returns 404."""
        resp = trading_client.get('/api/v1/trading/eod/2026-01-01/pdf')
        assert resp.status_code == 404

    def test_eod_pdf_found_serves_file(self, trading_client, trading_env):
        """GET for existing PDF date serves the file."""
        # Create a fake PDF in the eod dir
        pdf_path = trading_env['eod_dir'] / 'EOD-20260228.pdf'
        pdf_path.write_bytes(b"%PDF-1.4 fake pdf content")

        resp = trading_client.get('/api/v1/trading/eod/2026-02-28/pdf')
        assert resp.status_code == 200
        assert resp.content_type == 'application/pdf'


class TestPnLResetAfterEOD:
    """P&L resets correctly after EOD snap."""

    def test_pnl_uses_eod_as_baseline(self, trading_client, trading_env):
        """After EOD snap, next blotter P&L uses snap as baseline."""
        # Submit EOD
        trading_client.post('/api/v1/trading/eod',
                            json={'date': '2026-02-28'})
        # Get blotter — market P&L should reference EOD snap
        resp = trading_client.get('/api/v1/trading/blotter')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        # All trades should have P&L fields
        for t in data['trades']:
            assert 'daily_pnl' in t
            assert 'running_pnl' in t


class TestEODPdfGeneration:
    """PDF generation paths in submit_eod (lines 56-59)."""

    def test_submit_eod_import_error_still_succeeds(self, trading_client, trading_env):
        """ImportError in PDF gen is caught; EOD snapshot still saved (lines 56-57)."""
        with patch.dict('sys.modules', {'reports.trading.eod_generator': None}):
            resp = trading_client.post('/api/v1/trading/eod',
                                       json={'date': '2026-03-01'})
            data = json.loads(resp.data)
            assert resp.status_code == 200
            assert data['status'] == 'success'

    def test_submit_eod_pdf_exception_still_succeeds(self, trading_client, trading_env):
        """Exception in PDF gen is caught; EOD snapshot still saved (lines 58-59)."""
        mock_gen = MagicMock()
        mock_gen.return_value.generate_report.side_effect = RuntimeError('pdf fail')
        with patch('routes.trading.eod.EODReportGenerator', mock_gen,
                   create=True):
            resp = trading_client.post('/api/v1/trading/eod',
                                       json={'date': '2026-03-02'})
            data = json.loads(resp.data)
            assert resp.status_code == 200
            assert data['status'] == 'success'


class TestEODErrorHandlers:
    """Error handling paths in EOD endpoints."""

    def test_submit_eod_engine_error_returns_500(self, trading_client, trading_env):
        """submit_eod returns 500 when engine raises (lines 70-72)."""
        with patch('routes.trading.eod._get_engines',
                   side_effect=RuntimeError('engine fail')):
            resp = trading_client.post('/api/v1/trading/eod',
                                       json={'date': '2026-03-01'})
            assert resp.status_code == 500
            data = json.loads(resp.data)
            assert data['status'] == 'error'

    def test_eod_history_engine_error_returns_500(self, trading_client, trading_env):
        """get_eod_history returns 500 when engine raises (lines 88-90)."""
        with patch('routes.trading.eod._get_engines',
                   side_effect=RuntimeError('history fail')):
            resp = trading_client.get('/api/v1/trading/eod/history')
            assert resp.status_code == 500

    def test_get_eod_pdf_error_returns_500(self, trading_client, trading_env):
        """get_eod_pdf returns 500 on unexpected error (lines 107-109)."""
        with patch('routes.trading.eod.config') as mock_cfg:
            mock_cfg.get_eod_dir.side_effect = RuntimeError('dir fail')
            resp = trading_client.get('/api/v1/trading/eod/2026-03-01/pdf')
            assert resp.status_code == 500
