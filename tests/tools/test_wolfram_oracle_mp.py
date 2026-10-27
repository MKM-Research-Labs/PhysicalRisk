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
"""Tests for tools.wolfram_oracle.mortgage, the MP-001 benchmark.

Benchmark v0.2: the pricer after its fair-value and recovery fixes, against model
document v1.3.

The reference is checked against figures it does not compute from -- a textbook
annuity payment, and a pathwise value summed path by path rather than period by
period -- and the model gate then runs the full grid, so a change to the pricer that
breaks its documented formulae fails here. Wolfram is stood in for by a results file.
"""

import importlib
import re

import mpmath as mp
import pytest

from config.models import ORACLE_MP_PACKAGE, ORACLE_MP_REL_TOL
from tools.wolfram_oracle import __main__ as cli
from tools.wolfram_oracle._wl import save_wolfram
from tools.wolfram_oracle.mortgage import cases, claims

PRICER = importlib.import_module(ORACLE_MP_PACKAGE)


@pytest.fixture(scope="module")
def rows():
    return cases.run(PRICER)


def _loan(**over):
    k = dict(cases.loans()[0])
    k.update(over)
    return k


class TestReference:
    def test_payment_is_the_textbook_annuity(self):
        k = _loan(loan_amount=200_000.0, interest_rate=0.06, current_term=25, original_maturity=25)
        with mp.workdps(30):
            assert float(cases.value(k)["payment"]) == pytest.approx(1288.60, abs=0.005)

    def test_pathwise_value_summed_path_by_path(self):
        k = _loan(loan_amount=285_000.0, recovery_haircut=0.4, current_term=2, original_maturity=25,
                  gross_annual_income=30_000.0)
        with mp.workdps(40):
            v = cases.value(k)
            p, r, n = mp.mpf(k["loan_amount"]), mp.mpf(k["interest_rate"]) / 12, 24
            m, b = v["payment"], [p]
            for _ in range(n):
                b.append(b[-1] - (m - b[-1] * r))
            h, rv, d = 1 - mp.exp(-v["spread"] / 12), (1 - mp.mpf(0.4)) * mp.mpf(300_000.0), r
            total = (1 - h) ** n * mp.fsum(m * (1 + d) ** -j for j in range(1, n + 1))
            for t in range(1, n + 1):
                path = mp.fsum(m * (1 + d) ** -j for j in range(1, t))
                path += min(b[t - 1], rv) * (1 + d) ** -t
                total += (1 - h) ** (t - 1) * h * path
            assert v["fv"] == v["pv_cf"] == pytest.approx(total, rel=1e-30)
            assert v["v11"] < v["fv"]

    def test_the_ltv_band_is_judged_on_the_double(self):
        k = _loan(loan_amount=0.95 * 300_000.0)
        with mp.workdps(30):
            m = cases.value(k)["payment"]
            assert cases.spread(k, m) / cases.spread(_loan(loan_amount=0.9 * 300_000.0 + 1), m) == pytest.approx(1)


class TestModel:
    def test_matches_the_document(self, rows):
        for key in ("payment", "spread", "pv_cf", "pv_el", "fv"):
            assert max(r[f"{key}_rel_err"] for r in rows) <= ORACLE_MP_REL_TOL


class TestClaims:
    def test_document_v13_claims_hold(self, rows):
        fv, rec, t7, pay, zero, bound, par = claims.assess(rows, PRICER)
        assert all(c["met"] for c in (fv, rec, t7, pay, zero, bound, par))
        assert fv["correction"] > 0.3 and fv["fv"] > fv["v11"]
        assert rec["worst"] == 0 and t7["lgd_free"] and par["identity"] is None

    def test_wolfram_must_prove_the_par_identity(self, rows):
        assert not claims.assess(rows, PRICER, {"claim/par": "0"})[6]["met"]


class TestRun:
    def test_a_run_without_and_with_wolfram(self, tmp_path, rows):
        assert cli.main(["mp001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        assert "Wolfram pending" in (tmp_path / "evidence_tables_macros.tex").read_text()
        answers = {"claim/par": "1"}
        for r in rows:
            answers[f"{r['id']}/fv"] = r["fv_ref"]
            answers[f"{r['id']}/path"] = r["pathwise"]
        ids = re.findall(r'<\|"id" -> "([^"]+)"', (tmp_path / "mortgage.wl").read_text())
        save_wolfram(tmp_path / "mortgage_wolfram.json", "15.0 (file)",
                     {i: answers[i].replace("e", "*^") for i in ids})
        assert cli.main(["mp001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        macros = (tmp_path / "evidence_tables_macros.tex").read_text()
        assert "15.0 (file)" in macros and r"\bmOutcome}{all pass}" in macros
        assert "identity proved" in (tmp_path / "evidence_tables_claims.tex").read_text()
