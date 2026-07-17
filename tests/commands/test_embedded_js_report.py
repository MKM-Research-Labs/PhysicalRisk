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

"""Tests for docs.models.embedded_js — embedded JS/CSS audit generator."""

from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Sample source fixtures
# ---------------------------------------------------------------------------

# A violation: an inline <script> block of hand-written JS.
INLINE_SCRIPT_PY = '''\
def get_js():
    return """
        <script>
        (function() {
            var panel = document.createElement('div');
            panel.id = 'foo';
            document.body.appendChild(panel);
            panel.addEventListener('click', function() {
                console.log('clicked');
            });
        })();
        </script>
    """
'''

# Allowed: external CDN include + thin wrapper that injects config and reads
# the body from disk. Must NOT be flagged.
ALLOWED_WRAPPER_PY = '''\
def get_html(js_code, cfg):
    return (
        '<script src="https://cdn.example.com/chart.js"></script>\\n'
        f'<script>window.__FOO_CONFIG = {cfg};\\n{js_code}</script>'
    )
'''

# A violation: inline <style> block.
INLINE_STYLE_PY = '''\
def get_css():
    return """
        <style>
        #nav { display: flex; gap: 3px; }
        #nav button { padding: 4px 8px; border: 1px solid #ccc; }
        #nav button:hover { background: #e3f2fd; }
        </style>
    """
'''

# A violation: JS factory string with no <script> wrapper at all.
JS_FACTORY_PY = '''\
def build_js(namespace):
    return f"""
        (function() {{
            var panel = document.createElement('div');
            panel.id = '{namespace}-panel';
            var header = document.createElement('div');
            header.innerHTML = 'Title';
            panel.appendChild(header);
            var btn = document.createElement('button');
            btn.addEventListener('click', function() {{ window.close(); }});
            panel.appendChild(btn);
            document.body.appendChild(panel);
        }})();
    """
'''

# Clean: ordinary Python with no embedded front-end assets.
CLEAN_PY = '''\
def add(a, b):
    """Return the sum."""
    total = a + b
    return total
'''


@pytest.fixture
def src_tree(tmp_path):
    """Build a fake src/ tree and return (src_dir, root)."""
    src = tmp_path / 'src'
    (src / 'pkg').mkdir(parents=True)
    (src / 'pkg' / 'inline_script.py').write_text(INLINE_SCRIPT_PY)
    (src / 'pkg' / 'allowed_wrapper.py').write_text(ALLOWED_WRAPPER_PY)
    (src / 'pkg' / 'inline_style.py').write_text(INLINE_STYLE_PY)
    (src / 'pkg' / 'js_factory.py').write_text(JS_FACTORY_PY)
    (src / 'pkg' / 'clean.py').write_text(CLEAN_PY)
    return src, tmp_path


@pytest.fixture
def ej_mod():
    from docs.models import embedded_js
    return embedded_js


# ---------------------------------------------------------------------------
# Scanners
# ---------------------------------------------------------------------------

class TestScanInlineScripts:

    def test_flags_inline_script(self, ej_mod, src_tree):
        src, root = src_tree
        results = ej_mod.scan_inline_scripts(src, root)
        files = {r['file'] for r in results}
        assert 'src/pkg/inline_script.py' in files

    def test_ignores_allowed_wrapper(self, ej_mod, src_tree):
        src, root = src_tree
        results = ej_mod.scan_inline_scripts(src, root)
        files = {r['file'] for r in results}
        assert 'src/pkg/allowed_wrapper.py' not in files

    def test_records_line_range_and_count(self, ej_mod, src_tree):
        src, root = src_tree
        results = ej_mod.scan_inline_scripts(src, root)
        item = next(r for r in results if r['file'] == 'src/pkg/inline_script.py')
        assert item['line'] < item['end_line']
        assert item['js_lines'] >= ej_mod.MIN_JS_LINES


