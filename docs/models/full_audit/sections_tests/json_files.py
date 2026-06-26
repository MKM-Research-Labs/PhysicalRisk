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

"""Subsection 4.5: JSON-file audit (json->postgres zero-tolerance tracker).

Sibling to the data-access audit (4.4). **Policy goal: no first-party module
loads, creates, or updates a ``.json`` file on disk** — every such artifact
(port data, governance inventory, market/trading state, classifiers, …) lives
in PostgreSQL behind the single ``src/database`` seam, reached through the
``database`` public API.

The JSON->Postgres migration is ~90% complete, so this is currently a **tracked
report, not a gate**: it enumerates the remaining backlog of ``.py`` modules
still bound to ``.json`` files, split into *load* (reads) and *create/update*
(writes), and surfaces it for visibility — it never fails the build. The switch
to a hard gate is a single flag flip (``GATED = True``): the gate test already
asserts the enforcement path so the zero-tolerance day is one line away.

A finding is a non-comment, non-docstring line — **anywhere in first-party code,
including the ``src/database`` seam** (only ``tests/`` and inert non-source dirs
are skipped) — that either calls ``json.load(`` / ``json.dump(`` (file
(de)serialisation) or names a ``".json"`` path literal. Each finding carries a
``kind``:

* ``read``  — ``json.load(`` or a ``.json`` literal alongside ``open`` /
  ``read_text`` / ``read_bytes`` / ``glob`` / ``read_json``.
* ``write`` — ``json.dump(`` or a ``.json`` literal alongside ``open(...,'w'/'a')``
  / ``write_text`` / ``write_bytes`` / ``to_json``.
* ``ref``   — a ``.json`` literal that is neither (e.g. building a path, passing a
  filename onward); still a binding to a JSON file, so still tracked.

The prune-dir set is shared with the data-access scanner (4.4); the walker here
deliberately drops that audit's ``src/database`` exemption.
"""

import os
import re
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer

from .._constants import NAVY, _root
from .data_access import _PRUNE_DIRS, _rel

# Unlike the data-access audit (4.4), this audit does NOT exempt ``src/database``:
# the zero-tolerance goal is *no .json files anywhere*, so the seam's own file
# backend is in scope and surfaced too. Only ``tests/`` (scratch I/O) and the
# inert non-source prune dirs are skipped, plus the two scanner modules whose
# source literally contains the detection patterns (they would self-match).
_SCANNER_MODULES = {'json_files.py', 'data_access.py'}

# Flip to True once the backlog reaches zero to turn the tracker into a
# zero-tolerance gate (the gate test honours this flag).
GATED = False

# First-party files exempt by explicit, justified registration — JSON files that
# are intentionally NOT migrating to the database (kept minimal; reviewed by the
# allowlist test, which removes stale entries automatically).
_ALLOWLIST = {
    # (none yet — every .json touch is tracked backlog)
}

# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------
# A ``".json"`` filename literal anywhere on the line — the strongest signal
# that a module is bound to a JSON file on disk.
_JSON_LITERAL_RE = re.compile(r"""['"][^'"]*\.json['"]""")
# File-object (de)serialisation (``json.load(fp)`` / ``json.dump(obj, fp)``);
# the trailing-(`` excludes the string forms ``json.loads`` / ``json.dumps``.
_JSON_LOAD_RE = re.compile(r'\bjson\.load\s*\(')
_JSON_DUMP_RE = re.compile(r'\bjson\.dump\s*\(')
# Read / write hints used to classify a bare ``.json`` literal line.
_READ_HINT_RE = re.compile(
    r'\bopen\s*\(|\.read_text\b|\.read_bytes\b|\.glob\s*\(|\bread_json\s*\(')
_WRITE_HINT_RE = re.compile(
    r"""\bopen\s*\([^)]*['"][wax]|\.write_text\b|\.write_bytes\b|\.to_json\s*\(""")


def _classify(line: str):
    """Return ``'read'`` / ``'write'`` / ``'ref'`` for a JSON-file line, else None."""
    if _JSON_DUMP_RE.search(line):
        return 'write'
    if _JSON_LOAD_RE.search(line):
        return 'read'
    if _JSON_LITERAL_RE.search(line):
        if _WRITE_HINT_RE.search(line):
            return 'write'
        if _READ_HINT_RE.search(line):
            return 'read'
        return 'ref'
    return None


def scan_text(text: str) -> list:
    """Return ``[{'line', 'kind', 'snippet'}, …]`` JSON-file findings for one file.

    Comment lines and triple-quoted block interiors are skipped, so prose and
    examples that mention ``.json`` are not mistaken for live file access."""
    findings = []
    in_doc = None  # active triple-quote delimiter, or None
    for i, line in enumerate(text.splitlines(), 1):
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
        kind = _classify(line)
        if kind is not None:
            findings.append({'line': i, 'kind': kind, 'snippet': stripped[:90]})
    return findings


