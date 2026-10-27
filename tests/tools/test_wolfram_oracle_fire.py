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
"""Tests for tools.wolfram_oracle.fire, the FIRE-001 benchmark.

The exact credit is checked against cases it does not compute from -- the
deterministic race, a chain that latches at ignition, and the fundamental matrix
for the mean absorption time -- and the model gate then runs every printed cell,
so a change to the fire model that breaks its documented behaviour fails here.
Wolfram is stood in for by a results file.
"""

import re

import mpmath as mp
import pytest

from config.models import ORACLE_FIRE_REL_TOL, ORACLE_FIRE_Z_LIMIT
from tools.wolfram_oracle import __main__ as cli
from tools.wolfram_oracle._wl import save_wolfram, wl_number
from tools.wolfram_oracle.fire import cases, claims, exact


@pytest.fixture(scope="module")
def model():
    return cases.load()


@pytest.fixture(scope="module")
def run(model):
    return cases.run(model)


def _prof(**over):
    base = {"growth": mp.mpf(2), "i_crit": mp.mpf(5), "detection_steps": mp.mpf(1),
            "suppression_bite_steps": mp.mpf(10), "intensity_ceiling": mp.mpf(100),
            "suppression_reachable": True, "structure_combustible": True, "blend_weight": mp.mpf(1)}
    return {**base, **over}


class TestReference:
    def test_the_race_without_jitter_latches_where_it_should(self):
        jitter = {"growth_sigma": 1e-9, "timing_sigma": 1e-9, "ceiling_sigma": 1e-9}
        with mp.workdps(40):
            law = exact.pnr_step_law(_prof(), jitter, 20)
        assert float(law[2]) == pytest.approx(1.0)          # 3 x 2 > 5, before the bite at 11
        assert float(mp.fsum(law)) == pytest.approx(1.0)

    def test_an_unreachable_combustible_frame_latches_at_ignition(self, model):
        prog = model["config"].progression
        with mp.workdps(40):
            o = exact.outcome(_prof(suppression_reachable=False), prog.transition_matrices,
                              prog.race_jitter, 200)
        pnr = prog.transition_matrices["point_of_no_return"]
        assert o["contained"] == 0 and o["pnr"] == 1
        assert float(o["total"]) == pytest.approx(pnr[1][7], abs=1e-30)

    def test_mean_steps_is_the_fundamental_matrix(self, model):
        prog = model["config"].progression
        with mp.workdps(40):
            o = exact.outcome(_prof(growth=mp.mpf(0)), prog.transition_matrices, prog.race_jitter, 200)
            m = prog.transition_matrices["AA_controllable"]
            q = mp.matrix([[m[i][j] for j in range(5)] for i in range(5)])
            n = (mp.eye(5) - q) ** -1
            assert o["mean_steps"] == pytest.approx(sum(n[0, j] for j in range(5)), rel=1e-25)

    def test_tails_keep_their_digits(self):
        with mp.workdps(50):
            assert exact._sf(mp.mpf(30)) > 0
            assert float(exact._between(mp.mpf(29), mp.mpf(30)) / exact._sf(mp.mpf(29))) == pytest.approx(1.0)

    def test_lists_with_an_accuracy_zero_parse(self):
        assert wl_number("{SetAccuracy[0, 60.], 0.4}") == [0, mp.mpf("0.4")]


class TestModel:
    def test_model_c_and_the_monte_carlo_match(self, run):
        rows, _ = run
        assert max(r["profile_rel_err"] for r in rows) <= ORACLE_FIRE_REL_TOL
        assert all(r["flags_ok"] for r in rows)
        for k in cases.METRICS:
            assert max(abs(r[f"{k}_z"]) for r in rows) <= ORACLE_FIRE_Z_LIMIT


class TestClaims:
    def test_the_documents_claims(self, run, model):
        c = claims.assess(run[0], model)
        rep, vs, absorb, grow, resid, tall, cliff, t13, race, s6, timing, noise = c
        assert all(x["met"] for x in (rep, vs, absorb, grow, resid, cliff, t13))
        assert tall["met"] is False and tall["exact"] < 0.01
        assert race["race_lost"] > 10 * race["recorded"]
        assert noise["exact_low"] == pytest.approx(noise["exact_high"], abs=1e-9)
        assert cliff["production_se"] > 40


class TestRun:
    def test_a_run_without_and_with_wolfram(self, tmp_path, run):
        assert cli.main(["fire001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        assert "Wolfram pending" in (tmp_path / "evidence_tables_macros.tex").read_text()
        _, exact_by = run
        ids = cases.asset_ids(exact_by)
        answers = {ids[k]: "{" + ", ".join(mp.nstr(c[x], 30) for x in ("contained", "partial", "total", "pnr", "q")) + "}"
                   for k, (_, c, *_) in exact_by.items()}
        wanted = re.findall(r'<\|"id" -> "([^"]+)"', (tmp_path / "fire.wl").read_text())
        save_wolfram(tmp_path / "fire_wolfram.json", "15.0 (file)",
                     {i: answers[i].replace("e", "*^") for i in wanted})
        assert cli.main(["fire001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        macros = (tmp_path / "evidence_tables_macros.tex").read_text()
        assert "15.0 (file)" in macros and r"\bmOutcome}{all pass}" in macros
