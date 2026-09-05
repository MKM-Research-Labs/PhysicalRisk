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

"""Tests for the trading desk market state manager."""

import pytest

import database
from db_helpers import seed_gauge_hazard_curves, active_test_backend, tmp_catchment
from models.trading.market_state import MarketStateManager


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend (catchment "thames"); the migrated MarketStateManager
    reads gauge hazard curves and reads/writes market state through ``database``."""
    with tmp_catchment(tmp_path, catchment="thames"):
        yield


@pytest.fixture
def sample_gaugehc():
    """Seed sample gauge hazard curves through the database seam (list form,
    which ``_load_base_curves`` handles) and return them for inspection."""
    gaugehc = [
        {
            'gauge_id': 'GAUGE-001',
            'gauge_name': 'Test Gauge 1',
            'annual_hazard_rate_alert': 0.04,
            'annual_hazard_rate_warning': 0.025,
            'annual_hazard_rate_severe': 0.01,
            'curve_points': [],
            'gev_location': 3.0,
            'gev_scale': 0.5,
            'gev_shape': 0.0,
        },
        {
            'gauge_id': 'GAUGE-002',
            'gauge_name': 'Test Gauge 2',
            'annual_hazard_rate_alert': 0.05,
            'annual_hazard_rate_warning': 0.03,
            'annual_hazard_rate_severe': 0.015,
            'curve_points': [],
        },
    ]
    seed_gauge_hazard_curves(database.active_catchment(), gaugehc)
    return gaugehc


@pytest.fixture
def market_mgr(sample_gaugehc):
    """Create a MarketStateManager bound to the tmp backend (gaugehc pre-seeded)."""
    return MarketStateManager()


class TestMarketStateLoad:
    """Tests for market state loading."""

    def test_initial_load_creates_state(self, market_mgr):
        """First load should initialise from base curves."""
        state = market_mgr.load()
        assert 'base_rates' in state
        assert 'gauge_adjustments' in state
        assert 'GAUGE-001' in state['base_rates']
        assert 'GAUGE-002' in state['base_rates']

    def test_base_rates_match_gaugehc(self, market_mgr):
        """Base rates should match what's in gaugehc.json."""
        state = market_mgr.load()
        g1 = state['base_rates']['GAUGE-001']
        assert g1['annual_hazard_rate_warning'] == 0.025
        assert g1['annual_hazard_rate_severe'] == 0.01

    def test_load_persists(self, market_mgr):
        """Subsequent loads should return the saved state."""
        state1 = market_mgr.load()
        state2 = market_mgr.load()
        assert state1['base_rates'] == state2['base_rates']


class TestMarketStateUpdate:
    """Tests for updating market state."""

    def test_update_gauge_rate(self, market_mgr):
        """Updating a rate should persist."""
        market_mgr.update_gauge_rate('GAUGE-001', 'warning', 0.035)
        state = market_mgr.load()
        adj = state['gauge_adjustments']['GAUGE-001']
        assert adj['annual_hazard_rate_warning'] == 0.035

    def test_get_effective_rate_with_adjustment(self, market_mgr):
        """Effective rate should use adjustment if present."""
        state = market_mgr.load()

        # Before adjustment
        rate = market_mgr.get_gauge_rate(state, 'GAUGE-001', 'warning')
        assert rate == 0.025

        # After adjustment
        state = market_mgr.update_gauge_rate('GAUGE-001', 'warning', 0.04)
        rate = market_mgr.get_gauge_rate(state, 'GAUGE-001', 'warning')
        assert rate == 0.04

    def test_unadjusted_gauge_returns_base(self, market_mgr):
        """Gauge without adjustment should return base rate."""
        market_mgr.update_gauge_rate('GAUGE-001', 'warning', 0.04)
        state = market_mgr.load()

        # GAUGE-002 not adjusted
        rate = market_mgr.get_gauge_rate(state, 'GAUGE-002', 'warning')
        assert rate == 0.03


