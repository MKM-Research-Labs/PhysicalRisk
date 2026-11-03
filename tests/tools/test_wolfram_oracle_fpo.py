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
"""Tests for tools.wolfram_oracle.floodpoly, the FPO-001 benchmark.

The reference is checked against cases it does not compute from -- the logistic at
the severe level and final hour is sigma(f), the P = 1/2 levels solve the kernel --
and the gate runs the production code against it. The GBM comparison runs on a
synthetic catalogue with a stand-in classifier, so it needs no data store; Wolfram
is stood in for by a file.
"""

import re

import mpmath as mp
import numpy as np
import pytest

from config.models import ORACLE_FPO_CODE_TOL, ORACLE_FPO_DOC_COEFFS
from tools.wolfram_oracle import __main__ as cli
from tools.wolfram_oracle._wl import save_wolfram
from tools.wolfram_oracle.floodpoly import cases, claims, gbm, reference as ref, run as runner
from tools.wolfram_oracle.floodpoly import wolfram as oracle


class _GBM:
    """A stand-in classifier: the document's surface, nudged by the rate of rise."""

    def predict_proba(self, X):
        p = np.clip(claims.predict(X[:, 0], X[:, 1]) + 0.3 * X[:, 2], 0, 1)
        return np.column_stack([1 - p, p])


def _catalogue(ids, n_storms):
    rng = np.random.RandomState(3)
    for gid in ids:
        n = 168 * 40
        h = np.log(rng.uniform(0.3, 1.1, n))
        t = np.log((np.tile(np.arange(168), 40) + 1) / 168)
        X = np.column_stack([h, t, rng.normal(0, 0.02, n), np.zeros(n)])
        yield gid, X, (rng.uniform(size=n) < claims.predict(h, t)).astype(int)


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setattr(gbm, "catalogue", _catalogue)
    monkeypatch.setattr(gbm, "classifier", lambda gid: _GBM())
    monkeypatch.setattr(gbm, "gauge_ids", lambda: ["GAUGE-a", "GAUGE-b"])


@pytest.fixture(scope="module")
def model():
    return cases.load()


class TestReference:
    def test_at_severe_and_the_final_hour_it_is_sigma_f(self):
        with mp.workdps(30):
            assert ref.p_flood(6.58, 167, 6.58) == pytest.approx(1 / (1 + mp.exp(-mp.mpf(ORACLE_FPO_DOC_COEFFS[-1]))))

    def test_the_half_levels_solve_the_kernel(self):
        with mp.workdps(30):
            for hr in (24, 48, 96):
                for x in ref.half_levels(hr):
                    assert abs(ref.kernel(mp.log(x), mp.log(mp.mpf(hr + 1) / 168))) < 1e-20
            assert ref.half_levels(167) == []

    def test_a_kernel_linear_in_h_has_one_root(self, monkeypatch):
        monkeypatch.setattr(ref, "ORACLE_FPO_DOC_COEFFS", ("1", "0", "0", "0", "0", "0.5"))
        with mp.workdps(30):
            assert [float(x) for x in ref.half_levels(48)] == pytest.approx([float(mp.exp(-0.5))])

    def test_a_threshold_at_zero(self):
        assert ref.p_flood(5, 3, 0) == 0 and ref.p_simple(5, 0) == 0 and ref.p_simple(9, 6) == 1


class TestModel:
    def test_the_code_computes_the_document(self, model):
        c = cases.run(model)
        for k in ("poly", "simple", "copy", "slope"):
            assert c[k] <= ORACLE_FPO_CODE_TOL, k
        assert c["zero_threshold"] and c["series"] == 0 and c["js"]

    def test_the_javascript_parser(self):
        assert cases.js_coefficients("var _fpCoeffs = {a: 1.5, b: -2, c: 0, d: 1, e: 2, f: -3};") == \
            ["1.5", "-2", "0", "1", "2", "-3"]
        assert cases.js_coefficients("nothing here") is None


class TestGBM:
    def test_the_comparison_and_the_claims(self, offline, model):
        r, c = runner.evaluate(model)
        assert len(r["gauges"]) == 2 and all(g["near"]["n"] > 0 for g in r["gauges"])
        assert c["t0"]["met"] and not c["t1"]["met"] and not c["at_severe"]["met"]
        assert c["latch"]["met"] is None and c["fit"]["n"] > 0 and c["cubic"]["r2"] > 0.5


def _answers():
    with mp.workdps(50):
        out = {i: mp.nstr(r, 35).replace("e", "*^") for i, _, r in oracle.items() if r is not None}
        for hr in (24, 48, 72, 96, 120, 167):
            out[f"half/{hr}"] = "{" + ", ".join(mp.nstr(x, 35) for x in ref.half_levels(hr)) + "}"
    return out


class TestRun:
    def test_a_run_without_and_with_wolfram(self, tmp_path, offline):
        assert cli.main(["fpo001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        assert "Wolfram pending" in (tmp_path / "evidence_tables_macros.tex").read_text()
        wanted = re.findall(r'<\|"id" -> "([^"]+)"', (tmp_path / "floodpoly.wl").read_text())
        answers = _answers()
        save_wolfram(tmp_path / "floodpoly_wolfram.json", "15.0 (file)", {i: answers[i] for i in wanted})
        assert cli.main(["fpo001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        macros = (tmp_path / "evidence_tables_macros.tex").read_text()
        assert "15.0 (file)" in macros and r"\bmOutcome}{all pass}" in macros
        assert "passes" in (tmp_path / "evidence_tables_claims.tex").read_text()

    def test_a_missing_root_fails_the_agreement(self):
        answers = _answers()
        answers["half/24"] = "{0.5}"
        assert oracle.judge(answers)[0] == 1.0

    def test_an_empty_root_set(self):
        assert oracle._roots("{}") == [] and oracle._roots("{0.5}") == [mp.mpf("0.5")]
