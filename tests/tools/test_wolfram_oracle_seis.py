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
"""Tests for tools.wolfram_oracle.seismic, the SEIS-001 benchmark.

The exact credit is checked against cases it does not compute from -- the mean of
a clipped lognormal by quadrature, the great-circle offset, and the fragility
integral collapsing to a single normal CDF when the magnitude range is a point --
and the model gate then runs every printed cell, so a change to the seismic model
that breaks its documented behaviour fails here. Wolfram is stood in for by a file.
"""

import re

import mpmath as mp
import pytest

from config.models import ORACLE_SEIS_BASELINE, ORACLE_SEIS_KM_PER_DEG, ORACLE_SEIS_REL_TOL, ORACLE_SEIS_Z_LIMIT
from tools.wolfram_oracle import __main__ as cli
from tools.wolfram_oracle._wl import save_wolfram
from tools.wolfram_oracle.seismic import cases, claims, exact


@pytest.fixture(scope="module")
def model():
    return cases.load()


@pytest.fixture(scope="module")
def run(model):
    return cases.run(model)


class TestReference:
    def test_clipped_mean_by_quadrature(self):
        with mp.workdps(40):
            med, s = mp.mpf("0.35"), mp.mpf("0.4")
            pdf = lambda x: mp.npdf(mp.log(x), mp.log(med), s) / x
            direct = mp.quad(lambda x: x * pdf(x), [0, 1]) + mp.quad(pdf, [1, mp.inf])
            assert exact.clipped_mean(med, s) == pytest.approx(direct, rel=1e-25)

    def test_the_offset_is_the_great_circle_distance(self):
        with mp.workdps(40):
            assert float(exact.r_jb(111.0, 111.0)) == pytest.approx(6371.0 * mp.pi / 180, rel=1e-15)

    def test_a_point_magnitude_is_one_normal_cdf(self, model):
        cfg = model["config"]
        with mp.workdps(40):
            ev = exact.event_inputs(ORACLE_SEIS_BASELINE, cfg, ORACLE_SEIS_KM_PER_DEG)
            thetas, beta = exact.theta(ORACLE_SEIS_BASELINE, cfg)
            m0 = mp.mpf(6)
            narrow = {**ev, "m_min": m0, "m_max": m0 + mp.mpf(10) ** -12}
            p = exact.exceedance(narrow, thetas, beta)["DS3"]
            z = (exact.ln_median(m0, ev["r_jb"], ev["vs30"], ev["gmpe"]) - mp.log(thetas["DS3"])) / mp.sqrt(
                ev["sigma"] ** 2 + beta ** 2)
            assert float(p) == pytest.approx(float(exact._phi(z)), rel=1e-9)

    def test_a_zero_standard_error_is_exact_or_infinite(self):
        assert cases._z(0.0, mp.mpf(0), 0) == 0.0 and cases._z(1.0, mp.mpf(0), 0) == float("inf")

    def test_damage_state_probabilities_are_nested(self, run):
        _, exact_by = run
        for _, ex, *_ in exact_by.values():
            assert ex["p"]["DS1"] >= ex["p"]["DS2"] >= ex["p"]["DS3"] >= 0


class TestModel:
    def test_model_and_monte_carlo_match(self, run):
        rows, _ = run
        assert max(r["check_rel_err"] for r in rows) <= ORACLE_SEIS_REL_TOL
        assert max(r["rjb_rel_err"] for r in rows) <= ORACLE_SEIS_REL_TOL
        for k in cases.METRICS:
            assert max(abs(r[f"{k}_z"]) for r in rows if f"{k}_z" in r) <= ORACLE_SEIS_Z_LIMIT


class TestClaims:
    def test_the_documents_claims(self, run, model):
        rep, vs, gates, rev, stab, prod, t18, gmpe = claims.assess(run[0], model)
        assert rep["met"] and vs["met"] and gates["met"]
        assert rev["reversals"] and rev["met"] is None
        assert stab["met"] is False and stab["worst_rel_se"] > 0.5
        assert t18["met"] is False and t18["exact"]["DS2"] > 0.37
        assert prod["se"] > 5


class TestRun:
    def test_a_run_without_and_with_wolfram(self, tmp_path, run):
        assert cli.main(["seis001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        assert "Wolfram pending" in (tmp_path / "evidence_tables_macros.tex").read_text()
        _, exact_by = run
        ids = cases.asset_ids(exact_by)
        answers = {ids[k]: "{" + ", ".join(mp.nstr(ex["p"][d], 30) for d in exact.DS) + "}"
                   for k, (_, ex, *_) in exact_by.items()}
        wanted = re.findall(r'<\|"id" -> "([^"]+)"', (tmp_path / "seismic.wl").read_text())
        save_wolfram(tmp_path / "seismic_wolfram.json", "15.0 (file)",
                     {i: answers[i].replace("e", "*^") for i in wanted})
        assert cli.main(["seis001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        macros = (tmp_path / "evidence_tables_macros.tex").read_text()
        assert "15.0 (file)" in macros and r"\bmOutcome}{all pass}" in macros