class TestMarketStateReset:
    """Tests for resetting market state."""

    def test_reset_single_gauge(self, market_mgr):
        """Reset a single gauge's adjustments."""
        market_mgr.update_gauge_rate('GAUGE-001', 'warning', 0.04)
        market_mgr.update_gauge_rate('GAUGE-002', 'warning', 0.05)

        market_mgr.reset('GAUGE-001')
        state = market_mgr.load()

        assert 'GAUGE-001' not in state['gauge_adjustments']
        assert 'GAUGE-002' in state['gauge_adjustments']

    def test_reset_all(self, market_mgr):
        """Reset all adjustments."""
        market_mgr.update_gauge_rate('GAUGE-001', 'warning', 0.04)
        market_mgr.update_gauge_rate('GAUGE-002', 'warning', 0.05)

        market_mgr.reset()
        state = market_mgr.load()

        assert len(state['gauge_adjustments']) == 0


class TestEffectiveRates:
    """Tests for get_all_effective_rates."""

    def test_effective_rates_include_all_gauges(self, market_mgr):
        """All gauges from base should appear."""
        rates = market_mgr.get_all_effective_rates()
        assert 'GAUGE-001' in rates
        assert 'GAUGE-002' in rates

    def test_effective_rates_mark_adjusted(self, market_mgr):
        """Adjusted gauges should be flagged."""
        market_mgr.update_gauge_rate('GAUGE-001', 'warning', 0.04)
        rates = market_mgr.get_all_effective_rates()
        assert rates['GAUGE-001']['is_adjusted'] is True
        assert rates['GAUGE-002']['is_adjusted'] is False

    def test_effective_rates_merge_correctly(self, market_mgr):
        """Adjusted rates should override base, non-adjusted should use base."""
        market_mgr.update_gauge_rate('GAUGE-001', 'warning', 0.04)
        rates = market_mgr.get_all_effective_rates()

        assert rates['GAUGE-001']['annual_hazard_rate_warning'] == 0.04
        assert rates['GAUGE-001']['annual_hazard_rate_alert'] == 0.04  # base
        assert rates['GAUGE-002']['annual_hazard_rate_warning'] == 0.03  # base


