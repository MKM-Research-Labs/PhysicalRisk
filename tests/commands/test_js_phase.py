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

"""Tests for the jest phase and the run verdict.

The phase must skip cleanly on a machine with no JS toolchain — a CI box
without node should report SKIPPED, not fail the build — and a genuinely
failing JS suite must fail the run the same way a failing Python suite does.
"""

import json

import pytest

from app.commands.test.artefacts import run_verdict
from config import js_coverage
from app.commands.test.js import (
    _preflight,
    _read_counts,
    _read_pct,
    _run_js_tests,
    _skipped,
)


@pytest.fixture
def repo(tmp_path):
    """A tree that satisfies every preflight check."""
    (tmp_path / "node_modules").mkdir()
    cfg = tmp_path / "tests" / "js"
    cfg.mkdir(parents=True)
    (cfg / "jest.config.js").write_text("module.exports = {};")
    return tmp_path


class TestPreflight:
    def test_passes_when_everything_present(self, repo):
        assert _preflight(repo) is None

    def test_missing_node_modules(self, repo):
        (repo / "node_modules").rmdir()
        assert "node_modules" in _preflight(repo)

    def test_missing_config(self, repo):
        (repo / "tests" / "js" / "jest.config.js").unlink()
        assert "jest.config.js" in _preflight(repo)

    def test_missing_node(self, repo, monkeypatch):
        monkeypatch.setattr("app.commands.test.js.shutil.which",
                            lambda name: None if name == "node" else "/usr/bin/npx")
        assert "node not on PATH" in _preflight(repo)

    def test_missing_npx(self, repo, monkeypatch):
        monkeypatch.setattr("app.commands.test.js.shutil.which",
                            lambda name: None if name == "npx" else "/usr/bin/node")
        assert "npx not on PATH" in _preflight(repo)


class TestSkip:
    def test_writes_a_summary_so_the_audit_still_has_an_entry(self, tmp_path):
        out = tmp_path / "js"
        s = _skipped("no node", str(out))
        assert s["status"] == "SKIPPED" and s["failed"] == 0
        assert json.loads((out / "js_results.json").read_text())["reason"] == "no node"

    def test_unwritable_dir_does_not_raise(self, tmp_path):
        """Coverage plumbing must never be what breaks a run."""
        blocker = tmp_path / "blocked"
        blocker.write_text("not a directory")
        assert _skipped("x", str(blocker / "js"))["status"] == "SKIPPED"


class TestReadPct:
    def test_reads_statement_percentage(self, tmp_path):
        (tmp_path / "coverage-summary.json").write_text(
            json.dumps({"total": {"statements": {"pct": 2.71}}}))
        assert _read_pct(str(tmp_path)) == 2.71

    @pytest.mark.parametrize("content", [None, "{not json", "{}"])
    def test_missing_or_corrupt_yields_none(self, tmp_path, content):
        if content is not None:
            (tmp_path / "coverage-summary.json").write_text(content)
        assert _read_pct(str(tmp_path)) is None


class TestReadCounts:
    def test_reads_jest_totals(self, tmp_path):
        f = tmp_path / "r.json"
        f.write_text(json.dumps(
            {"numTotalTests": 87, "numPassedTests": 87, "numFailedTests": 0}))
        assert _read_counts(str(f)) == (87, 87, 0)

    def test_missing_file_yields_zeros(self, tmp_path):
        assert _read_counts(str(tmp_path / "nope.json")) == (0, 0, 0)

    def test_corrupt_file_yields_zeros(self, tmp_path):
        f = tmp_path / "r.json"
        f.write_text("{not json")
        assert _read_counts(str(f)) == (0, 0, 0)


class TestRunJsTests:
    def test_skips_without_toolchain(self, tmp_path):
        s = _run_js_tests(tmp_path, str(tmp_path / "audit"))
        assert s["status"] == "SKIPPED"

    def test_reports_counts_and_pct(self, repo, monkeypatch):
        audit = repo / "audit"

        def _fake_run(cmd, **kw):
            out = audit / "js"
            out.mkdir(parents=True, exist_ok=True)
            (out / "js_results.json").write_text(json.dumps(
                {"numTotalTests": 87, "numPassedTests": 87, "numFailedTests": 0}))
            # Report exactly the baseline rather than a literal: a fixed
            # number here would fail the moment the ratchet is raised, which
            # is a test pinning a config value instead of a behaviour.
            (out / "coverage-summary.json").write_text(json.dumps(
                {"total": {"statements": {"pct": js_coverage.BASELINE_PCT}}}))
            (out / "cobertura-coverage.xml").write_text("<coverage/>")
            return None

        monkeypatch.setattr("app.commands.test.js.sp.run", _fake_run)
        s = _run_js_tests(repo, str(audit))
        assert s == {"total": 87, "passed": 87, "failed": 0,
                     "status": "OK",
                     "statements_pct": js_coverage.BASELINE_PCT,
                     "coverage_baseline_pct": js_coverage.BASELINE_PCT,
                     "coverage_ok": True,
                     "coverage_message": js_coverage.classify(
                         js_coverage.BASELINE_PCT)[1]}
        # cobertura is renamed to match the Python side's coverage.xml shape
        assert (audit / "js" / "js_coverage.xml").exists()
        assert not (audit / "js" / "cobertura-coverage.xml").exists()

    def test_failures_are_reported(self, repo, monkeypatch):
        audit = repo / "audit"

        def _fake_run(cmd, **kw):
            out = audit / "js"
            out.mkdir(parents=True, exist_ok=True)
            (out / "js_results.json").write_text(json.dumps(
                {"numTotalTests": 87, "numPassedTests": 83, "numFailedTests": 4}))
            return None

        monkeypatch.setattr("app.commands.test.js.sp.run", _fake_run)
        s = _run_js_tests(repo, str(audit))
        assert s["failed"] == 4 and s["status"] == "FAILURES"

    def test_timeout_skips_rather_than_raising(self, repo, monkeypatch):
        import subprocess
        def _boom(cmd, **kw):
            raise subprocess.TimeoutExpired(cmd, 600)
        monkeypatch.setattr("app.commands.test.js.sp.run", _boom)
        assert _run_js_tests(repo, str(repo / "audit"))["status"] == "SKIPPED"

    def test_launch_failure_skips(self, repo, monkeypatch):
        def _boom(cmd, **kw):
            raise OSError("npx vanished")
        monkeypatch.setattr("app.commands.test.js.sp.run", _boom)
        assert _run_js_tests(repo, str(repo / "audit"))["status"] == "SKIPPED"


