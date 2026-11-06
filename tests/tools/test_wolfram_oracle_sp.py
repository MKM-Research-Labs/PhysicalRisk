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
"""Tests for tools.wolfram_oracle.spatial, the SP-001 benchmark.

The reference is checked against cases it does not compute from -- a degree on the
equator, IDW's threshold and its symmetric case, a point past a segment's end -- and the
gate runs the production code against it. Wolfram is stood in for by the answers the
filed run recorded, and the random spatial-index networks are cut from twenty to two.
"""

import json
import math
import shutil

import mpmath as mp
import pytest
from tools.wolfram_oracle import __main__ as cli
from tools.wolfram_oracle.spatial import cases, claims, latex
from tools.wolfram_oracle.spatial import reference as ref
from tools.wolfram_oracle.spatial import run as runner
from tools.wolfram_oracle.spatial import wolfram as oracle

from config import config
from config.models import ORACLE_SP_CODE_TOL, ORACLE_SP_OUT_DIR, ORACLE_SP_TREE_RANDOM

RECORDED = config.get_project_root() / ORACLE_SP_OUT_DIR / "spatial_wolfram.json"
# v1.0's claims that the benchmark finds do not hold.
NOT_MET = {"t2_label", "configurable", "tree", "correlation", "outputs", "lineage", "unit_tests", "validation",
           "kriging"}


@pytest.fixture(scope="module")
def sp():
    return cases.load()


@pytest.fixture
def quick(monkeypatch):
    monkeypatch.setattr(cases, "ORACLE_SP_TREE_RANDOM", {**ORACLE_SP_TREE_RANDOM, "networks": 2})


def _recorded():
    return {r["id"]: r["value"] for r in json.loads(RECORDED.read_text())["results"]}


class TestReference:
    def test_a_degree_on_the_equator(self):
        with mp.workdps(30):
            assert ref.haversine(0, 0, 0, 1) == pytest.approx(6371000 * math.pi / 180, rel=1e-15)

    def test_idw_threshold_and_symmetry(self):
        assert ref.idw([(0.5, 7.0), (10, 3.0)]) == 7
        assert ref.idw([(100, 9.0), (100, 11.0)]) == 10
        assert float(ref.idw([(1, 4.0), (3, 6.0)], p=1)) == pytest.approx(4.5)

    def test_the_wse_is_depth_plus_elevation(self):
        g = ((51.5, -0.1, 3.0, 1.25),)
        assert ref.wse((51.5, -0.1), g) == 4.25

    def test_the_two_correlations(self):
        pts = ((51.5, -0.1), (51.5, -0.1), (51.5, 0.0))
        assert ref.correlation(pts, 2000, 0.6)[(0, 1)] == mp.mpf(0.6)
        deg = ref.correlation_degrees(pts, 2000, 0.6)[(0, 2)]
        assert float(deg) == pytest.approx(0.6 * math.exp(-0.1 * 111 / 2), rel=1e-12)

    def test_nearest_and_the_segment(self):
        assert ref.nearest((51.5, -0.1), ((51.51, -0.1), (51.5, -0.088))) == 1
        d, t = ref.on_segment((51.5, 0.2), (51.5, -1.0), (51.5, 0.0))
        assert t == 1 and float(d) == pytest.approx(float(ref.haversine(51.5, 0.2, 51.5, 0.0)))
        d, t = ref.on_segment((51.5, -0.5), (51.5, -1.0), (51.5, 0.0))
        assert float(d) < 1e-20 and float(t) == pytest.approx(0.5)
        assert ref.on_polyline((51.5, -0.5), ((51.5, -2.0), (51.5, -1.0), (51.5, 0.0)))[1] == 1


class TestTheCode:
    def test_the_code_computes_the_documents_distance_and_idw(self, sp):
        with mp.workdps(50):
            det = cases.deterministic(sp)
        assert det["haversine_m"] < 1e-6 and det["corr_diagonal"] == 0
        assert all(det[k] <= ORACLE_SP_CODE_TOL for k in ("idw", "wse", "corr_degrees"))
        assert det["corr_doc"] > 0.5

    def test_the_projection(self, sp):
        with mp.workdps(50):
            p = cases.projection(sp)
        assert p["near"] < 1e-4 < p["far"] * 10 and p["polyline_segments_off"] == 0 and p["cases"] == 84

    def test_the_spatial_index_picks_the_wrong_gauge(self, sp, quick):
        with mp.workdps(50):
            t = cases.tree(sp)
        assert (t["picked"], t["nearest"]) == (0, 1) and t["queries"] == 100 and t["wrong"] > 0


class TestClaims:
    @pytest.fixture(scope="class")
    def assessed(self, sp):
        with pytest.MonkeyPatch.context() as mp_, mp.workdps(50):
            mp_.setattr(cases, "ORACLE_SP_TREE_RANDOM", {**ORACLE_SP_TREE_RANDOM, "networks": 2})
            return claims.assess(sp, cases.projection(sp), cases.tree(sp), cases.deterministic(sp))

    def test_what_v1_gets_wrong(self, assessed):
        assert {k for k, v in assessed.items() if not v["met"]} == NOT_MET
        assert sum(assessed[k]["of"] for k in ("t1", "t2", "t3")) == 26
        assert assessed["lineage"]["users"]["haversine_distance"]

    def test_the_format(self):
        assert claims.fmt(0.5) == "0.5000" and claims.fmt(1.0) == "1.00" and claims.fmt(12.438) == "12.4"

    def test_the_sphere_waits_for_wolfram(self):
        assert claims.ellipsoid(None)["sufficient"] is None
        got = claims.ellipsoid([-0.317, -0.06])
        assert got["sufficient"] and not got["exact"] and got["worst"] == -0.317

    def test_evidence_found_is_reported(self, assessed, monkeypatch):
        monkeypatch.setattr(claims.subprocess, "run", lambda *a, **k: type("R", (), {"stdout": "src/x/krige.py\n"})())
        assert claims.kriging() == {"files": ["src/x/krige.py"], "met": True}
        assert claims.validation()["met"] and claims.unit_tests()["met"]
        c = {**assessed, "kriging": claims.kriging()}
        table = latex._claims_table(c, claims.ellipsoid(None))
        assert "src/x/krige.py" in table.replace("\\_", "_") and "pending" in table


class TestRun:
    def test_wolfram_agrees_with_the_reference(self, sp):
        worst, pct = oracle.judge(sp, _recorded())
        assert worst < 1e-25 and 0.3 < max(abs(p) for p in pct) < 0.33

    def test_a_run_without_and_with_wolfram(self, tmp_path, quick):
        assert cli.main(["sp001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        assert "Wolfram pending" in (tmp_path / "evidence_tables_macros.tex").read_text()
        shutil.copy(RECORDED, tmp_path / RECORDED.name)
        assert runner.main(["--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        macros = (tmp_path / "evidence_tables_macros.tex").read_text()
        assert r"\bmOutcome}{1 fail}" in macros and r"\bmClaimsMet}{5}" in macros
        assert "WGS84" in (tmp_path / "evidence_tables_claims.tex").read_text()
