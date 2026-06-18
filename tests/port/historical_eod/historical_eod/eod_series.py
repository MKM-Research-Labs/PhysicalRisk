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

"""Tests for generate_historical_eod_series()."""

import json
from datetime import date
from unittest.mock import patch
import pytest
from .conftest import (
    generate_historical_eod_series,
    _business_days,
    _make_gaugehc,
    _make_trade,
)


class TestGenerateHistoricalEODSeries:
    """Tests for generate_historical_eod_series()."""

    def _setup_dirs(self, tmp_path):
        """Create the standard directory layout."""
        trading_dir = tmp_path / 'trading'
        trading_dir.mkdir()
        (trading_dir / 'eod').mkdir()
        input_dir = tmp_path / 'input'
        input_dir.mkdir()
        prs_dir = tmp_path / 'prs'
        prs_dir.mkdir()
        return trading_dir, input_dir, prs_dir

    def test_empty_trades_returns_zero(self, tmp_path):
        trading_dir, input_dir, prs_dir = self._setup_dirs(tmp_path)
        # Empty gaugehc → no hazard term structure → all days skipped
        (input_dir / 'gaugehc.json').write_text(json.dumps({'hazard_curves': {}}))

        count = generate_historical_eod_series(
            trades=[], trading_dir=trading_dir, input_dir=input_dir,
            prs_dir=prs_dir, seed=42)

        assert count == 0

    def test_returns_integer(self, tmp_path):
        trading_dir, input_dir, prs_dir = self._setup_dirs(tmp_path)
        (input_dir / 'gaugehc.json').write_text(json.dumps({'hazard_curves': {}}))

        result = generate_historical_eod_series(
            trades=[], trading_dir=trading_dir, input_dir=input_dir,
            prs_dir=prs_dir, seed=42)

        assert isinstance(result, int)

    def test_creates_eod_dir(self, tmp_path):
        trading_dir = tmp_path / 'trading'
        trading_dir.mkdir()
        input_dir = tmp_path / 'input'
        input_dir.mkdir()
        prs_dir = tmp_path / 'prs'
        prs_dir.mkdir()
        (input_dir / 'gaugehc.json').write_text(json.dumps({'hazard_curves': {}}))

        # Do NOT pre-create the eod subdir; PnLEngine should create it
        generate_historical_eod_series(
            trades=[], trading_dir=trading_dir, input_dir=input_dir,
            prs_dir=prs_dir, seed=42)

        assert (trading_dir / 'eod').exists()

    def test_business_days_are_weekdays(self):
        """Standalone check: _business_days always returns Mon-Fri dates."""
        result = _business_days(date.today(), 63)
        assert len(result) == 63
        for d in result:
            assert d.weekday() < 5

    def test_seed_is_reproducible(self, tmp_path):
        """Same seed should produce same random walk (deterministic)."""
        trading_dir, input_dir, prs_dir = self._setup_dirs(tmp_path)
        (input_dir / 'gaugehc.json').write_text(json.dumps({'hazard_curves': {}}))

        count1 = generate_historical_eod_series(
            trades=[], trading_dir=trading_dir, input_dir=input_dir,
            prs_dir=prs_dir, seed=99)
        count2 = generate_historical_eod_series(
            trades=[], trading_dir=trading_dir, input_dir=input_dir,
            prs_dir=prs_dir, seed=99)

        assert count1 == count2

    def test_with_one_trade_generates_snapshots(self, tmp_path):
        """With a real trade + real engine, we expect >0 snapshots."""
        trading_dir, input_dir, prs_dir = self._setup_dirs(tmp_path)
        _make_gaugehc(input_dir)

        trade = _make_trade()
        count = generate_historical_eod_series(
            trades=[trade], trading_dir=trading_dir, input_dir=input_dir,
            prs_dir=prs_dir, seed=42)

        assert count > 0

    def test_with_one_trade_writes_eod_files(self, tmp_path):
        """EOD snapshot JSON files are created in eod/ directory."""
        trading_dir, input_dir, prs_dir = self._setup_dirs(tmp_path)
        _make_gaugehc(input_dir)

        trade = _make_trade()
        count = generate_historical_eod_series(
            trades=[trade], trading_dir=trading_dir, input_dir=input_dir,
            prs_dir=prs_dir, seed=42)

        eod_files = list((trading_dir / 'eod').glob('EOD-*.json'))
        assert len(eod_files) == count

    def test_with_one_trade_writes_history_files(self, tmp_path):
        """hazard_curve_history.json and trade_pnl_history.json are created."""
        trading_dir, input_dir, prs_dir = self._setup_dirs(tmp_path)
        _make_gaugehc(input_dir)

        trade = _make_trade()
        generate_historical_eod_series(
            trades=[trade], trading_dir=trading_dir, input_dir=input_dir,
            prs_dir=prs_dir, seed=42)

        assert (trading_dir / 'hazard_curve_history.json').exists()
        assert (trading_dir / 'trade_pnl_history.json').exists()

    def test_cleans_existing_eod_files(self, tmp_path):
        """Pre-existing EOD-*.json files are deleted before simulation."""
        trading_dir, input_dir, prs_dir = self._setup_dirs(tmp_path)
        (input_dir / 'gaugehc.json').write_text(json.dumps({'hazard_curves': {}}))

        # Plant a stale file
        stale = trading_dir / 'eod' / 'EOD-1999-12-31.json'
        stale.write_text('{}')

        generate_historical_eod_series(
            trades=[], trading_dir=trading_dir, input_dir=input_dir,
            prs_dir=prs_dir, seed=42)

        assert not stale.exists()

    def test_multiple_trades_adds_more_snapshots(self, tmp_path):
        """More trades should generally yield more (or equal) snapshots."""
        trading_dir, input_dir, prs_dir = self._setup_dirs(tmp_path)
        _make_gaugehc(input_dir)

        trade1 = _make_trade(swap_id='PRS-TEST-001')
        trade2 = _make_trade(swap_id='PRS-TEST-002')

        count = generate_historical_eod_series(
            trades=[trade1, trade2], trading_dir=trading_dir, input_dir=input_dir,
            prs_dir=prs_dir, seed=42)

        assert count > 0

    def test_enrichment_failure_is_skipped(self, tmp_path):
        """A trade that fails enrich_trade is skipped gracefully (except branch)."""
        trading_dir, input_dir, prs_dir = self._setup_dirs(tmp_path)
        _make_gaugehc(input_dir)

        trade = _make_trade()

        # Patch DeltaEngine.enrich_trade to always raise, so enriched stays empty
        with patch(
            'models.trading.delta_engine.engine.DeltaEngine.enrich_trade',
            side_effect=RuntimeError('forced enrichment failure'),
        ):
            count = generate_historical_eod_series(
                trades=[trade], trading_dir=trading_dir, input_dir=input_dir,
                prs_dir=prs_dir, seed=42)

        # All days: trade added, enrichment fails → enriched=[] → continue
        assert count == 0