class TestRunVerdict:
    def test_all_pass(self, capsys):
        assert run_verdict(True, True, [], {"failed": 0}) == 0
        assert "ALL PASS" in capsys.readouterr().out

    def test_unit_failure(self):
        assert run_verdict(True, False, [], None) == 1

    def test_js_failure_fails_the_run(self, capsys):
        """A front end failing its own tests is not a passing build."""
        assert run_verdict(True, True, [], {"failed": 4}) == 1
        assert "4 JS TEST FAILURES" in capsys.readouterr().out

    def test_stale_artefact_fails_the_run(self):
        assert run_verdict(True, True, ["Full Audit Report PDF"], None) == 1

    def test_skipped_js_phase_does_not_fail(self):
        """No node_modules must not fail a Python-only machine."""
        assert run_verdict(True, True, [], {"status": "SKIPPED", "failed": 0}) == 0

    def test_all_three_problems_are_named(self, capsys):
        run_verdict(True, False, ["X"], {"failed": 2})
        out = capsys.readouterr().out
        assert "TEST FAILURES" in out and "JS TEST" in out and "STALE" in out


class TestCoverageRatchet:
    """The ratchet fails in both directions, through the phase's summary."""

    @staticmethod
    def _run_with_pct(repo, audit, monkeypatch, pct):
        def _fake_run(cmd, **kw):
            out = audit / "js"
            out.mkdir(parents=True, exist_ok=True)
            (out / "js_results.json").write_text(json.dumps(
                {"numTotalTests": 87, "numPassedTests": 87,
                 "numFailedTests": 0}))
            (out / "coverage-summary.json").write_text(json.dumps(
                {"total": {"statements": {"pct": pct}}}))
            return None
        monkeypatch.setattr("app.commands.test.js.sp.run", _fake_run)
        return _run_js_tests(repo, str(audit))

    def test_regression_below_the_baseline_fails(self, repo, monkeypatch):
        s = self._run_with_pct(repo, repo / "audit", monkeypatch,
                               js_coverage.BASELINE_PCT - 1)
        assert s["status"] == "COVERAGE"
        assert s["coverage_ok"] is False
        assert "below" in s["coverage_message"]

    def test_gain_above_the_baseline_also_fails(self, repo, monkeypatch):
        """A rise that is not locked in leaves the baseline describing nothing."""
        s = self._run_with_pct(repo, repo / "audit", monkeypatch,
                               js_coverage.BASELINE_PCT
                               + js_coverage.TOLERANCE_PCT + 1)
        assert s["status"] == "COVERAGE"
        assert s["coverage_ok"] is False
        assert "raise" in s["coverage_message"]

    def test_within_tolerance_passes(self, repo, monkeypatch):
        s = self._run_with_pct(repo, repo / "audit", monkeypatch,
                               js_coverage.BASELINE_PCT
                               + js_coverage.TOLERANCE_PCT / 2)
        assert s["status"] == "OK"
        assert s["coverage_ok"] is True

    def test_a_failing_suite_outranks_the_ratchet(self, repo, monkeypatch):
        """Broken tests are the headline; the coverage figure is unreliable."""
        audit = repo / "audit"

        def _fake_run(cmd, **kw):
            out = audit / "js"
            out.mkdir(parents=True, exist_ok=True)
            (out / "js_results.json").write_text(json.dumps(
                {"numTotalTests": 87, "numPassedTests": 80,
                 "numFailedTests": 7}))
            (out / "coverage-summary.json").write_text(json.dumps(
                {"total": {"statements": {"pct": 0.0}}}))
            return None

        monkeypatch.setattr("app.commands.test.js.sp.run", _fake_run)
        s = _run_js_tests(repo, str(audit))
        assert s["status"] == "FAILURES"

    def test_skipped_phase_carries_no_coverage_verdict(self, tmp_path):
        """No toolchain must not become a coverage failure."""
        s = _run_js_tests(tmp_path, str(tmp_path / "audit"))
        assert s["status"] == "SKIPPED"
        assert s.get("coverage_ok", True) is True
