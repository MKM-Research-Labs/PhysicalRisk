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

"""Subsection 4.7: model-chain consistency audit.

The **model chain** (the "string of pearls" dependency graph shown on the Model
Governance dashboard) is *hand-maintained* in
``docs/models/governance_data/model_inventory.json``.  Three pieces of that file
describe the same graph in three different places and can drift apart:

* ``model_chain.links`` — the ordered ``from → to`` handoffs the diagram draws.
* each model's ``downstream_models`` / ``upstream_models`` — the adjacency lists.
* each model's ``source_module`` — the file that actually implements the model.

Nothing in the app scans or regenerates these; the governance route
(``src/routes/governance/models.py``) and the diagram
(``src/static/js/governance/models/mg_chain.js``) *consume* them read-only.  So
when a model is renamed, moved, or re-wired, the JSON silently goes stale.

This module is the scanner that has been missing.  ``scan_model_chain`` loads the
inventory and cross-checks the three views for referential integrity, and
``_build_model_chain`` renders the read-only compliance subsection for the
consolidated audit report.  The scan is also exercised by the characterisation
test in ``tests/commands/test_model_chain_report.py``.

Finding kinds (all reported; none currently fail the build — see ``GATED``):

* ``link_unknown_model`` — a ``links`` entry names a ``from``/``to`` model_id
  that is not in the inventory.
* ``edge_unknown_model`` — a ``downstream_models``/``upstream_models`` entry
  names a model_id that is not in the inventory.
* ``link_not_in_downstream`` — a ``links`` entry ``A → B`` exists but ``B`` is
  absent from ``A.downstream_models`` (the diagram draws an edge the adjacency
  list does not know about).
* ``nonreciprocal_edge`` — ``A.downstream_models`` lists ``B`` but
  ``B.upstream_models`` omits ``A`` (or the mirror image), so the graph
  disagrees with itself about direction.
* ``source_module_missing`` — a model's ``source_module`` path does not exist on
  disk (typically a stale entry after a rename/move).
* ``source_module_absent`` — a model has no ``source_module`` at all, so the
  chain node cannot be traced back to code.
"""

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from .._constants import NAVY, _TBL_STYLE_BASE, _root
from reports.theme_pdf import pdf_colour

# This audit reports drift without failing the build: the inventory currently
# carries known stale entries (e.g. post-rename source_module paths).  Flip to
# True — and add a zero-tolerance assertion to the gate test — once the backlog
# in scan_model_chain()['findings'] reaches zero, mirroring the path-definition
# audit's history.
GATED = False


def _inventory_path() -> Path:
    """Locate model_inventory.json via config (single-sourced with the app)."""
    from config import config
    return config.get_governance_data_dir() / "model_inventory.json"


def load_inventory(path: Path = None) -> dict:
    """Read and parse the model inventory JSON. Returns {} if unreadable."""
    path = Path(path) if path is not None else _inventory_path()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def scan_model_chain(inventory: dict = None, root: Path = None) -> dict:
    """Cross-check the inventory's three views of the model dependency graph.

    Returns ``{'models', 'links', 'findings', 'checks'}`` where ``findings`` is a
    list of ``{'kind', 'model_id', 'detail'}`` records describing each
    inconsistency (empty == fully consistent).
    """
    if inventory is None:
        inventory = load_inventory()
    root = Path(root) if root is not None else _root

    models = inventory.get("models", []) or []
    links = (inventory.get("model_chain") or {}).get("links", []) or []
    by_id = {m.get("model_id"): m for m in models if m.get("model_id")}
    ids = set(by_id)

    findings = []

    def add(kind, model_id, detail):
        findings.append({"kind": kind, "model_id": model_id, "detail": detail})

    # 1) chain links must reference real models
    for link in links:
        frm, to = link.get("from"), link.get("to")
        for role, mid in (("from", frm), ("to", to)):
            if mid not in ids:
                add("link_unknown_model", mid or "<none>",
                    f"chain link {frm} → {to} references unknown '{role}' model")
        # 3) every drawn edge should be present in the source node's downstream list
        if frm in by_id and to in ids:
            if to not in (by_id[frm].get("downstream_models") or []):
                add("link_not_in_downstream", frm,
                    f"link {frm} → {to} not listed in {frm}.downstream_models")

    # 2) adjacency lists must reference real models; 4) and be reciprocal
    for m in models:
        mid = m.get("model_id")
        downs = m.get("downstream_models") or []
        ups = m.get("upstream_models") or []
        for d in downs:
            if d not in ids:
                add("edge_unknown_model", mid,
                    f"downstream_models references unknown model '{d}'")
            elif mid not in (by_id[d].get("upstream_models") or []):
                add("nonreciprocal_edge", mid,
                    f"{mid} lists {d} downstream, but {d} omits {mid} upstream")
        for u in ups:
            if u not in ids:
                add("edge_unknown_model", mid,
                    f"upstream_models references unknown model '{u}'")
            elif mid not in (by_id[u].get("downstream_models") or []):
                add("nonreciprocal_edge", mid,
                    f"{mid} lists {u} upstream, but {u} omits {mid} downstream")

        # 5/6) source_module must be present and exist on disk
        sm = m.get("source_module")
        if not sm:
            add("source_module_absent", mid, "model has no source_module")
        elif not (root / sm).exists():
            add("source_module_missing", mid, f"source_module not found: {sm}")

    return {
        "models": len(models),
        "links": len(links),
        "findings": findings,
        "checks": {
            "link_unknown_model": sum(1 for f in findings if f["kind"] == "link_unknown_model"),
            "edge_unknown_model": sum(1 for f in findings if f["kind"] == "edge_unknown_model"),
            "link_not_in_downstream": sum(1 for f in findings if f["kind"] == "link_not_in_downstream"),
            "nonreciprocal_edge": sum(1 for f in findings if f["kind"] == "nonreciprocal_edge"),
            "source_module_missing": sum(1 for f in findings if f["kind"] == "source_module_missing"),
            "source_module_absent": sum(1 for f in findings if f["kind"] == "source_module_absent"),
        },
    }


