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

"""Tests for DeltaEngine class and hazard curve revaluation end-to-end."""

import copy
import json

import pytest

from models.trading.delta_engine.engine import DeltaEngine


def _make_gaugehc(input_dir):
    gaugehc = [{
        'gauge_id': 'GAUGE-TEST-001',
        'gauge_name': 'Test Gauge',
        'annual_hazard_rate_alert': 0.04,
        'annual_hazard_rate_warning': 0.025,
        'annual_hazard_rate_severe': 0.01,
    }]
    with open(input_dir / 'gaugehc.json', 'w') as f:
        json.dump(gaugehc, f)


def _base_trade(swap_id='PRS-TEST001', is_payer=True):
    return {
        'PhysicalSwap': {
            'Header': {'SwapID': swap_id, 'ValuationDate': '2026-01-01'},
            'LegData': {'Notional': 10_000_000, 'Payer': is_payer},
            'ScheduleData': {'EndDate': '2031-01-01'},
            'GaugeSet': {'GaugeBasket': [{'GaugeID': 'GAUGE-TEST-001'}]},
            'Pricing': {'SpreadBps': 250.0, 'TriggerLevel': 'warning', 'Recovery': 0.0},
        }
    }


class TestDeltaEngine:
    """Integration tests for the DeltaEngine class."""

    def test_enrich_trade(self, tmp_path):
        """Test trade enrichment with sample data."""
        from models.trading.market_state import MarketStateManager

        input_dir = tmp_path / 'input'
        input_dir.mkdir()
        trading_dir = tmp_path / 'trading'
        trading_dir.mkdir()
        _make_gaugehc(input_dir)

        market_mgr = MarketStateManager(trading_dir, input_dir)
        engine = DeltaEngine(market_mgr)

        enriched = engine.enrich_trade(_base_trade())

        assert enriched['swap_id'] == 'PRS-TEST001'
        assert enriched['gauge_id'] == 'GAUGE-TEST-001'
        assert enriched['notional'] == 10_000_000
        assert enriched['fair_spread_bps'] > 0
        assert enriched['gauge_fs01'] > 0
        assert enriched['risky_annuity'] > 0

    def test_enrich_receiver_trade_negative_dv01(self, tmp_path):
        """Receiver trade should have negative gauge DV01."""
        from models.trading.market_state import MarketStateManager

        input_dir = tmp_path / 'input'
        input_dir.mkdir()
        trading_dir = tmp_path / 'trading'
        trading_dir.mkdir()
        _make_gaugehc(input_dir)

        market_mgr = MarketStateManager(trading_dir, input_dir)
        engine = DeltaEngine(market_mgr)

        enriched = engine.enrich_trade(_base_trade('PRS-RCV001', is_payer=False))

        assert enriched['gauge_fs01'] < 0
        assert enriched['is_payer'] is False

    def test_payer_receiver_dv01_opposite(self, tmp_path):
        """Payer and receiver DV01 should be equal magnitude, opposite sign."""
        from models.trading.market_state import MarketStateManager

        input_dir = tmp_path / 'input'
        input_dir.mkdir()
        trading_dir = tmp_path / 'trading'
        trading_dir.mkdir()
        _make_gaugehc(input_dir)

        market_mgr = MarketStateManager(trading_dir, input_dir)
        engine = DeltaEngine(market_mgr)

        payer_enriched = engine.enrich_trade(_base_trade(is_payer=True))
        rcv_enriched = engine.enrich_trade(_base_trade(is_payer=False))

        assert abs(payer_enriched['gauge_fs01'] + rcv_enriched['gauge_fs01']) < 0.01

    def test_build_risk_grid(self):
        """Test risk grid construction."""
        engine = DeltaEngine.__new__(DeltaEngine)

        enriched = [
            {'gauge_id': 'G1', 'tenor': 3, 'gauge_fs01': 5000,
             'trade_status': 'Open', 'counterparty': 'C1'},
            {'gauge_id': 'G1', 'tenor': 0, 'gauge_fs01': 3000,
             'trade_status': 'Open', 'counterparty': 'C1'},
            {'gauge_id': 'G2', 'tenor': 5, 'gauge_fs01': -2000,
             'trade_status': 'Open', 'counterparty': 'C2'},
            {'gauge_id': 'G1', 'tenor': 7, 'gauge_fs01': 1000,
             'trade_status': 'Closed', 'counterparty': 'C1'},
        ]

        grid = engine.build_risk_grid(enriched)

        assert len(grid['buckets']) == 3
        assert len(grid['gauges']) == 2
        assert grid['grand_total'] == 6000

        g1 = next(g for g in grid['gauges'] if g['gauge_id'] == 'G1')
        assert g1['cells']['0Y'] == 3000
        assert g1['cells']['3Y'] == 5000


