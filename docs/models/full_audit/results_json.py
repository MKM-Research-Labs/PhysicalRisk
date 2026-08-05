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

"""Shared JSON sink/source for audit summaries.

Each audit renders a human PDF; this lets it *also* drop a compact
``<name>_results.json`` next to that PDF so downstream tooling (the
test-interpretation assessment) can read structured counts instead of parsing
the PDF. Convention: ``{"generated_at": <iso>, "summary": {...}}`` — matching the
shape ``init_audit`` already writes.
"""

import json
from datetime import datetime

from ._constants import AUDIT_DIR


def write_results(name: str, summary: dict) -> None:
    """Write ``<name>_results.json`` (with a timestamp) into the audit dir."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'summary': summary,
    }
    with open(AUDIT_DIR / f'{name}_results.json', 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, indent=2)


def read_results(name: str):
    """Return the counts dict from ``<name>_results.json``, or None if the file
    is absent or unreadable (so consumers degrade gracefully). Prefers the
    ``summary`` block, falling back to the whole document for audits (e.g.
    data_lineage) that write a flat shape."""
    path = AUDIT_DIR / f'{name}_results.json'
    if not path.exists():
        return None
    try:
        with open(path, encoding='utf-8') as fh:
            data = json.load(fh)
        return data.get('summary', data) if isinstance(data, dict) else None
    except Exception:
        return None
