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

"""Tests for docs.models.data_lineage — BCBS 239 data lineage PDF generator."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

SAMPLE_MANIFEST = {
    "runs": {
        "run-20260320-120000": ["gauges", "properties", "hazard"],
    },
    "steps": {
        "gauges": {
            "run_id": "run-20260320-120000",
            "timestamp": "2026-03-20T12:00:00",
            "generator": "port (step 1)",
            "status": "success",
            "elapsed_seconds": 2.5,
            "parameters": {"catchment": "thames"},
            "inputs": {},
            "outputs": {
                "gauge.json": {
                    "hash": "abc123def456",
                    "type": "file",
                },
            },
        },
        "properties": {
            "run_id": "run-20260320-120100",
            "timestamp": "2026-03-20T12:01:00",
            "generator": "port (step 2)",
            "status": "success",
            "elapsed_seconds": 1.8,
            "parameters": {},
            "inputs": {
                "gauge.json": {
                    "hash": "abc123def456",
                    "type": "file",
                },
            },
            "outputs": {
                "property.json": {
                    "hash": "789ghi012jkl",
                    "type": "file",
                },
            },
        },
        "hazard": {
            "run_id": "run-20260320-120200",
            "timestamp": "2026-03-20T12:02:00",
            "generator": "port (step 6)",
            "status": "success",
            "elapsed_seconds": 5.1,
            "parameters": {"model": "gev"},
            "inputs": {
                "gauge.json": {
                    "hash": "abc123def456",
                    "type": "file",
                },
            },
            "outputs": {
                "gaugehc.json": {
                    "hash": "mno345pqr678",
                    "type": "file",
                },
            },
        },
    },
}

SAMPLE_LINEAGE_RESULTS = {
    "total": 15,
    "passed": 14,
    "failed": 1,
    "skipped": 0,
    "failures": [
        {
            "name": "test_trade_gauges_exist_in_gauge_json",
            "message": "1 trade gauge_id not found in gauge.json",
        },
    ],
}

SAMPLE_LINEAGE_RESULTS_CLEAN = {
    "total": 15,
    "passed": 15,
    "failed": 0,
    "skipped": 0,
    "failures": [],
}

SAMPLE_CHAIN_CONSISTENT = {
    "is_consistent": True,
    "stale_steps": [],
    "missing_steps": [],
    "details": {},
}

SAMPLE_CHAIN_ISSUES = {
    "is_consistent": False,
    "stale_steps": ["hazard", "blotter"],
    "missing_steps": ["propertyhc"],
    "details": {
        "hazard": [
            "Input 'gauge.json' is stale: producer 'gauges' hash "
            "changed (abc123.. -> def456..)",
        ],
    },
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def dl_mod():
    """Import data_lineage module."""
    from docs.models import data_lineage
    return data_lineage


@pytest.fixture
def sample_data_consistent(dl_mod):
    """Collected data dict with a consistent pipeline."""
    return {
        "manifest": SAMPLE_MANIFEST,
        "graph": {
            "gauges": [],
            "properties": ["gauges"],
            "hazard": ["gauges"],
        },
        "step_io": {
            "gauges": {"inputs": [], "outputs": ["gauge.json"]},
            "properties": {"inputs": ["gauge.json"],
                           "outputs": ["property.json"]},
            "hazard": {"inputs": ["gauge.json"],
                       "outputs": ["gaugehc.json"]},
        },
        "chain_result": SAMPLE_CHAIN_CONSISTENT,
        "lineage_results": SAMPLE_LINEAGE_RESULTS_CLEAN,
        "step_details": [
            {
                "step": "gauges",
                "dependencies": [],
                "inputs": [],
                "outputs": ["gauge.json"],
                "generator": "port (step 1)",
                "run_id": "run-20260320-120000",
                "timestamp": "2026-03-20T12:00:00",
                "elapsed_s": 2.5,
                "status": "fresh",
                "hash_status": "success",
                "parameters": {"catchment": "thames"},
                "input_hashes": {},
                "output_hashes": {"gauge.json": {"hash": "abc123"}},
            },
            {
                "step": "properties",
                "dependencies": ["gauges"],
                "inputs": ["gauge.json"],
                "outputs": ["property.json"],
                "generator": "port (step 2)",
                "run_id": "run-20260320-120100",
                "timestamp": "2026-03-20T12:01:00",
                "elapsed_s": 1.8,
                "status": "fresh",
                "hash_status": "success",
                "parameters": {},
                "input_hashes": {"gauge.json": {"hash": "abc123"}},
                "output_hashes": {"property.json": {"hash": "789ghi"}},
            },
            {
                "step": "hazard",
                "dependencies": ["gauges"],
                "inputs": ["gauge.json"],
                "outputs": ["gaugehc.json"],
                "generator": "port (step 6)",
                "run_id": "run-20260320-120200",
                "timestamp": "2026-03-20T12:02:00",
                "elapsed_s": 5.1,
                "status": "fresh",
                "hash_status": "success",
                "parameters": {"model": "gev"},
                "input_hashes": {"gauge.json": {"hash": "abc123"}},
                "output_hashes": {"gaugehc.json": {"hash": "mno345"}},
            },
        ],
        "num_runs": 1,
        "num_steps": 3,
        "num_recorded": 3,
    }


@pytest.fixture
def sample_data_issues(sample_data_consistent):
    """Collected data dict with stale/missing steps."""
    data = dict(sample_data_consistent)
    data["chain_result"] = SAMPLE_CHAIN_ISSUES
    data["lineage_results"] = SAMPLE_LINEAGE_RESULTS
    data["step_details"] = list(data["step_details"])
    # Mark hazard as stale
    data["step_details"][2] = dict(data["step_details"][2])
    data["step_details"][2]["status"] = "stale"
    return data


# ---------------------------------------------------------------------------
# collect_all()
# ---------------------------------------------------------------------------

class TestCollectAll:

    def test_returns_dict(self, dl_mod):
        """collect_all() returns a dict with expected keys."""
        data = dl_mod.collect_all()
        assert isinstance(data, dict)
        assert 'manifest' in data
        assert 'graph' in data
        assert 'step_io' in data
        assert 'chain_result' in data
        assert 'step_details' in data

    def test_num_steps_positive(self, dl_mod):
        """Pipeline must have at least one step."""
        data = dl_mod.collect_all()
        assert data['num_steps'] > 0

    def test_step_details_list(self, dl_mod):
        """step_details is a list of dicts."""
        data = dl_mod.collect_all()
        assert isinstance(data['step_details'], list)
        for sd in data['step_details']:
            assert isinstance(sd, dict)
            assert 'step' in sd
            assert 'dependencies' in sd
            assert 'inputs' in sd
            assert 'outputs' in sd
            assert 'status' in sd

    def test_chain_result_structure(self, dl_mod):
        """chain_result has expected keys."""
        data = dl_mod.collect_all()
        chain = data['chain_result']
        assert 'is_consistent' in chain
        assert 'stale_steps' in chain
        assert 'missing_steps' in chain

    def test_graph_matches_step_details(self, dl_mod):
        """Every step in graph should have a step_details entry."""
        data = dl_mod.collect_all()
        graph_steps = set(data['graph'].keys())
        detail_steps = {sd['step'] for sd in data['step_details']}
        assert graph_steps == detail_steps


# ---------------------------------------------------------------------------
# create_pdf_report() — PDF generation
# ---------------------------------------------------------------------------

class TestCreatePdfReport:

    def test_returns_path(self, dl_mod, tmp_path, sample_data_consistent):
        """create_pdf_report() returns a Path object."""
        out = tmp_path / 'data_lineage_report.pdf'
        with patch.object(dl_mod, 'OUTPUT_PDF', out), \
             patch.object(dl_mod, 'AUDIT_DIR', tmp_path):
            result = dl_mod.create_pdf_report(sample_data_consistent)
        assert isinstance(result, Path)

    def test_pdf_created(self, dl_mod, tmp_path, sample_data_consistent):
        """PDF file is created on disk."""
        out = tmp_path / 'data_lineage_report.pdf'
        with patch.object(dl_mod, 'OUTPUT_PDF', out), \
             patch.object(dl_mod, 'AUDIT_DIR', tmp_path):
            dl_mod.create_pdf_report(sample_data_consistent)
        assert out.exists()

    def test_pdf_header(self, dl_mod, tmp_path, sample_data_consistent):
        """Generated file has PDF magic bytes."""
        out = tmp_path / 'data_lineage_report.pdf'
        with patch.object(dl_mod, 'OUTPUT_PDF', out), \
             patch.object(dl_mod, 'AUDIT_DIR', tmp_path):
            dl_mod.create_pdf_report(sample_data_consistent)
        assert out.read_bytes()[:4] == b'%PDF'

    def test_pdf_nonempty(self, dl_mod, tmp_path, sample_data_consistent):
        """PDF has reasonable size (multi-page report)."""
        out = tmp_path / 'data_lineage_report.pdf'
        with patch.object(dl_mod, 'OUTPUT_PDF', out), \
             patch.object(dl_mod, 'AUDIT_DIR', tmp_path):
            dl_mod.create_pdf_report(sample_data_consistent)
        assert out.stat().st_size > 5000

    def test_pdf_with_issues(self, dl_mod, tmp_path, sample_data_issues):
        """PDF generates correctly when pipeline has stale/missing steps."""
        out = tmp_path / 'data_lineage_report.pdf'
        with patch.object(dl_mod, 'OUTPUT_PDF', out), \
             patch.object(dl_mod, 'AUDIT_DIR', tmp_path):
            dl_mod.create_pdf_report(sample_data_issues)
        assert out.exists()
        assert out.read_bytes()[:4] == b'%PDF'
        assert out.stat().st_size > 5000

    def test_pdf_with_no_lineage_results(self, dl_mod, tmp_path,
                                          sample_data_consistent):
        """PDF renders when lineage_results is empty (tests not run)."""
        data = dict(sample_data_consistent)
        data['lineage_results'] = {}
        out = tmp_path / 'data_lineage_report.pdf'
        with patch.object(dl_mod, 'OUTPUT_PDF', out), \
             patch.object(dl_mod, 'AUDIT_DIR', tmp_path):
            dl_mod.create_pdf_report(data)
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_pdf_with_empty_step_details(self, dl_mod, tmp_path):
        """PDF renders when no steps have been recorded."""
        data = {
            "manifest": {"runs": {}, "steps": {}},
            "graph": {},
            "step_io": {},
            "chain_result": {
                "is_consistent": False,
                "stale_steps": [],
                "missing_steps": [],
                "details": {},
            },
            "lineage_results": {},
            "step_details": [],
            "num_runs": 0,
            "num_steps": 0,
            "num_recorded": 0,
        }
        out = tmp_path / 'data_lineage_report.pdf'
        with patch.object(dl_mod, 'OUTPUT_PDF', out), \
             patch.object(dl_mod, 'AUDIT_DIR', tmp_path):
            dl_mod.create_pdf_report(data)
        assert out.exists()
        assert out.read_bytes()[:4] == b'%PDF'


# ---------------------------------------------------------------------------
# Internal section builders — no crashes on edge-case data
# ---------------------------------------------------------------------------

class TestSectionBuilders:
    """Each _build_* function must return without error for both
    healthy and degraded datasets."""

    def test_cover_healthy(self, dl_mod, sample_data_consistent):
        S = dl_mod._styles()
        story = []
        dl_mod._build_cover(sample_data_consistent, story, S)
        assert len(story) > 0

    def test_cover_issues(self, dl_mod, sample_data_issues):
        S = dl_mod._styles()
        story = []
        dl_mod._build_cover(sample_data_issues, story, S)
        assert len(story) > 0

    def test_exec_summary_healthy(self, dl_mod, sample_data_consistent):
        S = dl_mod._styles()
        story = []
        dl_mod._build_exec_summary(sample_data_consistent, story, S)
        assert len(story) > 0

    def test_exec_summary_issues(self, dl_mod, sample_data_issues):
        S = dl_mod._styles()
        story = []
        dl_mod._build_exec_summary(sample_data_issues, story, S)
        assert len(story) > 0

    def test_topology(self, dl_mod, sample_data_consistent):
        S = dl_mod._styles()
        story = []
        dl_mod._build_topology(sample_data_consistent, story, S)
        assert len(story) > 0

    def test_quality_metrics_healthy(self, dl_mod, sample_data_consistent):
        S = dl_mod._styles()
        story = []
        dl_mod._build_quality_metrics(sample_data_consistent, story, S)
        assert len(story) > 0

    def test_quality_metrics_with_stale_details(self, dl_mod,
                                                 sample_data_issues):
        S = dl_mod._styles()
        story = []
        dl_mod._build_quality_metrics(sample_data_issues, story, S)
        assert len(story) > 0

    def test_reconciliation_with_results(self, dl_mod,
                                          sample_data_consistent):
        S = dl_mod._styles()
        story = []
        dl_mod._build_reconciliation(sample_data_consistent, story, S)
        assert len(story) > 0

    def test_reconciliation_with_failures(self, dl_mod, sample_data_issues):
        S = dl_mod._styles()
        story = []
        dl_mod._build_reconciliation(sample_data_issues, story, S)
        assert len(story) > 0

    def test_reconciliation_no_results(self, dl_mod, sample_data_consistent):
        S = dl_mod._styles()
        story = []
        data = dict(sample_data_consistent)
        data['lineage_results'] = {}
        dl_mod._build_reconciliation(data, story, S)
        assert len(story) > 0

    def test_source_documentation(self, dl_mod, sample_data_consistent):
        S = dl_mod._styles()
        story = []
        dl_mod._build_source_documentation(sample_data_consistent, story, S)
        assert len(story) > 0

    def test_source_documentation_empty_params(self, dl_mod,
                                                sample_data_consistent):
        """Step with no parameters should still render."""
        S = dl_mod._styles()
        story = []
        data = dict(sample_data_consistent)
        data['step_details'] = [dict(sd) for sd in data['step_details']]
        for sd in data['step_details']:
            sd['parameters'] = {}
        dl_mod._build_source_documentation(data, story, S)
        assert len(story) > 0

    def test_retention_policy(self, dl_mod, sample_data_consistent):
        S = dl_mod._styles()
        story = []
        dl_mod._build_retention_policy(sample_data_consistent, story, S)
        assert len(story) > 0

    def test_remediation_compliant(self, dl_mod, sample_data_consistent):
        S = dl_mod._styles()
        story = []
        dl_mod._build_remediation(sample_data_consistent, story, S)
        assert len(story) > 0

    def test_remediation_with_issues(self, dl_mod, sample_data_issues):
        S = dl_mod._styles()
        story = []
        dl_mod._build_remediation(sample_data_issues, story, S)
        # Should have bullet points for missing/stale steps
        assert len(story) > 2


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

class TestHelpers:

    def test_status_colour_fresh(self, dl_mod):
        col = dl_mod._status_colour('fresh')
        assert col == dl_mod.GREEN

    def test_status_colour_stale(self, dl_mod):
        col = dl_mod._status_colour('stale')
        assert col == dl_mod.AMBER

    def test_status_colour_missing(self, dl_mod):
        col = dl_mod._status_colour('missing')
        assert col == dl_mod.RED

    def test_status_colour_unknown(self, dl_mod):
        col = dl_mod._status_colour('something_else')
        assert col == dl_mod.STEEL

    def test_status_label_values(self, dl_mod):
        assert dl_mod._status_label('fresh') == 'FRESH'
        assert dl_mod._status_label('stale') == 'STALE'
        assert dl_mod._status_label('missing') == 'MISSING'

    def test_status_label_unknown_uppercased(self, dl_mod):
        assert dl_mod._status_label('degraded') == 'DEGRADED'


# ---------------------------------------------------------------------------
# Manifest loading
# ---------------------------------------------------------------------------

class TestLoadManifest:

    def test_returns_dict(self, dl_mod, tmp_path):
        """Returns empty skeleton when file doesn't exist."""
        with patch.object(dl_mod, 'LINEAGE_PATH',
                          tmp_path / 'nonexistent.json'):
            result = dl_mod._load_manifest()
        assert isinstance(result, dict)
        assert 'runs' in result
        assert 'steps' in result

    def test_loads_existing_file(self, dl_mod, tmp_path):
        """Reads and parses an existing manifest."""
        manifest_path = tmp_path / 'data_lineage.json'
        manifest_path.write_text(json.dumps(SAMPLE_MANIFEST))
        with patch.object(dl_mod, 'LINEAGE_PATH', manifest_path):
            result = dl_mod._load_manifest()
        assert 'gauges' in result['steps']

    def test_handles_corrupt_json(self, dl_mod, tmp_path):
        """Returns empty skeleton for corrupt JSON."""
        manifest_path = tmp_path / 'data_lineage.json'
        manifest_path.write_text('{corrupt json!!!')
        with patch.object(dl_mod, 'LINEAGE_PATH', manifest_path):
            result = dl_mod._load_manifest()
        assert result == {"runs": {}, "steps": {}}


