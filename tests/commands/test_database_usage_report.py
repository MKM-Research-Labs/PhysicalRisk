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

"""Database-usage audit (4.6) — the positive map of database-seam adoption.

Sibling to the json-file audit tests. 4.6 answers: which first-party module calls
the ``database`` seam and exactly which public functions; per-function coverage
(which public API is exercised, which is never called); and the inverse — modules
still on ``.json`` (the 4.5 backlog, reused). This is an informational MAP, not a
gate, so the tests pin scan correctness, scope, and the report builders rather
than asserting a pass/fail threshold.
"""

from pathlib import Path

from docs.models.full_audit.sections_tests import database_usage as scanner

# tests/commands/test_database_usage_report.py -> repo root
ROOT = Path(__file__).resolve().parents[2]

_API = {'get_gauge_portfolio', 'save_gauges', 'active_catchment', 'read_json_document'}


class TestApiSurface:
    """The authoritative API surface is the database package's __all__."""

    def test_loads_real_api_surface(self):
        names = scanner.load_api_names(ROOT)
        assert len(names) > 50            # the seam exposes a large public API
        assert 'active_catchment' in names
        assert 'get_gauge_portfolio' in names

    def test_missing_init_returns_empty(self, tmp_path):
        assert scanner.load_api_names(tmp_path) == set()


class TestDatabaseUsageReport:
    """scan_repo over the real tree — a complete adoption map."""

    def test_some_files_scanned(self):
        scan = scanner.scan_repo(ROOT)
        assert scan['scanned'] > 0

    def test_maps_callers_to_functions(self):
        scan = scanner.scan_repo(ROOT)
        assert scan['caller_files']
        # every recorded call belongs to the public API surface
        api = set(scan['api_names'])
        assert {c['func'] for c in scan['calls']} <= api
        # by_func and by_file are mutually consistent
        for f, funcs in scan['by_file'].items():
            assert funcs == sorted(set(funcs))
        print(f"\n[db-usage] {len(scan['caller_files'])} seam callers, "
              f"{len(scan['calls'])} call sites, "
              f"{len(scan['used_funcs'])}/{len(scan['api_names'])} API used, "
              f"{len(scan['unused_funcs'])} never called, "
              f"{len(scan['json_io_files'])} still on .json.")

    def test_used_and_unused_partition_the_api(self):
        scan = scanner.scan_repo(ROOT)
        api = set(scan['api_names'])
        assert set(scan['used_funcs']).isdisjoint(scan['unused_funcs'])
        assert set(scan['used_funcs']) | set(scan['unused_funcs']) == api

    def test_complement_is_the_json_backlog(self):
        """'Not on the seam' reuses the 4.5 backlog verbatim (single source)."""
        from docs.models.full_audit.sections_tests import json_files
        scan = scanner.scan_repo(ROOT)
        assert scan['json_io_files'] == json_files.scan_repo(ROOT)['io_files']
        # 'both' is the intersection of seam callers and json backlog
        assert set(scan['both_files']) == (
            set(scan['caller_files']) & set(scan['json_io_files']))

    def test_seam_package_excluded_from_callers(self):
        scan = scanner.scan_repo(ROOT)
        for rel in scan['caller_files']:
            assert not rel.startswith('src/database/'), rel
            assert not rel.startswith('tests/'), rel


class TestScanText:
    """Pure detection against synthetic source (no repo scan)."""

    def test_detects_attribute_call(self):
        res = scanner.scan_text('x = database.get_gauge_portfolio(c)\n', _API)
        assert [c['func'] for c in res['calls']] == ['get_gauge_portfolio']
        assert res['imports_database'] is False  # no import line here

    def test_attribute_reference_without_call_is_counted(self):
        # dispatch pattern: fn = database.get_x ... fn(...)
        res = scanner.scan_text('fn = database.active_catchment\n', _API)
        assert [c['func'] for c in res['calls']] == ['active_catchment']

    def test_ignores_non_api_attribute(self):
        res = scanner.scan_text('database.not_a_real_function(x)\n', _API)
        assert res['calls'] == []

    def test_from_import_binds_bare_call(self):
        text = ('from database import read_json_document\n'
                'd = read_json_document(p, name)\n')
        res = scanner.scan_text(text, _API)
        assert [c['func'] for c in res['calls']] == ['read_json_document']
        assert res['imports_database'] is True

    def test_from_import_alias_is_tracked(self):
        text = ('from database import get_gauge_portfolio as ggp\n'
                'rows = ggp(c)\n')
        res = scanner.scan_text(text, _API)
        # the alias is bound; the call resolves to the canonical API function
        assert res['calls'] and res['calls'][0]['func'] == 'get_gauge_portfolio'

    def test_import_database_sets_flag(self):
        res = scanner.scan_text('import database\n', _API)
        assert res['imports_database'] is True
        assert res['calls'] == []

    def test_submodule_import_recorded(self):
        res = scanner.scan_text(
            'from database.config_binding import use_configured_backend\n', _API)
        assert 'config_binding' in res['submodules']
        assert res['imports_database'] is True

    def test_skips_comments_and_docstrings(self):
        assert scanner.scan_text('# database.get_gauge_portfolio(c)\n', _API)['calls'] == []
        doc = '"""\ncalls database.save_gauges(x) in prose\n"""\n'
        assert scanner.scan_text(doc, _API)['calls'] == []

    def test_bound_call_not_double_counted_with_attr(self):
        # `database.read_json_document(` must count once (attr), not also as bare
        text = ('from database import read_json_document\n'
                'd = database.read_json_document(p, n)\n')
        res = scanner.scan_text(text, _API)
        assert [c['func'] for c in res['calls']] == ['read_json_document']


