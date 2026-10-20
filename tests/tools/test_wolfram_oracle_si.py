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

"""Tests for tools.wolfram_oracle.intensity, the SI-001 benchmark.

The reference is checked on its own terms -- continuity at u, the quantile undoing
the exceedance, the clamp mass agreeing with the model's own quantile, the jitter
integral at known values -- so it is not merely agreeing with itself. The model
gate then runs the full grid, so a change to the intensity code that breaks its
documented formulae fails here. Wolfram is stood in for by a results file.
"""

import importlib
import re

import mpmath as mp
import pytest

from config.models import ORACLE_SI_EXC_TOL, ORACLE_SI_INV_TOL, ORACLE_SI_PACKAGE
from tools.wolfram_oracle import __main__ as cli
from tools.wolfram_oracle._wl import save_wolfram, wl_number
from tools.wolfram_oracle.intensity import claims, distribution as dist

PKG = importlib.import_module(ORACLE_SI_PACKAGE)
BASELINE = PKG.SCENARIO_FAMILIES["baseline"]


@pytest.fixture(scope="module")
def rows():
    return dist.run(PKG.IntensityDistribution, PKG.SCENARIO_FAMILIES)


@pytest.fixture(scope="module")
def ack_rows():
    return dist.acklam(PKG.IntensityDistribution)


class TestReference:
    def test_exceedance_is_continuous_at_the_threshold(self):
        u = BASELINE.tail_threshold
        assert dist.exceedance_ref(BASELINE, u) == dist.exceedance_ref(BASELINE, u + 1e-30)

    def test_quantile_undoes_the_exceedance(self):
        for x in (20.0, 45.0, 70.0, 95.0):
            p = dist.exceedance_ref(BASELINE, x)
            assert dist.quantile_ref(BASELINE, p) == pytest.approx(x, rel=1e-30)

    def test_cap_mass_matches_the_models_own_quantile(self):
        _, m_max = dist.cap_masses(BASELINE)
        d = PKG.IntensityDistribution(params=BASELINE)
        below, above = float(m_max) * (1 - 1e-9), float(m_max) * (1 + 1e-9)
        assert d.inverse_exceedance(below) == BASELINE.max_intensity
        assert d.inverse_exceedance(above) < BASELINE.max_intensity

    def test_jitter_integral_away_from_the_bounds(self):
        y, tau = mp.mpf(50), mp.mpf("0.5")
        assert claims._clamped_jitter(y, 10, 100, tau, 1) == pytest.approx(y, rel=1e-30)
        assert claims._clamped_jitter(y, 10, 100, tau, 2) == pytest.approx(y * y + tau * tau, rel=1e-30)

    def test_accuracy_marked_zero_parses(self):
        assert wl_number("SetAccuracy[0, 59.69897000433602]") == 0


class TestModel:
    def test_exceedance_and_return_periods_match(self, rows):
        assert max(r["rel_err"] for r in rows if r["kind"] == "exc") <= ORACLE_SI_EXC_TOL
        assert max(r["rel_err"] for r in rows if r["kind"] == "rp") <= ORACLE_SI_EXC_TOL

    def test_quantile_carries_only_acklams_error(self, rows):
        assert max(r["rel_err"] for r in rows if r["kind"] == "inv") <= ORACLE_SI_INV_TOL

    def test_acklam_holds_in_relative_terms(self, ack_rows):
        assert max(r["rel_err"] for r in ack_rows) <= 1.2e-9

    def test_wolfram_items_avoid_the_machine_precision_survival_function(self, rows, ack_rows):
        items = dist.wl_items(rows, ack_rows, PKG.SCENARIO_FAMILIES)
        assert len(items) == len(rows) + len(ack_rows)
        assert not any("SurvivalFunction" in e for _, e in items)


class TestClaims:
    def test_the_claims_as_found(self, ack_rows):
        scenarios = claims.by_scenario(PKG.IntensityDistribution, PKG.SCENARIO_FAMILIES)
        cont, pdf, ack, mass, rp, jit = claims.assess(scenarios, ack_rows)
        assert cont["met"] and jit["met"]
        assert pdf["met"] is False and ack["met"] is False and mass["met"] is False
        assert rp["met"] is None and rp["worst"] < rp["high"]


class TestRun:
    def test_a_run_without_and_with_wolfram(self, tmp_path, rows, ack_rows):
        assert cli.main(["si001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        assert "Wolfram pending" in (tmp_path / "evidence_tables_macros.tex").read_text()
        answers = {r["id"]: r["ref"].replace("e", "*^") for r in rows + ack_rows}
        for s in claims.by_scenario(PKG.IntensityDistribution, PKG.SCENARIO_FAMILIES):
            answers[f"{s['scenario']}/m1"] = repr(s["mean"])
            answers[f"{s['scenario']}/m2"] = repr(s["sd"] ** 2 + s["mean"] ** 2)
        ids = re.findall(r'<\|"id" -> "([^"]+)"', (tmp_path / "intensity.wl").read_text())
        save_wolfram(tmp_path / "intensity_wolfram.json", "15.0 (file)", {i: answers[i] for i in ids})
        assert cli.main(["si001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        macros = (tmp_path / "evidence_tables_macros.tex").read_text()
        assert r"\bmOutcome}{all pass}" in macros and "15.0 (file)" in macros
        assert "wolfram_vs_ref" in (tmp_path / "intensity.csv").read_text()
