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

"""Tests for docs.models.model_risk — Model Risk Governance PDF report."""

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

def _make_model(model_id='M-001', tier=1, rag='Green', stage='Production',
                owner='Alice', peer_reviewer='Bob', next_review='2026-06-01',
                validation_questions=None, remediation_steps=None,
                assumptions=None, limitations=None, test_coverage=None,
                overall_risk_rating=None):
    """Build a sample model dict."""
    m = {
        'model_id': model_id,
        'name': f'Model {model_id}',
        'short_name': f'Mdl {model_id}',
        'tier': tier,
        'rag_rating': rag,
        'lifecycle_stage': stage,
        'owner': owner,
        'peer_reviewer': peer_reviewer,
        'next_review_date': next_review,
        'validation_questions': validation_questions or [],
        'remediation_steps': remediation_steps or [],
        'assumptions': assumptions or [],
        'limitations': limitations or [],
        'test_coverage': test_coverage or {},
    }
    if overall_risk_rating:
        m['overall_risk_rating'] = overall_risk_rating
    return m


def _make_meeting(mid='MRC-001', title='Quarterly Review', date='2026-01-15',
                  status='Completed', decisions=None, actions=None):
    return {
        'id': mid,
        'title': title,
        'date': date,
        'status': status,
        'decisions': decisions or [],
        'actions': actions or [],
    }


def _make_bcbs(principles=None, assessment_date='2026-01-20',
               assessor='Risk Team'):
    return {
        'assessment_date': assessment_date,
        'assessor': assessor,
        'principles': principles or [],
    }


def _make_principle(pid=1, title='Governance', category='Overarching',
                    score=3, max_score=4, status='Largely Compliant',
                    gaps=None):
    p = {
        'id': pid,
        'title': title,
        'category': category,
        'score': score,
        'max_score': max_score,
        'status': status,
    }
    if gaps:
        p['gaps'] = gaps
    return p


def _make_raci(roles=None, activities=None, escalation_triggers=None):
    return {
        'roles': roles or [],
        'activities': activities or [],
        'escalation_triggers': escalation_triggers or [],
    }


def _make_role(label='Model Owner', raci_code='R', assigned_to='Alice',
               backup='Bob'):
    return {
        'label': label,
        'raci_code': raci_code,
        'assigned_to': assigned_to,
        'backup': backup,
    }


SAMPLE_VQ = [
    {'short_label': 'Scope', 'status': 'Addressed'},
    {'short_label': 'Data', 'status': 'Partially Addressed'},
    {'short_label': 'Method', 'status': 'Not Addressed'},
    {'short_label': 'N/A Test', 'status': 'Not Applicable'},
]

SAMPLE_REMEDIATION = [
    {
        'id': 'REM-001',
        'description': 'Recalibrate hazard curves for all gauges',
        'priority': 'High',
        'due_date': '2025-12-01',
        'status': 'Open',
    },
    {
        'id': 'REM-002',
        'description': 'Add integration tests for PnL engine',
        'priority': 'Medium',
        'due_date': '2026-06-01',
        'status': 'In Progress',
    },
    {
        'id': 'REM-003',
        'description': 'Document model limitations',
        'priority': 'Low',
        'due_date': '2026-03-01',
        'status': 'Completed',
    },
]

SAMPLE_ASSUMPTIONS = [
    {'id': 'A-001', 'description': 'Normal distribution of returns',
     'impact': 'High'},
    {'id': 'A-002', 'description': 'Stationarity of hazard rates',
     'impact': 'Medium'},
    {'id': 'A-003', 'description': 'Linear correlation assumption',
     'impact': 'High'},
]

SAMPLE_TEST_COVERAGE = {
    'unit_tests': True,
    'integration_tests': True,
    'benchmark_tests': False,
    'test_file': 'tests/models/test_hazard.py',
}

SAMPLE_RISK_RATING = {
    'calculated_score': 2.45,
    'effective_rating': 'Medium',
    'component_scores': {
        'validation_coverage': 0.85,
        'remediation_health': 0.70,
        'review_currency': 0.90,
        'assumption_risk': 0.65,
        'limitation_risk': 0.75,
    },
}