class TestScanInlineStyles:

    def test_flags_inline_style(self, ej_mod, src_tree):
        src, root = src_tree
        results = ej_mod.scan_inline_styles(src, root)
        files = {r['file'] for r in results}
        assert 'src/pkg/inline_style.py' in files

    def test_clean_file_not_flagged(self, ej_mod, src_tree):
        src, root = src_tree
        results = ej_mod.scan_inline_styles(src, root)
        files = {r['file'] for r in results}
        assert 'src/pkg/clean.py' not in files


class TestScanJsFactories:

    def test_flags_factory(self, ej_mod, src_tree):
        src, root = src_tree
        results = ej_mod.scan_js_factories(src, root)
        files = {r['file'] for r in results}
        assert 'src/pkg/js_factory.py' in files

    def test_does_not_double_count_script_block(self, ej_mod, src_tree):
        """JS already inside a <script> block must not also be a 'factory'."""
        src, root = src_tree
        results = ej_mod.scan_js_factories(src, root)
        files = {r['file'] for r in results}
        assert 'src/pkg/inline_script.py' not in files

    def test_clean_file_not_flagged(self, ej_mod, src_tree):
        src, root = src_tree
        results = ej_mod.scan_js_factories(src, root)
        files = {r['file'] for r in results}
        assert 'src/pkg/clean.py' not in files


class TestCollectAll:

    def test_shape(self, ej_mod, src_tree):
        src, root = src_tree
        findings = ej_mod.collect_all(src, root)
        for key in ('scripts', 'styles', 'factories',
                    'files_scanned', 'files_flagged'):
            assert key in findings

    def test_counts(self, ej_mod, src_tree):
        src, root = src_tree
        findings = ej_mod.collect_all(src, root)
        assert findings['files_scanned'] == 5
        assert len(findings['scripts']) == 1
        assert len(findings['styles']) == 1
        assert len(findings['factories']) == 1
        # inline_script, inline_style, js_factory — allowed_wrapper & clean excluded
        assert findings['files_flagged'] == 3

    def test_empty_tree_compliant(self, ej_mod, tmp_path):
        src = tmp_path / 'src'
        src.mkdir()
        (src / 'ok.py').write_text(CLEAN_PY)
        findings = ej_mod.collect_all(src, tmp_path)
        assert findings['files_flagged'] == 0
        assert findings['scripts'] == []


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------

class TestPdf:

    def test_writes_pdf(self, ej_mod, src_tree, tmp_path):
        src, root = src_tree
        findings = ej_mod.collect_all(src, root)
        out = tmp_path / 'embedded_js_report.pdf'
        ej_mod.create_pdf_report(findings, out, root)
        assert out.exists()
        assert out.read_bytes()[:4] == b'%PDF'
        assert out.stat().st_size > 1000

    def test_compliant_pdf(self, ej_mod, tmp_path):
        findings = {
            'scripts': [], 'styles': [], 'factories': [],
            'files_scanned': 10, 'files_flagged': 0,
        }
        out = tmp_path / 'embedded_js_report.pdf'
        ej_mod.create_pdf_report(findings, out, tmp_path)
        assert out.read_bytes()[:4] == b'%PDF'


# ---------------------------------------------------------------------------
# main() integration
# ---------------------------------------------------------------------------

class TestMain:

    def test_main_writes_report(self, ej_mod, tmp_path, monkeypatch):
        """main() writes embedded_js_report.pdf into the audit dir."""
        from config import config
        monkeypatch.setattr(config, 'get_reports_dir', lambda which='audit': tmp_path)
        ej_mod.main()
        assert (tmp_path / 'embedded_js_report.pdf').exists()

    def test_main_prints_stats(self, ej_mod, tmp_path, monkeypatch, capsys):
        from config import config
        monkeypatch.setattr(config, 'get_reports_dir', lambda which='audit': tmp_path)
        ej_mod.main()
        out = capsys.readouterr().out
        assert 'files scanned' in out
        assert 'total action items' in out
