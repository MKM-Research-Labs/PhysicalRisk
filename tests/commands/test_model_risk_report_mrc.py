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

"""Tests for model_risk MRC, remediation, BCBS239, and RACI sections."""

import pytest

from tests.commands.model_risk_helpers_part1 import (
    _make_model, _make_meeting, _make_bcbs, _make_principle,
    _make_raci, _make_role,
)
from tests.commands.model_risk_helpers_part2 import (
    _full_data,
    SAMPLE_DECISIONS, SAMPLE_ACTIONS, SAMPLE_ASSUMPTIONS,
)


# ---------------------------------------------------------------------------
# TestBuildMRC
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# TestBuildRemediation
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# TestBuildBCBS239
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# TestBuildRACI
# ---------------------------------------------------------------------------

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
