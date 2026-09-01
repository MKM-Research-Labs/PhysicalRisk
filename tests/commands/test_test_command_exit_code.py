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

"""``cmd_test`` reports the unit suite's verdict as its exit status.

The child pytest is stubbed, so these pin the contract — a failing suite must
exit non-zero — without running the real 13-minute suite.
"""

import time
from types import SimpleNamespace

import pytest
from app.commands.test import command as cmd


@pytest.fixture
def _stub_run(monkeypatch, tmp_path):
    """Stub every subprocess and side effect; returns a setter for pytest's rc."""
    state = {'rc': 0}

    class _Result:
        def __init__(self, rc, stdout=''):
            self.returncode = rc
            self.stdout = stdout

    def _fake_run(argv, **kwargs):
        # The git rev-parse probe wants stdout; the pytest child wants the rc.
        if 'rev-parse' in argv:
            return _Result(0, 'deadbeef\n')
        return _Result(state['rc'])

    monkeypatch.setattr(cmd.sp, 'run', _fake_run)
    monkeypatch.setattr(cmd, '_cleanup_worktree_data', lambda *a, **k: None)
    monkeypatch.setattr(cmd, '_parse_coverage_pct', lambda *a, **k: 99.1)
    monkeypatch.setattr(cmd, '_write_failures_report', lambda *a, **k: None)
    monkeypatch.setattr(cmd, 'check_live_services', lambda *a, **k: 0)
    monkeypatch.setattr(cmd.config, 'get_reports_dir', lambda *a, **k: tmp_path)

    def _set(rc):
        state['rc'] = rc
    return _set


def _args(**over):
    base = dict(unit=True, e2e=False, lineage=False, run_all=False, audit=False,
                pdf=False, params=False, check_deps=False, model=None,
                catchment_id=None)
    base.update(over)
    return SimpleNamespace(**base)


def test_returns_zero_when_unit_suite_passes(_stub_run):
    _stub_run(0)
    assert cmd.cmd_test(_args()) == 0


def test_returns_one_when_unit_suite_fails(_stub_run):
    """The regression this pins: pytest failed, so the command must not exit 0."""
    _stub_run(1)
    assert cmd.cmd_test(_args()) == 1


def test_returns_one_when_coverage_gate_fails(_stub_run):
    """A missed coverage gate is also a non-zero pytest rc — same contract."""
    _stub_run(2)
    assert cmd.cmd_test(_args()) == 1


def test_returns_zero_without_a_unit_suite(_stub_run):
    """--audit alone generates evidence; there is no verdict to report."""
    _stub_run(1)
    assert cmd.cmd_test(_args(unit=False, audit=True)) == 0


def test_aborts_with_one_when_preflight_blocks(_stub_run, monkeypatch):
    """A blocked preflight (Postgres down) must not be reported as success."""
    monkeypatch.setattr(cmd, 'check_live_services', lambda *a, **k: 1)
    _stub_run(0)
    assert cmd.cmd_test(_args()) == 1


def _stale(audit_dir, name='hardcoding_report.pdf', age_days=26):
    """Write an artefact dated well before the run starts.

    ``audit_dir`` is the stubbed ``get_reports_dir('audit')`` result, which is
    ``tmp_path`` itself — not a subdirectory of it.
    """
    import os
    audit_dir.mkdir(parents=True, exist_ok=True)
    f = audit_dir / name
    f.write_text('old')
    old = time.time() - age_days * 86400
    os.utime(f, (old, old))
    return f


def test_returns_one_when_an_artefact_is_stale(_stub_run, tmp_path):
    """A generator that dies on import leaves its last good PDF on disk. The
    suite can pass while the evidence package is four weeks out of date — that
    must not exit zero."""
    _stub_run(0)
    _stale(tmp_path)
    assert cmd.cmd_test(_args(audit=True)) == 1


def test_stale_artefact_is_named_in_the_output(_stub_run, tmp_path, capsys):
    _stub_run(0)
    _stale(tmp_path)
    cmd.cmd_test(_args(audit=True))
    out = capsys.readouterr().out
    assert '[STALE] Hard-Coding Audit PDF' in out
    assert 'NOT regenerated this run' in out
    assert 'STALE ARTEFACT(S)' in out


def test_stale_does_not_fail_when_its_phase_did_not_run(_stub_run, tmp_path):
    """Without --audit the doc generators never ran, so an old PDF is carried
    over rather than defective. Failing here would make the check cry wolf on
    every `--unit` run and get it switched off."""
    _stub_run(0)
    _stale(tmp_path)
    assert cmd.cmd_test(_args(audit=False)) == 0


def test_missing_artefact_does_not_fail_the_run(_stub_run, tmp_path):
    """An artefact whose phase never wrote it is absent by design, not broken;
    test_report.pdf is MISSING on every run without --pdf."""
    _stub_run(0)
    assert cmd.cmd_test(_args(audit=True)) == 0
