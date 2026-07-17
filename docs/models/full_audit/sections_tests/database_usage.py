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

"""4.6 — Database-usage audit: the positive map of database-seam adoption.

Where 4.4 (data-access) forbids raw SQL/connections outside ``src/database`` and
4.5 (json-files) tracks the shrinking ``.json`` backlog, this section answers the
complementary question directly: **which first-party module calls the database
seam, and exactly which public functions does it call?** — together with the
inverse view, **which modules still persist/read state as ``.json`` instead**
(reusing the 4.5 backlog verbatim).

Together the three give a complete handle on state access:

* every call into the ``database`` package, mapped file -> function(s);
* per-function coverage — which of the public API is exercised, and which
  public functions are **never called** by first-party code;
* the residual ``.json`` I/O that has not yet moved onto the seam.

Detection (lexical, matching the codebase's grep-friendly call style):

* the authoritative API surface is the ``__all__`` of ``src/database/__init__``
  (parsed, not imported — importing would configure a backend), so new seam
  functions are tracked automatically;
* ``database.<name>`` where ``<name>`` is in that surface — the dominant form,
  including attribute references used in dispatch (``fn = database.get_x``);
* ``from database import a, b`` binds ``a``/``b`` locally — a bare ``a(`` call in
  the same file is counted against the bound function;
* ``from database.<sub> import ...`` (e.g. ``config_binding``) marks the file as
  a seam consumer even when no public function name appears.

Scope: all first-party ``.py`` except ``tests/`` and inert dirs, and except
``src/database`` itself (the seam defines the API — it is not a consumer). Unlike
4.5 this deliberately INCLUDES ``src/models`` and ``docs/models`` so the map is
exhaustive over runtime code.
"""

import ast
import os
import re
from collections import defaultdict
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer

from .._constants import NAVY, _root
from .data_access import _PRUNE_DIRS, _rel

# The seam package itself — defines the API, so excluded from the consumer scan.
SANCTIONED_PACKAGE = 'src/database'
# Scanner modules whose own source contains the detection patterns (self-match).
_SCANNER_MODULES = {'database_usage.py', 'data_access.py', 'json_files.py'}


# ---------------------------------------------------------------------------
# Authoritative API surface
# ---------------------------------------------------------------------------
def load_api_names(root: Path = None) -> set:
    """Return the public symbol set of the database package (its ``__all__``).

    Parsed from ``src/database/__init__.py`` via ``ast`` — never imported, so the
    scan stays side-effect free (importing ``database`` configures a backend)."""
    root = Path(root) if root is not None else _root
    init = root / 'src' / 'database' / '__init__.py'
    try:
        tree = ast.parse(init.read_text(encoding='utf-8'))
    except (OSError, SyntaxError):
        return set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == '__all__':
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        return {e.value for e in node.value.elts
                                if isinstance(e, ast.Constant)
                                and isinstance(e.value, str)}
    return set()


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------
_IMPORT_DATABASE_RE = re.compile(r'^\s*import\s+database\b')
_FROM_DATABASE_IMPORT_RE = re.compile(
    r'^\s*from\s+database\s+import\s+(.+)$')
_FROM_DATABASE_SUB_RE = re.compile(
    r'^\s*from\s+database\.([A-Za-z_][\w]*)\s+import\b')


def _imported_names(import_clause: str):
    """Parse a ``from database import a, b as c`` clause.

    Returns ``[(local, source), …]`` — *source* is the original API name, *local*
    is what the file actually calls (the alias, when ``as`` is used)."""
    clause = import_clause.split('#', 1)[0].strip().strip('()')
    pairs = []
    for piece in clause.split(','):
        piece = piece.strip()
        if not piece:
            continue
        if ' as ' in piece:
            source, local = (p.strip() for p in piece.split(' as ', 1))
        else:
            source = local = piece
        if local.isidentifier() and source.isidentifier():
            pairs.append((local, source))
    return pairs


def scan_text(text: str, api_names: set) -> dict:
    """Scan one module's source for database-seam usage.

    Returns ``{'calls': [{'func', 'line'}], 'submodules': set, 'imports_database':
    bool}``. ``calls`` records each ``database.<func>`` reference and each call of
    a name bound via ``from database import``. Comment lines and docstring
    interiors are skipped so prose mentioning ``database`` is not miscounted."""
    bound = {}          # locally-bound name -> the database function it refers to
    submodules = set()
    imports_database = False
    lines = text.splitlines()

    # Pass 1 — resolve imports (so bound bare calls can be attributed).
    in_doc = None
    for line in lines:
        stripped = line.strip()
        if in_doc:
            if in_doc in line:
                in_doc = None
            continue
        delim = next((d for d in ('"""', "'''") if stripped.startswith(d)), None)
        if delim is not None:
            if line.count(delim) % 2 == 1:
                in_doc = delim
            continue
        if stripped.startswith('#'):
            continue
        if _IMPORT_DATABASE_RE.match(line):
            imports_database = True
        msub = _FROM_DATABASE_SUB_RE.match(line)
        if msub:
            submodules.add(msub.group(1))
            imports_database = True
        mfrom = _FROM_DATABASE_IMPORT_RE.match(line)
        if mfrom:
            imports_database = True
            for local, source in _imported_names(mfrom.group(1)):
                if source in api_names:
                    bound[local] = source   # local call name -> canonical API func

    # Pre-compile a matcher for the bound bare names, if any.
    bare_re = None
    if bound:
        alternation = '|'.join(re.escape(name) for name in bound)
        bare_re = re.compile(r'\b(' + alternation + r')\s*\(')
    attr_re = re.compile(r'\bdatabase\.([A-Za-z_][\w]*)')

    # Pass 2 — record calls.
    calls = []
    in_doc = None
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if in_doc:
            if in_doc in line:
                in_doc = None
            continue
        delim = next((d for d in ('"""', "'''") if stripped.startswith(d)), None)
        if delim is not None:
            if line.count(delim) % 2 == 1:
                in_doc = delim
            continue
        if stripped.startswith('#'):
            continue
        for m in attr_re.finditer(line):
            name = m.group(1)
            if name in api_names:
                calls.append({'func': name, 'line': i})
        if bare_re is not None:
            for m in bare_re.finditer(line):
                # skip a `database.name(` already counted by attr_re on this line
                start = m.start()
                if start >= 9 and line[start - 9:start].endswith('database.'):
                    continue
                # attribute the call to the canonical API name (resolves aliases)
                calls.append({'func': bound[m.group(1)], 'line': i})
    return {'calls': calls, 'submodules': submodules,
            'imports_database': imports_database}