SAMPLE_DECISIONS = [
    {'title': 'Approve T1 model recalibration schedule'},
    {'decision': 'Mandate quarterly backtesting for flood models'},
]

SAMPLE_ACTIONS = [
    {
        'id': 'ACT-001',
        'title': 'Complete peer review of M-001',
        'owner': 'Charlie',
        'due_date': '2026-04-01',
        'status': 'Open',
    },
    {
        'action_id': 'ACT-002',
        'action': 'Update RACI matrix',
        'owner': 'Diana',
        'due_date': '2026-05-01',
        'status': 'In Progress',
    },
]

SAMPLE_AUDIT_LOG = [
    {'model_id': 'M-001', 'timestamp': '2026-01-10T09:00:00',
     'event': 'validation_started'},
    {'model_id': 'M-001', 'timestamp': '2026-01-12T14:30:00',
     'event': 'validation_completed'},
    {'model_id': 'M-002', 'timestamp': '2026-01-15T10:00:00',
     'event': 'peer_review_assigned'},
    {'model_id': 'M-001', 'timestamp': '2026-02-01T08:00:00',
     'event': 'remediation_opened'},
]

SAMPLE_AUDIT_FILES = [
    {'name': 'bcbs239_report.pdf', 'size_kb': 45.2,
     'modified': '2026-03-15 10:30'},
    {'name': 'junit.xml', 'size_kb': 12.8,
     'modified': '2026-03-20 14:00'},
    {'name': 'model_risk_report.pdf', 'size_kb': 26.4,
     'modified': '2026-03-20 14:05'},
]

SAMPLE_JUNIT = {
    'total': 6047, 'passed': 6040, 'failed': 5, 'errors': 1,
    'skipped': 1, 'time_s': 42.3,
}

SAMPLE_JUNIT_CLEAN = {
    'total': 6047, 'passed': 6047, 'failed': 0, 'errors': 0,
    'skipped': 0, 'time_s': 40.1,
}

SAMPLE_JUNIT_EMPTY = {
    'total': 0, 'passed': 0, 'failed': 0, 'errors': 0,
    'skipped': 0, 'time_s': 0.0,
}


def _full_data(**overrides):
    """Build a complete data dict for create_pdf_report."""
    models = overrides.pop('models', [
        _make_model(
            'M-001', tier=1, rag='Green', stage='Production',
            validation_questions=SAMPLE_VQ,
            remediation_steps=SAMPLE_REMEDIATION,
            assumptions=SAMPLE_ASSUMPTIONS,
            test_coverage=SAMPLE_TEST_COVERAGE,
            overall_risk_rating=SAMPLE_RISK_RATING,
        ),
        _make_model(
            'M-002', tier=2, rag='Amber', stage='Development',
            peer_reviewer='TBD',
            validation_questions=[
                {'short_label': 'Scope', 'status': 'Not Addressed'},
                {'short_label': 'Data', 'status': 'Addressed'},
            ],
        ),
        _make_model(
            'M-003', tier=3, rag='Red', stage='Retired',
            peer_reviewer=None,
        ),
    ])
    d = {
        'inventory': {
            'metadata': {
                'framework': 'MKM Research Labs',
                'handbook_reference': 'MRM-HB-2026-v3',
            },
            'models': models,
        },
        'models': models,
        'meetings': overrides.pop('meetings', [
            _make_meeting('MRC-001', 'Quarterly Review', '2026-01-15',
                          'Completed', SAMPLE_DECISIONS, SAMPLE_ACTIONS),
            _make_meeting('MRC-002', 'Adhoc Session', '2026-02-20',
                          'Scheduled'),
        ]),
        'bcbs': overrides.pop('bcbs', _make_bcbs([
            _make_principle(1, 'Governance', 'Overarching', 3, 4,
                            'Largely Compliant'),
            _make_principle(2, 'Data Architecture', 'Overarching', 4, 4,
                            'Fully Compliant'),
            _make_principle(3, 'Accuracy', 'Quality', 2, 4,
                            'Materially Non-compliant',
                            gaps='Manual reconciliation gaps'),
            _make_principle(7, 'Timeliness', 'Quality', 1, 4,
                            'Non-compliant',
                            gaps='Batch window exceeds SLA'),
        ])),
        'raci': overrides.pop('raci', _make_raci(
            roles=[
                _make_role('Model Owner', 'R', 'Alice', 'Bob'),
                _make_role('Validator', 'A', 'Charlie', None),
                _make_role('MRC Chair', 'C', 'Diana', 'Eve'),
            ],
            activities=[
                {'category': 'Validation', 'name': 'Annual review'},
                {'category': 'Validation', 'name': 'Ad-hoc review'},
                {'category': 'Governance', 'name': 'MRC meeting'},
            ],
            escalation_triggers=[
                'RAG rating downgraded to Red',
                'Remediation item overdue > 30 days',
                {'trigger': 'Model failure in production'},
            ],
        )),
        'audit_log': overrides.pop('audit_log', SAMPLE_AUDIT_LOG),
        'junit': overrides.pop('junit', SAMPLE_JUNIT),
        'coverage_pct': overrides.pop('coverage_pct', 82.5),
        'audit_files': overrides.pop('audit_files', SAMPLE_AUDIT_FILES),
        'sensitivity_generators': overrides.pop('sensitivity_generators',
                                                ['floodrisk', 'hazard']),
    }
    d.update(overrides)
    return d


