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

"""Tests for model_risk sections init, PDF report creation, and edge cases."""

import pytest
from unittest.mock import MagicMock, patch

from tests.commands.model_risk_helpers_part1 import (
    _make_model, _make_meeting, _make_bcbs, _make_principle,
    _make_raci, _make_role,
)
from tests.commands.model_risk_helpers_part2 import (
    _full_data,
    SAMPLE_RISK_RATING, SAMPLE_JUNIT_EMPTY, SAMPLE_JUNIT_CLEAN,
    SAMPLE_ASSUMPTIONS, SAMPLE_TEST_COVERAGE,
)


# ---------------------------------------------------------------------------
# TestSectionsInit — verify all exports
# ---------------------------------------------------------------------------

class TestSectionsInit:
    """Test sections/__init__.py exports."""

    def test_all_builders_exported(self, sections_mod):
        expected = [
            'build_cover', 'build_exec_summary', 'build_model_inventory',
            'build_validation_status', 'build_mrc_activity',
            'build_remediation', 'build_bcbs239', 'build_raci',
            'build_test_evidence', 'build_audit_trail',
            'build_document_inventory', 'build_recommendations',
        ]
        for name in expected:
            assert hasattr(sections_mod, name), f"Missing export: {name}"
            assert callable(getattr(sections_mod, name))

    def test_all_list(self, sections_mod):
        assert len(sections_mod.__all__) == 12


# ---------------------------------------------------------------------------
# TestCreatePdfReport — full PDF assembly
# ---------------------------------------------------------------------------

