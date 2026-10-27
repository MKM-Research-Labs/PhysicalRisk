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
"""Tests for tools.wolfram_oracle.frequency, the EF-001 benchmark.

The reference is checked against figures it does not compute from (a hand value of
1 - exp(-x), the Poisson limit of the Negative Binomial), and the model gate then
runs the full grid, so a change to the frequency model that breaks its documented
formulae fails here. Wolfram is stood in for by a results file.
"""

import re

import mpmath as mp
import pytest

from config.models import ORACLE_EF_LL_TOL, ORACLE_EF_PVALUE_TOL, ORACLE_EF_REL_TOL
from tools.wolfram_oracle import __main__ as cli
from tools.wolfram_oracle._wl import save_wolfram
from tools.wolfram_oracle.frequency import cases, claims


@pytest.fixture(scope="module")
def rows():
    m = cases.load()
    return cases.annualisation(m) + cases.term(m) + cases.compound(m) + cases.families(m)


def _group(rows, g):
    return [r for r in rows if r["group"] == g]


class TestReference:
    def test_annual_probability_by_hand(self, rows):
        r = next(r for r in _group(rows, "annual") if r["lam"] == 2.0 and r["p"] == 0.2)
        assert float(r["ref"]) == pytest.approx(0.3296799539643607, rel=1e-15)

    def test_a_constant_rate_tenor_is_the_annual_compounded(self, rows):
        r = next(r for r in _group(rows, "term") if r["id"] == "term/const,lam=2.0,p=0.01,T=10")
        assert float(r["ref"]) == pytest.approx(1 - mp.e ** -0.2, rel=1e-15)

    def test_poisson_counts_have_their_maximum_in_the_poisson_limit(self, rows):
        for r in _group(rows, "nb_ll"):
            if r["alpha_ref"] == 0:
                pois = next(p for p in _group(rows, "pois_ll") if p["id"][8:] == r["id"][6:])
                assert r["ref"] == pois["ref"]


class TestModel:
    @pytest.mark.parametrize("group, tol", [
        ("rate", ORACLE_EF_REL_TOL), ("term", ORACLE_EF_REL_TOL), ("aal", ORACLE_EF_REL_TOL),
        ("aal_se", ORACLE_EF_REL_TOL), ("disp_stat", ORACLE_EF_REL_TOL),
        ("p_over", ORACLE_EF_PVALUE_TOL), ("p_under", ORACLE_EF_PVALUE_TOL),
        ("pois_ll", ORACLE_EF_REL_TOL), ("nb_ll", ORACLE_EF_LL_TOL)])
    def test_matches_the_reference(self, rows, group, tol):
        assert max(r["rel_err"] for r in _group(rows, group)) <= tol

    def test_annual_probability_in_its_operating_range(self, rows):
        assert max(r["rel_err"] for r in claims.operating(rows) if r["group"] == "annual") <= ORACLE_EF_REL_TOL


class TestClaims:
    def test_document_claims_and_findings(self, rows):
        eq4, z, samp, term, prec, nb = claims.assess(rows)
        assert eq4["met"] and eq4["identity"] is None
        assert z["met"] and samp["met"] and nb["met"]
        assert term["met"] is None and term["high"] < term["low"] < 0
        assert prec["met"] is None and prec["worst"] > ORACLE_EF_REL_TOL

    def test_wolfram_must_confirm_the_identity(self, rows):
        assert not claims.assess(rows, {"claim/eq4": "0", "claim/mean_abs_z": "0.7978845608"})[0]["met"]


class TestRun:
    def test_a_run_without_and_with_wolfram(self, tmp_path, rows):
        assert cli.main(["ef001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        assert "Wolfram pending" in (tmp_path / "evidence_tables_macros.tex").read_text()
        answers = {r["id"]: r["ref"] for r in rows}
        answers["claim/eq4"] = "1"
        answers["claim/mean_abs_z"] = mp.nstr(mp.sqrt(2 / mp.pi), 30)
        ids = re.findall(r'<\|"id" -> "([^"]+)"', (tmp_path / "frequency.wl").read_text())
        save_wolfram(tmp_path / "frequency_wolfram.json", "15.0 (file)",
                     {i: answers[i].replace("e", "*^") for i in ids})
        assert cli.main(["ef001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        macros = (tmp_path / "evidence_tables_macros.tex").read_text()
        assert "15.0 (file)" in macros and r"\bmOutcome}{all pass}" in macros
        assert "identity confirmed" in (tmp_path / "evidence_tables_claims.tex").read_text()
