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
"""Tests for tools.wolfram_oracle.depthdamage, the DD-001 benchmark.

The reference is checked against cases it does not compute from -- the clipped
expectation by quadrature, a degree of the equator, the curve at its control points
-- and the gate then runs every family against the production code, so a change to
the flood risk functions that breaks their documented behaviour fails here. Wolfram
is stood in for by a file.
"""

import re

import mpmath as mp
import pytest
from tools.wolfram_oracle import __main__ as cli
from tools.wolfram_oracle._wl import save_wolfram
from tools.wolfram_oracle.depthdamage import cases, claims
from tools.wolfram_oracle.depthdamage import reference as ref
from tools.wolfram_oracle.depthdamage import run as runner
from tools.wolfram_oracle.depthdamage import wolfram as oracle

from config.damage import DAMAGE_POINTS, DD_POLY_COEFFS, DEPTH_POINTS
from config.models import ORACLE_DD_CODE_TOL, ORACLE_DD_EARTH_R_M, ORACLE_DD_Z_LIMIT


@pytest.fixture(scope="module")
def model():
    return cases.load()


@pytest.fixture(scope="module")
def evaluated(model):
    return runner.evaluate(model)


class TestReference:
    def test_the_curve_passes_through_table_1(self):
        assert ref.table1_matches_config()
        with mp.workdps(30):
            for d, v in zip(DEPTH_POINTS, DAMAGE_POINTS):
                assert float(ref.damage(d)) == pytest.approx(v, abs=1e-15)
            assert ref.damage(-1) == 0 and ref.damage(9) == 1

    @pytest.mark.parametrize("delta", [0.0, 0.2, 0.7, 0.95, 1.0])
    def test_the_clipped_expectation_by_quadrature(self, delta):
        def f(z):
            return min(max(delta * (1 + mp.mpf("0.2") * z), 0), 1) * mp.npdf(z)

        with mp.workdps(30):
            # split at both kinks of the clip: z = -5 and z = (1/delta - 1)/0.2
            want = mp.quad(f, sorted({-mp.inf, -5, (1 / mp.mpf(delta) - 1) * 5, mp.inf})) if delta else 0
            assert float(ref.expected_clipped(delta)) == pytest.approx(float(want), rel=1e-20, abs=1e-30)

    def test_a_degree_of_the_equator(self):
        with mp.workdps(30):
            assert float(ref.haversine(0, 0, 0, 1)) == pytest.approx(ORACLE_DD_EARTH_R_M * float(mp.pi) / 180, rel=1e-15)

    def test_no_velocity_is_an_infinite_travel_time(self):
        assert ref.travel_hours(1000, 0, 0.005, 0.04) == mp.inf and ref.manning(1, 0.005, -0.1) == 0

    def test_the_slope_floor(self):
        assert ref.slope(5, 3, 0) == ref.slope(10, 10, 100) == mp.mpf("0.001")


class TestModel:
    def test_every_family_agrees(self, model, evaluated):
        r, _ = evaluated
        for k in ("damage", "manning", "travel", "slope", "attenuation", "idw"):
            assert r["det"][k] <= ORACLE_DD_CODE_TOL, k
        assert r["det"]["travel_inf"] and r["det"]["haversine_m"] < 1e-6
        assert r["corr_err"] <= ORACLE_DD_CODE_TOL and r["hydro_err"] <= 1e-4
        assert cases.hydrographs(model) <= 1e-4

    def test_the_monte_carlo_mean_is_the_exact_expected_loss(self, evaluated):
        r, _ = evaluated
        assert abs(r["mc"]["z"]) <= ORACLE_DD_Z_LIMIT and r["mc"]["es99_err"] <= ORACLE_DD_CODE_TOL


class TestClaims:
    def test_the_documents_claims_all_hold(self, evaluated):
        _, c = evaluated
        assert all(v["met"] for v in c.values()), [k for k, v in c.items() if not v["met"]]
        assert c["ell"]["code"] == 10_000 and c["t7"]["of"] == 7 and c["deg"]["error"] > 0.6

    def test_the_generators_number_format(self):
        assert claims.printed(0.89095, 3) == "0.8910" and claims.printed(1.0, 4) == "1.00"

    def test_a_changed_default_would_fail(self, model, monkeypatch):
        monkeypatch.setattr(claims, "ORACLE_DD_DOC_ATTENUATION_M", 2000.0)
        assert claims.assess(model, 0.0, 1.0)["ell"]["met"] is False

    def test_the_draws_are_by_svd(self):
        assert claims.draws_by_svd()


def _answers():
    with mp.workdps(50):
        out = {i: mp.nstr(r, 35).replace("e", "*^") for i, _, r in oracle.items() if r is not None}
    out["poly/ls"] = "{" + ", ".join(repr(c) for c in DD_POLY_COEFFS) + "}"
    out["ew/0.1"] = "6944.051124228148"
    return out


class TestRun:
    def test_a_run_without_and_with_wolfram(self, tmp_path, evaluated, monkeypatch):
        monkeypatch.setattr(runner, "evaluate", lambda m: evaluated)
        assert cli.main(["dd001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        assert "Wolfram pending" in (tmp_path / "evidence_tables_macros.tex").read_text()
        wanted = re.findall(r'<\|"id" -> "([^"]+)"', (tmp_path / "depthdamage.wl").read_text())
        answers = _answers()
        save_wolfram(tmp_path / "depthdamage_wolfram.json", "15.0 (file)", {i: answers[i] for i in wanted})
        assert cli.main(["dd001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        macros = (tmp_path / "evidence_tables_macros.tex").read_text()
        assert "15.0 (file)" in macros and r"\bmOutcome}{all pass}" in macros
        assert "6{,}944" in (tmp_path / "evidence_tables_claims.tex").read_text()
