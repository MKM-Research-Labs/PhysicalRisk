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
Tests for models.prs.prshc — QuantLib CDS pricing.

Covers: flat hazard curve construction, survival curve from term structure,
full price_prs for all three triggers, notional scaling, flat vs term
structure, and survival probability monotonicity.
"""

import pytest

try:
    import QuantLib as ql
    HAS_QUANTLIB = True
except ImportError:
    HAS_QUANTLIB = False

pytestmark = pytest.mark.skipif(not HAS_QUANTLIB, reason="QuantLib not installed")

from models.prs.prshc import (
    create_flat_hazard_curve,
    create_survival_curve_from_hazard,
    price_prs,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _term_structure(annual_rate: float):
    """Build a simple geometric survival term structure."""
    return [
        {'year': y, 'survival_prob': (1 - annual_rate) ** y}
        for y in range(1, 6)
    ]


@pytest.fixture(scope="module")
def today():
    t = ql.Date.todaysDate()
    ql.Settings.instance().evaluationDate = t
    return t


@pytest.fixture(scope="module")
def gauge_data():
    return {
        'gauge_id': 'GAUGE-T001',
        'gauge_name': 'Test Thames Gauge',
        'annual_hazard_rate_alert':   0.15,
        'annual_hazard_rate_warning': 0.10,
        'annual_hazard_rate_severe':  0.05,
        'term_structure_alert':   _term_structure(0.15),
        'term_structure_warning': _term_structure(0.10),
        'term_structure_severe':  _term_structure(0.05),
        'flood_alert_m':           3.5,
        'flood_warning_m':         4.5,
        'severe_flood_warning_m':  5.5,
    }


# ===========================================================================
# create_flat_hazard_curve
# ===========================================================================

class TestFlatHazardCurve:

    def test_returns_curve_and_quote(self, today):
        curve, quote = create_flat_hazard_curve(today, 0.10)
        assert curve is not None
        assert quote is not None

    def test_survival_at_evaluation_date_is_one(self, today):
        curve, _ = create_flat_hazard_curve(today, 0.10)
        assert curve.survivalProbability(today) == pytest.approx(1.0, abs=0.001)

    def test_survival_decreases_over_time(self, today):
        curve, _ = create_flat_hazard_curve(today, 0.10)
        s1 = curve.survivalProbability(today + ql.Period(1, ql.Years))
        s5 = curve.survivalProbability(today + ql.Period(5, ql.Years))
        assert s1 > s5

    def test_higher_hazard_lower_survival(self, today):
        curve_low, _ = create_flat_hazard_curve(today, 0.05)
        curve_high, _ = create_flat_hazard_curve(today, 0.20)
        date = today + ql.Period(3, ql.Years)
        assert curve_high.survivalProbability(date) < curve_low.survivalProbability(date)

    def test_zero_hazard_survival_near_one(self, today):
        curve, _ = create_flat_hazard_curve(today, 0.001)
        date = today + ql.Period(1, ql.Years)
        assert curve.survivalProbability(date) > 0.99

    def test_default_day_counter(self, today):
        # Should not raise when day_counter omitted
        curve, _ = create_flat_hazard_curve(today, 0.10, day_counter=None)
        assert curve is not None


# ===========================================================================
# create_survival_curve_from_hazard
# ===========================================================================

class TestSurvivalCurveFromHazard:

    def test_builds_without_error(self, today):
        ts = _term_structure(0.10)
        curve = create_survival_curve_from_hazard(today, ts)
        assert curve is not None

    def test_survival_at_start_is_one(self, today):
        ts = _term_structure(0.10)
        curve = create_survival_curve_from_hazard(today, ts)
        assert curve.survivalProbability(today) == pytest.approx(1.0, abs=0.001)

    def test_survival_decreases_with_time(self, today):
        ts = _term_structure(0.10)
        curve = create_survival_curve_from_hazard(today, ts)
        s1 = curve.survivalProbability(today + ql.Period(1, ql.Years))
        s3 = curve.survivalProbability(today + ql.Period(3, ql.Years))
        assert s1 > s3

    def test_custom_day_counter(self, today):
        ts = _term_structure(0.08)
        curve = create_survival_curve_from_hazard(today, ts, ql.Actual360())
        assert curve is not None

    def test_high_survival_ts_gives_near_one(self, today):
        ts = [{'year': y, 'survival_prob': 0.999 ** y} for y in range(1, 6)]
        curve = create_survival_curve_from_hazard(today, ts)
        s1 = curve.survivalProbability(today + ql.Period(1, ql.Years))
        assert s1 > 0.90  # very low hazard rate

    def test_zero_survival_falls_back_to_default(self, today):
        # survival_prob exactly 0 triggers the fallback hazard rate
        ts = [{'year': y, 'survival_prob': 0.0} for y in range(1, 6)]
        # Should not raise
        curve = create_survival_curve_from_hazard(today, ts)
        assert curve is not None


# ===========================================================================
# price_prs — alert trigger
# ===========================================================================

class TestPricePRSAlert:

    def test_returns_required_keys(self, gauge_data):
        r = price_prs(gauge_data, trigger_level='alert')
        for key in ['gauge_id', 'gauge_name', 'trigger_level', 'trigger_threshold_m',
                    'annual_hazard_rate', 'npv', 'fair_spread', 'fair_spread_bps',
                    'fair_upfront', 'premium_leg_npv', 'protection_leg_npv',
                    'survival_probabilities', 'use_term_structure']:
            assert key in r, f"Missing key: {key}"

    def test_gauge_id_matches(self, gauge_data):
        r = price_prs(gauge_data, trigger_level='alert')
        assert r['gauge_id'] == 'GAUGE-T001'

    def test_trigger_threshold_matches(self, gauge_data):
        r = price_prs(gauge_data, trigger_level='alert')
        assert r['trigger_threshold_m'] == gauge_data['flood_alert_m']

    def test_fair_spread_positive(self, gauge_data):
        r = price_prs(gauge_data, trigger_level='alert')
        assert r['fair_spread_bps'] > 0

    def test_spread_bps_consistent(self, gauge_data):
        r = price_prs(gauge_data, trigger_level='alert')
        assert r['fair_spread_bps'] == pytest.approx(r['fair_spread'] * 10000, rel=1e-4)

    def test_survival_probs_present_for_all_years(self, gauge_data):
        r = price_prs(gauge_data, trigger_level='alert', tenor_years=5)
        assert len(r['survival_probabilities']) == 5

    def test_survival_probs_monotone(self, gauge_data):
        r = price_prs(gauge_data, trigger_level='alert')
        probs = list(r['survival_probabilities'].values())
        assert all(probs[i] >= probs[i + 1] for i in range(len(probs) - 1))


# ===========================================================================
# price_prs — warning and severe triggers
# ===========================================================================

class TestPricePRSTriggerOrdering:

    def test_alert_spread_greater_than_warning(self, gauge_data):
        r_alert = price_prs(gauge_data, trigger_level='alert')
        r_warn = price_prs(gauge_data, trigger_level='warning')
        assert r_alert['fair_spread_bps'] > r_warn['fair_spread_bps']

    def test_warning_spread_greater_than_severe(self, gauge_data):
        r_warn = price_prs(gauge_data, trigger_level='warning')
        r_severe = price_prs(gauge_data, trigger_level='severe')
        assert r_warn['fair_spread_bps'] > r_severe['fair_spread_bps']

    def test_severe_trigger_key_name(self, gauge_data):
        r = price_prs(gauge_data, trigger_level='severe')
        assert r['trigger_threshold_m'] == gauge_data['severe_flood_warning_m']

    def test_warning_trigger_key_name(self, gauge_data):
        r = price_prs(gauge_data, trigger_level='warning')
        assert r['trigger_threshold_m'] == gauge_data['flood_warning_m']


# ===========================================================================
# price_prs — flat hazard rate vs term structure
# ===========================================================================

class TestPricePRSHazardMode:

    def test_flat_mode_no_error(self, gauge_data):
        r = price_prs(gauge_data, trigger_level='warning', use_term_structure=False)
        assert r['fair_spread_bps'] > 0
        assert r['use_term_structure'] is False

    def test_term_structure_mode_flag(self, gauge_data):
        r = price_prs(gauge_data, trigger_level='warning', use_term_structure=True)
        assert r['use_term_structure'] is True

    def test_both_modes_give_positive_spread(self, gauge_data):
        r_ts = price_prs(gauge_data, trigger_level='warning', use_term_structure=True)
        r_flat = price_prs(gauge_data, trigger_level='warning', use_term_structure=False)
        assert r_ts['fair_spread_bps'] > 0
        assert r_flat['fair_spread_bps'] > 0


# ===========================================================================
# price_prs — parameter sensitivity
# ===========================================================================

class TestPricePRSSensitivity:

    def test_larger_notional_larger_premium_leg(self, gauge_data):
        r1 = price_prs(gauge_data, notional=10_000_000)
        r2 = price_prs(gauge_data, notional=20_000_000)
        assert abs(r2['premium_leg_npv']) > abs(r1['premium_leg_npv'])

    def test_running_spread_in_result(self, gauge_data):
        r = price_prs(gauge_data, running_spread=0.02)
        assert r['running_spread'] == pytest.approx(0.02)
        assert r['running_spread_bps'] == pytest.approx(200.0)

    def test_recovery_rate_in_result(self, gauge_data):
        r = price_prs(gauge_data, recovery_rate=0.0)
        assert r['recovery_rate'] == pytest.approx(0.0)

    def test_tenor_3yr_survival_probs_length(self, gauge_data):
        r = price_prs(gauge_data, trigger_level='warning', tenor_years=3)
        assert len(r['survival_probabilities']) == 3
