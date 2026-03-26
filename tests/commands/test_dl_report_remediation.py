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

"""Tests for data_lineage — remediation, cover badge, exec summary, retention, loading, main()."""

import json
from unittest.mock import patch

import pytest

from tests.commands.data_lineage_helpers import (
    SAMPLE_LINEAGE_RESULTS,
    SAMPLE_LINEAGE_RESULTS_MULTI_FAIL,
    SAMPLE_LINEAGE_RESULTS_STALE,
    SAMPLE_MANIFEST,
    get_dl_mod,
    make_sample_data_consistent,
    make_sample_data_issues,
)


@pytest.fixture
def dl_mod():
    return get_dl_mod()

@pytest.fixture
def sample_data_consistent(dl_mod):
    return make_sample_data_consistent()

@pytest.fixture
def sample_data_issues(sample_data_consistent):
    return make_sample_data_issues(sample_data_consistent)


# ---------------------------------------------------------------------------
# Failed check structured breakdown
# ---------------------------------------------------------------------------

class TestFailedCheckBreakdown:
    """Failed checks with known metadata should render as structured tables."""

    def test_known_failure_renders_table(self, dl_mod,
                                          sample_data_consistent):
        """A failure matching FAILURE_METADATA renders a structured table."""
        S = dl_mod._styles()
        story = []
        data = dict(sample_data_consistent)
        data['lineage_results'] = SAMPLE_LINEAGE_RESULTS_STALE
        dl_mod._build_reconciliation(data, story, S)
        from reportlab.platypus import Table
        tables = [e for e in story if isinstance(e, Table)]
        # Should have at least 3 tables: recon checks, results, failure detail
        assert len(tables) >= 3

    def test_unknown_failure_renders_bullet(self, dl_mod,
                                             sample_data_consistent):
        """A failure NOT in FAILURE_METADATA falls back to bullet point."""
        S = dl_mod._styles()
        story = []
        data = dict(sample_data_consistent)
        data['lineage_results'] = SAMPLE_LINEAGE_RESULTS
        dl_mod._build_reconciliation(data, story, S)
        from reportlab.platypus import Paragraph
        paras = [e for e in story if isinstance(e, Paragraph)]
        texts = [p.text for p in paras]
        assert any('test_trade_gauges_exist_in_gauge_json' in t
                    for t in texts)


# ---------------------------------------------------------------------------
# Remediation verdict consistency
# ---------------------------------------------------------------------------

class TestRemediationVerdict:
    """Remediation section must never say COMPLIANT when issues exist."""

    def test_compliant_run_is_suitable(self, dl_mod,
                                        sample_data_consistent):
        S = dl_mod._styles()
        story = []
        dl_mod._build_remediation(sample_data_consistent, story, S)
        from reportlab.platypus import Paragraph
        texts = ' '.join(p.text for p in story
                         if isinstance(p, Paragraph))
        assert 'suitable for regulatory risk reporting' in texts

    def test_issues_run_not_suitable(self, dl_mod, sample_data_issues):
        S = dl_mod._styles()
        story = []
        dl_mod._build_remediation(sample_data_issues, story, S)
        from reportlab.platypus import Paragraph
        texts = ' '.join(p.text for p in story
                         if isinstance(p, Paragraph))
        assert 'not suitable for regulatory risk reporting' in texts
        assert 'COMPLIANT' not in texts.replace(
            'PARTIALLY COMPLIANT', '').replace('NON-COMPLIANT', '')

    def test_shows_strengths_and_weaknesses(self, dl_mod,
                                             sample_data_issues):
        S = dl_mod._styles()
        story = []
        dl_mod._build_remediation(sample_data_issues, story, S)
        from reportlab.platypus import Paragraph
        texts = ' '.join(p.text for p in story
                         if isinstance(p, Paragraph))
        assert 'Strengths' in texts
        assert 'Weaknesses' in texts

    def test_remediation_lists_stale_steps(self, dl_mod,
                                            sample_data_issues):
        S = dl_mod._styles()
        story = []
        dl_mod._build_remediation(sample_data_issues, story, S)
        from reportlab.platypus import Paragraph
        texts = ' '.join(p.text for p in story
                         if isinstance(p, Paragraph))
        assert 'Stale data' in texts
        assert 'hazard' in texts

    def test_remediation_with_stale_failure_metadata(self, dl_mod,
                                                      sample_data_consistent):
        """When lineage_results has a known failure, remediation cites it."""
        S = dl_mod._styles()
        story = []
        data = dict(sample_data_consistent)
        data['lineage_results'] = SAMPLE_LINEAGE_RESULTS_STALE
        data['chain_result'] = {
            "is_consistent": True, "stale_steps": ["propertyhc"],
            "missing_steps": [], "details": {},
        }
        dl_mod._build_remediation(data, story, S)
        from reportlab.platypus import Paragraph
        texts = ' '.join(p.text for p in story
                         if isinstance(p, Paragraph))
        assert 'PARTIALLY COMPLIANT' in texts or 'NON-COMPLIANT' in texts


# ---------------------------------------------------------------------------
# Cover badge worst-case health
# ---------------------------------------------------------------------------

class TestCoverBadgeHealth:
    """Cover badge must reflect worst-case health status."""

    def test_consistent_cover(self, dl_mod, sample_data_consistent):
        S = dl_mod._styles()
        story = []
        dl_mod._build_cover(sample_data_consistent, story, S)
        from reportlab.platypus import Table
        tables = [e for e in story if isinstance(e, Table)]
        badge = tables[0]
        assert badge._cellvalues[1][0] == 'CONSISTENT'

    def test_degraded_cover_on_failures(self, dl_mod,
                                         sample_data_consistent):
        S = dl_mod._styles()
        story = []
        data = dict(sample_data_consistent)
        data['lineage_results'] = SAMPLE_LINEAGE_RESULTS
        dl_mod._build_cover(data, story, S)
        from reportlab.platypus import Table
        tables = [e for e in story if isinstance(e, Table)]
        badge = tables[0]
        assert badge._cellvalues[1][0] == 'DEGRADED'

    def test_inconsistent_cover_on_broken_chain(self, dl_mod,
                                                  sample_data_issues):
        S = dl_mod._styles()
        story = []
        dl_mod._build_cover(sample_data_issues, story, S)
        from reportlab.platypus import Table
        tables = [e for e in story if isinstance(e, Table)]
        badge = tables[0]
        assert badge._cellvalues[1][0] == 'INCONSISTENT'


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