def iter_source_files(root: Path):
    """Yield every in-scope first-party ``.py`` file under *root*.

    Prunes inert dirs (incl. ``tests`` and the ``data`` symlink), the ``src/
    database`` seam itself, and the scanner modules."""
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _PRUNE_DIRS]
        rel_dir = Path(dirpath).relative_to(root).as_posix()
        if rel_dir == SANCTIONED_PACKAGE or rel_dir.startswith(SANCTIONED_PACKAGE + '/'):
            dirnames[:] = []
            continue
        for name in filenames:
            if name.endswith('.py') and name not in _SCANNER_MODULES:
                yield Path(dirpath) / name


def scan_repo(root: Path = None) -> dict:
    """Map database-seam usage across the first-party tree.

    Returns ``{'scanned', 'api_names', 'calls', 'by_file', 'caller_files',
    'by_func', 'used_funcs', 'unused_funcs', 'submodule_files', 'json_io_files',
    'json_reads', 'json_writes', 'both_files'}``. The ``.json`` complement is the
    4.5 backlog verbatim (single source of truth)."""
    root = Path(root) if root is not None else _root
    api_names = load_api_names(root)

    scanned = 0
    calls = []                       # [{'file', 'func', 'line'}]
    by_file = defaultdict(set)       # file -> {funcs}
    submodule_files = defaultdict(set)
    caller_files = set()
    for path in iter_source_files(root):
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        scanned += 1
        rel = _rel(path, root)
        res = scan_text(text, api_names)
        if res['imports_database'] or res['calls']:
            caller_files.add(rel)
        for c in res['calls']:
            calls.append({'file': rel, **c})
            by_file[rel].add(c['func'])
        if res['submodules']:
            submodule_files[rel] = res['submodules']

    by_func = defaultdict(set)
    for c in calls:
        by_func[c['func']].add(c['file'])
    used_funcs = set(by_func)
    unused_funcs = api_names - used_funcs

    # --- complement: modules still on .json (the 4.5 backlog, verbatim) -----
    from .json_files import scan_repo as _json_scan
    jscan = _json_scan(root)
    json_io_files = set(jscan['io_files'])
    both_files = sorted(caller_files & json_io_files)

    return {
        'scanned': scanned,
        'api_names': sorted(api_names),
        'calls': calls,
        'by_file': {f: sorted(v) for f, v in by_file.items()},
        'caller_files': sorted(caller_files),
        'by_func': {f: sorted(v) for f, v in by_func.items()},
        'used_funcs': sorted(used_funcs),
        'unused_funcs': sorted(unused_funcs),
        'submodule_files': {f: sorted(v) for f, v in submodule_files.items()},
        'json_io_files': sorted(json_io_files),
        'json_reads': jscan['reads'],
        'json_writes': jscan['writes'],
        'both_files': both_files,
    }


# ---------------------------------------------------------------------------
# Full-audit subsection (read-only render)
# ---------------------------------------------------------------------------
def _build_database_usage(styles) -> list:
    """4.6 — map database-seam adoption (callers -> functions) + .json complement."""
    elems = []
    elems.append(Spacer(1, 5 * mm))
    elems.append(Paragraph('4.6 Database-Usage Audit', styles['h3']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 2 * mm))

    scan = scan_repo()
    n_callers = len(scan['caller_files'])
    n_api = len(scan['api_names'])
    n_used = len(scan['used_funcs'])
    n_unused = len(scan['unused_funcs'])

    elems.append(Paragraph(
        f'Positive map of seam adoption: <b>{n_callers}</b> first-party module(s) '
        f'call the <b>database</b> package, exercising <b>{n_used}</b> of its '
        f'<b>{n_api}</b> public symbols (<b>{n_unused}</b> never called by '
        f'first-party code). Companion to 4.4 (no DB access outside src/database) '
        f'and 4.5 (no .json outside the seam) — here every call is mapped '
        f'file&nbsp;-&gt;&nbsp;function.', styles['body']))
    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(
        f'Complement — still on .json, not the seam: <b>{len(scan["json_io_files"])}'
        f'</b> module(s) (the 4.5 backlog: <b>{scan["json_reads"]}</b> load, '
        f'<b>{scan["json_writes"]}</b> create/update). '
        f'<b>{len(scan["both_files"])}</b> module(s) currently do both (mid-'
        f'migration).', styles['body']))

    if scan['unused_funcs']:
        elems.append(Spacer(1, 2 * mm))
        preview = ', '.join(scan['unused_funcs'][:18])
        more = (f' … +{n_unused - 18} more' if n_unused > 18 else '')
        elems.append(Paragraph(
            f'<b>Public functions never called by first-party code</b> '
            f'({n_unused}): {preview}{more}.', styles['body']))
    return elems
