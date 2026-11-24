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

"""Tests for tools.wolfram_oracle.sequence, the SS-001 benchmark.

The exact half of the reference is checked against probabilities worked by hand -- Table 9's
type mix, a cap that never binds, two uniforms compared -- and the replay against the
production code on a small batch. The gate pins which of v3.1's claims fail (none), so a
change to the code or the document shows up here. Wolfram is stood in for by the answers the filed
run recorded, and the batches are cut from 10,000 sequences to a few hundred.
"""

import json
import shutil
from fractions import Fraction as Q

import mpmath as mp
import pytest
from tools.wolfram_oracle import __main__ as cli
from tools.wolfram_oracle.sequence import cases, claims, evidence, latex
from tools.wolfram_oracle.sequence import reference as ref
from tools.wolfram_oracle.sequence import run as runner
from tools.wolfram_oracle.sequence import wolfram as oracle

from config import config
from config.models import ORACLE_SS_OUT_DIR, ORACLE_SS_WEIGHTS

RECORDED = config.get_project_root() / ORACLE_SS_OUT_DIR / "storm_sequence_wolfram.json"
FAILING = set()
# s7.2 states a pooled figure for 100 seeds of 10,000; the cut-down runs here (3 of 300)
# are compared with Table 9's 10,000 counts, so that one claim fails by construction.
QUICK_FAILING = FAILING | {"seeds"}


@pytest.fixture(scope="module")
def code():
    return cases.load()


@pytest.fixture
def quick(monkeypatch):
    for name, value in (("ORACLE_SS_COUNT", 300), ("ORACLE_SS_SEEDS", 3), ("ORACLE_SS_FORCED_COUNT", 3)):
        monkeypatch.setattr(cases, name, value)


def _recorded():
    return {r["id"]: r["value"] for r in json.loads(RECORDED.read_text())["results"]}


class TestReference:
    def test_the_rounded_law_sums_to_one(self):
        p = ref.rounded(6, 18, 36)
        assert sum(p.values()) == 1 and min(p) == 6 and max(p) == 36
        assert p[6] == Q(1, 2) ** 2 / (30 * 12)  # half an hour of the rising edge

    def test_table9_by_hand(self):
        types = ref.batch(ORACLE_SS_WEIGHTS)["types"]
        assert types["isolated"] == Q(4, 10) * Q(7, 10) + Q(35, 100) * Q(1, 2) + Q(2, 10) * Q(3, 10) + Q(5, 100) * Q(15, 100)
        assert sum(types.values()) == 1 and types["persistent"] == Q(119, 1000)

    def test_a_cap_that_never_binds(self):
        """v3.1: an isolated storm's cap is 156 h and the longest storm 80 h; a persistent
        sequence's cap is 34.5 h, which a catastrophic storm sometimes exceeds."""
        assert ref.capped("catastrophic", "isolated", 1) == 0 and ref.cap_of("persistent", 4) == Q(69, 2)
        assert 0 < ref.capped("catastrophic", "persistent", 4) < 1 and ref.gaps("catastrophic", "persistent", 4)[0] < 1

    def test_two_uniforms_compared(self):
        assert ref.subsequent_vs_first() == Q(17, 20)

    def test_compressed_is_a_share(self):
        assert Q(99, 100) < ref.compressed(ORACLE_SS_WEIGHTS, ("catastrophic",), "persistent") < 1
        # two moderate storms and the longest medium gap always fit: 2 x 20 + 72 = 112 <= 156
        assert ref.compressed(ORACLE_SS_WEIGHTS, ("moderate",), "doublet") == 0