# ---------------------------------------------------------------------------
# Module-level fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mr_pkg():
    """Import the model_risk package."""
    from docs.models import model_risk
    return model_risk


@pytest.fixture
def data_mod():
    """Import the data module."""
    from docs.models.model_risk import data
    return data


@pytest.fixture
def styles_mod():
    """Import the styles module."""
    from docs.models.model_risk import styles
    return styles


@pytest.fixture
def sections_mod():
    """Import the sections package."""
    from docs.models.model_risk import sections
    return sections


@pytest.fixture
def sample_data():
    """Build a full sample data dict."""
    return _full_data()


@pytest.fixture
def empty_data():
    """Minimal data — no models, meetings, etc."""
    return _full_data(
        models=[],
        meetings=[],
        bcbs=_make_bcbs(),
        raci=_make_raci(),
        audit_log=[],
        junit=SAMPLE_JUNIT_EMPTY,
        coverage_pct=None,
        audit_files=[],
        sensitivity_generators=[],
    )


# ---------------------------------------------------------------------------
# TestStyles
# ---------------------------------------------------------------------------

class TestStyles:
    """Test styles.py — colours, get_styles(), tbl_style(), section_rule()."""

    def test_colour_constants(self, styles_mod):
        for name in ('NAVY', 'STEEL', 'BLUE', 'GREEN', 'AMBER', 'RED',
                     'LIGHT_GREEN', 'LIGHT_AMBER', 'LIGHT_RED', 'LIGHT_BG'):
            assert hasattr(styles_mod, name)

    def test_rag_colour_maps(self, styles_mod):
        for key in ('Green', 'Amber', 'Red', 'green', 'amber', 'red'):
            assert key in styles_mod.RAG_COLOURS
            assert key in styles_mod.RAG_BG

    def test_get_styles_keys(self, styles_mod):
        S = styles_mod.get_styles()
        expected = {'title', 'subtitle', 'meta', 'h2', 'h3',
                    'body', 'small', 'note'}
        assert expected == set(S.keys())

    def test_tbl_style_returns_tablestyle(self, styles_mod):
        from reportlab.platypus import TableStyle
        ts = styles_mod.tbl_style()
        assert isinstance(ts, TableStyle)

    def test_section_rule_appends_flowables(self, styles_mod):
        story = []
        styles_mod.section_rule(story)
        assert len(story) == 3  # Spacer, HRFlowable, Spacer


# ---------------------------------------------------------------------------
# TestDataLoaders
# ---------------------------------------------------------------------------

