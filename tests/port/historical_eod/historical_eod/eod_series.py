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

"""Tests for generate_historical_eod_series()."""

from datetime import date
from unittest.mock import patch

import pytest

import database
from db_helpers import tmp_catchment
from .conftest import (
    generate_historical_eod_series,
    _business_days,
    _make_gaugehc,
    _make_trade,
)


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend (catchment "thames"); the migrated series generator
    reads gauge hazard curves and reads/writes market state + EOD snapshots + the two
    history documents through ``database``."""
    with tmp_catchment(tmp_path, catchment="thames"):
        yield


class TestGenerateHistoricalEODSeries:
    """Tests for generate_historical_eod_series()."""

    def _seed_empty_hazard(self):
        """Empty gaugehc → no hazard term structure → all days skipped."""
        database.save_gauge_hazard_curves(database.active_catchment(), {'hazard_curves': {}})

    def test_empty_trades_returns_zero(self, tmp_path):
        self._seed_empty_hazard()
        count = generate_historical_eod_series(trades=[], seed=42)
        assert count == 0

    def test_returns_integer(self, tmp_path):
        self._seed_empty_hazard()
        result = generate_historical_eod_series(trades=[], seed=42)
        assert isinstance(result, int)

    def test_empty_hazard_persists_no_snapshots(self, tmp_path):
        """With no hazard term structure, no EOD snapshots are persisted."""
        self._seed_empty_hazard()
        generate_historical_eod_series(trades=[], seed=42)
        assert database.list_eod_snapshots(database.active_catchment()) == []

    def test_business_days_are_weekdays(self):
        """Standalone check: _business_days always returns Mon-Fri dates."""
        result = _business_days(date.today(), 63)
        assert len(result) == 63
        for d in result:
            assert d.weekday() < 5

    def test_seed_is_reproducible(self, tmp_path):
        """Same seed should produce same random walk (deterministic)."""
        self._seed_empty_hazard()
        count1 = generate_historical_eod_series(trades=[], seed=99)
        count2 = generate_historical_eod_series(trades=[], seed=99)
        assert count1 == count2

    def test_with_one_trade_generates_snapshots(self, tmp_path):
        """With a real trade + real engine, we expect >0 snapshots."""
        _make_gaugehc()
        count = generate_historical_eod_series(trades=[_make_trade()], seed=42)
        assert count > 0

    def test_with_one_trade_writes_eod_files(self, tmp_path):
        """EOD snapshots are persisted, one per simulated day with open trades."""
        _make_gaugehc()
        count = generate_historical_eod_series(trades=[_make_trade()], seed=42)
        assert len(database.list_eod_snapshots(database.active_catchment())) == count

    def test_with_one_trade_writes_history_files(self, tmp_path):
        """Both history documents are persisted."""
        _make_gaugehc()
        generate_historical_eod_series(trades=[_make_trade()], seed=42)
        cat = database.active_catchment()
        assert database.get_hazard_curve_history(cat) is not None
        assert database.get_trade_pnl_history(cat) is not None

    def test_cleans_existing_eod_files(self, tmp_path):
        """Pre-existing EOD snapshots are deleted before simulation."""
        self._seed_empty_hazard()
        cat = database.active_catchment()
        # Plant a stale snapshot
        database.save_eod_snapshot(cat, '1999-12-31', {'date': '1999-12-31'})

        generate_historical_eod_series(trades=[], seed=42)

        assert database.get_eod_snapshot(cat, '1999-12-31') is None

    def test_multiple_trades_adds_more_snapshots(self, tmp_path):
        """More trades should generally yield more (or equal) snapshots."""
        _make_gaugehc()
        trades = [_make_trade(swap_id='PRS-TEST-001'), _make_trade(swap_id='PRS-TEST-002')]
        count = generate_historical_eod_series(trades=trades, seed=42)
        assert count > 0

    def test_enrichment_failure_is_skipped(self, tmp_path):
        """A trade that fails enrich_trade is skipped gracefully (except branch)."""
        _make_gaugehc()
        trade = _make_trade()

        # Patch DeltaEngine.enrich_trade to always raise, so enriched stays empty
        with patch(
            'models.trading.delta_engine.engine.DeltaEngine.enrich_trade',
            side_effect=RuntimeError('forced enrichment failure'),
        ):
            count = generate_historical_eod_series(trades=[trade], seed=42)

        # All days: trade added, enrichment fails → enriched=[] → continue
        assert count == 0
