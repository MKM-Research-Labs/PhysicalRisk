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
"""Tests for tools.wolfram_oracle.stormgauge, the SG-001 benchmark.

The reference is checked against cases it does not compute from -- a degree on the
equator, the kernels' boundaries, a held intensity reaching its target -- and the gate
runs the production code against it. Wolfram is stood in for by the answers the filed
run recorded, and the 780-run response family is cut to one duration and setting.
"""

import json
import math
import shutil

import mpmath as mp
import pytest
from tools.wolfram_oracle import __main__ as cli
from tools.wolfram_oracle.stormgauge import cases, claims, latex
from tools.wolfram_oracle.stormgauge import reference as ref
from tools.wolfram_oracle.stormgauge import run as runner
from tools.wolfram_oracle.stormgauge import wolfram as oracle

from config import config
from config.models import ORACLE_SG_CODE_TOL, ORACLE_SG_OUT_DIR, ORACLE_SG_SETTINGS, ORACLE_SG_TIMING

RECORDED = config.get_project_root() / ORACLE_SG_OUT_DIR / "stormgauge_wolfram.json"
# Timings depend on the machine, and on coverage's tracing; the tests do not.
SLACK = {**ORACLE_SG_TIMING, "factor": 1e6}


@pytest.fixture(scope="module")
def model():
    return cases.load()


@pytest.fixture
def quick(monkeypatch):
    monkeypatch.setattr(cases, "ORACLE_SG_DURATIONS", (23.7,))
    monkeypatch.setattr(cases, "ORACLE_SG_SETTINGS", ORACLE_SG_SETTINGS[2:3])
    monkeypatch.setattr(claims, "ORACLE_SG_TIMING", SLACK)


def _recorded():
    return {r["id"]: r["value"] for r in json.loads(RECORDED.read_text())["results"]}


class TestReference:
    def test_a_degree_on_the_equator(self):
        with mp.workdps(30):
            assert ref.haversine(0, 0, 1, 0) == pytest.approx(6371 * math.pi / 180, rel=1e-15)

    def test_the_kernels_boundaries(self):
        assert all(ref.kernel(0, 40, k, 0.5) == 1 and ref.kernel(-3, 40, k, 0.5) == 1 for k in ref.KERNELS)
        assert ref.kernel(20, 40, "linear", 0.5) == 0 and ref.kernel(40, 40, "linear", 0.5) == 0
        assert float(ref.kernel(20, 40, "gaussian", 0.5)) == pytest.approx(math.exp(-0.5))

    def test_the_storm_is_held_to_its_track_and_its_duration(self):
        track = cases.IRREGULAR
        assert ref.position(track, 0) == ref.position(track, 2.0)
        assert ref.position(track, 99) == ref.position(track, 20.0)
        assert ref.intensity_at(track, 23.9, -0.2, 51.6, 55, "exponential", 0.7, 23.7) == 0

    def test_the_power_law_and_its_default_high(self):
        g = cases.gauge()
        assert ref.contribution(0, g) == 0 and ref.contribution(-1, g) == 0
        assert float(ref.contribution(100, g)) == pytest.approx(1.1 * 1.58 * 4 - 0.35 * 4)

    def test_a_held_intensity_reaches_its_target(self):
        g = cases.gauge()
        track = [(g["longitude"], g["latitude"], 0.0, 60.0), (g["longitude"], g["latitude"], 24.0, 60.0)]
        times, ints, levels = ref.response(track, 24.0, g, 40.0, "gaussian", 0.5, 0.5, 2.0, 1.0, 12.0)
        assert len(times) == int((24 + 5 * 12) / 0.5) + 1
        assert float(max(levels)) == pytest.approx(float(g["base_level"] + ref.contribution(60, g)), rel=1e-9)
        st = ref.statistics(times, ints, levels, g, 0.5)
        assert st["peak_intensity"] == 60 and st["duration_alert"] > 0


class TestTheCode:
    def test_the_code_computes_the_document(self, model):
        with mp.workdps(50):
            det = cases.deterministic(model)
        assert det["haversine_m"] < 1e-6
        assert all(det[k] <= ORACLE_SG_CODE_TOL for k in ("kernel", "intensity", "level"))

    def test_an_underflowing_kernel_is_judged_absolutely(self):
        with mp.workdps(50):
            assert cases._err(0.0, mp.mpf("1e-500")) < 1e-300
            assert cases._err(0.5, mp.mpf("0.25")) == 1.0

    def test_the_response_and_its_recession(self, model, quick):
        with mp.workdps(50):
            r = cases.responses(model)
        assert r["cases"] == 13 * 5 and r["mismatches"] == 0
        assert r["level_m"] < 1e-9 and r["stats"] <= ORACLE_SG_CODE_TOL


class TestClaims:
    @pytest.fixture(scope="class")
    def assessed(self, model):
        with pytest.MonkeyPatch.context() as mp_:
            mp_.setattr(claims, "ORACLE_SG_TIMING", SLACK)
            return claims.assess(model)

    def test_every_claim_of_v2_holds(self, assessed):
        assert {k for k, v in assessed.items() if not v["met"]} == set()
        assert sum(assessed[k]["of"] for k in ("gauss", "t4", "t5", "t6", "t7", "t8", "t9")) == 169

    def test_the_formats(self):
        assert claims.printed(1.0, 4) == "1.00" and claims.printed(0.0, 4) == "0.0000"
        assert claims.to_places(0.13533, "0.135") == "0.135" and claims.to_places(0.0, "0.0") == "0.0"

    def test_the_sphere_waits_for_wolfram(self):
        assert claims.ellipsoid(None)["met"] is None
        got = claims.ellipsoid([-0.317, -0.063, -0.229, -0.194, -0.284, -0.259])
        assert got["met"] and got["east_west"] == -0.317
        assert not claims.ellipsoid([-0.5, -0.063])["met"]

    def test_a_storm_band_never_reached(self, model, monkeypatch):
        dull = cases.gauge(sensitivity=0.1)
        monkeypatch.setattr(cases, "gauge", lambda *a, **k: dull)
        assert claims.storm_targets(model) == {"alert": None, "warning": None, "severe": None}

    def test_a_caller_is_reported(self, model, assessed, monkeypatch):
        monkeypatch.setattr(claims.subprocess, "run", lambda *a, **k: type("R", (), {"stdout": "src/x/use.py\n"})())
        assert claims.importers() == ["src/x/use.py"]
        c = {**assessed, "lineage": {"importers": ["src/x/use.py"], "met": False}}
        table = latex._claims_table(c, claims.ellipsoid(None))
        assert "src/x/use.py" in table.replace("\\_", "_") and "pending" in table


class TestRun:
    def test_wolfram_agrees_with_the_reference(self, model):
        worst, pct = oracle.judge(model, _recorded())
        assert worst < 1e-25 and max(abs(p) for p in pct) < 0.33

    def test_a_run_without_and_with_wolfram(self, tmp_path, quick):
        assert cli.main(["sg001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        assert "Wolfram pending" in (tmp_path / "evidence_tables_macros.tex").read_text()
        shutil.copy(RECORDED, tmp_path / RECORDED.name)
        assert runner.main(["--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        macros = (tmp_path / "evidence_tables_macros.tex").read_text()
        assert r"\bmOutcome}{all pass}" in macros and r"\bmClaimsMet}{16}" in macros
        assert "east--west" in (tmp_path / "evidence_tables_claims.tex").read_text()
