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

"""Model-chain consistency audit — scan logic and full-audit section.

Sits with the other audit-report tests (test_path_definitions_report.py,
test_copyright_headers_report.py, …) and runs under ``phys.py test``.

``scan_model_chain`` cross-checks the three overlapping views of the model
dependency graph in ``model_inventory.json`` (chain links, upstream/downstream
adjacency, source_module on disk).  ``TestModelChainScanLogic`` pins the
detect/skip behaviour against synthetic inventories, ``TestModelChainRealData``
runs the scan against the committed inventory (characterisation, non-gating
while ``GATED`` is False), and ``TestModelChainSection`` smoke-tests the
full-audit subsection builder.
"""

from pathlib import Path

from docs.models.full_audit.sections_tests import model_chain as scanner

# tests/commands/test_model_chain_report.py -> repo root
ROOT = Path(__file__).resolve().parents[2]

_FINDING_KINDS = {
    "link_unknown_model", "edge_unknown_model", "link_not_in_downstream",
    "nonreciprocal_edge", "source_module_missing", "source_module_absent",
}


def _inv(models, links):
    return {"models": models, "model_chain": {"links": links}}


class TestModelChainScanLogic:
    """Detect/skip behaviour pinned against synthetic inventories."""

    def test_consistent_inventory_has_no_findings(self):
        # A → B, wired reciprocally, both source_modules exist (this test file).
        rel = "tests/commands/test_model_chain_report.py"
        models = [
            {"model_id": "MKM-A-001", "downstream_models": ["MKM-B-001"],
             "upstream_models": [], "source_module": rel},
            {"model_id": "MKM-B-001", "downstream_models": [],
             "upstream_models": ["MKM-A-001"], "source_module": rel},
        ]
        links = [{"from": "MKM-A-001", "to": "MKM-B-001"}]
        scan = scanner.scan_model_chain(_inv(models, links), root=ROOT)
        assert scan["findings"] == []
        assert scan["models"] == 2 and scan["links"] == 1

    def test_link_to_unknown_model_flagged(self):
        models = [{"model_id": "MKM-A-001", "downstream_models": [],
                   "upstream_models": [], "source_module": None}]
        links = [{"from": "MKM-A-001", "to": "MKM-GHOST-001"}]
        scan = scanner.scan_model_chain(_inv(models, links), root=ROOT)
        kinds = {f["kind"] for f in scan["findings"]}
        assert "link_unknown_model" in kinds

    def test_drawn_edge_absent_from_downstream_flagged(self):
        rel = "tests/commands/test_model_chain_report.py"
        models = [
            {"model_id": "MKM-A-001", "downstream_models": [],
             "upstream_models": [], "source_module": rel},
            {"model_id": "MKM-B-001", "downstream_models": [],
             "upstream_models": [], "source_module": rel},
        ]
        links = [{"from": "MKM-A-001", "to": "MKM-B-001"}]
        scan = scanner.scan_model_chain(_inv(models, links), root=ROOT)
        assert any(f["kind"] == "link_not_in_downstream" for f in scan["findings"])

    def test_nonreciprocal_edge_flagged(self):
        rel = "tests/commands/test_model_chain_report.py"
        models = [
            {"model_id": "MKM-A-001", "downstream_models": ["MKM-B-001"],
             "upstream_models": [], "source_module": rel},
            {"model_id": "MKM-B-001", "downstream_models": [],
             "upstream_models": [], "source_module": rel},  # omits A upstream
        ]
        scan = scanner.scan_model_chain(_inv(models, []), root=ROOT)
        assert any(f["kind"] == "nonreciprocal_edge" for f in scan["findings"])

    def test_missing_and_absent_source_module_flagged(self):
        models = [
            {"model_id": "MKM-A-001", "downstream_models": [],
             "upstream_models": [], "source_module": "src/does/not/exist.py"},
            {"model_id": "MKM-B-001", "downstream_models": [],
             "upstream_models": []},  # no source_module key
        ]
        scan = scanner.scan_model_chain(_inv(models, []), root=ROOT)
        kinds = {f["kind"] for f in scan["findings"]}
        assert "source_module_missing" in kinds
        assert "source_module_absent" in kinds

    def test_missing_inventory_returns_empty_scan(self):
        scan = scanner.scan_model_chain({}, root=ROOT)
        assert scan["models"] == 0 and scan["links"] == 0
        assert scan["findings"] == []


class TestModelChainRealData:
    """Characterisation against the committed inventory.

    Non-gating while GATED is False (the inventory carries known drift). When the
    backlog is cleared, flip scanner.GATED to True and this asserts zero findings.
    """

    def test_scan_runs_and_is_well_formed(self):
        scan = scanner.scan_model_chain(root=ROOT)
        assert scan["models"] > 0, "real inventory should have models"
        assert isinstance(scan["findings"], list)
        for f in scan["findings"]:
            assert f["kind"] in _FINDING_KINDS
            assert set(f) == {"kind", "model_id", "detail"}
        # check counts sum to the finding count
        assert sum(scan["checks"].values()) == len(scan["findings"])

    def test_gate_when_enabled(self):
        scan = scanner.scan_model_chain(root=ROOT)
        if scanner.GATED and scan["findings"]:
            lines = [f"  {f['model_id']}  [{f['kind']}]  {f['detail']}"
                     for f in scan["findings"][:40]]
            raise AssertionError(
                f"{len(scan['findings'])} model-chain inconsistency(ies) in "
                "model_inventory.json:\n" + "\n".join(lines))


class TestModelChainSection:
    """Full-audit subsection builder smoke test."""

    def test_build_returns_flowables(self):
        from docs.models.full_audit.styles import _styles
        elems = scanner._build_model_chain(_styles())
        assert elems and isinstance(elems, list)
