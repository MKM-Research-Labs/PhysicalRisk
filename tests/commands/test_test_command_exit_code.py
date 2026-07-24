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
    # Stubbed explicitly: it runs through the same sp.run as the pytest child,
    # so without this its verdict would silently track the suite's return code
    # instead of being the independent preflight it is.
    monkeypatch.setattr(cmd, '_check_test_attribution', lambda *a, **k: 0)
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


def test_aborts_with_one_when_attribution_is_stale(_stub_run, monkeypatch):
    """Unreconciled attribution rules mean the model documents are wrong."""
    monkeypatch.setattr(cmd, '_check_test_attribution', lambda *a, **k: 1)
    _stub_run(0)
    assert cmd.cmd_test(_args()) == 1


def test_audit_alone_still_aborts_on_stale_attribution(_stub_run, monkeypatch):
    """--audit has no suite verdict to report, but it does write the model
    documents — so broken attribution is a reason to stop even here."""
    monkeypatch.setattr(cmd, '_check_test_attribution', lambda *a, **k: 1)
    _stub_run(0)
    assert cmd.cmd_test(_args(unit=False, audit=True)) == 1