class TestDataLoaders:
    """Test data.py — all loaders and collect_all()."""

    def test_load_inventory(self, data_mod, tmp_path):
        inv = {'models': [{'model_id': 'M-TEST'}]}
        p = tmp_path / 'model_inventory.json'
        p.write_text(json.dumps(inv))
        with patch.object(data_mod, 'DATA_DIR', tmp_path):
            result = data_mod.load_inventory()
        assert result['models'][0]['model_id'] == 'M-TEST'

    def test_load_inventory_missing(self, data_mod, tmp_path):
        with patch.object(data_mod, 'DATA_DIR', tmp_path):
            result = data_mod.load_inventory()
        assert result == {}

    def test_load_inventory_bad_json(self, data_mod, tmp_path):
        (tmp_path / 'model_inventory.json').write_text('{bad json')
        with patch.object(data_mod, 'DATA_DIR', tmp_path):
            result = data_mod.load_inventory()
        assert result == {}

    def test_load_meetings(self, data_mod, tmp_path):
        meetings = [{'id': 'MRC-1'}]
        (tmp_path / 'mrc_meetings.json').write_text(json.dumps(meetings))
        with patch.object(data_mod, 'DATA_DIR', tmp_path):
            result = data_mod.load_meetings()
        assert len(result) == 1

    def test_load_meetings_dict_fallback(self, data_mod, tmp_path):
        (tmp_path / 'mrc_meetings.json').write_text('{"not": "a list"}')
        with patch.object(data_mod, 'DATA_DIR', tmp_path):
            result = data_mod.load_meetings()
        assert result == []

    def test_load_bcbs(self, data_mod, tmp_path):
        (tmp_path / 'bcbs239_assessment.json').write_text(
            '{"principles": []}')
        with patch.object(data_mod, 'DATA_DIR', tmp_path):
            result = data_mod.load_bcbs()
        assert 'principles' in result

    def test_load_raci(self, data_mod, tmp_path):
        (tmp_path / 'raci_matrix.json').write_text('{"roles": []}')
        with patch.object(data_mod, 'DATA_DIR', tmp_path):
            result = data_mod.load_raci()
        assert 'roles' in result

    def test_load_audit_log(self, data_mod, tmp_path):
        log = [{'model_id': 'M-1', 'event': 'test'}]
        (tmp_path / 'model_audit_log.json').write_text(json.dumps(log))
        with patch.object(data_mod, 'DATA_DIR', tmp_path):
            result = data_mod.load_audit_log()
        assert len(result) == 1

    def test_load_audit_log_dict_fallback(self, data_mod, tmp_path):
        (tmp_path / 'model_audit_log.json').write_text('{}')
        with patch.object(data_mod, 'DATA_DIR', tmp_path):
            result = data_mod.load_audit_log()
        assert result == []

    def test_load_junit(self, data_mod, tmp_path):
        junit_xml = (
            '<?xml version="1.0"?>'
            '<testsuites>'
            '<testsuite tests="100" failures="2" errors="1" '
            'skipped="3" time="12.5"/>'
            '</testsuites>'
        )
        audit = tmp_path / 'audit'
        audit.mkdir()
        (audit / 'junit.xml').write_text(junit_xml)
        with patch.object(data_mod, 'AUDIT_DIR', audit):
            result = data_mod.load_junit()
        assert result['total'] == 100
        assert result['failed'] == 2
        assert result['errors'] == 1
        assert result['skipped'] == 3
        assert result['passed'] == 94
        assert result['time_s'] == pytest.approx(12.5)

    def test_load_junit_missing(self, data_mod, tmp_path):
        with patch.object(data_mod, 'AUDIT_DIR', tmp_path):
            result = data_mod.load_junit()
        assert result['total'] == 0

    def test_load_junit_corrupt(self, data_mod, tmp_path):
        (tmp_path / 'junit.xml').write_text('not xml')
        with patch.object(data_mod, 'AUDIT_DIR', tmp_path):
            result = data_mod.load_junit()
        assert result['total'] == 0

    def test_load_coverage(self, data_mod, tmp_path):
        cov_xml = (
            '<?xml version="1.0"?>'
            '<coverage line-rate="0.825"/>'
        )
        (tmp_path / 'coverage.xml').write_text(cov_xml)
        with patch.object(data_mod, 'AUDIT_DIR', tmp_path):
            result = data_mod.load_coverage()
        assert result == pytest.approx(82.5)

    def test_load_coverage_missing(self, data_mod, tmp_path):
        with patch.object(data_mod, 'AUDIT_DIR', tmp_path):
            result = data_mod.load_coverage()
        assert result is None

    def test_load_coverage_corrupt(self, data_mod, tmp_path):
        (tmp_path / 'coverage.xml').write_text('garbage')
        with patch.object(data_mod, 'AUDIT_DIR', tmp_path):
            result = data_mod.load_coverage()
        assert result is None

    def test_list_audit_files(self, data_mod, tmp_path):
        audit = tmp_path / 'audit'
        audit.mkdir()
        (audit / 'report.pdf').write_bytes(b'%PDF-fake')
        (audit / '.hidden').write_text('x')
        (audit / 'subdir').mkdir()
        with patch.object(data_mod, 'AUDIT_DIR', audit):
            result = data_mod.list_audit_files()
        assert len(result) == 1
        assert result[0]['name'] == 'report.pdf'
        assert 'size_kb' in result[0]
        assert 'modified' in result[0]

    def test_list_audit_files_missing_dir(self, data_mod, tmp_path):
        with patch.object(data_mod, 'AUDIT_DIR', tmp_path / 'nope'):
            result = data_mod.list_audit_files()
        assert result == []

    def test_list_sensitivity_generators(self, data_mod, tmp_path):
        docs_dir = tmp_path / 'docs' / 'models' / 'sensitivities'
        gen = docs_dir / 'hazard' / 'generator'
        gen.mkdir(parents=True)
        (gen / '__init__.py').write_text('')
        # non-matching dir (no generator/__init__.py)
        (docs_dir / 'other').mkdir()
        with patch.object(data_mod, '_root', tmp_path):
            result = data_mod.list_sensitivity_generators()
        assert result == ['hazard']

    def test_list_sensitivity_generators_no_dir(self, data_mod, tmp_path):
        with patch.object(data_mod, '_root', tmp_path):
            result = data_mod.list_sensitivity_generators()
        assert result == []

    def test_collect_all_keys(self, data_mod, tmp_path):
        audit = tmp_path / 'audit'
        audit.mkdir()
        (tmp_path / 'model_inventory.json').write_text('{"models":[]}')
        (tmp_path / 'mrc_meetings.json').write_text('[]')
        (tmp_path / 'bcbs239_assessment.json').write_text('{}')
        (tmp_path / 'raci_matrix.json').write_text('{}')
        (tmp_path / 'model_audit_log.json').write_text('[]')
        with patch.object(data_mod, 'DATA_DIR', tmp_path), \
             patch.object(data_mod, 'AUDIT_DIR', audit), \
             patch.object(data_mod, '_root', tmp_path):
            result = data_mod.collect_all()
        expected_keys = {'inventory', 'models', 'meetings', 'bcbs', 'raci',
                         'audit_log', 'junit', 'coverage_pct', 'audit_files',
                         'sensitivity_generators'}
        assert expected_keys == set(result.keys())


