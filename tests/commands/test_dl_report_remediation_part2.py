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

"""Tests for data_lineage — exec summary, retention, loading, main()."""

import json
from unittest.mock import patch

import pytest

from tests.commands.data_lineage_helpers import (
    SAMPLE_LINEAGE_RESULTS,
    SAMPLE_MANIFEST,
)


# ---------------------------------------------------------------------------
# Executive summary verdict badge
# ---------------------------------------------------------------------------

class TestExecSummaryVerdict:
    """Executive summary must show an explicit BCBS 239 verdict."""

    def test_compliant_verdict(self, dl_mod, sample_data_consistent):
        S = dl_mod._styles()
        story = []
        dl_mod._build_exec_summary(sample_data_consistent, story, S)
        from reportlab.platypus import Table
        tables = [e for e in story if isinstance(e, Table)]
        verdict_badge = tables[1]
        assert verdict_badge._cellvalues[1][0] == 'COMPLIANT'

    def test_non_compliant_verdict(self, dl_mod, sample_data_issues):
        S = dl_mod._styles()
        story = []
        dl_mod._build_exec_summary(sample_data_issues, story, S)
        from reportlab.platypus import Table
        tables = [e for e in story if isinstance(e, Table)]
        verdict_badge = tables[1]
        assert verdict_badge._cellvalues[1][0] in (
            'PARTIALLY COMPLIANT', 'NON-COMPLIANT')

    def test_run_history_shown(self, dl_mod, sample_data_consistent):
        S = dl_mod._styles()
        story = []
        dl_mod._build_exec_summary(sample_data_consistent, story, S)
        from reportlab.platypus import Paragraph
        texts = ' '.join(p.text for p in story
                         if isinstance(p, Paragraph))
        assert 'Run History' in texts


# ---------------------------------------------------------------------------
# Retention principle linkage
# ---------------------------------------------------------------------------

class TestRetentionPrincipleLinkage:
    """Retention section must reference BCBS 239 Principle 5/6."""

    def test_retention_mentions_reproducibility(self, dl_mod,
                                                 sample_data_consistent):
        S = dl_mod._styles()
        story = []
        dl_mod._build_retention_policy(sample_data_consistent, story, S)
        from reportlab.platypus import Paragraph
        texts = ' '.join(p.text for p in story
                         if isinstance(p, Paragraph))
        assert 'Principle 5/6' in texts
        assert 'Reproducibility' in texts


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
