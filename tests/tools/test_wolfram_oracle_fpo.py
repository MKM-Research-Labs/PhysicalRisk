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

The reference is checked against cases it does not compute from -- P = 1 at severe,
the hold at the envelope's knots, its slope against a difference -- and the gate runs
the production code, and the screen's JavaScript, against it. The GBM comparison runs
on a synthetic catalogue with a stand-in classifier, so it needs no data store;
Wolfram is stood in for by a file.
"""

import re
import shutil
from types import SimpleNamespace

import mpmath as mp
import numpy as np
import pytest
from tools.wolfram_oracle import __main__ as cli
from tools.wolfram_oracle._wl import save_wolfram
from tools.wolfram_oracle.floodpoly import cases, claims, gbm
from tools.wolfram_oracle.floodpoly import reference as ref
from tools.wolfram_oracle.floodpoly import run as runner
from tools.wolfram_oracle.floodpoly import wolfram as oracle

from config.models import ORACLE_FPO_CODE_TOL, ORACLE_FPO_DOC_ENVELOPE

NODE = shutil.which("node") is not None


class _GBM:
    """A stand-in classifier: the document's surface, nudged by the rate of rise."""

    def predict_proba(self, X):
        p = np.clip(claims.predict(X[:, 0], X[:, 1]) + 0.3 * X[:, 2], 0, 1)
        return np.column_stack([1 - p, p])


def _states(n_storms=40, seed=3):
    rng = np.random.RandomState(seed)
    n = 168 * n_storms
    hour = np.tile(np.arange(168), n_storms)
    h = np.log(np.minimum(rng.uniform(0.25, 1.1, n), 0.33 + hour / 40))     # storms take time to rise
    X = np.column_stack([h, np.log((hour + 1) / 168), rng.normal(0, 0.02, n), np.zeros(n)])
    return X, np.repeat(np.arange(n_storms), 168)


def _catalogue(ids, n_storms):
    for gid in ids:
        X, _ = _states()
        yield gid, X, (np.random.RandomState(1).uniform(size=len(X)) < claims.predict(X[:, 0], X[:, 1])).astype(int)


@pytest.fixture
def offline(monkeypatch):
    import tools.flood_classifier_challenger._data as data
    monkeypatch.setattr(gbm, "catalogue", _catalogue)
    monkeypatch.setattr(gbm, "classifier", lambda gid: _GBM())
    monkeypatch.setattr(gbm, "gauge_ids", lambda: ["GAUGE-a", "GAUGE-b"])
    monkeypatch.setattr(data, "load_catalogue", lambda ids, n_storms, seed: [
        SimpleNamespace(gauge_id=gid, X=X, groups=grp, n_real=len(X)) for gid in ids for X, grp in [_states()]])


@pytest.fixture(scope="module")
def model():
    return cases.load()


class TestReference:
    def test_at_or_above_severe_a_flood_has_happened(self):
        assert ref.p_flood(6.58, 0, 6.58) == 1 and ref.p_flood(9.0, 167, 6.58) == 1

    def test_below_the_floor_it_holds_its_value_there(self):
        assert ref.p_flood(0.1, 50, 1.0) == ref.p_flood(0.2, 50, 1.0)

    def test_the_hour_is_held_at_the_envelope(self):
        with mp.workdps(30):
            r, hr = ORACLE_FPO_DOC_ENVELOPE[3]
            h = mp.log(mp.mpf(r))
            assert ref.tau(h) == pytest.approx(ref.log_time(mp.mpf(hr)))
            assert ref.p_flood(mp.mpf(r), 0, 1) == ref.p_features(h, ref.log_time(mp.mpf(hr)))
            assert ref.held(mp.mpf(r), 0, 1) and not ref.held(mp.mpf(r), 100, 1)
            assert ref.tau(mp.log(mp.mpf("0.3"))) == -mp.inf and ref.tau(mp.mpf("0.1")) == ref.knots()[-1][1]

    @pytest.mark.parametrize("hour", [0, 60])
    def test_the_slope_is_the_derivative_at_a_fixed_hour(self, hour):
        with mp.workdps(30):
            h, t, d = mp.log(mp.mpf("0.52")), ref.log_time(hour), mp.mpf("1e-10")
            numeric = (ref.p_features(h + d, t) - ref.p_features(h - d, t)) / (2 * d)
            assert ref.slope(h, t) == pytest.approx(numeric, rel=1e-8)
            assert ref.slope(mp.mpf("0.1"), t) == 0 and ref.tau_slope(mp.mpf("0.1")) == 0

    def test_a_threshold_at_zero(self):
        assert ref.p_flood(5, 3, 0) == 0 and ref.p_simple(5, 0) == 0 and ref.p_simple(9, 6) == 1


