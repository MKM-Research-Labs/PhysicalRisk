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
Tests for models.hazard.pricing — QuantLib credit curve pricing.

Covers: hazard_points_to_credit_curve (basic, default day_count),
create_cds_pricing_engines, create_hazard_rate_curve_approach.
"""

import pytest

try:
    import QuantLib as ql
    HAS_QUANTLIB = True
except ImportError:
    HAS_QUANTLIB = False

pytestmark = pytest.mark.skipif(not HAS_QUANTLIB, reason="QuantLib not installed")


def _setup_date():
    """Set QuantLib evaluation date to a fixed date."""
    evaluation_date = ql.Date(1, 1, 2026)
    ql.Settings.instance().evaluationDate = evaluation_date
    return evaluation_date


def _make_risk_free_curve(evaluation_date):
    """Create a flat risk-free yield curve at 3%."""
    dates = [evaluation_date, evaluation_date + ql.Period(10, ql.Years)]
    rates = [0.03, 0.03]
    return ql.ZeroCurve(dates, rates, ql.Actual365Fixed(), ql.TARGET())


# ===========================================================================
# hazard_points_to_credit_curve
# ===========================================================================

class TestHazardPointsToCreditCurve:

    def test_returns_credit_curve(self):
        from models.hazard.pricing import hazard_points_to_credit_curve
        date = _setup_date()
        curve = hazard_points_to_credit_curve(
            hazard_points=[0.05, 0.05, 0.05, 0.05, 0.05],
            years=[1, 2, 3, 4, 5],
            evaluation_date=date,
        )
        assert curve is not None

    def test_survival_prob_decreases(self):
        from models.hazard.pricing import hazard_points_to_credit_curve
        date = _setup_date()
        curve = hazard_points_to_credit_curve(
            hazard_points=[0.1, 0.1, 0.1, 0.1, 0.1],
            years=[1, 2, 3, 4, 5],
            evaluation_date=date,
        )
        # Survival probability at year 2 < year 1
        sp1 = curve.survivalProbability(date + ql.Period(1, ql.Years))
        sp2 = curve.survivalProbability(date + ql.Period(2, ql.Years))
        assert sp2 < sp1

    def test_custom_day_count(self):
        from models.hazard.pricing import hazard_points_to_credit_curve
        date = _setup_date()
        curve = hazard_points_to_credit_curve(
            hazard_points=[0.02, 0.02, 0.02, 0.02, 0.02],
            years=[1, 2, 3, 4, 5],
            evaluation_date=date,
            day_count=ql.Actual360(),
        )
        assert curve is not None

    def test_zero_hazard_gives_survival_near_one(self):
        from models.hazard.pricing import hazard_points_to_credit_curve
        date = _setup_date()
        curve = hazard_points_to_credit_curve(
            hazard_points=[0.0, 0.0, 0.0, 0.0, 0.0],
            years=[1, 2, 3, 4, 5],
            evaluation_date=date,
        )
        sp = curve.survivalProbability(date + ql.Period(1, ql.Years))
        assert sp >= 0.999

    def test_high_hazard_gives_low_survival(self):
        from models.hazard.pricing import hazard_points_to_credit_curve
        date = _setup_date()
        curve = hazard_points_to_credit_curve(
            hazard_points=[0.5, 0.5, 0.5, 0.5, 0.5],
            years=[1, 2, 3, 4, 5],
            evaluation_date=date,
        )
        sp = curve.survivalProbability(date + ql.Period(5, ql.Years))
        assert sp < 0.1


# ===========================================================================
# create_cds_pricing_engines
# ===========================================================================

class TestCreateCdsPricingEngines:

    def test_returns_dict_with_engines(self):
        from models.hazard.pricing import hazard_points_to_credit_curve, create_cds_pricing_engines
        date = _setup_date()
        credit_curve = hazard_points_to_credit_curve(
            [0.05] * 5, [1, 2, 3, 4, 5], date
        )
        risk_free = _make_risk_free_curve(date)
        engines = create_cds_pricing_engines(credit_curve, 0.4, risk_free)
        assert isinstance(engines, dict)
        assert "ISDA" in engines
        assert "Integral" in engines
        assert "Midpoint" in engines

    def test_engines_not_none(self):
        from models.hazard.pricing import hazard_points_to_credit_curve, create_cds_pricing_engines
        date = _setup_date()
        credit_curve = hazard_points_to_credit_curve(
            [0.03] * 5, [1, 2, 3, 4, 5], date
        )
        risk_free = _make_risk_free_curve(date)
        engines = create_cds_pricing_engines(credit_curve, 0.0, risk_free)
        for key, engine in engines.items():
            assert engine is not None, f"Engine {key} is None"


# ===========================================================================
# create_hazard_rate_curve_approach
# ===========================================================================

class TestCreateHazardRateCurveApproach:

    def test_returns_hazard_curve(self):
        from models.hazard.pricing import create_hazard_rate_curve_approach
        date = _setup_date()
        curve = create_hazard_rate_curve_approach(
            hazard_points=[0.05, 0.05, 0.05, 0.05, 0.05],
            years=[1, 2, 3, 4, 5],
            evaluation_date=date,
        )
        assert curve is not None

    def test_survival_probability_decreases(self):
        from models.hazard.pricing import create_hazard_rate_curve_approach
        date = _setup_date()
        curve = create_hazard_rate_curve_approach(
            hazard_points=[0.1, 0.1, 0.1, 0.1, 0.1],
            years=[1, 2, 3, 4, 5],
            evaluation_date=date,
        )
        sp1 = curve.survivalProbability(date + ql.Period(1, ql.Years))
        sp2 = curve.survivalProbability(date + ql.Period(2, ql.Years))
        assert sp2 < sp1

    def test_zero_hazard_near_full_survival(self):
        from models.hazard.pricing import create_hazard_rate_curve_approach
        import math
        date = _setup_date()
        # Very small hazard
        curve = create_hazard_rate_curve_approach(
            hazard_points=[0.001, 0.001, 0.001, 0.001, 0.001],
            years=[1, 2, 3, 4, 5],
            evaluation_date=date,
        )
        sp = curve.survivalProbability(date + ql.Period(1, ql.Years))
        assert sp > 0.99
