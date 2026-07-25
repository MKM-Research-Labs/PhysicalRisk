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

"""Tests for model test attribution and its reconciliation.

The reconciliation cases matter more than they look: the failure they guard
against is silent. Under the exact-path mapping these rules replaced, splitting
a test module cost a model its documented evidence with nothing in any output
to say so, and the loss only surfaced when someone read the LaTeX.
"""

from docs.models.test_results.generator.attribution import (
    Resolver,
    collectable_paths,
    format_reconciliation,
    reconcile,
)
from docs.models.test_results.generator.models import MODEL_INFO

from config import config


class TestRuleResolution:
    """Rules resolve most-specific-first, regardless of the order written."""

    def test_directory_rule_claims_the_whole_subtree(self):
        r = Resolver([('tests/models/seismic/', 'MKM-SEIS-001')])
        assert r.model_for('tests/models/seismic/test_damage.py') == 'MKM-SEIS-001'
        assert r.model_for('tests/models/seismic/deep/test_x.py') == 'MKM-SEIS-001'

    def test_unmatched_path_falls_to_platform(self):
        r = Resolver([('tests/models/seismic/', 'MKM-SEIS-001')])
        assert r.model_for('tests/routes/test_pages.py') == 'PLATFORM'

    def test_file_glob_beats_a_directory_rule_covering_it(self):
        r = Resolver([
            ('tests/models/trading/', 'MKM-TD-001'),
            ('tests/models/trading/delta/engine.py', 'MKM-DE-001'),
        ])
        assert r.model_for('tests/models/trading/pnl/eod.py') == 'MKM-TD-001'
        assert r.model_for('tests/models/trading/delta/engine.py') == 'MKM-DE-001'

    def test_longer_directory_prefix_wins(self):
        r = Resolver([
            ('tests/models/', 'MKM-TD-001'),
            ('tests/models/typhoon/pipeline/', 'MKM-TC-001'),
        ])
        assert r.model_for('tests/models/typhoon/pipeline/event.py') == 'MKM-TC-001'

    def test_rule_order_does_not_change_the_outcome(self):
        rules = [
            ('tests/models/trading/delta/engine.py', 'MKM-DE-001'),
            ('tests/models/trading/', 'MKM-TD-001'),
        ]
        forward, reverse = Resolver(rules), Resolver(list(reversed(rules)))
        path = 'tests/models/trading/delta/engine.py'
        assert forward.model_for(path) == reverse.model_for(path) == 'MKM-DE-001'

    def test_glob_never_crosses_a_directory_boundary(self):
        r = Resolver([('tests/models/*.py', 'MKM-DD-001')])
        assert r.model_for('tests/models/velocity.py') == 'MKM-DD-001'
        assert r.model_for('tests/models/fire/test_initiation.py') == 'PLATFORM'


class TestSplitSurvival:
    """The regression these rules exist for: an oversized module gets split."""

    RULES = [('tests/models/typhoon/genesis*.py', 'MKM-TC-001')]

    def test_split_into_parts_keeps_its_attribution(self):
        r = Resolver(self.RULES)
        for part in ('genesis_part1', 'genesis_part2', 'genesis_part3'):
            assert r.model_for(f'tests/models/typhoon/{part}.py') == 'MKM-TC-001'

    def test_a_split_leaves_the_rule_reconciled(self):
        rec = reconcile(
            ['tests/models/typhoon/genesis_part1.py',
             'tests/models/typhoon/genesis_part2.py'],
            rules=self.RULES,
        )
        assert rec.ok
        assert rec.unused_rules == []

    def test_a_stem_glob_does_not_swallow_a_neighbour(self):
        r = Resolver([('tests/models/typhoon/wind_field/radial*.py', 'MKM-TC-001')])
        assert r.model_for(
            'tests/models/typhoon/wind_field/test_radial_coverage.py') == 'PLATFORM'


class TestReconciliation:
    """What the gate fails on."""

    def test_rule_matching_nothing_is_reported_unused(self):
        rules = [('tests/models/typhoon/genesis*.py', 'MKM-TC-001')]
        rec = reconcile(['tests/models/typhoon/origins_part1.py'], rules=rules)

        assert not rec.ok
        assert rec.unused_rules == [
            ('tests/models/typhoon/genesis*.py', 'MKM-TC-001')]

    def test_model_losing_every_test_is_reported(self):
        rules = [('tests/models/typhoon/genesis*.py', 'MKM-TC-001')]
        rec = reconcile(['tests/routes/test_pages.py'], rules=rules)

        assert rec.models_without_tests == ['MKM-TC-001']

    def test_rule_shadowed_by_a_more_specific_one_reads_as_unused(self):
        # The directory rule wins nothing: every file it covers is claimed by
        # the glob. Leaving it in place would misrepresent MKM-TD-001 as having
        # evidence it does not have.
        rules = [
            ('tests/models/trading/delta/', 'MKM-TD-001'),
            ('tests/models/trading/delta/engine*.py', 'MKM-DE-001'),
        ]
        rec = reconcile(['tests/models/trading/delta/engine.py'], rules=rules)

        assert ('tests/models/trading/delta/', 'MKM-TD-001') in rec.unused_rules

    def test_counts_split_between_attributed_and_platform(self):
        rules = [('tests/models/fire/', 'MKM-FIRE-001')]
        rec = reconcile(
            ['tests/models/fire/test_initiation.py', 'tests/routes/test_pages.py'],
            rules=rules,
        )

        assert rec.total_files == 2
        assert rec.attributed_files == 1
        assert rec.per_model['PLATFORM'] == ['tests/routes/test_pages.py']

    def test_report_names_the_rule_and_the_file_to_edit(self):
        rules = [('tests/models/typhoon/genesis*.py', 'MKM-TC-001')]
        text = format_reconciliation(reconcile(['tests/routes/test_x.py'],
                                               rules=rules))

        assert 'tests/models/typhoon/genesis*.py' in text
        assert 'models.py' in text


class TestCollectablePaths:
    """The static walk must agree with what pytest actually collects."""

    def test_finds_this_very_file(self):
        paths = collectable_paths(config.get_project_root())
        assert 'tests/docs/test_model_attribution.py' in paths

    def test_includes_non_prefixed_files_in_registered_directories(self):
        paths = collectable_paths(config.get_project_root())
        assert 'tests/models/velocity.py' in paths

    def test_excludes_conftest_private_modules_and_e2e(self):
        paths = collectable_paths(config.get_project_root())
        assert not [p for p in paths if p.startswith('tests/e2e/')]
        assert not [p for p in paths if p.endswith('/conftest.py')]
        assert not [p for p in paths
                    if p.rsplit('/', 1)[-1].startswith('_')]


class TestProjectRules:
    """Static invariants of the rule list itself.

    Deliberately not asserting that every rule still resolves against the tree —
    that check is reported by the generator on each run, not enforced here.
    """

    def test_every_rule_target_is_a_known_model(self):
        from docs.models.test_results.generator.models import TEST_MODEL_RULES
        unknown = {m for _, m in TEST_MODEL_RULES if m not in MODEL_INFO}
        assert not unknown