class TestTheCode:
    def test_the_replay_matches_number_for_number(self, code, quick):
        with mp.workdps(50):
            rp = cases.replay(code)
        assert rp["sequences"] == 300 + 6 * 4 * 3 and rp["structure_off"] == 0 and rp["worst"] < 1e-12

    def test_a_structural_difference_is_caught(self, code):
        seq = code.batch.generate_event_set(1, seed=3)[0]
        r = ref.replay_batch(1, 3, ORACLE_SS_WEIGHTS, 35.0)[0]
        assert cases.compare(seq, {**r, "type": "tornado"}) == (True, 0.0)

    def test_monte_carlo_and_the_validator(self, code, quick):
        with mp.workdps(50):
            rp = cases.replay(code)
        mc = cases.monte_carlo(code, rp["batch"], ref.batch(ORACLE_SS_WEIGHTS))
        assert mc["seeds"] == 3 and mc["z_types"] < 4 and mc["z_counts"] < 4 and mc["z_pinned"] < 4
        v = cases.validator(code, rp["batch"])
        assert v["invalid"] == 0 and v["caught"] == v["faults"] == 5

    def test_z_at_the_edges(self):
        assert cases._z(5, 5, 1) == 0 and cases._z(4, 5, 1) == float("inf")


class TestEvidence:
    def test_the_classifier_summary(self, tmp_path, monkeypatch):
        monkeypatch.setattr(evidence.config, "get_classifiers_dir", lambda: tmp_path)
        assert evidence.classifier() == {"found": False, "met": False}
        gauges = [{"gauge_id": f"GAUGE-{i}"} for i in range(10)] + [{"gauge_id": "GAUGE-1aaf8b08"}]
        (tmp_path / "training_summary.json").write_text(json.dumps(
            {"num_trained": 11, "avg_auc_roc": 0.9842, "gauges": gauges}))
        assert evidence.classifier()["met"]

    def test_a_missing_module_or_name_is_reported(self, monkeypatch):
        monkeypatch.setattr(evidence, "ORACLE_SS_STATED_MODULES",
                            {"gone.py": (), "utils/validation.py": ("validate_sequence", "no_such_name")})
        assert evidence.modules() == {"missing": ["gone.py", "utils/validation.py:no_such_name"], "met": False}

    def test_a_failed_override_run_is_reported(self, monkeypatch):
        monkeypatch.setattr(evidence.subprocess, "run",
                            lambda *a, **k: type("R", (), {"returncode": 1, "stderr": "x\nBoom", "stdout": ""})())
        assert evidence._override_run("after") == {"error": "Boom"}
        assert "failed" in latex._override({"callers": [], "runs": {"after": {"error": "Boom"}}})
        neither = {"probability": False, "durations": False}
        text = latex._override({"callers": ["c.py"], "runs": {"after": {"probability": True, "durations": False},
                                                             "before": neither}})
        assert "the probability only" in text and "neither" in text


class TestRun:
    def test_wolfram_agrees_with_the_reference(self):
        assert oracle.judge(_recorded()) < 1e-25
        assert len(oracle.items()) == 33

    def test_a_run_without_and_with_wolfram(self, tmp_path, quick):
        assert cli.main(["ss001", "--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        assert "Wolfram pending" in (tmp_path / "evidence_tables_macros.tex").read_text()
        shutil.copy(RECORDED, tmp_path / RECORDED.name)
        assert runner.main(["--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        macros = (tmp_path / "evidence_tables_macros.tex").read_text()
        assert r"\bmOutcome}{all pass}" in macros and r"\bmClaimsFailed}{1}" in macros
        assert "storm\\_control.json" in (tmp_path / "evidence_tables_claims.tex").read_text()


class TestClaims:
    def test_which_claims_of_v3_1_fail(self, code, quick):
        with mp.workdps(50):
            rp = cases.replay(code)
        exact = ref.batch(ORACLE_SS_WEIGHTS)
        c = claims.assess(code, rp, cases.monte_carlo(code, rp["batch"], exact), exact)
        e = evidence.assess(code)
        assert {k for k, v in {**c, **e}.items() if not v["met"]} == QUICK_FAILING
        assert all(r["probability"] and r["durations"] for r in e["override"]["runs"].values())
        assert c["precipitation"]["got"]["mekong"] == 90.0 and round(c["cap"]["share"], 1) == 8.6