class TestModel:
    def test_the_code_computes_the_document(self, model):
        c = cases.run(model)
        for k in ("poly", "simple", "copy", "slope"):
            assert c[k] <= ORACLE_FPO_CODE_TOL, k
        assert c["zero_threshold"] and c["series"] == 0 and c["served"] and not c["js_own_coefficients"]
        assert c["js"] is None if not NODE else c["js"] <= ORACLE_FPO_CODE_TOL

    def test_the_javascript_finders(self):
        assert cases.js_literal_coefficients("var _fpCoeffs = {a: 1};") and not cases.js_literal_coefficients("x")
        assert cases.js_function("nothing here") is None
        assert cases.run_js({}, [[1, 0, 2]], fn=None, node="no-such-node") is None


class TestGBM:
    def test_the_first_hour_a_level_is_reached(self):
        top = np.array([0.3, 0.4, 0.6, 0.6, 1.0])
        assert gbm.first_reached(top, 0.25) == 0.0 and gbm.first_reached(top, 0.5) == pytest.approx(1.5)
        assert gbm.first_reached(top, 1.2) is None

    def test_the_comparison_and_the_claims(self, offline, model):
        r, c = runner.evaluate(model)
        assert len(r["gauges"]) == 2 and all(g["near"]["n"] > 0 for g in r["gauges"])
        for k in ("coeffs", "step", "floor", "monotone", "t0", "latch"):
            assert c[k]["met"], k
        assert c["grid"]["met"] and c["envelope"]["config"]
        assert not c["fit"]["met"] and c["fit"]["of"] == 11 and len(r["held"]["rows"]) == 2


def _answers():
    with mp.workdps(50):
        out = {i: mp.nstr(r, 35).replace("e", "*^") for i, _, r in oracle.items() if r is not None}
        for i, _, r in oracle.items():
            if r is None:
                rid = i[len("min/"):]
                _, h, t = oracle.dense_minimum(rid)
                v = oracle._rate(rid, mp.mpf(h), mp.mpf(t))
                out[i] = "{" + ", ".join(mp.nstr(x, 35).replace("e", "*^") for x in (v, mp.mpf(h), mp.mpf(t))) + "}"
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
        assert "15.0 (file)" in macros and (r"\bmOutcome}{all pass}" in macros or not NODE)
        assert "along the envelope" in (tmp_path / "evidence_tables_claims.tex").read_text()

    def test_a_minimum_that_is_not_the_lowest_fails(self):
        answers = _answers()
        with mp.workdps(50):
            h, t = mp.log(mp.mpf("0.2")), ref.log_time(100)     # the floor at hour 100: right, but not lowest
            v = oracle._rate("free/100", h, t)
            assert v > oracle.dense_minimum("free/100")[0]
            answers["min/free/100"] = "{" + ", ".join(mp.nstr(x, 35) for x in (v, h, t)) + "}"
        assert oracle.judge(answers)[0] == 1.0

    def test_a_minimum_wolfram_misreports_fails(self):
        answers = _answers()
        v, h, t = oracle.dense_minimum("env/2")
        answers["min/env/2"] = "{" + f"{v - 1}, {h}, {t}" + "}"
        assert oracle.judge(answers)[0] == 1.0
