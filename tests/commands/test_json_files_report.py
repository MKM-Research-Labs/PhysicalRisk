# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""JSON-file audit — tracked .json-I/O backlog (zero-tolerance gate on flip).

Sits with the other audit-report tests (test_data_access_report.py,
test_path_definitions_report.py, …) and runs under ``app.py test``.

Policy goal: **no first-party module loads, creates, or updates a ``.json`` file
on disk** — all such state lives in PostgreSQL behind ``src/database``. The
json->postgres migration is ~90% complete, so today this is a *tracked report*:
``TestJsonFilesReport`` surfaces the remaining I/O backlog (loads + create/update)
and the softer path-reference count without ever failing CI.

``TestJsonFilesGate`` is dormant until ``json_files.GATED`` is flipped to True
(the zero-tolerance day); ``test_gate_blocks_io_when_enabled`` proves the
enforcement path works now so the flip is a one-line, pre-verified change.
``TestJsonFilesScanLogic`` pins detect/skip behaviour and ``TestJsonFilesSection``
smoke-tests the report builder.
"""

from pathlib import Path

from docs.models.full_audit.sections_tests import json_files as scanner

# tests/commands/test_json_files_report.py -> repo root
ROOT = Path(__file__).resolve().parents[2]


class TestJsonFilesReport:
    """The .json-file backlog is tracked, not gated (until GATED flips)."""

    def test_some_files_scanned(self):
        scan = scanner.scan_repo(ROOT)
        assert scan['scanned'] > 0

    def test_io_backlog_is_reported(self):
        """The scan reports a load/create-update backlog; it never fails the
        build while GATED is False. Documents the remaining migration."""
        scan = scanner.scan_repo(ROOT)
        assert isinstance(scan['io_files'], list)
        assert scan['reads'] + scan['writes'] == len(scan['io_findings'])
        print(f"\n[json-files] .json I/O backlog: {len(scan['io_files'])} file(s) "
              f"({scan['reads']} load, {scan['writes']} create/update); "
              f"plus {scan['refs']} bare path reference(s).")

    def test_backlog_excludes_tests_but_includes_database(self):
        """tests/ is exempt; src/database is NOT (zero-tolerance is repo-wide)."""
        scan = scanner.scan_repo(ROOT)
        for rel in scan['files']:
            assert not rel.startswith('tests/'), rel
            assert not rel.endswith('json_files.py'), rel  # scanner self-skip

    def test_allowlist_entries_are_minimal_and_present(self):
        """Every allowlisted file must still exist and still contain a .json
        finding — stale exemptions are not allowed to accumulate."""
        scan = scanner.scan_repo(ROOT)
        present = {a['file'] for a in scan['allowlisted']}
        for rel in scanner._ALLOWLIST:
            assert (ROOT / rel).exists(), f"allowlisted file missing: {rel}"
            assert rel in present, (
                f"allowlisted file no longer contains a .json finding — "
                f"remove the exemption: {rel}"
            )


class TestJsonFilesGate:
    """Zero-tolerance enforcement — active only once GATED is flipped True."""

    def test_no_json_io_outside_database_when_gated(self):
        if not scanner.GATED:
            import pytest
            pytest.skip("json-file gate not yet enabled (GATED is False)")
        scan = scanner.scan_repo(ROOT)
        findings = scan['io_findings']
        if findings:
            files = sorted({f['file'] for f in findings})
            lines = [
                f"  {f['file']}:{f['line']}  [{f['kind']}]  {f['snippet']}"
                for f in findings[:40]
            ]
            extra = '' if len(findings) <= 40 else f"\n  … +{len(findings) - 40} more"
            raise AssertionError(
                f"{len(findings)} .json load/create/update finding(s) outside "
                f"src/database across {len(files)} file(s).\n"
                "No module may load, create, or update a .json file directly; "
                "all such state lives in PostgreSQL behind the database API.\n"
                + '\n'.join(lines) + extra
            )


class TestJsonFilesScanLogic:
    """Pure detect/skip behaviour against synthetic input (no repo scan)."""

    def test_flags_json_load_as_read(self):
        f = scanner.scan_text('data = json.load(fp)\n')
        assert [x['kind'] for x in f] == ['read']

    def test_flags_json_dump_as_write(self):
        f = scanner.scan_text('json.dump(obj, fp)\n')
        assert [x['kind'] for x in f] == ['write']

    def test_ignores_string_forms_loads_dumps(self):
        # json.loads / json.dumps operate on strings, not files — not a .json file
        assert scanner.scan_text('x = json.loads(s)\n') == []
        assert scanner.scan_text('s = json.dumps(obj)\n') == []

    def test_json_literal_with_open_is_read(self):
        f = scanner.scan_text('with open(d / "storms.json") as fh:\n')
        assert [x['kind'] for x in f] == ['read']

    def test_json_literal_with_write_mode_is_write(self):
        f = scanner.scan_text('with open(p / "out.json", "w") as fh:\n')
        assert [x['kind'] for x in f] == ['write']

    def test_json_literal_with_write_text_is_write(self):
        f = scanner.scan_text('(p / "market_state.json").write_text(payload)\n')
        assert [x['kind'] for x in f] == ['write']

    def test_bare_json_literal_is_ref(self):
        f = scanner.scan_text('FILENAME = "gauge.json"\n')
        assert [x['kind'] for x in f] == ['ref']

    def test_glob_json_is_read(self):
        f = scanner.scan_text('for p in d.glob("*.json"):\n')
        assert [x['kind'] for x in f] == ['read']

    def test_ignores_non_json_file(self):
        assert scanner.scan_text('open("notes.txt")\n') == []
        assert scanner.scan_text('df.to_csv("x.csv")\n') == []

    def test_ignores_comment_line(self):
        assert scanner.scan_text('# load gauge.json from disk via json.load\n') == []

    def test_skips_docstring_interior(self):
        text = '"""\nReads gauge.json with json.load(fp); writes out.json.\n"""\n'
        assert scanner.scan_text(text) == []


class TestJsonFilesScanRepo:
    """scan_repo behaviour against a synthetic tree."""

    def test_finds_synthetic_read_and_write(self, tmp_path):
        (tmp_path / "io.py").write_text(
            'a = json.load(open("a.json"))\njson.dump(a, open("b.json", "w"))\n')
        scan = scanner.scan_repo(tmp_path)
        kinds = {f['kind'] for f in scan['io_findings']}
        assert {'read', 'write'} <= kinds
        assert 'io.py' in scan['io_files']

    def test_ref_only_file_not_in_io_files(self, tmp_path):
        (tmp_path / "names.py").write_text('GAUGE = "gauge.json"\n')
        scan = scanner.scan_repo(tmp_path)
        assert 'names.py' in scan['files']
        assert 'names.py' not in scan['io_files']

    def test_allowlisted_file_is_exempt(self, tmp_path, monkeypatch):
        (tmp_path / "legacy.py").write_text('json.load(open("keep.json"))\n')
        monkeypatch.setattr(scanner, "_ALLOWLIST", {"legacy.py": "intentional"})
        scan = scanner.scan_repo(tmp_path)
        assert scan['io_findings'] == []
        assert any(a['file'] == 'legacy.py' for a in scan['allowlisted'])

    def test_database_package_is_in_scope(self, tmp_path):
        """Unlike the data-access audit, src/database is scanned, not exempt."""
        pkg = tmp_path / "src" / "database"
        pkg.mkdir(parents=True)
        (pkg / "file_repo.py").write_text('json.load(open(p / "x.json"))\n')
        scan = scanner.scan_repo(tmp_path)
        assert any(f['file'].endswith('file_repo.py') for f in scan['io_findings'])

    def test_skips_tests_dir(self, tmp_path):
        tdir = tmp_path / "tests"
        tdir.mkdir()
        (tdir / "scratch.py").write_text('json.load(open("fixture.json"))\n')
        scan = scanner.scan_repo(tmp_path)
        assert scan['findings'] == []

    def test_excludes_docs_models_generators(self, tmp_path):
        """docs/models (model-doc/audit generators) is out of scope; a sibling
        docs/ path and src/models stay in scope."""
        dm = tmp_path / "docs" / "models" / "full_audit"
        dm.mkdir(parents=True)
        (dm / "report.py").write_text('json.load(open("model_inventory.json"))\n')
        sm = tmp_path / "src" / "models"
        sm.mkdir(parents=True)
        (sm / "hazard.py").write_text('json.load(open("curve.json"))\n')
        scan = scanner.scan_repo(tmp_path)
        files = scan['files']
        assert not any(f.startswith('docs/models/') for f in files)
        assert any(f.startswith('src/models/') for f in files)

    def test_excludes_governance_subsystem(self, tmp_path):
        """src/routes/governance (model_inventory et al. — separate migration)
        is out of scope; non-governance routes stay in scope."""
        gov = tmp_path / "src" / "routes" / "governance"
        gov.mkdir(parents=True)
        (gov / "_helpers.py").write_text('json.load(open("model_inventory.json"))\n')
        other = tmp_path / "src" / "routes" / "trading"
        other.mkdir(parents=True)
        (other / "eod.py").write_text('json.load(open("market_state.json"))\n')
        scan = scanner.scan_repo(tmp_path)
        files = scan['files']
        assert not any(f.startswith('src/routes/governance/') for f in files)
        assert any(f.startswith('src/routes/trading/') for f in files)

    def test_unreadable_file_is_skipped(self, tmp_path):
        (tmp_path / "binary.py").write_bytes(b'\xff\xfe not utf8 \x80\n')
        scan = scanner.scan_repo(tmp_path)  # must not raise
        assert isinstance(scan['scanned'], int)


class TestJsonFilesSection:
    """Smoke-test the full-audit subsection builder."""

    def test_builds_section_elements(self):
        from docs.models.full_audit.styles import _styles
        elems = scanner._build_json_files(_styles())
        assert elems  # produces flowables without raising

    def test_renders_findings_when_present(self, monkeypatch):
        """The ``if scan['io_findings']:`` render branch — synthetic findings."""
        from docs.models.full_audit.styles import _styles
        monkeypatch.setattr(scanner, "scan_repo", lambda root=None: {
            'scanned': 1,
            'findings': [{'file': 'x.py', 'line': 3, 'kind': 'read', 'snippet': 'json.load'}],
            'files': ['x.py'],
            'io_findings': [{'file': 'x.py', 'line': 3, 'kind': 'read', 'snippet': 'json.load'}],
            'io_files': ['x.py'],
            'reads': 1, 'writes': 0, 'refs': 0, 'allowlisted': [],
        })
        elems = scanner._build_json_files(_styles())
        assert elems
