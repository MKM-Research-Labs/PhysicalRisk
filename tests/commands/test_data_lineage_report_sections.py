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

"""Tests for data_lineage — section builders, helpers, loading, and main()."""

import json
from unittest.mock import patch

import pytest

from tests.commands.data_lineage_helpers import (
    SAMPLE_LINEAGE_RESULTS,
    SAMPLE_MANIFEST,
    get_dl_mod,
    make_sample_data_consistent,
    make_sample_data_issues,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def dl_mod():
    """Import data_lineage module."""
    return get_dl_mod()


@pytest.fixture
def sample_data_consistent(dl_mod):
    """Collected data dict with a consistent pipeline."""
    return make_sample_data_consistent()


@pytest.fixture
def sample_data_issues(sample_data_consistent):
    """Collected data dict with stale/missing steps."""
    return make_sample_data_issues(sample_data_consistent)


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
