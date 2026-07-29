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

"""Standalone json-file audit PDF — builder + entry-point tests.

Companion to test_json_files_report.py (the scanner/§4.5 tests). Exercises the
dedicated ``docs.models.json_files`` report package: the PDF builder branches
(populated vs empty, tracking vs gated) and the ``main`` entry point."""

from pathlib import Path

from docs.models.json_files import pdf as pdfmod
from docs.models.json_files import report as reportmod


def _scan(io_findings, refs=0, scanned=5):
    io_files = sorted({f['file'] for f in io_findings})
    return {
        'scanned': scanned,
        'findings': io_findings,
        'files': io_files,
        'io_findings': io_findings,
        'io_files': io_files,
        'reads': sum(1 for f in io_findings if f['kind'] == 'read'),
        'writes': sum(1 for f in io_findings if f['kind'] == 'write'),
        'refs': refs,
        'allowlisted': [],
    }


class TestHelpers:
    def test_area_with_subdir(self):
        assert pdfmod._area('src/port/loader.py') == 'src/port'

    def test_area_top_level_file(self):
        assert pdfmod._area('phys.py') == 'phys.py'


class TestPdfBuilder:
    def test_builds_with_findings(self, tmp_path):
        scan = _scan([
            {'file': 'src/port/a.py', 'line': 1, 'kind': 'read', 'snippet': ''},
            {'file': 'src/port/a.py', 'line': 2, 'kind': 'write', 'snippet': ''},
            {'file': 'app/cmd/b.py', 'line': 9, 'kind': 'read', 'snippet': ''},
        ], refs=4)
        out = tmp_path / 'r.pdf'
        res = pdfmod.create_pdf_report(scan, out, tmp_path, '2026-06-26 00:00:00')
        assert res == out and out.exists() and out.stat().st_size > 0

    def test_builds_when_backlog_clear(self, tmp_path):
        """Empty-backlog branch: 'backlog clear' + 'None.' render paths."""
        out = tmp_path / 'empty.pdf'
        pdfmod.create_pdf_report(_scan([], refs=0), out, tmp_path,
                                 '2026-06-26 00:00:00')
        assert out.exists()

    def test_gated_red_branch(self, tmp_path, monkeypatch):
        """Mode=GATING with outstanding findings -> RED status colour branch."""
        monkeypatch.setattr(pdfmod, 'GATED', True)
        scan = _scan([{'file': 'x.py', 'line': 1, 'kind': 'write', 'snippet': ''}])
        out = tmp_path / 'gated.pdf'
        pdfmod.create_pdf_report(scan, out, tmp_path, '2026-06-26 00:00:00')
        assert out.exists()


class TestMain:
    def test_main_writes_pdf(self, tmp_path, monkeypatch):
        from config import config as cfg
        monkeypatch.setattr(cfg, 'get_reports_dir', lambda name: tmp_path)
        out = reportmod.main()
        assert Path(out).exists()
        assert Path(out).name == 'json_files_report.pdf'
        assert Path(out).parent == tmp_path
