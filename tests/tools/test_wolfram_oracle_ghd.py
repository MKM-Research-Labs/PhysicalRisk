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
"""Tests for tools.wolfram_oracle.gaugehd, the GHD-001 benchmark.

The closed forms are checked against quadrature they do not use, and the model gate
then generates every gauge, so a change to the synthetic generator that breaks its
documented process fails here. Wolfram is stood in for by a file.
"""

import re

import mpmath as mp
import numpy as np
import pytest
from tools.wolfram_oracle import __main__ as cli
from tools.wolfram_oracle._wl import save_wolfram
from tools.wolfram_oracle.gaugehd import cases, claims, exact

from config.models import ORACLE_GHD_TABLE1, ORACLE_GHD_Z_LIMIT


@pytest.fixture(scope="module")
def run():
    return cases.run(cases.load())


def _quad(alpha, beta, r1, r2, gamma):
    def q(r, v):
        return mp.erfc((alpha - beta * r - gamma * v) / mp.sqrt(2)) / 2

    if gamma == 0:
        return mp.quad(lambda r: q(r, 0), [r1, r2]) / (r2 - r1)
    return mp.quad(q, [r1, r2], [-1, 1]) / (2 * (r2 - r1))


class TestReference:
    @pytest.mark.parametrize("alpha, beta, gamma", [(2.0, 0.7, 0.4), (9.0, 1.3, 0.0), (-1.0, 0.2, 2.5)])
    def test_the_tail_over_two_uniforms_by_quadrature(self, alpha, beta, gamma):
        with mp.workdps(30):
            want = _quad(alpha, beta, 1.0, 2.5, gamma)
        assert float(exact.tail_uniforms(alpha, beta, 1.0, 2.5, gamma)) == pytest.approx(float(want), rel=1e-9)

    @pytest.mark.parametrize("gamma", [0.0, 0.8])
    def test_a_point_flood_level(self, gamma):
        with mp.workdps(30):
            want = mp.quad(lambda v: mp.erfc((1.5 - gamma * v) / mp.sqrt(2)) / 2, [-1, 1]) / 2 if gamma \
                else mp.erfc(1.5 / mp.sqrt(2)) / 2
        assert float(exact.tail_uniforms(1.5, 0.0, 0.0, 0.0, gamma)) == pytest.approx(float(want), rel=1e-12)

    def test_g_and_h_are_the_iterated_tails(self):
        with mp.workdps(30):
            g = mp.quad(lambda x: mp.erfc(x / mp.sqrt(2)) / 2, [0.7, mp.inf])
            h = mp.quad(lambda y: mp.quad(lambda x: mp.erfc(x / mp.sqrt(2)) / 2, [y, mp.inf]), [0.7, mp.inf])
        assert float(exact.g_int(0.7)) == pytest.approx(float(g), rel=1e-12)
        assert float(exact.h_int(0.7)) == pytest.approx(float(h), rel=1e-10)

    def test_the_flood_free_lag1_is_phi_without_a_cycle(self, monkeypatch):
        monkeypatch.setitem(ORACLE_GHD_TABLE1, "Flat", (0.1, 0.0, 0.0, 0.85))
        assert exact.lag1_flood_free("Flat", np.arange(1, 36501) % 365 + 1) == pytest.approx(0.85, rel=1e-4)


class TestModel:
    def test_every_statistic_within_sampling_error(self, run):
        rows, _ = run
        for k in cases.STATS:
            assert max(abs(r[f"{k}_z"]) for r in rows) <= ORACLE_GHD_Z_LIMIT

    def test_replications_across_midnight_are_refused(self):
        class Syn:
            @staticmethod
            def generate_synthetic_timeseries(gauge, years, seed):
                return [{"date": f"2026-01-0{1 + seed % 2}", "level_meters": 1.0}]
        with pytest.raises(RuntimeError, match="midnight"):
            cases.run(Syn)


class TestClaims:
    def test_the_documents_claims(self, run):
        lag1, alert, spikes, seas, sev, rep, lag7, phase, below = claims.assess(run[0])
        assert not lag1["met"] and lag1["flood_free"] > 0.95
        assert not alert["met"] and alert["exact"][0] > 12
        assert not spikes["met"] and not sev["met"] and sev["factor"] == 10
        assert seas["met"] and lag7["met"] and below["met"]
        assert not rep["met"] and phase["met"] is None and phase["jump_days"] == pytest.approx(9.8)


class TestRun:
    def test_a_run_without_and_with_wolfram(self, tmp_path, run, monkeypatch):
        monkeypatch.setattr(cases, "run", lambda syn: run)
        assert cli.main(["ghd001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        assert "Wolfram pending" in (tmp_path / "evidence_tables_macros.tex").read_text()
        wanted = re.findall(r'<\|"id" -> "([^"]+)"', (tmp_path / "gaugehd.wl").read_text())
        ref = cases.reference_points()
        save_wolfram(tmp_path / "gaugehd_wolfram.json", "15.0 (file)",
                     {i: mp.nstr(mp.mpf(ref[i]), 17).replace("e", "*^") for i in wanted})
        assert cli.main(["ghd001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        macros = (tmp_path / "evidence_tables_macros.tex").read_text()
        assert "15.0 (file)" in macros and r"\bmOutcome}{all pass}" in macros
