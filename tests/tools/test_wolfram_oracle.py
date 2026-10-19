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
here, not only in the filed PDF — and fake a Wolfram run to cover the read-back.
"""

import json
import re
from fractions import Fraction

import mpmath as mp
import pytest

from config.models import ORACLE_FIT_LL_TOL, ORACLE_REL_TOL
from tools.wolfram_oracle import __main__ as cli
from tools.wolfram_oracle import fit, return_levels
from tools.wolfram_oracle._model import load_gev_fitter, provenance
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
        assert wl_gev(100.0, 20.0, 0.5) == "MaxStableDistribution[100, 20, 1/2]"

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


def _fake_wolfram(out):
    """Answer every .wl item from the Python side, as a Wolfram run would."""
    rl = json.loads((out / "rl.json").read_text())
    for wl in out.glob("*.wl"):
        ids = re.findall(r'<\|"id" -> "([^"]+)"', wl.read_text())
        values = {i: rl[i] for i in ids}
        (out / f"{wl.stem}_wolfram.json").write_text(json.dumps({
            "wolfram_version": "14.3 (fake)",
            "results": [{"id": i, "value": v} for i, v in values.items()]}))


class TestCli:
    def test_run_without_then_with_wolfram(self, tmp_path, monkeypatch, gev_fitter):
        monkeypatch.setattr(fit, "synthetic_series", _series)
        assert cli.main(["--out", str(tmp_path)]) == 0
        assert (tmp_path / "gev_hazard_benchmark.pdf").stat().st_size > 0
        assert (tmp_path / "return_levels.csv").read_text().startswith("id,")
        rl = {r["id"] + "/level": r["level_ref"] for r in return_levels.run(gev_fitter)}
        rl.update({r["id"] + "/exc": r["exc_ref"].replace("e", "*^") for r in return_levels.run(gev_fitter)})
        for r in fit.run(gev_fitter, _series(), ONE_SERIES):
            rl[r["id"] + "/ll_at_model"] = r["ll_model"]
            rl[r["id"] + "/fit_xi_loc_scale"] = "{%r, %r, %r}" % tuple(r["indep_xi_loc_scale"])
            rl[r["id"] + "/ll_at_fit"] = r["ll_indep"]
        (tmp_path / "rl.json").write_text(json.dumps(rl))
        _fake_wolfram(tmp_path)
        assert cli.main(["--out", str(tmp_path)]) == 0
        assert "level_model_vs_wolfram" in (tmp_path / "return_levels.csv").read_text()

    def test_run_on_a_gauge_export(self, tmp_path):
        g = tmp_path / "g.json"
        g.write_text(json.dumps({"G1": [float(v) for v in _series()["n30_xi0.1"]]}))
        assert cli.main(["--out", str(tmp_path), "--gauges", str(g)]) == 0
        assert "G1/gev" in (tmp_path / "fit.csv").read_text()

    def test_stale_wolfram_output_is_ignored(self, tmp_path, capsys):
        write_wl(tmp_path / "x.wl", [("a", "1")], "x_wolfram.json")
        (tmp_path / "x_wolfram.json").write_text(json.dumps(
            {"wolfram_version": "v", "results": [{"id": "old", "value": "1"}]}))
        assert cli._wolfram(tmp_path, "x.wl", [("a", "1")]) == (None, None)
        assert "different inputs" in capsys.readouterr().err

    def test_provenance_names_the_code(self):
        prov = provenance()
        assert prov["file"] == "src/models/hazard/gev.py" and len(prov["sha256"]) == 64


_SYNTHETIC = fit.synthetic_series


def _series():
    return _SYNTHETIC(ONE_SERIES)
