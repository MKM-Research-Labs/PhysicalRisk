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
Tests for load_hazard_curves, create_survival_curve_from_hazard,
and create_flat_hazard_curve.
"""

import json
import math

import pytest

try:
    import QuantLib as ql
    HAS_QUANTLIB = True
except ImportError:
    HAS_QUANTLIB = False

pytestmark = pytest.mark.skipif(not HAS_QUANTLIB, reason="QuantLib not installed")

from .conftest import term_structure, make_gauge


class TestLoadHazardCurvesErrors:

    def test_missing_file_raises_file_not_found(self, tmp_path):
        from models.prs.prshc import load_hazard_curves
        with pytest.raises(FileNotFoundError):
            load_hazard_curves(str(tmp_path / "nonexistent.json"))

    def test_invalid_json_raises_json_decode_error(self, tmp_path):
        from models.prs.prshc import load_hazard_curves
        bad = tmp_path / "bad.json"
        bad.write_text("{ this is not valid json }")
        with pytest.raises(json.JSONDecodeError):
            load_hazard_curves(str(bad))

    def test_empty_json_object_returns_empty_dict(self, tmp_path):
        from models.prs.prshc import load_hazard_curves
        empty = tmp_path / "empty.json"
        empty.write_text("{}")
        result = load_hazard_curves(str(empty))
        assert result == {}

    def test_returns_full_structure(self, tmp_path):
        from models.prs.prshc import load_hazard_curves
        payload = {"hazard_curves": {"G-001": make_gauge("G-001")}, "meta": {"version": 2}}
        p = tmp_path / "curves.json"
        p.write_text(json.dumps(payload))
        result = load_hazard_curves(str(p))
        assert result["meta"]["version"] == 2
        assert "G-001" in result["hazard_curves"]


class TestCreateSurvivalCurveAdditional:

    def test_single_point_term_structure(self, today):
        from models.prs.prshc import create_survival_curve_from_hazard
        ts = [{"year": 5, "survival_prob": 0.60}]
        curve = create_survival_curve_from_hazard(today, ts)
        assert curve is not None

    def test_near_zero_survival_positive_hazard(self, today):
        from models.prs.prshc import create_survival_curve_from_hazard
        ts = [{"year": y, "survival_prob": 0.01 ** y} for y in range(1, 6)]
        curve = create_survival_curve_from_hazard(today, ts)
        s1 = curve.survivalProbability(today + ql.Period(1, ql.Years))
        assert s1 < 0.9

    def test_implied_hazard_rate_formula(self, today):
        from models.prs.prshc import create_survival_curve_from_hazard
        annual_rate = 0.10
        final_survival = (1 - annual_rate) ** 5
        ts = term_structure(annual_rate)
        implied_lambda = -math.log(final_survival) / 5
        expected_5yr = math.exp(-implied_lambda * 5)
        curve = create_survival_curve_from_hazard(today, ts)
        sp5 = curve.survivalProbability(today + ql.Period(5, ql.Years))
        assert sp5 == pytest.approx(expected_5yr, rel=0.01)

    def test_survival_strictly_positive(self, today):
        from models.prs.prshc import create_survival_curve_from_hazard
        ts = term_structure(0.20)
        curve = create_survival_curve_from_hazard(today, ts)
        for yr in [1, 2, 3, 5]:
            sp = curve.survivalProbability(today + ql.Period(yr, ql.Years))
            assert sp > 0.0

    def test_single_point_high_risk_ts(self, today):
        from models.prs.prshc import create_survival_curve_from_hazard
        ts = [{"year": 5, "survival_prob": 0.05}]
        curve = create_survival_curve_from_hazard(today, ts)
        assert curve is not None

    def test_actual360_day_counter_produces_curve(self, today):
        from models.prs.prshc import create_survival_curve_from_hazard
        ts = term_structure(0.07)
        curve = create_survival_curve_from_hazard(today, ts, day_counter=ql.Actual360())
        sp = curve.survivalProbability(today + ql.Period(2, ql.Years))
        assert 0.0 < sp <= 1.0


class TestCreateFlatHazardCurveAdditional:

    def test_quote_value_matches_input(self, today):
        from models.prs.prshc import create_flat_hazard_curve
        rate = 0.073
        _, quote = create_flat_hazard_curve(today, rate)
        assert quote.value() == pytest.approx(rate, rel=1e-10)

    def test_quote_is_simple_quote(self, today):
        from models.prs.prshc import create_flat_hazard_curve
        _, quote = create_flat_hazard_curve(today, 0.10)
        assert isinstance(quote, ql.SimpleQuote)

    def test_very_high_hazard_rate_near_zero_survival(self, today):
        from models.prs.prshc import create_flat_hazard_curve
        curve, _ = create_flat_hazard_curve(today, 2.0)
        s1 = curve.survivalProbability(today + ql.Period(1, ql.Years))
        assert s1 == pytest.approx(math.exp(-2.0), rel=0.01)

    def test_actual360_day_counter_accepted(self, today):
        from models.prs.prshc import create_flat_hazard_curve
        curve, _ = create_flat_hazard_curve(today, 0.05, day_counter=ql.Actual360())
        assert curve is not None

    def test_survival_probability_formula(self, today):
        from models.prs.prshc import create_flat_hazard_curve
        lam = 0.08
        curve, _ = create_flat_hazard_curve(today, lam)
        date3 = today + ql.Period(3, ql.Years)
        sp = curve.survivalProbability(date3)
        assert sp == pytest.approx(math.exp(-lam * 3), rel=0.02)