class TestScanRepo:
    """scan_repo behaviour against a synthetic tree."""

    def _seed_api(self, tmp_path):
        pkg = tmp_path / 'src' / 'database'
        pkg.mkdir(parents=True)
        (pkg / '__init__.py').write_text(
            '__all__ = ["get_gauge_portfolio", "save_gauges", "unused_fn"]\n')
        return pkg

    def test_maps_caller_and_marks_unused(self, tmp_path):
        self._seed_api(tmp_path)
        app = tmp_path / 'app'
        app.mkdir()
        (app / 'route.py').write_text(
            'import database\nrows = database.get_gauge_portfolio(c)\n')
        scan = scanner.scan_repo(tmp_path)
        assert 'app/route.py' in scan['caller_files']
        assert scan['by_file']['app/route.py'] == ['get_gauge_portfolio']
        assert 'get_gauge_portfolio' in scan['used_funcs']
        assert 'unused_fn' in scan['unused_funcs']
        assert 'save_gauges' in scan['unused_funcs']

    def test_seam_package_itself_not_scanned_as_caller(self, tmp_path):
        pkg = self._seed_api(tmp_path)
        (pkg / 'file_repo.py').write_text(
            'import database\ndatabase.get_gauge_portfolio(c)\n')
        scan = scanner.scan_repo(tmp_path)
        assert not any(f.startswith('src/database/') for f in scan['caller_files'])

    def test_tests_dir_pruned(self, tmp_path):
        self._seed_api(tmp_path)
        tdir = tmp_path / 'tests'
        tdir.mkdir()
        (tdir / 'scratch.py').write_text('database.get_gauge_portfolio(c)\n')
        scan = scanner.scan_repo(tmp_path)
        assert not any(f.startswith('tests/') for f in scan['caller_files'])

    def test_both_file_in_complement_and_callers(self, tmp_path, monkeypatch):
        self._seed_api(tmp_path)
        app = tmp_path / 'app'
        app.mkdir()
        # a module that calls the seam AND still does .json I/O
        (app / 'mid.py').write_text(
            'import database\n'
            'rows = database.get_gauge_portfolio(c)\n'
            'json.load(open("legacy.json"))\n')
        scan = scanner.scan_repo(tmp_path)
        assert 'app/mid.py' in scan['caller_files']
        assert 'app/mid.py' in scan['json_io_files']
        assert 'app/mid.py' in scan['both_files']

    def test_unreadable_file_skipped(self, tmp_path):
        self._seed_api(tmp_path)
        (tmp_path / 'binary.py').write_bytes(b'\xff\xfe \x80 not utf8\n')
        scan = scanner.scan_repo(tmp_path)   # must not raise
        assert isinstance(scan['scanned'], int)


class TestSectionBuilder:
    """Smoke-test the full-audit 4.6 subsection builder."""

    def test_builds_section_elements(self):
        from docs.models.full_audit.styles import _styles
        elems = scanner._build_database_usage(_styles())
        assert elems

    def test_renders_full_coverage_branch(self, monkeypatch):
        """When every API function is used, the 'unused' block is skipped."""
        from docs.models.full_audit.styles import _styles
        monkeypatch.setattr(scanner, 'scan_repo', lambda root=None: {
            'scanned': 1, 'api_names': ['a'], 'calls': [{'file': 'x.py', 'func': 'a', 'line': 1}],
            'by_file': {'x.py': ['a']}, 'caller_files': ['x.py'], 'by_func': {'a': ['x.py']},
            'used_funcs': ['a'], 'unused_funcs': [], 'submodule_files': {},
            'json_io_files': [], 'json_reads': 0, 'json_writes': 0, 'both_files': [],
        })
        elems = scanner._build_database_usage(_styles())
        assert elems


class TestPdfReport:
    """The standalone PDF renders without raising, both populated and empty."""

    def _scan(self, populated):
        if populated:
            return {
                'scanned': 3, 'api_names': ['a', 'b', 'c'],
                'calls': [{'file': 'app/x.py', 'func': 'a', 'line': 2}],
                'by_file': {'app/x.py': ['a', 'b']}, 'caller_files': ['app/x.py'],
                'by_func': {'a': ['app/x.py'], 'b': ['app/x.py']},
                'used_funcs': ['a', 'b'], 'unused_funcs': ['c'], 'submodule_files': {},
                'json_io_files': ['app/x.py', 'src/legacy.py'], 'json_reads': 2,
                'json_writes': 1, 'both_files': ['app/x.py'],
            }
        return {
            'scanned': 0, 'api_names': [], 'calls': [], 'by_file': {},
            'caller_files': [], 'by_func': {}, 'used_funcs': [], 'unused_funcs': [],
            'submodule_files': {}, 'json_io_files': [], 'json_reads': 0,
            'json_writes': 0, 'both_files': [],
        }

    def test_renders_populated(self, tmp_path):
        from docs.models.database_usage.pdf import create_pdf_report
        out = tmp_path / 'db.pdf'
        create_pdf_report(self._scan(True), out, ROOT, '2026-06-28 00:00:00')
        assert out.exists() and out.stat().st_size > 0

    def test_renders_empty(self, tmp_path):
        from docs.models.database_usage.pdf import create_pdf_report
        out = tmp_path / 'db_empty.pdf'
        create_pdf_report(self._scan(False), out, ROOT, '2026-06-28 00:00:00')
        assert out.exists() and out.stat().st_size > 0