def iter_source_files(root: Path):
    """Yield every in-scope first-party ``.py`` file under *root*.

    Prunes the inert non-source dirs (incl. ``tests`` and the ``data`` symlink)
    and skips the two scanner modules whose source contains the detection
    patterns. Unlike the data-access walker, ``src/database`` is **not** skipped —
    the seam's own ``.json`` file I/O is in scope for the zero-tolerance goal."""
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _PRUNE_DIRS]
        for name in filenames:
            if name.endswith('.py') and name not in _SCANNER_MODULES:
                yield Path(dirpath) / name


def scan_repo(root: Path = None) -> dict:
    """Scan the first-party tree for ``.json``-file access (incl. ``src/database``).

    Returns ``{'scanned', 'findings', 'files', 'io_findings', 'io_files',
    'reads', 'writes', 'refs', 'allowlisted'}``. ``findings`` is every .json
    touch; ``io_findings`` is the load + create/update subset — the gated set
    once ``GATED`` flips. The read/write/ref counts split loads from
    creates/updates from bare path references."""
    root = Path(root) if root is not None else _root
    findings, allowlisted = [], []
    scanned = 0
    for path in iter_source_files(root):
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        scanned += 1
        rel = _rel(path, root)
        for f in scan_text(text):
            rec = {'file': rel, **f}
            if rel in _ALLOWLIST:
                rec['reason'] = _ALLOWLIST[rel]
                allowlisted.append(rec)
            else:
                findings.append(rec)
    reads = sum(1 for f in findings if f['kind'] == 'read')
    writes = sum(1 for f in findings if f['kind'] == 'write')
    refs = sum(1 for f in findings if f['kind'] == 'ref')
    # The actionable backlog is the load + create/update I/O — the literal
    # "loads, creates, or updates a .json file" policy. Bare ``.json`` path/
    # filename literals (``ref``) are softer downstream cleanup: tracked, but
    # never the gated set even once GATED flips.
    io_findings = [f for f in findings if f['kind'] in ('read', 'write')]
    return {
        'scanned': scanned,
        'findings': findings,
        'files': sorted({f['file'] for f in findings}),
        'io_findings': io_findings,
        'io_files': sorted({f['file'] for f in io_findings}),
        'reads': reads,
        'writes': writes,
        'refs': refs,
        'allowlisted': allowlisted,
    }


# ---------------------------------------------------------------------------
# Full-audit subsection (read-only render)
# ---------------------------------------------------------------------------
_KIND_LABEL = {'read': 'load', 'write': 'create/update', 'ref': 'path reference'}


def _build_json_files(styles) -> list:
    """4.5 — track ``.py`` modules still bound to ``.json`` files on disk."""
    elems = []
    elems.append(Spacer(1, 5 * mm))
    elems.append(Paragraph('4.5 JSON-File Audit', styles['h3']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 2 * mm))

    scan = scan_repo()
    n_io = len(scan['io_files'])
    status = ('GATE PASS' if not scan['io_findings'] else
              f'GATE FAIL ({n_io} file(s))') if GATED else 'TRACKING'

    elems.append(Paragraph(
        f'Policy goal: <b>no module loads, creates, or updates a .json file on '
        f'disk</b> — all such state lives in PostgreSQL behind src/database '
        f'(the seam itself is in scope; only tests/ are exempt). '
        f'Mode: <b>{status}</b>. Scanned <b>{scan["scanned"]}</b> files.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(
        f'JSON-file I/O backlog (the gated set): <b>{n_io}</b> file(s) '
        f'still load or create/update .json directly — '
        f'<b>{scan["reads"]}</b> load, <b>{scan["writes"]}</b> create/update. '
        f'This shrinks to zero as each artifact moves onto the database seam, at '
        f'which point the audit flips to a zero-tolerance gate.', styles['body']))
    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(
        f'Plus <b>{scan["refs"]}</b> bare .json path/filename reference(s) '
        f'(tracked, non-gating downstream cleanup).', styles['body']))

    if scan['io_findings']:
        elems.append(Spacer(1, 2 * mm))
        for f in scan['io_findings'][:40]:
            elems.append(Paragraph(
                f'• {f["file"]}:{f["line"]} — '
                f'{_KIND_LABEL.get(f["kind"], f["kind"])}', styles['body']))
        if len(scan['io_findings']) > 40:
            elems.append(Paragraph(
                f'… +{len(scan["io_findings"]) - 40} more I/O finding(s)',
                styles['body']))
    return elems
