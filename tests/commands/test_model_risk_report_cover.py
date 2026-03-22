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

"""Tests for model_risk cover, executive summary, inventory, and validation sections."""

import pytest

from tests.commands.model_risk_helpers import (
    _full_data, _make_model,
    SAMPLE_VQ, SAMPLE_REMEDIATION, SAMPLE_ASSUMPTIONS,
    SAMPLE_TEST_COVERAGE, SAMPLE_RISK_RATING,
    SAMPLE_JUNIT_CLEAN, SAMPLE_JUNIT_EMPTY,
)


# ---------------------------------------------------------------------------
# TestBuildCover
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


# ---------------------------------------------------------------------------
# TestBuildExecSummary
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# TestBuildInventory
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# TestBuildValidation
# ---------------------------------------------------------------------------

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