# ---------------------------------------------------------------------------
# Full-audit subsection (read-only render)
# ---------------------------------------------------------------------------
_KIND_LABEL = {
    "link_unknown_model": "Chain link → unknown model",
    "edge_unknown_model": "Adjacency → unknown model",
    "link_not_in_downstream": "Drawn edge missing from downstream_models",
    "nonreciprocal_edge": "Non-reciprocal upstream/downstream",
    "source_module_missing": "source_module file not found",
    "source_module_absent": "source_module absent",
}


def _build_model_chain(styles) -> list:
    """4.7 — report model-chain consistency across the model inventory."""
    elems = []
    elems.append(Spacer(1, 5 * mm))
    elems.append(Paragraph('4.7 Model-Chain Consistency Audit', styles['h3']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(
        'The model dependency chain (the "string of pearls" on the Model '
        'Governance dashboard) is hand-maintained in '
        '<b>docs/models/governance_data/model_inventory.json</b> and consumed '
        'read-only by the governance route and the mg_chain diagram — nothing '
        'scans or regenerates it. This audit cross-checks its three overlapping '
        'views for referential integrity: the <b>model_chain.links</b> the '
        'diagram draws, each model’s <b>upstream/downstream_models</b> '
        'adjacency lists, and each model’s <b>source_module</b> on disk. '
        'Findings indicate the JSON has drifted from the code (typically after a '
        'model rename, move, or re-wiring).', styles['body']))
    elems.append(Spacer(1, 2 * mm))

    try:
        scan = scan_model_chain()
    except Exception as exc:
        elems.append(Paragraph(
            f'Could not run model-chain audit: {exc}', styles['body']))
        return elems

    findings = scan['findings']
    from ..results_json import write_results
    write_results('model_chain', {
        'models': scan['models'],
        'links': scan['links'],
        'inconsistencies': len(findings),
    })
    elems.append(Paragraph(
        f'Models: <b>{scan["models"]}</b> &nbsp;|&nbsp; '
        f'Chain links: <b>{scan["links"]}</b> &nbsp;|&nbsp; '
        f'Inconsistencies: <b>{len(findings)}</b>.', styles['body']))
    elems.append(Spacer(1, 2 * mm))

    if not findings:
        elems.append(Paragraph(
            'The chain links, adjacency lists, and source modules are mutually '
            'consistent. <b>PASS</b>', styles['body']))
        return elems

    elems.append(Paragraph(
        f'{len(findings)} inconsistency(ies) found (showing up to 30). Reconcile '
        'model_inventory.json with the current model wiring.', styles['body']))
    elems.append(Spacer(1, 2 * mm))
    data = [[
        Paragraph('<b>Model</b>', styles['tbl_hdr']),
        Paragraph('<b>Kind</b>', styles['tbl_hdr']),
        Paragraph('<b>Detail</b>', styles['tbl_hdr']),
    ]]
    for r in findings[:30]:
        data.append([
            Paragraph(r['model_id'], styles['tbl_cell']),
            Paragraph(_KIND_LABEL.get(r['kind'], r['kind']), styles['tbl_cell']),
            Paragraph(r['detail'][:110], styles['tbl_cell']),
        ])
    tbl = Table(data, colWidths=[30 * mm, 46 * mm, 92 * mm])
    tbl.setStyle(TableStyle(list(_TBL_STYLE_BASE) + [
        ('BACKGROUND', (0, 1), (-1, -1), pdf_colour('warn-bg-warm')),
    ]))
    elems.append(tbl)
    return elems