class TestCreatePdfReport:
    """Test create_pdf_report() and main()."""

    @pytest.fixture
    def report_mod(self):
        from docs.models.model_risk import report
        return report

    def _patch_paths(self, report_mod, data_mod, out, audit):
        """Context manager to patch OUTPUT_PDF and AUDIT_DIR in both modules."""
        from contextlib import ExitStack
        stack = ExitStack()
        stack.enter_context(patch.object(data_mod, 'OUTPUT_PDF', out))
        stack.enter_context(patch.object(data_mod, 'AUDIT_DIR', audit))
        stack.enter_context(patch.object(report_mod, 'OUTPUT_PDF', out))
        stack.enter_context(patch.object(report_mod, 'AUDIT_DIR', audit))
        return stack

    def test_creates_pdf(self, report_mod, data_mod, tmp_path, sample_data):
        out = tmp_path / 'model_risk_report.pdf'
        audit = tmp_path / 'audit'
        audit.mkdir()
        with self._patch_paths(report_mod, data_mod, out, audit):
            result = report_mod.create_pdf_report(sample_data)
        assert result.exists()
        assert result.stat().st_size > 0

    def test_creates_pdf_empty_data(self, report_mod, data_mod, tmp_path,
                                    empty_data):
        out = tmp_path / 'model_risk_report.pdf'
        audit = tmp_path / 'audit'
        audit.mkdir()
        with self._patch_paths(report_mod, data_mod, out, audit):
            result = report_mod.create_pdf_report(empty_data)
        assert result.exists()

    def test_creates_audit_dir(self, report_mod, data_mod, tmp_path,
                               sample_data):
        audit = tmp_path / 'new' / 'audit'
        out = audit / 'model_risk_report.pdf'
        with self._patch_paths(report_mod, data_mod, out, audit):
            result = report_mod.create_pdf_report(sample_data)
        assert audit.is_dir()
        assert result.exists()

    def test_collect_all_fallback(self, report_mod, data_mod, tmp_path):
        """create_pdf_report(None) calls collect_all()."""
        audit = tmp_path / 'audit'
        audit.mkdir()
        out = audit / 'model_risk_report.pdf'
        with self._patch_paths(report_mod, data_mod, out, audit), \
             patch.object(report_mod, 'collect_all',
                          return_value=_full_data()) as mock_ca:
            report_mod.create_pdf_report(None)
        mock_ca.assert_called_once()

    def test_main_prints_summary(self, report_mod, data_mod, tmp_path,
                                 capsys):
        audit = tmp_path / 'audit'
        audit.mkdir()
        out = audit / 'model_risk_report.pdf'
        with self._patch_paths(report_mod, data_mod, out, audit), \
             patch.object(report_mod, 'collect_all',
                          return_value=_full_data()):
            report_mod.main()
        captured = capsys.readouterr().out
        assert 'Generating Model Risk Governance Report' in captured
        assert 'models in inventory' in captured
        assert 'RAG:' in captured
        assert 'remediation items' in captured
        assert 'MRC meetings' in captured
        assert 'audit trail events' in captured
        assert 'model_risk_report.pdf' in captured

    def test_main_with_real_collect(self, report_mod, data_mod, tmp_path):
        """Integration: main() with actual data loading against empty dirs."""
        audit = tmp_path / 'audit'
        audit.mkdir()
        out = audit / 'model_risk_report.pdf'
        data_dir = tmp_path / 'data'
        data_dir.mkdir()
        (data_dir / 'model_inventory.json').write_text('{"models":[]}')
        (data_dir / 'mrc_meetings.json').write_text('[]')
        (data_dir / 'bcbs239_assessment.json').write_text('{}')
        (data_dir / 'raci_matrix.json').write_text('{}')
        (data_dir / 'model_audit_log.json').write_text('[]')
        with patch.object(data_mod, 'DATA_DIR', data_dir), \
             patch.object(data_mod, 'AUDIT_DIR', audit), \
             patch.object(data_mod, 'OUTPUT_PDF', out), \
             patch.object(data_mod, '_root', tmp_path), \
             patch.object(report_mod, 'OUTPUT_PDF', out), \
             patch.object(report_mod, 'AUDIT_DIR', audit):
            report_mod.main()
        assert out.exists()


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_model_with_no_name(self, styles_mod):
        from docs.models.model_risk.sections.inventory import build_model_inventory
        data = _full_data(models=[
            {'model_id': 'M-X', 'tier': 1, 'rag_rating': 'Green',
             'lifecycle_stage': 'Production', 'owner': None,
             'next_review_date': None},
        ])
        S = styles_mod.get_styles()
        story = []
        build_model_inventory(data, story, S)
        assert len(story) >= 3

    def test_model_with_long_name(self, styles_mod):
        from docs.models.model_risk.sections.inventory import build_model_inventory
        data = _full_data(models=[
            _make_model('M-001'),
        ])
        data['models'][0]['short_name'] = 'A' * 100
        S = styles_mod.get_styles()
        story = []
        build_model_inventory(data, story, S)
        assert len(story) >= 3

    def test_remediation_null_due_date(self, styles_mod):
        from docs.models.model_risk.sections.remediation import build_remediation
        data = _full_data(models=[
            _make_model('M-001', remediation_steps=[
                {'id': 'R1', 'description': 'No due', 'priority': 'Medium',
                 'due_date': None, 'status': 'Open'},
            ]),
        ])
        S = styles_mod.get_styles()
        story = []
        build_remediation(data, story, S)
        assert len(story) >= 4

    def test_mrc_actions_with_missing_fields(self, styles_mod):
        from docs.models.model_risk.sections.mrc import build_mrc_activity
        data = _full_data(meetings=[
            _make_meeting('MRC-001', actions=[
                {'status': 'Open'},  # minimal — missing id, title, etc.
            ]),
        ])
        S = styles_mod.get_styles()
        story = []
        build_mrc_activity(data, story, S)
        assert len(story) >= 3

    def test_audit_log_single_event(self, styles_mod):
        from docs.models.model_risk.sections.audit_trail import build_audit_trail
        data = _full_data(audit_log=[
            {'model_id': 'M-001', 'timestamp': '2026-03-01T09:00:00'},
        ])
        S = styles_mod.get_styles()
        story = []
        build_audit_trail(data, story, S)
        assert len(story) >= 5

    def test_bcbs_zero_max_score(self, styles_mod):
        from docs.models.model_risk.sections.bcbs239 import build_bcbs239
        data = _full_data(bcbs=_make_bcbs([
            _make_principle(1, 'Gov', 'O', 0, 0, 'N/A'),
        ]))
        S = styles_mod.get_styles()
        story = []
        # Should not divide by zero
        build_bcbs239(data, story, S)
        assert len(story) >= 4

    def test_cover_no_coverage(self, styles_mod):
        from docs.models.model_risk.sections.cover import build_cover
        data = _full_data(coverage_pct=None)
        S = styles_mod.get_styles()
        story = []
        build_cover(data, story, S)
        assert len(story) >= 3

    def test_validation_question_no_short_label(self, styles_mod):
        from docs.models.model_risk.sections.validation import build_validation_status
        data = _full_data(models=[
            _make_model('M-001', validation_questions=[
                {'status': 'Addressed'},  # no short_label
                {'short_label': '', 'status': 'Addressed'},
                {'short_label': 'Valid', 'status': 'Addressed'},
            ]),
        ])
        S = styles_mod.get_styles()
        story = []
        build_validation_status(data, story, S)
        assert len(story) >= 1

    def test_raci_no_activities_no_triggers(self, styles_mod):
        from docs.models.model_risk.sections.raci import build_raci
        data = _full_data(raci=_make_raci(
            roles=[_make_role()],
            activities=[],
            escalation_triggers=[],
        ))
        S = styles_mod.get_styles()
        story = []
        build_raci(data, story, S)
        assert len(story) >= 3

    def test_multiple_models_risk_ratings(self, styles_mod):
        from docs.models.model_risk.sections.inventory import build_model_inventory
        data = _full_data(models=[
            _make_model('M-001', overall_risk_rating=SAMPLE_RISK_RATING),
            _make_model('M-002', overall_risk_rating={
                'calculated_score': 3.8,
                'effective_rating': 'High',
                'component_scores': {
                    'validation_coverage': 0.5,
                    'remediation_health': 0.4,
                    'review_currency': 0.6,
                    'assumption_risk': 0.8,
                    'limitation_risk': 0.9,
                },
            }),
            _make_model('M-003'),  # no risk rating
        ])
        S = styles_mod.get_styles()
        story = []
        build_model_inventory(data, story, S)
        assert len(story) >= 5
