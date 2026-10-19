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

"""Tests for tools.wolfram_oracle.prs, the PR-001 benchmark.

The reference is checked against two closed forms it does not use — the flat
curve's quarterly spread and the continuous-time (1 - R) lambda — so it is not
merely agreeing with itself. The model gate then runs over the full grid, so a
change to prs_analytical.py that breaks the documented formula fails here, not
only in the filed PDF. Wolfram is stood in for by a results file.
"""

import json
import re

import mpmath as mp
import pytest

from config.models import MIN_PRS_SPREAD_BPS, ORACLE_PRS_REL_TOL, ORACLE_PRS_SOURCE
from config.port import DEFAULT_YIELD_CURVE
from tools.wolfram_oracle import __main__ as cli
from tools.wolfram_oracle._model import load_module, provenance
from tools.wolfram_oracle._wl import save_wolfram
from tools.wolfram_oracle.prs import claims, latex, spread


@pytest.fixture(scope="module")
def pricing():
    return load_module(ORACLE_PRS_SOURCE)


@pytest.fixture(scope="module")
def rows(pricing):
    return spread.run(pricing)


class TestReference:
    def test_flat_curve_matches_its_closed_form(self):
        p, recovery, r, dt = 0.02, 0.4, mp.mpf("0.03"), mp.mpf(1) / 4
        lam = -mp.log(1 - mp.mpf(p))
        closed = 1e4 * (1 - mp.mpf(recovery)) * (mp.exp(lam * dt) - 1) / dt * mp.exp(r * dt / 2)
        assert spread.discrete_ref(p, 5, recovery, None) == pytest.approx(closed, rel=1e-40)

    def test_continuous_is_one_minus_r_times_lambda(self):
        assert float(spread.continuous_ref(0.02, 0.0)) == pytest.approx(-1e4 * mp.log(0.98))

    def test_curve_rate_is_linear_between_years_and_flat_beyond(self):
        c = DEFAULT_YIELD_CURVE
        assert spread.curve_rate(c, 0.25) == mp.mpf(c["1"])
        assert spread.curve_rate(c, 1.5) == pytest.approx((c["1"] + c["2"]) / 2)
        assert spread.curve_rate(c, 50) == mp.mpf(c[max(c, key=int)])

    def test_the_cap_applies_before_the_log(self):
        assert spread.hazard(1.0) == spread.hazard(0.999)


class TestModel:
    def test_model_matches_the_documented_formula(self, rows):
        assert max(r["rel_err"] for r in rows) <= ORACLE_PRS_REL_TOL

    def test_the_floor_is_exercised(self, rows):
        floored = [r for r in rows if r["floored"]]
        assert floored and all(float(r["model"]) == MIN_PRS_SPREAD_BPS for r in floored)

    def test_rules_hold(self, pricing):
        assert all(ok for _, ok, _ in spread.rules(pricing))

    def test_wolfram_items_cover_every_case(self, rows):
        items = spread.wl_items(rows)
        assert len(items) == len(rows)
        assert "Piecewise" in dict(items)[rows[-1]["id"]]
        assert "e-" not in "".join(e for _, e in items)


class TestClaims:
    def test_both_numerical_claims_are_tested(self, rows):
        disc, curve, basis = claims.assess(rows)
        assert disc["met"] is False and disc["low"] > disc["limit"]
        assert curve["met"] is False and curve["first_over"] is not None
        assert basis["met"] is None and basis["first_over"] is not None

    def test_relative_overstatement_follows_lambda_plus_r(self, rows):
        for t in claims.by_probability(rows):
            lam = -mp.log(1 - mp.mpf(t["p"]))
            assert t["disc_rel"] == pytest.approx(float((lam + mp.mpf("0.03")) / 8), rel=0.1)


def _wolfram_answers(rows):
    return {r["id"]: r["ref"].replace("e", "*^") for r in rows}


class TestRun:
    def test_unknown_model_is_a_usage_error(self, capsys):
        assert cli.main([]) == 2 and cli.main(["xx001"]) == 2
        assert "pr001" in capsys.readouterr().err

    def test_a_run_without_and_with_wolfram(self, tmp_path, rows):
        assert cli.main(["pr001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        macros = (tmp_path / "evidence_tables_macros.tex").read_text()
        assert "Wolfram pending" in macros
        ids = re.findall(r'<\|"id" -> "([^"]+)"', (tmp_path / "spreads.wl").read_text())
        answers = _wolfram_answers(rows)
        save_wolfram(tmp_path / "spreads_wolfram.json", "15.0 (file)", {i: answers[i] for i in ids})
        assert cli.main(["pr001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        macros = (tmp_path / "evidence_tables_macros.tex").read_text()
        assert r"\bmOutcome}{all pass}" in macros and "15.0 (file)" in macros
        assert "Model vs W." in (tmp_path / "evidence_tables_spreads.tex").read_text()
        assert "model_vs_wolfram" in (tmp_path / "spreads.csv").read_text()

    def test_findings_mark_a_failure(self, rows, pricing):
        broken = [dict(r) for r in rows]
        broken[0]["rel_err"] = 1.0
        checks = latex.findings(broken, spread.rules(pricing), None)
        assert checks[0][3] == r"\textbf{FAIL}" and checks[1][3] == r"\textbf{pending}"

    def test_provenance_names_the_code(self):
        assert provenance(ORACLE_PRS_SOURCE)["file"] == ORACLE_PRS_SOURCE
        assert json.dumps(provenance(ORACLE_PRS_SOURCE))
