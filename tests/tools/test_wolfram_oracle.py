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

"""Tests for tools.wolfram_oracle, the GH-001 benchmark.

The Wolfram-literal tests pin the three bugs the pilot shipped with: e-notation
that Wolfram misparses, machine reals that cap N[] at machine precision, and
GumbelDistribution (the minimum law) standing in for the maximum one. The rest
run the benchmark itself — so a change to gev.py that breaks its numerics fails
here, not only in the filed PDF. The run itself — CLI, LaTeX, Wolfram read-back —
is covered in test_wolfram_oracle_run.py.
"""

import json
from fractions import Fraction

import mpmath as mp
import pytest

from config.models import ORACLE_FIT_LL_TOL, ORACLE_REL_TOL
from tools.wolfram_oracle.gev import fit, return_levels
from tools.wolfram_oracle.gev._code import load_gev_fitter
from tools.wolfram_oracle._wl import (
    load_wolfram, rel_err, wl_exact, wl_gev, wl_machine, wl_number, write_wl,
)

ONE_SERIES = {"n30_xi0.1": (30, 3.0, 0.4, 0.1)}


@pytest.fixture(scope="module")
def gev_fitter():
    return load_gev_fitter()


class TestWolframLiterals:
    def test_exact_is_the_binary_double(self):
        assert Fraction(*map(int, wl_exact(0.2).split("/"))) == Fraction(0.2)
        assert wl_exact(100.0) == "100"

    def test_machine_never_uses_e_notation(self):
        s = wl_machine(1e-9)
        assert "e" not in s and s.endswith("*^-9")

    def test_gumbel_is_the_maximum_law(self):
        assert wl_gev(100.0, 20.0, 0.0) == "ExtremeValueDistribution[100, 20]"
        assert wl_gev(100.0, 20.0, 0.5) == "MaxStableDistribution[100, 20, SetPrecision[1/2, 60]]"

    def test_number_parsing(self):
        assert wl_number("1.5*^-15") == mp.mpf("1.5e-15")
        assert wl_number("{0.25, 3, 0.5}") == [0.25, 3, 0.5]

    def test_rel_err_against_zero(self):
        assert rel_err(1e-3, 0) == pytest.approx(1e-3)

    def test_write_wl_brackets_balance(self, tmp_path):
        p = tmp_path / "x.wl"
        write_wl(p, [("a", "N[Quantile[ExtremeValueDistribution[1, 2], 1/2], 30]")], "x_wolfram.json")
        depth = 0
        for c in p.read_text().replace('"', ""):
            depth += c in "([{"
            depth -= c in ")]}"
            assert depth >= 0
        assert depth == 0

    def test_load_wolfram_absent(self, tmp_path):
        assert load_wolfram(tmp_path / "none.json") == (None, None)


class TestReturnLevels:
    def test_model_within_tolerance_in_operating_range(self, gev_fitter):
        rows = return_levels.run(gev_fitter)
        assert return_levels.worst(rows, "level_rel_err")["level_rel_err"] <= ORACLE_REL_TOL
        assert return_levels.worst(rows, "exc_rel_err")["exc_rel_err"] <= ORACLE_REL_TOL

    def test_exceedance_at_the_t_year_level_is_one_over_t(self, gev_fitter):
        row = return_levels.run(gev_fitter, {"g": (0.0, 1.0, 0.0)}, (100,))[0]
        assert float(row["exc_ref"]) == pytest.approx(0.01, rel=1e-14)

    def test_sign_trap_differs(self):
        trap = return_levels.sign_trap()
        assert trap["correct (c = -xi)"] > trap["unflipped (c = +xi)"]


class TestFit:
    def test_model_reaches_the_maximum(self, gev_fitter):
        rows = fit.run(gev_fitter, fit.synthetic_series(ONE_SERIES), ONE_SERIES)
        assert {r["family"] for r in rows} == {"gev", "gumbel"}
        assert all(r["ll_gain_indep"] <= ORACLE_FIT_LL_TOL for r in rows)

    def test_loglik_off_support_is_minus_infinity(self):
        assert fit.loglik_mp([0.0], 10.0, 1.0, 0.5) == -mp.inf

    def test_independent_fit_rejects_off_support(self):
        assert fit._nll([10.0, 0.0, 0.5], _series()["n30_xi0.1"] - 20, False) == float("inf")

    def test_load_gauges_both_shapes(self, tmp_path):
        p = tmp_path / "g.json"
        p.write_text(json.dumps({"a": [1.0, 2.0], "b": {"storm_responses": {"responses": [
            {"peak_level_m": 3.0}]}}}))
        got = fit.load_gauges(p)
        assert list(got["a"]) == [1.0, 2.0] and list(got["b"]) == [3.0]


_SYNTHETIC = fit.synthetic_series


def _series():
    return _SYNTHETIC(ONE_SERIES)
