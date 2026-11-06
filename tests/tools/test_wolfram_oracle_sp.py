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

"""Tests for tools.wolfram_oracle.spatial, the SP-001 benchmark.

The reference is checked against cases it does not compute from -- a degree on the
equator, IDW's threshold and its symmetric case, a point past a segment's end -- and the
gate runs the production code against it: every claim of v2.0 holds. Wolfram is stood in for by the answers the
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

    def test_the_correlation_at_111_km_a_degree(self):
        pts = ((51.5, -0.1), (51.5, -0.1), (51.5, 0.0))
        corr = ref.correlation_degrees(pts, 2000, 0.6)
        assert corr[(0, 1)] == mp.mpf(0.6)
        assert float(corr[(0, 2)]) == pytest.approx(0.6 * math.exp(-0.1 * 111 / 2), rel=1e-12)

    def test_nearest_and_the_segment(self):
        assert ref.nearest((51.5, -0.1), ((51.51, -0.1), (51.5, -0.088))) == 1
        d, t = ref.on_segment((51.5, 0.2), (51.5, -1.0), (51.5, 0.0))
        assert t == 1 and float(d) == pytest.approx(float(ref.haversine(51.5, 0.2, 51.5, 0.0)))
        d, t = ref.on_segment((51.5, -0.5), (51.5, -1.0), (51.5, 0.0))
        assert float(d) < 1e-20 and float(t) == pytest.approx(0.5)
        assert ref.on_polyline((51.5, -0.5), ((51.5, -2.0), (51.5, -1.0), (51.5, 0.0)))[1] == 1


class TestTheCode:
    def test_the_code_computes_the_document(self, sp):
        with mp.workdps(50):
            det = cases.deterministic(sp)
        assert det["haversine_m"] < 1e-6 and det["corr_diagonal"] == 0
        assert all(det[k] <= ORACLE_SP_CODE_TOL for k in ("idw", "wse", "corr_degrees"))

    def test_the_projection(self, sp):
        with mp.workdps(50):
            p = cases.projection(sp)
        assert p["near"] < 1e-4 < p["far"] * 10 and p["polyline_segments_off"] == 0 and p["cases"] == 84
        assert p["table4"][-1] == (200, "0.0195", "38.953")

    def test_the_index_names_the_nearest_gauge(self, sp, quick):
        with mp.workdps(50):
            t = cases.tree(sp)
        assert (t["picked"], t["nearest"]) == (1, 1) and t["queries"] == 100 and t["wrong"] == 0
        assert t["distance_err"] < 1e-9


class TestClaims:
    @pytest.fixture(scope="class")
    def assessed(self, sp):
        with pytest.MonkeyPatch.context() as mp_, mp.workdps(50):
            mp_.setattr(cases, "ORACLE_SP_TREE_RANDOM", {**ORACLE_SP_TREE_RANDOM, "networks": 2})
            return claims.assess(sp, cases.projection(sp), cases.tree(sp), cases.deterministic(sp))

    def test_every_claim_of_v2_holds(self, assessed):
        assert {k for k, v in assessed.items() if not v["met"]} == set()
        assert sum(assessed[k]["of"] for k in ("t1", "t2", "t3", "t4")) == 27
        assert assessed["lineage"]["areas"] == ["gauge", "property", "seismic"]

    def test_the_sphere_waits_for_wolfram(self):
        assert claims.ellipsoid(None)["met"] is None
        got = claims.ellipsoid([-0.317, -0.06])
        assert got["met"] and got["worst"] == -0.317
        assert not claims.ellipsoid([-0.5])["met"]

    def test_a_caller_or_a_comparison_is_reported(self, assessed, monkeypatch):
        """Every search finds src/port/src/x/krige.py, which imports the module and calls everything."""
        monkeypatch.setattr(claims.subprocess, "run",
                            lambda *a, **k: type("R", (), {"stdout": "src/port/src/x/krige.py\n"})())
        assert claims.kriging() == {"files": ["src/port/src/x/krige.py"], "met": False}
        assert not claims.validation()["met"] and claims.unit_tests()["met"] and not claims.lineage()["met"]
        c = {**assessed, "kriging": claims.kriging(), "validation": claims.validation(), "lineage": claims.lineage()}
        table = latex._claims_table(c, claims.ellipsoid(None)).replace("\\_", "_")
        assert table.count("src/port/src/x/krige.py") == 3 and "pending" in table


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
        assert r"\bmOutcome}{all pass}" in macros and r"\bmClaimsMet}{13}" in macros
        assert "WGS84" in (tmp_path / "evidence_tables_claims.tex").read_text()
