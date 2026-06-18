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

"""Tests for generate_trade_pnl_history_file()."""

import json
import pytest
from .conftest import generate_trade_pnl_history_file, _write_eod_with_positions


class TestGenerateTradePnlHistory:
    """Tests for generate_trade_pnl_history_file()."""

    def test_creates_output_file(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()
        _write_eod_with_positions(eod_dir, 'EOD-2026-01-01', '2026-01-01')
        output = tmp_path / 'trade_pnl_history.json'

        generate_trade_pnl_history_file(eod_dir, output)

        assert output.exists()

    def test_output_has_metadata(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()
        _write_eod_with_positions(eod_dir, 'EOD-2026-01-01', '2026-01-01')
        output = tmp_path / 'trade_pnl_history.json'

        generate_trade_pnl_history_file(eod_dir, output)

        data = json.loads(output.read_text())
        assert 'metadata' in data
        assert 'num_trades' in data['metadata']

    def test_output_has_trades(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()
        _write_eod_with_positions(eod_dir, 'EOD-2026-01-01', '2026-01-01')
        output = tmp_path / 'trade_pnl_history.json'

        generate_trade_pnl_history_file(eod_dir, output)

        data = json.loads(output.read_text())
        assert 'trades' in data
        assert 'PRS-001' in data['trades']

    def test_trade_has_history(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()
        _write_eod_with_positions(eod_dir, 'EOD-2026-01-01', '2026-01-01')
        output = tmp_path / 'trade_pnl_history.json'

        generate_trade_pnl_history_file(eod_dir, output)

        data = json.loads(output.read_text())
        trade = data['trades']['PRS-001']
        assert 'history' in trade
        assert len(trade['history']) == 1

    def test_no_eod_files_returns_early(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()
        output = tmp_path / 'trade_pnl_history.json'

        generate_trade_pnl_history_file(eod_dir, output)

        assert not output.exists()

    def test_position_without_swap_id_skipped(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()

        snapshot = {
            'eod_id': 'EOD-2026-01-01',
            'date': '2026-01-01',
            'market_state_snapshot': {'hazard_term_structure': {}},
            'positions': [
                {
                    'swap_id': '',   # blank — should be skipped
                    'trade_date': '2026-01-01',
                    'trade_spread_bps': 200.0,
                    'gauge_id': 'GAUGE-001',
                    'trigger': 'severe',
                    'notional': 10_000_000,
                    'is_payer': True,
                    'fair_spread_bps': 205.0,
                    'market_pnl': 0.0,
                    'running_pnl': 0.0,
                }
            ],
            'portfolio_summary': {},
        }
        (eod_dir / 'EOD-2026-01-01.json').write_text(json.dumps(snapshot))
        output = tmp_path / 'trade_pnl_history.json'

        generate_trade_pnl_history_file(eod_dir, output)

        data = json.loads(output.read_text())
        assert data['trades'] == {}
        assert data['metadata']['num_trades'] == 0

    def test_multiple_eods_accumulate(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()
        _write_eod_with_positions(eod_dir, 'EOD-2026-01-01', '2026-01-01')
        _write_eod_with_positions(eod_dir, 'EOD-2026-01-02', '2026-01-02')
        _write_eod_with_positions(eod_dir, 'EOD-2026-01-03', '2026-01-03')
        output = tmp_path / 'trade_pnl_history.json'

        generate_trade_pnl_history_file(eod_dir, output)

        data = json.loads(output.read_text())
        trade = data['trades']['PRS-001']
        assert len(trade['history']) == 3

    def test_history_entry_has_required_keys(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()
        _write_eod_with_positions(eod_dir, 'EOD-2026-01-01', '2026-01-01')
        output = tmp_path / 'trade_pnl_history.json'

        generate_trade_pnl_history_file(eod_dir, output)

        data = json.loads(output.read_text())
        entry = data['trades']['PRS-001']['history'][0]
        assert 'date' in entry
        assert 'mark' in entry
        assert 'mkt_pnl' in entry
        assert 'running_pnl' in entry

    def test_trade_metadata_preserved(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()
        _write_eod_with_positions(eod_dir, 'EOD-2026-01-01', '2026-01-01', swap_id='PRS-999')
        output = tmp_path / 'trade_pnl_history.json'

        generate_trade_pnl_history_file(eod_dir, output)

        data = json.loads(output.read_text())
        trade = data['trades']['PRS-999']
        assert trade['gauge_id'] == 'GAUGE-001'
        assert trade['trigger'] == 'severe'
        assert trade['notional'] == 10_000_000
        assert trade['is_payer'] is True
        assert trade['trade_spread_bps'] == 200.0

    def test_multiple_trades_in_same_eod(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()

        snapshot = {
            'eod_id': 'EOD-2026-01-01',
            'date': '2026-01-01',
            'market_state_snapshot': {'hazard_term_structure': {}},
            'positions': [
                {
                    'swap_id': 'PRS-A',
                    'trade_date': '2026-01-01',
                    'trade_spread_bps': 180.0,
                    'gauge_id': 'GAUGE-001',
                    'trigger': 'severe',
                    'notional': 5_000_000,
                    'is_payer': True,
                    'fair_spread_bps': 182.0,
                    'market_pnl': 500.0,
                    'running_pnl': 500.0,
                },
                {
                    'swap_id': 'PRS-B',
                    'trade_date': '2026-01-01',
                    'trade_spread_bps': 210.0,
                    'gauge_id': 'GAUGE-002',
                    'trigger': 'warning',
                    'notional': 8_000_000,
                    'is_payer': False,
                    'fair_spread_bps': 208.0,
                    'market_pnl': -300.0,
                    'running_pnl': -300.0,
                },
            ],
            'portfolio_summary': {},
        }
        (eod_dir / 'EOD-2026-01-01.json').write_text(json.dumps(snapshot))
        output = tmp_path / 'trade_pnl_history.json'

        generate_trade_pnl_history_file(eod_dir, output)

        data = json.loads(output.read_text())
        assert 'PRS-A' in data['trades']
        assert 'PRS-B' in data['trades']
        assert data['metadata']['num_trades'] == 2

    def test_num_snapshots_in_metadata(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()
        _write_eod_with_positions(eod_dir, 'EOD-2026-01-01', '2026-01-01')
        _write_eod_with_positions(eod_dir, 'EOD-2026-01-02', '2026-01-02')
        output = tmp_path / 'trade_pnl_history.json'

        generate_trade_pnl_history_file(eod_dir, output)

        data = json.loads(output.read_text())
        assert data['metadata']['num_snapshots'] == 2
