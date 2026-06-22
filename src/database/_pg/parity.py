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

"""Dual-read parity harness (JSON→Postgres WP1.7).

The regression net for the cutover: for every tier-1 artifact of a catchment,
read it from the file backend and from Postgres and assert the two documents are
equal. This is what lets WP2 flip catchments one at a time with confidence.

The one subtlety is record order. ``PostgresRepository`` reassembles a collection
in *id* order, while the file backend preserves *source-file* order, so a positional
``==`` on real data flags false diffs. The harness therefore normalises every list
collection by id before comparing (dict collections and the document envelope are
already order-independent under ``==``).

Pure ``Repository`` calls — no SQL of its own. It lives under ``_pg`` only because
it reuses the artifact maps (``_COLLECTIONS`` / ``_KEYED``) that define how each
document shreds into rows.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config_binding import from_config
from .pg_repo import _COLLECTIONS, _KEYED, PostgresRepository, _nested_get


@dataclass
class ParityResult:
    """Outcome of one artifact's file-vs-pg comparison."""

    artifact: str
    kind: str          # "collection" | "keyed"
    equal: bool
    file_count: int
    pg_count: int
    detail: str = ""   # one-line description of the first diff; "" when equal


def _record_id(record, id_path) -> str:
    """The id Postgres orders a collection by — stringified for a total order."""
    try:
        return str(_nested_get(record, id_path))
    except (KeyError, TypeError):
        return ""


def normalize_collection(artifact: str, doc: dict) -> dict:
    """Return ``doc`` with its record list sorted by id, so two backends that
    differ only in record order compare equal. Dict-container collections and the
    envelope already compare order-independently, so they are returned as-is."""
    _model, _id_col, ckey, ctype, id_path = _COLLECTIONS[artifact]
    if ctype != "list":
        return doc
    records = doc.get(ckey)
    if not isinstance(records, list):
        return doc
    out = dict(doc)
    out[ckey] = sorted(records, key=lambda r: _record_id(r, id_path))
    return out


def _count(doc: dict, ckey: str, ctype: str) -> int:
    container = doc.get(ckey)
    return len(container or ({} if ctype == "dict" else []))


def _diff_detail(file_doc, pg_doc) -> str:
    """Best-effort one-line description of where two documents first differ."""
    if not isinstance(file_doc, dict) or not isinstance(pg_doc, dict):
        return "values differ"
    fk, pk = set(file_doc), set(pg_doc)
    if fk != pk:
        return f"top-level keys differ: only-file={fk - pk}, only-pg={pk - fk}"
    for key in sorted(fk):
        if file_doc[key] != pg_doc[key]:
            return f"value for '{key}' differs"
    return "documents differ"  # pragma: no cover - only reached if called on equal docs


def check_collection(artifact, catchment, file_repo, pg) -> ParityResult | None:
    """Compare one collection artifact; ``None`` when absent from both backends."""
    file_present = file_repo.exists(artifact, catchment)
    pg_present = pg.exists(artifact, catchment)
    if not file_present and not pg_present:
        return None
    if file_present != pg_present:
        only = "file" if file_present else "pg"
        return ParityResult(artifact, "collection", False,
                            int(file_present), int(pg_present),
                            f"present only in {only} backend")
    _model, _id_col, ckey, ctype, _id_path = _COLLECTIONS[artifact]
    file_doc = normalize_collection(artifact, file_repo.load(artifact, catchment))
    pg_doc = normalize_collection(artifact, pg.load(artifact, catchment))
    equal = file_doc == pg_doc
    return ParityResult(artifact, "collection", equal,
                        _count(file_doc, ckey, ctype), _count(pg_doc, ckey, ctype),
                        "" if equal else _diff_detail(file_doc, pg_doc))


def check_keyed(artifact, catchment, file_repo, pg) -> ParityResult:
    """Compare one keyed artifact: the key sets must match, then each record."""
    file_keys = sorted(file_repo.iter_keys(artifact, catchment))
    pg_keys = sorted(pg.iter_keys(artifact, catchment))
    if file_keys != pg_keys:
        fk, pk = set(file_keys), set(pg_keys)
        return ParityResult(artifact, "keyed", False, len(file_keys), len(pg_keys),
                            f"key sets differ: only-file={fk - pk}, only-pg={pk - fk}")
    for key in file_keys:
        file_rec = file_repo.load(artifact, catchment, key)
        pg_rec = pg.load(artifact, catchment, key)
        if file_rec != pg_rec:
            return ParityResult(artifact, "keyed", False, len(file_keys), len(pg_keys),
                                f"record '{key}' differs: {_diff_detail(file_rec, pg_rec)}")
    return ParityResult(artifact, "keyed", True, len(file_keys), len(pg_keys))


def check_catchment(catchment, *, file_repo=None, pg=None) -> list[ParityResult]:
    """Run every tier-1 parity check for ``catchment``.

    Defaults read via the config-bound file backend and a fresh
    ``PostgresRepository``; both are injectable for tests. Collection artifacts
    absent from both backends are skipped (omitted from the report)."""
    file_repo = file_repo if file_repo is not None else from_config()
    pg = pg if pg is not None else PostgresRepository()
    results: list[ParityResult] = []
    for artifact in _COLLECTIONS:
        result = check_collection(artifact, catchment, file_repo, pg)
        if result is not None:
            results.append(result)
    for artifact in _KEYED:
        results.append(check_keyed(artifact, catchment, file_repo, pg))
    return results


def all_ok(results) -> bool:
    """True when every check passed."""
    return all(r.equal for r in results)


def format_report(catchment, results) -> str:
    """Human-readable summary for CI logs."""
    lines = [f"dual-read parity — catchment '{catchment}'"]
    for r in results:
        tag = "OK  " if r.equal else "FAIL"
        extra = f"  ({r.detail})" if r.detail else ""
        lines.append(f"  [{tag}] {r.artifact:<20} file={r.file_count} pg={r.pg_count}{extra}")
    lines.append("ALL PARITY CHECKS PASSED" if all_ok(results)
                 else "PARITY MISMATCHES FOUND")
    return "\n".join(lines)