class TestHazardCurveRevaluation:
    """End-to-end: changing a hazard curve revalues PRS trades and produces non-zero P&L."""

    @pytest.fixture
    def trading_setup(self, tmp_path):
        """Set up market state, engines, and a sample trade."""
        from models.trading.market_state import MarketStateManager
        from models.trading.pnl_engine import PnLEngine

        input_dir = tmp_path / 'input'
        input_dir.mkdir()
        trading_dir = tmp_path / 'trading'
        trading_dir.mkdir()
        prs_dir = tmp_path / 'prs'
        prs_dir.mkdir()

        gaugehc = [{
            'gauge_id': 'GAUGE-WM-001',
            'gauge_name': 'Thames Westminster',
            'annual_hazard_rate_alert': 0.04,
            'annual_hazard_rate_warning': 0.025,
            'annual_hazard_rate_severe': 0.01,
        }]
        with open(input_dir / 'gaugehc.json', 'w') as f:
            json.dump(gaugehc, f)

        market_mgr = MarketStateManager(trading_dir, input_dir)
        delta_eng = DeltaEngine(market_mgr)
        pnl_eng = PnLEngine(trading_dir, prs_dir)

        trade = {
            'PhysicalSwap': {
                'Header': {'SwapID': 'PRS-REVAL-001', 'ValuationDate': '2026-02-01'},
                'LegData': {'Notional': 10_000_000, 'Payer': True},
                'ScheduleData': {'EndDate': '2031-02-01'},
                'GaugeSet': {
                    'GaugeBasket': [{'GaugeID': 'GAUGE-WM-001',
                                     'GaugeName': 'Thames Westminster'}],
                },
                'Pricing': {'SpreadBps': 250.0, 'TriggerLevel': 'warning', 'Recovery': 0.0},
            }
        }

        return {
            'market_mgr': market_mgr,
            'delta_eng': delta_eng,
            'pnl_eng': pnl_eng,
            'trade': trade,
            'trades': [trade],
        }

    def _bump_warning_curve(self, setup, bump=0.005):
        """Bump warning hazard curve by `bump` at all tenors."""
        state = setup['market_mgr'].load()
        ts = state.get('hazard_term_structure', {})
        gauge_ts = ts.get('GAUGE-WM-001', {}).get('warning', {})
        bumped = {t: gauge_ts.get(t, 0.025) + bump for t in ['1', '2', '3', '4', '5']}
        return setup['market_mgr'].commit_hazard_term_structure('GAUGE-WM-001', 'warning', bumped)

    def test_curve_change_moves_fair_spread(self, trading_setup):
        """Bumping hazard curve higher should increase fair PRS spread."""
        s = trading_setup
        state_before = s['market_mgr'].load()
        spread_before = s['delta_eng'].enrich_trade(s['trade'], state_before)['fair_spread_bps']

        state_after = self._bump_warning_curve(s)
        spread_after = s['delta_eng'].enrich_trade(s['trade'], state_after)['fair_spread_bps']

        assert spread_after > spread_before
        assert spread_after - spread_before > 1.0

    def test_curve_change_moves_mtm(self, trading_setup):
        """Bumping hazard curve should change trade MTM."""
        s = trading_setup
        state_before = s['market_mgr'].load()
        mtm_before = s['delta_eng'].enrich_trade(s['trade'], state_before)['mtm']

        state_after = self._bump_warning_curve(s)
        mtm_after = s['delta_eng'].enrich_trade(s['trade'], state_after)['mtm']

        assert mtm_after > mtm_before

    def test_curve_change_produces_daily_pnl(self, trading_setup):
        """Full cycle: enrich → EOD snap → bump curve → re-enrich → daily P&L non-zero."""
        s = trading_setup
        state_before = s['market_mgr'].load()

        enriched_before = s['delta_eng'].revalue_all(s['trades'], state_before)

        market_snapshot = {
            'risk_free_rate': state_before.get('risk_free_rate', 0.03),
            'gauge_adjustments': state_before.get('gauge_adjustments', {}),
        }
        eod_date = '2026-02-20'
        s['pnl_eng'].generate_eod_snapshot(enriched_before, market_snapshot, eod_date)

        eod_snap = s['pnl_eng'].get_eod_snapshot(eod_date)
        assert len(eod_snap['positions']) == 1
        prev_fair = eod_snap['positions'][0]['fair_spread_bps']

        state_after = self._bump_warning_curve(s)
        enriched_after = s['delta_eng'].revalue_all(s['trades'], state_after)
        new_fair = enriched_after[0]['fair_spread_bps']

        assert new_fair != prev_fair
        assert new_fair > prev_fair

        pnl_result = s['pnl_eng'].compute_daily_pnl(enriched_after, eod_snap)

        assert pnl_result['total_daily_pnl'] != 0
        assert pnl_result['daily_pnl_from_market'] != 0

        pos = pnl_result['positions'][0]
        assert pos['market_pnl'] > 0
        assert pos['daily_pnl'] > 0

    def test_curve_change_pnl_consistent_with_fs01(self, trading_setup):
        """P&L from a 1bp parallel shift should approximately equal FS01."""
        s = trading_setup
        state_before = s['market_mgr'].load()

        enriched = s['delta_eng'].enrich_trade(s['trade'], state_before)
        fs01 = enriched['gauge_fs01']
        mtm_before = enriched['mtm']

        state_after = self._bump_warning_curve(s, bump=0.0001)
        enriched_after = s['delta_eng'].enrich_trade(s['trade'], state_after)
        mtm_after = enriched_after['mtm']

        mtm_change = mtm_after - mtm_before
        # Allow 20% tolerance (FS01 is a local linear approximation)
        assert abs(mtm_change - fs01) < abs(fs01) * 0.20
