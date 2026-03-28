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

"""Tests for model_risk test evidence, audit trail, documents, and recommendations sections."""

import pytest

from tests.commands.model_risk_helpers_part1 import (
    _make_model, _make_bcbs, _make_principle, _make_raci, _make_role,
)
from tests.commands.model_risk_helpers_part2 import (
    _full_data,
    SAMPLE_TEST_COVERAGE, SAMPLE_JUNIT, SAMPLE_JUNIT_CLEAN,
)


# ---------------------------------------------------------------------------
# TestBuildTestEvidence
# ---------------------------------------------------------------------------

class TestBuildTestEvidence:
    """Test sections/testing.py."""

    def test_testing_renders(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.testing import build_test_evidence
        S = styles_mod.get_styles()
        story = []
        build_test_evidence(sample_data, story, S)
        assert len(story) > 0

    def test_testing_no_junit(self, styles_mod, empty_data):
        from docs.models.model_risk.sections.testing import build_test_evidence
        S = styles_mod.get_styles()
        story = []
        build_test_evidence(empty_data, story, S)
        assert len(story) >= 3

    def test_testing_with_coverage(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.testing import build_test_evidence
        S = styles_mod.get_styles()
        story = []
        build_test_evidence(sample_data, story, S)
        assert len(story) >= 5

    def test_testing_per_model_coverage(self, styles_mod):
        from docs.models.model_risk.sections.testing import build_test_evidence
        data = _full_data(models=[
            _make_model('M-001', test_coverage=SAMPLE_TEST_COVERAGE),
            _make_model('M-002', test_coverage={
                'unit_tests': False, 'integration_tests': False,
                'benchmark_tests': False, 'test_file': ''}),
        ])
        S = styles_mod.get_styles()
        story = []
        build_test_evidence(data, story, S)
        assert len(story) >= 6

    def test_testing_no_sensitivity_generators(self, styles_mod):
        from docs.models.model_risk.sections.testing import build_test_evidence
        data = _full_data(sensitivity_generators=[])
        S = styles_mod.get_styles()
        story = []
        build_test_evidence(data, story, S)
        assert len(story) >= 4

    def test_testing_with_sensitivity_generators(self, styles_mod):
        from docs.models.model_risk.sections.testing import build_test_evidence
        data = _full_data(sensitivity_generators=['floodrisk', 'hazard'])
        S = styles_mod.get_styles()
        story = []
        build_test_evidence(data, story, S)
        assert len(story) >= 6


# ---------------------------------------------------------------------------
# TestBuildAuditTrail
# ---------------------------------------------------------------------------

class TestBuildAuditTrail:
    """Test sections/audit_trail.py."""

    def test_audit_trail_renders(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.audit_trail import build_audit_trail
        S = styles_mod.get_styles()
        story = []
        build_audit_trail(sample_data, story, S)
        assert len(story) > 0

    def test_audit_trail_empty(self, styles_mod, empty_data):
        from docs.models.model_risk.sections.audit_trail import build_audit_trail
        S = styles_mod.get_styles()
        story = []
        build_audit_trail(empty_data, story, S)
        assert len(story) >= 2

    def test_audit_trail_date_range(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.audit_trail import build_audit_trail
        S = styles_mod.get_styles()
        story = []
        build_audit_trail(sample_data, story, S)
        # Should have heading, rule, body, spacer, h3, table, spacer, note
        assert len(story) >= 6

    def test_audit_trail_no_timestamps(self, styles_mod):
        from docs.models.model_risk.sections.audit_trail import build_audit_trail
        data = _full_data(audit_log=[
            {'model_id': 'M-001', 'event': 'test'},
        ])
        S = styles_mod.get_styles()
        story = []
        build_audit_trail(data, story, S)
        assert len(story) >= 4


# ---------------------------------------------------------------------------
# TestBuildDocuments
# ---------------------------------------------------------------------------

class TestBuildDocuments:
    """Test sections/documents.py."""

    def test_documents_renders(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.documents import build_document_inventory
        S = styles_mod.get_styles()
        story = []
        build_document_inventory(sample_data, story, S)
        assert len(story) > 0

    def test_documents_empty(self, styles_mod, empty_data):
        from docs.models.model_risk.sections.documents import build_document_inventory
        S = styles_mod.get_styles()
        story = []
        build_document_inventory(empty_data, story, S)
        assert len(story) >= 2

    def test_documents_file_list(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.documents import build_document_inventory
        S = styles_mod.get_styles()
        story = []
        build_document_inventory(sample_data, story, S)
        assert len(story) >= 4


# ---------------------------------------------------------------------------
# TestBuildRecommendations
# ---------------------------------------------------------------------------

class TestBuildRecommendations:
    """Test sections/recommendations.py."""

    def test_recommendations_renders(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.recommendations import build_recommendations
        S = styles_mod.get_styles()
        story = []
        build_recommendations(sample_data, story, S)
        assert len(story) > 0

    def test_recommendations_all_clean(self, styles_mod):
        from docs.models.model_risk.sections.recommendations import build_recommendations
        data = _full_data(
            models=[_make_model(
                'M-001',
                validation_questions=[
                    {'short_label': 'Q1', 'status': 'Addressed'}],
                remediation_steps=[
                    {'status': 'Completed', 'due_date': '2025-01-01'}],
            )],
            bcbs=_make_bcbs([
                _make_principle(1, 'Gov', 'O', 4, 4, 'Fully Compliant'),
            ]),
            raci=_make_raci(roles=[_make_role()]),
            junit=SAMPLE_JUNIT_CLEAN,
        )
        S = styles_mod.get_styles()
        story = []
        build_recommendations(data, story, S)
        # "No critical recommendations" paragraph
        assert len(story) >= 3

    def test_recommendations_validation_gap(self, styles_mod):
        from docs.models.model_risk.sections.recommendations import build_recommendations
        data = _full_data(models=[
            _make_model('M-001', validation_questions=[
                {'short_label': 'Q1', 'status': 'Not Addressed'},
            ]),
        ])
        S = styles_mod.get_styles()
        story = []
        build_recommendations(data, story, S)
        assert len(story) >= 4

    def test_recommendations_peer_reviewer_gap(self, styles_mod):
        from docs.models.model_risk.sections.recommendations import build_recommendations
        data = _full_data(models=[
            _make_model('M-001', peer_reviewer='TBD'),
        ])
        S = styles_mod.get_styles()
        story = []
        build_recommendations(data, story, S)
        assert len(story) >= 4

    def test_recommendations_overdue_remediation(self, styles_mod):
        from docs.models.model_risk.sections.recommendations import build_recommendations
        data = _full_data(models=[
            _make_model('M-001', remediation_steps=[
                {'id': 'R1', 'status': 'Open', 'due_date': '2020-01-01'},
            ]),
        ])
        S = styles_mod.get_styles()
        story = []
        build_recommendations(data, story, S)
        assert len(story) >= 4

    def test_recommendations_bcbs_at_risk(self, styles_mod):
        from docs.models.model_risk.sections.recommendations import build_recommendations
        data = _full_data(bcbs=_make_bcbs([
            _make_principle(7, 'Timeliness', 'Q', 1, 4, 'Non-compliant'),
        ]))
        S = styles_mod.get_styles()
        story = []
        build_recommendations(data, story, S)
        assert len(story) >= 4

    def test_recommendations_raci_backup_gaps(self, styles_mod):
        from docs.models.model_risk.sections.recommendations import build_recommendations
        data = _full_data(raci=_make_raci(
            roles=[_make_role('Owner', 'R', 'Alice', None)],
        ))
        S = styles_mod.get_styles()
        story = []
        build_recommendations(data, story, S)
        assert len(story) >= 4

    def test_recommendations_test_failures(self, styles_mod):
        from docs.models.model_risk.sections.recommendations import build_recommendations
        data = _full_data(junit=SAMPLE_JUNIT)
        S = styles_mod.get_styles()
        story = []
        build_recommendations(data, story, S)
        assert len(story) >= 4