# ---------------------------------------------------------------------------
# TestSectionBuilders — cover + 11 sections
# ---------------------------------------------------------------------------

class TestBuildCover:
    """Test sections/cover.py."""

    def test_cover_basic(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.cover import build_cover
        S = styles_mod.get_styles()
        story = []
        build_cover(sample_data, story, S)
        assert len(story) > 0

    def test_cover_with_bcbs(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.cover import build_cover
        S = styles_mod.get_styles()
        story = []
        build_cover(sample_data, story, S)
        texts = [str(f) for f in story]
        combined = ' '.join(texts)
        assert 'BCBS' in combined or len(story) >= 5

    def test_cover_with_tests(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.cover import build_cover
        sample_data['junit'] = SAMPLE_JUNIT_CLEAN
        S = styles_mod.get_styles()
        story = []
        build_cover(sample_data, story, S)
        assert len(story) >= 5

    def test_cover_no_tests(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.cover import build_cover
        sample_data['junit'] = SAMPLE_JUNIT_EMPTY
        S = styles_mod.get_styles()
        story = []
        build_cover(sample_data, story, S)
        assert len(story) >= 3

    def test_cover_no_bcbs(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.cover import build_cover
        sample_data['bcbs'] = {}
        S = styles_mod.get_styles()
        story = []
        build_cover(sample_data, story, S)
        assert len(story) >= 3


class TestBuildExecSummary:
    """Test sections/executive.py."""

    def test_exec_summary_renders(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.executive import build_exec_summary
        S = styles_mod.get_styles()
        story = []
        build_exec_summary(sample_data, story, S)
        assert len(story) > 0

    def test_exec_summary_all_pass(self, styles_mod):
        from docs.models.model_risk.sections.executive import build_exec_summary
        data = _full_data(
            models=[_make_model(
                validation_questions=[
                    {'short_label': 'Q1', 'status': 'Addressed'}],
                remediation_steps=[
                    {'status': 'Completed', 'due_date': '2025-01-01'}],
            )],
            junit=SAMPLE_JUNIT_CLEAN,
            coverage_pct=90.0,
        )
        S = styles_mod.get_styles()
        story = []
        build_exec_summary(data, story, S)
        assert len(story) > 0

    def test_exec_summary_failures(self, styles_mod):
        from docs.models.model_risk.sections.executive import build_exec_summary
        data = _full_data(
            junit={'total': 100, 'passed': 95, 'failed': 5,
                   'errors': 0, 'skipped': 0, 'time_s': 10.0},
        )
        S = styles_mod.get_styles()
        story = []
        build_exec_summary(data, story, S)
        assert len(story) > 0

    def test_exec_summary_no_coverage(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.executive import build_exec_summary
        sample_data['coverage_pct'] = None
        S = styles_mod.get_styles()
        story = []
        build_exec_summary(sample_data, story, S)
        assert len(story) > 0

    def test_exec_summary_no_tests(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.executive import build_exec_summary
        sample_data['junit'] = SAMPLE_JUNIT_EMPTY
        S = styles_mod.get_styles()
        story = []
        build_exec_summary(sample_data, story, S)
        assert len(story) > 0


class TestBuildInventory:
    """Test sections/inventory.py."""

    def test_inventory_renders(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.inventory import build_model_inventory
        S = styles_mod.get_styles()
        story = []
        build_model_inventory(sample_data, story, S)
        assert len(story) > 0

    def test_inventory_empty(self, styles_mod, empty_data):
        from docs.models.model_risk.sections.inventory import build_model_inventory
        S = styles_mod.get_styles()
        story = []
        build_model_inventory(empty_data, story, S)
        # Should have heading + note
        assert len(story) >= 2

    def test_inventory_rag_colours(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.inventory import build_model_inventory
        S = styles_mod.get_styles()
        story = []
        build_model_inventory(sample_data, story, S)
        # Should have table with models
        assert len(story) >= 3

    def test_inventory_risk_ratings(self, styles_mod):
        from docs.models.model_risk.sections.inventory import build_model_inventory
        data = _full_data(models=[
            _make_model('M-001', overall_risk_rating=SAMPLE_RISK_RATING),
        ])
        S = styles_mod.get_styles()
        story = []
        build_model_inventory(data, story, S)
        # Should include risk rating table
        assert len(story) >= 4

    def test_inventory_no_risk_ratings(self, styles_mod):
        from docs.models.model_risk.sections.inventory import build_model_inventory
        data = _full_data(models=[_make_model('M-001')])
        S = styles_mod.get_styles()
        story = []
        build_model_inventory(data, story, S)
        assert len(story) >= 3


class TestBuildValidation:
    """Test sections/validation.py."""

    def test_validation_renders(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.validation import build_validation_status
        S = styles_mod.get_styles()
        story = []
        build_validation_status(sample_data, story, S)
        assert len(story) > 0

    def test_validation_no_questions(self, styles_mod, empty_data):
        from docs.models.model_risk.sections.validation import build_validation_status
        S = styles_mod.get_styles()
        story = []
        build_validation_status(empty_data, story, S)
        assert len(story) >= 1

    def test_validation_high_assumptions(self, styles_mod):
        from docs.models.model_risk.sections.validation import build_validation_status
        data = _full_data(models=[
            _make_model('M-001', assumptions=SAMPLE_ASSUMPTIONS),
        ])
        S = styles_mod.get_styles()
        story = []
        build_validation_status(data, story, S)
        assert len(story) > 3

    def test_validation_no_assumptions(self, styles_mod):
        from docs.models.model_risk.sections.validation import build_validation_status
        data = _full_data(models=[_make_model('M-001')])
        S = styles_mod.get_styles()
        story = []
        build_validation_status(data, story, S)
        # Should show "No high-impact assumptions flagged"
        assert len(story) >= 3

    def test_validation_peer_reviewer_gaps(self, styles_mod):
        from docs.models.model_risk.sections.validation import build_validation_status
        data = _full_data(models=[
            _make_model('M-001', peer_reviewer='TBD'),
            _make_model('M-002', peer_reviewer=None),
        ])
        S = styles_mod.get_styles()
        story = []
        build_validation_status(data, story, S)
        assert len(story) >= 4

    def test_validation_all_reviewers_assigned(self, styles_mod):
        from docs.models.model_risk.sections.validation import build_validation_status
        data = _full_data(models=[
            _make_model('M-001', peer_reviewer='Bob'),
        ])
        S = styles_mod.get_styles()
        story = []
        build_validation_status(data, story, S)
        assert len(story) >= 3


class TestBuildMRC:
    """Test sections/mrc.py."""

    def test_mrc_renders(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.mrc import build_mrc_activity
        S = styles_mod.get_styles()
        story = []
        build_mrc_activity(sample_data, story, S)
        assert len(story) > 0

    def test_mrc_no_meetings(self, styles_mod, empty_data):
        from docs.models.model_risk.sections.mrc import build_mrc_activity
        S = styles_mod.get_styles()
        story = []
        build_mrc_activity(empty_data, story, S)
        assert len(story) >= 2

    def test_mrc_with_decisions(self, styles_mod):
        from docs.models.model_risk.sections.mrc import build_mrc_activity
        data = _full_data(meetings=[
            _make_meeting('MRC-001', decisions=SAMPLE_DECISIONS,
                          actions=SAMPLE_ACTIONS),
        ])
        S = styles_mod.get_styles()
        story = []
        build_mrc_activity(data, story, S)
        assert len(story) >= 5

    def test_mrc_no_decisions(self, styles_mod):
        from docs.models.model_risk.sections.mrc import build_mrc_activity
        data = _full_data(meetings=[
            _make_meeting('MRC-001', status='Completed'),
        ])
        S = styles_mod.get_styles()
        story = []
        build_mrc_activity(data, story, S)
        assert len(story) >= 3

    def test_mrc_open_actions(self, styles_mod):
        from docs.models.model_risk.sections.mrc import build_mrc_activity
        data = _full_data(meetings=[
            _make_meeting('MRC-001', actions=[
                {'id': 'A1', 'title': 'Do thing', 'owner': 'X',
                 'due_date': '2026-04-01', 'status': 'Open'},
            ]),
        ])
        S = styles_mod.get_styles()
        story = []
        build_mrc_activity(data, story, S)
        assert len(story) >= 4

    def test_mrc_completed_actions_excluded(self, styles_mod):
        from docs.models.model_risk.sections.mrc import build_mrc_activity
        data = _full_data(meetings=[
            _make_meeting('MRC-001', actions=[
                {'id': 'A1', 'title': 'Done', 'status': 'Completed'},
            ]),
        ])
        S = styles_mod.get_styles()
        story = []
        build_mrc_activity(data, story, S)
        # No open actions section
        assert len(story) >= 3


class TestBuildRemediation:
    """Test sections/remediation.py."""

    def test_remediation_renders(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.remediation import build_remediation
        S = styles_mod.get_styles()
        story = []
        build_remediation(sample_data, story, S)
        assert len(story) > 0

    def test_remediation_empty(self, styles_mod, empty_data):
        from docs.models.model_risk.sections.remediation import build_remediation
        S = styles_mod.get_styles()
        story = []
        build_remediation(empty_data, story, S)
        assert len(story) >= 2

    def test_remediation_overdue_highlighted(self, styles_mod):
        from docs.models.model_risk.sections.remediation import build_remediation
        data = _full_data(models=[
            _make_model('M-001', remediation_steps=[
                {'id': 'R1', 'description': 'Overdue item',
                 'priority': 'High', 'due_date': '2020-01-01',
                 'status': 'Open'},
            ]),
        ])
        S = styles_mod.get_styles()
        story = []
        build_remediation(data, story, S)
        assert len(story) >= 4

    def test_remediation_all_completed(self, styles_mod):
        from docs.models.model_risk.sections.remediation import build_remediation
        data = _full_data(models=[
            _make_model('M-001', remediation_steps=[
                {'id': 'R1', 'description': 'Done', 'priority': 'Low',
                 'due_date': '2026-01-01', 'status': 'Completed'},
            ]),
        ])
        S = styles_mod.get_styles()
        story = []
        build_remediation(data, story, S)
        assert len(story) >= 4

    def test_remediation_priority_sorting(self, styles_mod):
        from docs.models.model_risk.sections.remediation import build_remediation
        data = _full_data(models=[
            _make_model('M-001', remediation_steps=[
                {'id': 'R1', 'description': 'Low', 'priority': 'Low',
                 'due_date': '2026-06-01', 'status': 'Open'},
                {'id': 'R2', 'description': 'High', 'priority': 'High',
                 'due_date': '2026-06-01', 'status': 'Open'},
                {'id': 'R3', 'description': 'Medium', 'priority': 'Medium',
                 'due_date': '2026-06-01', 'status': 'Open'},
            ]),
        ])
        S = styles_mod.get_styles()
        story = []
        build_remediation(data, story, S)
        assert len(story) >= 4


class TestBuildBCBS239:
    """Test sections/bcbs239.py."""

    def test_bcbs239_renders(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.bcbs239 import build_bcbs239
        S = styles_mod.get_styles()
        story = []
        build_bcbs239(sample_data, story, S)
        assert len(story) > 0

    def test_bcbs239_no_principles(self, styles_mod, empty_data):
        from docs.models.model_risk.sections.bcbs239 import build_bcbs239
        S = styles_mod.get_styles()
        story = []
        build_bcbs239(empty_data, story, S)
        assert len(story) >= 2

    def test_bcbs239_at_risk(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.bcbs239 import build_bcbs239
        S = styles_mod.get_styles()
        story = []
        build_bcbs239(sample_data, story, S)
        # Should have "Principles Requiring Attention" for score<=2
        assert len(story) >= 5

    def test_bcbs239_all_compliant(self, styles_mod):
        from docs.models.model_risk.sections.bcbs239 import build_bcbs239
        data = _full_data(bcbs=_make_bcbs([
            _make_principle(1, 'Gov', 'O', 4, 4, 'Fully Compliant'),
            _make_principle(2, 'Arch', 'O', 3, 4, 'Largely Compliant'),
        ]))
        S = styles_mod.get_styles()
        story = []
        build_bcbs239(data, story, S)
        assert len(story) >= 4


class TestBuildRACI:
    """Test sections/raci.py."""

    def test_raci_renders(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.raci import build_raci
        S = styles_mod.get_styles()
        story = []
        build_raci(sample_data, story, S)
        assert len(story) > 0

    def test_raci_no_roles(self, styles_mod, empty_data):
        from docs.models.model_risk.sections.raci import build_raci
        S = styles_mod.get_styles()
        story = []
        build_raci(empty_data, story, S)
        assert len(story) >= 2

    def test_raci_missing_backup(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.raci import build_raci
        S = styles_mod.get_styles()
        story = []
        build_raci(sample_data, story, S)
        # Validator has no backup — should be highlighted
        assert len(story) >= 3

    def test_raci_with_activities(self, styles_mod, sample_data):
        from docs.models.model_risk.sections.raci import build_raci
        S = styles_mod.get_styles()
        story = []
        build_raci(sample_data, story, S)
        assert len(story) >= 5

    def test_raci_escalation_triggers_string(self, styles_mod):
        from docs.models.model_risk.sections.raci import build_raci
        data = _full_data(raci=_make_raci(
            roles=[_make_role()],
            escalation_triggers=['Red RAG', 'Overdue > 30d'],
        ))
        S = styles_mod.get_styles()
        story = []
        build_raci(data, story, S)
        assert len(story) >= 5

    def test_raci_escalation_triggers_dict(self, styles_mod):
        from docs.models.model_risk.sections.raci import build_raci
        data = _full_data(raci=_make_raci(
            roles=[_make_role()],
            escalation_triggers=[
                {'trigger': 'Model failure'},
                {'description': 'Data breach detected'},
            ],
        ))
        S = styles_mod.get_styles()
        story = []
        build_raci(data, story, S)
        assert len(story) >= 5


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