class TestMissingCoverage:
    """Tests targeting previously uncovered branches."""

    def _make_mgr(self, tmp_path, gaugehc_data=None):
        """Helper to create a MarketStateManager with optionally-seeded gauge curves."""
        from models.trading.market_state import MarketStateManager
        if gaugehc_data is not None:
            if isinstance(gaugehc_data, list):
                # Canonicalise a bare list so it round-trips on the pg backend too.
                seed_gauge_hazard_curves(database.active_catchment(), gaugehc_data)
            else:
                # Pre-shaped dict ({hazard_curves}/{gauges}/unknown) — seed as-is to
                # exercise MarketStateManager's shape handling.
                database.save_gauge_hazard_curves(database.active_catchment(), gaugehc_data)
        return MarketStateManager()

    def test_load_base_curves_no_file(self, tmp_path):
        """When gaugehc.json is missing, base curves returns empty dict."""
        mgr = self._make_mgr(tmp_path)
        state = mgr.load()
        assert isinstance(state, dict)

    @pytest.mark.skipif(
        active_test_backend() == "pg",
        reason="seeds the raw {'gauges': [...]} file shape, a MarketStateManager "
               "tolerance; pg stores gauge hazard curves as shredded rows under the "
               "canonical 'hazard_curves' container, so the gauges-key shape can't "
               "round-trip — file-only.")
    def test_load_base_curves_gauges_key(self, tmp_path):
        """gaugehc.json with 'gauges' key is handled."""
        gaugehc = {
            'gauges': [
                {'gauge_id': 'GAUGE-A', 'annual_hazard_rate_alert': 0.05,
                 'annual_hazard_rate_warning': 0.03, 'annual_hazard_rate_severe': 0.01,
                 'gauge_name': 'A', 'curve_points': [], 'gev_location': 0,
                 'gev_scale': 0, 'gev_shape': 0}
            ]
        }
        mgr = self._make_mgr(tmp_path, gaugehc)
        state = mgr.load()
        assert 'GAUGE-A' in state.get('base_rates', {})

    def test_load_base_curves_hazard_curves_key(self, tmp_path):
        """The production format — {'hazard_curves': {gauge_id: curve}} — is handled."""
        gaugehc = {
            'metadata': {'distribution': 'gev'},
            'hazard_curves': {
                'GAUGE-HC': {
                    'gauge_id': 'GAUGE-HC', 'gauge_name': 'HC',
                    'annual_hazard_rate_alert': 0.05,
                    'annual_hazard_rate_warning': 0.03,
                    'annual_hazard_rate_severe': 0.01,
                    'curve_points': [], 'gev_location': 0,
                    'gev_scale': 0, 'gev_shape': 0,
                },
            },
        }
        mgr = self._make_mgr(tmp_path, gaugehc)
        state = mgr.load()
        assert 'GAUGE-HC' in state.get('base_rates', {})

    def test_load_base_curves_unknown_format(self, tmp_path):
        """gaugehc.json with unknown format returns empty base_rates."""
        mgr = self._make_mgr(tmp_path, {'other_key': []})
        state = mgr.load()
        assert state.get('base_rates', {}) == {}

    def test_load_base_curves_gauge_with_no_id_skipped(self, tmp_path):
        """Gauge entries with no gauge_id are skipped."""
        gaugehc = [
            {'gauge_id': '', 'annual_hazard_rate_alert': 0.05},  # no ID
            {'gauge_id': 'GAUGE-B', 'annual_hazard_rate_alert': 0.05,
             'gauge_name': 'B', 'curve_points': [], 'gev_location': 0,
             'gev_scale': 0, 'gev_shape': 0},
        ]
        mgr = self._make_mgr(tmp_path, gaugehc)
        state = mgr.load()
        base = state.get('base_rates', {})
        assert 'GAUGE-B' in base
        assert '' not in base

    def test_update_gauge_rate_with_notes(self, market_mgr):
        """Notes parameter is stored in gauge adjustments."""
        market_mgr.update_gauge_rate('GAUGE-001', 'alert', 0.05,
                                     notes='Manual override for stress test')
        state = market_mgr.load()
        adj = state['gauge_adjustments']['GAUGE-001']
        assert 'adjustment_notes' in adj
        assert 'override' in adj['adjustment_notes']

    def test_get_yield_rate_exact_tenor(self, market_mgr):
        """Exact tenor match from yield curve."""
        state = market_mgr.load()
        rate = market_mgr.get_yield_rate(state, 3)
        assert isinstance(rate, float)
        assert rate > 0

    def test_get_yield_rate_interpolated(self, market_mgr):
        """Non-integer tenor triggers interpolation."""
        state = market_mgr.load()
        # 1.5 is between 1Y and 2Y, not in the curve
        rate = market_mgr.get_yield_rate(state, 1.5)
        r1 = market_mgr.get_yield_rate(state, 1)
        r2 = market_mgr.get_yield_rate(state, 2)
        assert min(r1, r2) <= rate <= max(r1, r2)

    def test_get_yield_rate_below_min_tenor(self, market_mgr):
        """Tenor below minimum returns first key rate."""
        state = market_mgr.load()
        rate = market_mgr.get_yield_rate(state, 0)
        r1 = market_mgr.get_yield_rate(state, 1)
        assert rate == r1

    def test_get_yield_rate_above_max_tenor(self, market_mgr):
        """Tenor above maximum returns last key rate."""
        state = market_mgr.load()
        rate = market_mgr.get_yield_rate(state, 100)
        r6 = market_mgr.get_yield_rate(state, 6)
        assert rate == r6

    def test_commit_yield_curve(self, market_mgr):
        """commit_yield_curve saves all tenors at once."""
        rates = {'1': 0.04, '2': 0.045, '3': 0.05}
        state = market_mgr.commit_yield_curve(rates)
        assert state['yield_curve']['1'] == 0.04
        assert state['yield_curve']['3'] == 0.05

    def test_reset_yield_curve(self, market_mgr):
        """reset_yield_curve restores defaults."""
        market_mgr.update_yield_curve(1, 0.10)
        market_mgr.reset_yield_curve()
        state = market_mgr.load()
        from models.trading.market_state import MarketStateManager
        assert state['yield_curve']['1'] == MarketStateManager.DEFAULT_YIELD_CURVE['1']
