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

"""Tests for tools.wolfram_oracle.delta, the DE-001 benchmark.

Benchmark v0.2: the engine after its MTM and floor fixes, against model document
v1.1. The reference's gradient is checked against the flat-curve closed form it does
not use, and its annuity against the document's own worked example, so it is not
merely agreeing with itself. The model gate then runs the full grid, so a change
to the delta engine that breaks its documented formulae fails here. Wolfram is
stood in for by a results file.
"""

import importlib
import re

import mpmath as mp
import pytest

from config.models import ORACLE_DE_ANNUITY_TOL, ORACLE_DE_PACKAGE, ORACLE_DE_ROUNDING
from config.port import BUMP_1BP
from tools.wolfram_oracle import __main__ as cli
from tools.wolfram_oracle._wl import save_wolfram, wl_precise
from tools.wolfram_oracle.delta import claims, sensitivity as sens

PRICER = importlib.import_module(ORACLE_DE_PACKAGE)


@pytest.fixture(scope="module")
def rows():
    return sens.run(PRICER)


class TestReference:
    def test_gradient_matches_the_flat_curve_closed_form(self):
        h, dt, r = mp.mpf("0.02"), mp.mpf(1) / 4, mp.mpf("0.03")
        lam = -mp.log(1 - h)
        closed = 1e4 * mp.exp(lam * dt) * mp.exp(r * dt / 2) / (1 - h)
        assert sens.gradient(0.02, 5, None) == pytest.approx(closed, rel=1e-25)

    def test_gradient_survives_a_short_binary_rate(self):
        assert sens.gradient(0.5, 5, None) > 0

    def test_the_documents_worked_annuity(self):
        assert float(sens.legs(0.02, 3, None, shift=0.01)[1]) == pytest.approx(2.724083983666923, rel=1e-15)


class TestModel:
    def test_annuity_and_rounded_outputs_match(self, rows):
        assert max(r["annuity_rel_err"] for r in rows) <= ORACLE_DE_ANNUITY_TOL
        for key in ORACLE_DE_ROUNDING:
            assert max(r[f"{key}_err"] for r in rows) <= ORACLE_DE_ROUNDING[key] / 2

    def test_the_floor_flag_matches_the_reference(self, rows):
        assert all(r["at_floor_model"] == r["floored"] for r in rows)
        assert any(r["floored"] for r in rows)

    def test_wolfram_gets_the_bumped_double(self, rows):
        items = dict(sens.wl_items(rows))
        assert wl_precise(0.02 + BUMP_1BP) in items["flat/T=5/h=0.02/ds"]
        assert len(items) == 3 * len(rows)


class TestClaims:
    def test_document_v11_claims_hold(self, rows):
        fd, lin, ten, yld, hand, cvx, floor, basis = claims.assess(rows)
        assert all(c["met"] for c in (fd, lin, ten, yld, hand, floor, basis))
        assert cvx["met"] is None
        assert floor["model"] < 0.1 * floor["gradient"]
        assert floor["hazard"] == pytest.approx(floor["gradient"], abs=1e-4)


class TestRun:
    def test_a_run_without_and_with_wolfram(self, tmp_path, rows):
        assert cli.main(["de001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        assert "Wolfram pending" in (tmp_path / "evidence_tables_macros.tex").read_text()
        answers = {}
        for r in rows:
            answers[f"{r['id']}/annuity"] = r["annuity_ref"]
            answers[f"{r['id']}/ds"] = r["delta_spread_bps_ref"]
            answers[f"{r['id']}/gradient"] = r["gradient_bp"]
        answers["claim/hand_annuity"] = mp.nstr(sens.legs(0.02, 3, None, shift=0.01)[1], 30)
        answers["claim/fs01_base"] = mp.nstr(sens.fs01(0.02, 5, None, notional=1), 30)
        answers["claim/fs01_shifted"] = mp.nstr(sens.fs01(0.02, 5, None, shift=0.01, notional=1), 30)
        ids = re.findall(r'<\|"id" -> "([^"]+)"', (tmp_path / "delta.wl").read_text())
        save_wolfram(tmp_path / "delta_wolfram.json", "15.0 (file)",
                     {i: answers[i].replace("e", "*^") for i in ids})
        assert cli.main(["de001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        macros = (tmp_path / "evidence_tables_macros.tex").read_text()
        assert "15.0 (file)" in macros and r"\bmOutcome}{all pass}" in macros