class TestLoadLineageResults:

    def test_returns_dict_when_missing(self, dl_mod, tmp_path):
        with patch.object(dl_mod, 'AUDIT_DIR', tmp_path):
            result = dl_mod._load_lineage_results()
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_loads_existing_results(self, dl_mod, tmp_path):
        results_path = tmp_path / 'data_lineage_results.json'
        results_path.write_text(json.dumps(SAMPLE_LINEAGE_RESULTS))
        with patch.object(dl_mod, 'AUDIT_DIR', tmp_path):
            result = dl_mod._load_lineage_results()
        assert result['total'] == 15
        assert result['failed'] == 1


# ---------------------------------------------------------------------------
# main() integration
# ---------------------------------------------------------------------------

class TestMain:

    def test_main_produces_pdf(self, dl_mod, tmp_path):
        """main() writes data_lineage_report.pdf to audit dir."""
        out = tmp_path / 'data_lineage_report.pdf'
        with patch.object(dl_mod, 'OUTPUT_PDF', out), \
             patch.object(dl_mod, 'AUDIT_DIR', tmp_path):
            dl_mod.main()
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_main_prints_summary(self, dl_mod, tmp_path, capsys):
        """main() prints step count and consistency status."""
        out = tmp_path / 'data_lineage_report.pdf'
        with patch.object(dl_mod, 'OUTPUT_PDF', out), \
             patch.object(dl_mod, 'AUDIT_DIR', tmp_path):
            dl_mod.main()
        output = capsys.readouterr().out
        assert 'pipeline steps' in output
        assert 'Consistency' in output
        assert 'data_lineage_report.pdf' in output

    def test_main_creates_audit_dir(self, dl_mod, tmp_path):
        """main() creates audit directory if it doesn't exist."""
        audit = tmp_path / 'sub' / 'audit'
        out = audit / 'data_lineage_report.pdf'
        with patch.object(dl_mod, 'OUTPUT_PDF', out), \
             patch.object(dl_mod, 'AUDIT_DIR', audit):
            dl_mod.main()
        assert audit.exists()
        assert out.exists()
