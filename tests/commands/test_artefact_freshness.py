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

"""Tests for audit-package artefact freshness.

The bug these guard against: the summary reported ``[OK]`` for any file that
existed, so four generators that died on import kept showing four-week-old PDFs
as current evidence.
"""

import os

import pytest

from app.commands.test.artefacts import (
    _describe_age,
    artefact_manifest,
    classify,
    report_artefacts,
)

NOW = 1_000_000.0
ALL_PHASES = {'unit', 'e2e', 'lineage', 'audit', 'pdf'}


def _touch(path, mtime):
    path.write_text('x')
    os.utime(path, (mtime, mtime))
    return str(path)


class TestClassify:
    def test_missing_when_absent(self, tmp_path):
        status, _ = classify(
            str(tmp_path / 'nope.pdf'), 'audit', NOW, ALL_PHASES)
        assert status == 'MISSING'

    def test_ok_when_written_during_run(self, tmp_path):
        p = _touch(tmp_path / 'a.pdf', NOW + 5)
        assert classify(p, 'audit', NOW, ALL_PHASES) == ('OK', '')

    def test_stale_when_phase_ran_but_file_is_old(self, tmp_path):
        """The regression: generator failed, last good file still on disk."""
        p = _touch(tmp_path / 'a.pdf', NOW - 30 * 86400)
        status, note = classify(p, 'audit', NOW, ALL_PHASES)
        assert status == 'STALE'
        assert '30 days old' in note

    def test_old_file_is_ok_when_its_phase_did_not_run(self, tmp_path):
        """`--e2e` alone must not brand the unit artefacts as defective."""
        p = _touch(tmp_path / 'junit.xml', NOW - 86400)
        status, note = classify(p, 'unit', NOW, {'e2e'})
        assert status == 'OK'
        assert 'not run' in note

    def test_tolerance_absorbs_clock_granularity(self, tmp_path):
        """A generator that starts writing fractionally early is not stale."""
        p = _touch(tmp_path / 'a.pdf', NOW - 1.0)
        assert classify(p, 'audit', NOW, ALL_PHASES)[0] == 'OK'

    def test_just_outside_tolerance_is_stale(self, tmp_path):
        p = _touch(tmp_path / 'a.pdf', NOW - 60)
        assert classify(p, 'audit', NOW, ALL_PHASES)[0] == 'STALE'

    def test_directory_artefact_supported(self, tmp_path):
        """Coverage HTML is a directory, not a file."""
        d = tmp_path / 'coverage'
        d.mkdir()
        os.utime(d, (NOW + 1, NOW + 1))
        assert classify(str(d), 'unit', NOW, ALL_PHASES)[0] == 'OK'


class TestDescribeAge:
    @pytest.mark.parametrize('seconds,expected', [
        (120, '2 min old'),
        (7200, '2 h old'),
        (30 * 86400, '30 days old'),
    ])
    def test_units(self, seconds, expected):
        assert expected in _describe_age(seconds)


class TestManifest:
    def _manifest(self):
        return artefact_manifest(
            '/audit', '/audit/junit.xml', '/audit/coverage.xml',
            '/audit/coverage', '/audit/assessment_x.pdf')

    def test_every_entry_is_label_path_phase(self):
        for entry in self._manifest():
            assert len(entry) == 3
            label, path, phase = entry
            assert label and path
            assert phase in ALL_PHASES

    def test_the_four_generators_that_broke_are_covered(self):
        """project, hardcoding, init_audit and embedded_js each ship a PDF."""
        paths = {p for _, p, _ in self._manifest()}
        for name in ('hardcoding_report.pdf', 'embedded_js_report.pdf',
                     'init_audit_report.pdf', 'large_file_report.pdf'):
            assert any(name in p for p in paths), name

    def test_test_report_pdf_is_gated_on_the_pdf_phase(self):
        """LaTeX compilation is opt-in; the audit phase writes only the .tex,
        so judging it against the audit phase would cry stale on every run."""
        phase = next(ph for label, _, ph in self._manifest()
                     if label == 'Test Report PDF')
        assert phase == 'pdf'


class TestReportArtefacts:
    def test_returns_stale_labels_and_prints(self, tmp_path, capsys):
        fresh = _touch(tmp_path / 'fresh.pdf', NOW + 1)
        old = _touch(tmp_path / 'old.pdf', NOW - 40 * 86400)
        stale = report_artefacts(
            [('Fresh', fresh, 'audit'),
             ('Old', old, 'audit'),
             ('Gone', str(tmp_path / 'gone.pdf'), 'audit')],
            NOW, {'audit'})

        assert stale == ['Old']
        out = capsys.readouterr().out
        assert '[OK] Fresh' in out
        assert '[STALE] Old' in out
        assert '[MISSING] Gone' in out

    def test_no_stale_when_all_fresh(self, tmp_path):
        p = _touch(tmp_path / 'a.pdf', NOW + 1)
        assert report_artefacts([('A', p, 'audit')], NOW, {'audit'}) == []


class TestRaceOnDisappearingFile:
    def test_getmtime_failure_reads_as_missing(self, tmp_path, monkeypatch):
        """exists() can pass and getmtime still fail — the file was removed
        between the two calls, or is unreadable. Report MISSING rather than
        letting an OSError abort the whole summary."""
        p = _touch(tmp_path / 'a.pdf', NOW + 1)

        def _boom(_):
            raise OSError('vanished')

        monkeypatch.setattr(os.path, 'getmtime', _boom)
        assert classify(p, 'audit', NOW, ALL_PHASES) == ('MISSING', '')
