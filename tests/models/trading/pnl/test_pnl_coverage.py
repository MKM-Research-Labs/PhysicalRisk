# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage expansion tests for pnl_engine.py — lines 93-94, 267, 350."""

import json
from datetime import date

import pytest

from models.trading.pnl_engine import PnLEngine


@pytest.fixture
def pnl_eng(tmp_path):
    """Create a PnLEngine for testing."""
    trading_dir = tmp_path / 'trading'
    trading_dir.mkdir()
    prs_dir = tmp_path / 'prs'
    prs_dir.mkdir()
    return PnLEngine(trading_dir, prs_dir)


class TestGetTradeMark:
    """Lines 93-94: get_trade_mark returns specific trade mark data."""

    def test_get_existing_trade_mark(self, pnl_eng):
        """get_trade_mark returns mark data for an existing trade."""
        pnl_eng.update_trade_mark('PRS-001', {'fair_spread_bps': 250.0})
        mark = pnl_eng.get_trade_mark('PRS-001')
        assert mark['fair_spread_bps'] == 250.0

    def test_get_nonexistent_trade_mark(self, pnl_eng):
        """get_trade_mark returns empty dict for unknown trade."""
        mark = pnl_eng.get_trade_mark('PRS-NONEXISTENT')
        assert mark == {}

    def test_get_trade_mark_after_multiple_updates(self, pnl_eng):
        """get_trade_mark returns merged data after multiple updates."""
        pnl_eng.update_trade_mark('PRS-002', {'fair_spread_bps': 200.0})
        pnl_eng.update_trade_mark('PRS-002', {'mtm': 5000.0})
        mark = pnl_eng.get_trade_mark('PRS-002')
        assert mark['fair_spread_bps'] == 200.0
        assert mark['mtm'] == 5000.0


class TestGenerateEodSnapshotDefaultDate:
    """Line 267: generate_eod_snapshot with eod_date=None uses today."""

    def test_eod_snapshot_default_date(self, pnl_eng):
        """When eod_date is None, uses today's date."""
        trades = [{
            'swap_id': 'PRS-001',
            'gauge_id': 'GAUGE-A',
            'property_id': None,
            'counterparty': 'Bank A',
            'trigger': 'warning',
            'notional': 10_000_000,
            'tenor': 5,
            'trade_spread_bps': 250.0,
            'fair_spread_bps': 260.0,
            'is_payer': True,
            'trade_date': '2026-01-15',
            'trade_status': 'Open',
            'gauge_fs01': 4500,
            'basis_dv01': 0,
            'risky_annuity': 4.35,
        }]
        market_state = {'risk_free_rate': 0.03, 'gauge_adjustments': {}}

        # Pass eod_date=None to trigger line 267
        snapshot = pnl_eng.generate_eod_snapshot(trades, market_state, eod_date=None)
        assert snapshot['date'] == date.today().isoformat()
        expected_id = f"EOD-{date.today().isoformat().replace('-', '')}"
        assert snapshot['eod_id'] == expected_id


class TestGetEodSnapshotNotFound:
    """Line 350: get_eod_snapshot returns None for non-existent date."""

    def test_nonexistent_snapshot_returns_none(self, pnl_eng):
        """get_eod_snapshot returns None when no snapshot exists for the date."""
        result = pnl_eng.get_eod_snapshot('2099-12-31')
        assert result is None

    def test_existing_snapshot_returns_data(self, pnl_eng):
        """get_eod_snapshot returns snapshot data for existing date."""
        trades = [{
            'swap_id': 'PRS-001',
            'gauge_id': 'GAUGE-A',
            'property_id': None,
            'counterparty': 'Bank A',
            'trigger': 'warning',
            'notional': 10_000_000,
            'tenor': 5,
            'trade_spread_bps': 250.0,
            'fair_spread_bps': 260.0,
            'is_payer': True,
            'trade_date': '2026-01-15',
            'trade_status': 'Open',
            'gauge_fs01': 4500,
            'basis_dv01': 0,
            'risky_annuity': 4.35,
        }]
        market_state = {'risk_free_rate': 0.03, 'gauge_adjustments': {}}
        pnl_eng.generate_eod_snapshot(trades, market_state, '2026-03-15')

        result = pnl_eng.get_eod_snapshot('2026-03-15')
        assert result is not None
        assert result['date'] == '2026-03-15'
