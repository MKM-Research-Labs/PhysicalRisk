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

"""Copyright-header audit — detect, fix and record license headers.

Every first-party ``.py`` and ``.js`` source file must begin with the exact
19-line MKM Research Labs license header defined in ``docs/shared/copyright.py``
— the single source of truth.  This module walks the tree, rewrites any file
whose header is missing or differs (byte-for-byte, including the intentional
trailing whitespace on a few lines of the canonical text), and returns a
per-file record so the audit report can state, for each non-compliant file:

  a) the file had the wrong (or missing) header,
  b) the header was replaced, and
  c) the file is now compatible.

For ``.py`` files the canonical lines are used verbatim; for ``.js`` the same
text is re-emitted with ``//`` comment prefixes.  Only a *license* block is ever
replaced — a file's first ordinary comment (a TODO, a section banner) is kept,
with the header inserted above it.  A leading ``#!`` shebang is preserved.
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Single source of truth for the canonical license text.
_CANONICAL_SOURCE = ('docs', 'shared', 'copyright.py')

# Directories never descended during the scan: vendored code, caches, the
# ``data`` symlink to the shared SSD, and sibling/nested git worktrees (which
# live under .claude / .claire and would otherwise have their copies rewritten).
_PRUNE_DIRS = {
    '.git', '.claude', '.claire', 'worktrees',
    '__pycache__', 'node_modules', '.venv', 'venv',
    'data', 'dist', 'build', '.pytest_cache', '.mypy_cache', '.ruff_cache',
}

# Substrings (matched case-insensitively) that mark an existing — but possibly
# wrong — license block, so we replace a header and never a file's first real
# comment.
_LICENSE_MARKERS = ('mkm research labs', 'copyright (c)', 'all rights reserved')

# Source extensions in scope, mapped to their line-comment prefix.
_COMMENT_CHAR = {'.py': '#', '.js': '//'}


# ---------------------------------------------------------------------------
# Canonical header
# ---------------------------------------------------------------------------
def canonical_source_path(root: Path) -> Path:
    return Path(root).joinpath(*_CANONICAL_SOURCE)


def load_canonical_py(root: Path):
    """Return the canonical header as a list of ``#``-prefixed lines, read
    verbatim from copyright.py (intentional trailing whitespace preserved)."""
    text = canonical_source_path(root).read_text(encoding='utf-8')
    return text.splitlines()


def _to_js(py_lines):
    """Re-emit the ``#``-prefixed canonical lines with ``//`` prefixes."""
    out = []
    for ln in py_lines:
        if ln == '':
            out.append('//')
        elif ln.startswith('# '):
            out.append('// ' + ln[2:])
        elif ln == '#':
            out.append('//')
        else:
            out.append(ln)  # defensive: canonical is all comments/blanks
    return out


def canonical_lines(root: Path, ext: str):
    """Canonical header lines for the given source extension (.py or .js)."""
    py = load_canonical_py(root)
    return py if ext == '.py' else _to_js(py)


# ---------------------------------------------------------------------------
# Compliance check + repair
# ---------------------------------------------------------------------------
def _is_shebang(line: str) -> bool:
    return line.startswith('#!')


def is_compliant(text: str, canon) -> bool:
    """True when *text* begins with the canonical header, allowing an optional
    shebang line and an optional single blank line after it."""
    lines = text.splitlines()
    i = 0
    if lines and _is_shebang(lines[0]):
        i = 1
        if i < len(lines) and lines[i] == '':
            i += 1
    return lines[i:i + len(canon)] == list(canon)


def fix_text(text: str, canon, ext: str):
    """Return ``(new_text, old_header)`` when *text* is non-compliant, else
    ``(None, None)``.

    An existing license block (identified by ``_LICENSE_MARKERS``) is replaced;
    otherwise the header is inserted at the top.  A shebang and any non-license
    leading comment are preserved.  ``old_header`` is the replaced block (empty
    string when no header was present).
    """
    if is_compliant(text, canon):
        return None, None

    lines = text.splitlines()
    comment_char = _COMMENT_CHAR[ext]

    shebang = None
    idx = 0
    if lines and _is_shebang(lines[0]):
        shebang = lines[0]
        idx = 1

    # Maximal run of leading blank/comment lines after the shebang.
    k = idx
    while k < len(lines):
        stripped = lines[k].strip()
        if stripped == '' or stripped.startswith(comment_char):
            k += 1
        else:
            break
    leading = lines[idx:k]
    has_license = any(
        any(m in ln.lower() for m in _LICENSE_MARKERS) for ln in leading
    )

    if has_license:
        old_header = '\n'.join(leading).strip()
        body = lines[k:]
    else:
        # Header-less (or only non-license leading comments): keep everything
        # below the shebang and insert the header above it.
        old_header = ''
        body = lines[idx:]

    # Re-insert exactly one blank line between header and body.
    while body and body[0].strip() == '':
        body.pop(0)

    out = []
    if shebang is not None:
        out.append(shebang)
        out.append('')
    out.extend(canon)
    if body:
        out.append('')
        out.extend(body)
    new_text = '\n'.join(out) + '\n'
    return new_text, old_header


# ---------------------------------------------------------------------------
# Repo-wide scan
# ---------------------------------------------------------------------------
def iter_source_files(root: Path):
    """Yield ``(path, ext)`` for every in-scope .py/.js file under *root*,
    pruning vendored/cache dirs and skipping the canonical source itself."""
    root = Path(root)
    canon_src = canonical_source_path(root).resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _PRUNE_DIRS]
        for name in filenames:
            ext = os.path.splitext(name)[1]
            if ext not in _COMMENT_CHAR:
                continue
            path = Path(dirpath) / name
            if path.resolve() == canon_src:
                continue
            yield path, ext


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def fix_repo(root: Path, apply: bool = True) -> dict:
    """Scan every in-scope file under *root*, repairing non-compliant headers.

    With ``apply=True`` the rewrites are written to disk; with ``apply=False``
    nothing is written (a dry run that still reports what *would* change).
    """
    root = Path(root)
    canon_py = load_canonical_py(root)
    canon_js = _to_js(canon_py)

    fixed, remaining = [], []
    already_compliant = 0
    scanned = 0

    for path, ext in iter_source_files(root):
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        scanned += 1
        canon = canon_py if ext == '.py' else canon_js
        if is_compliant(text, canon):
            already_compliant += 1
            continue

        new_text, old_header = fix_text(text, canon, ext)
        rec = {
            'file': _rel(path, root),
            'old_header': old_header or '(no header present)',
            'had_wrong_header': True,
        }
        if apply and new_text is not None:
            path.write_text(new_text, encoding='utf-8')
            rec['now_compliant'] = is_compliant(new_text, canon)
            fixed.append(rec)
        else:
            rec['now_compliant'] = False
            remaining.append(rec)

    return {
        'scanned': scanned,
        'already_compliant': already_compliant,
        'fixed': fixed,
        'remaining': remaining,
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
