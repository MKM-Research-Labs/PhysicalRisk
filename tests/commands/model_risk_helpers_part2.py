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

"""Shared sample data constants and _full_data builder for model_risk report tests (part 2)."""

from tests.commands.model_risk_helpers_part1 import (
    _make_model,
    _make_meeting,
    _make_bcbs,
    _make_principle,
    _make_raci,
    _make_role,
)


# ---------------------------------------------------------------------------
# Sample data constants
# ---------------------------------------------------------------------------

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
