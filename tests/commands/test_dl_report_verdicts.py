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

"""Tests for data_lineage — verdict, health, topology ownership, reconciliation principles."""

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
# Verdict and health helpers
# ---------------------------------------------------------------------------

class TestComputeVerdict:
    """_compute_verdict must return the most conservative status."""

    def test_compliant_when_all_pass(self, dl_mod):
        chain = {"is_consistent": True, "stale_steps": [],
                 "missing_steps": []}
        lr = {"total": 19, "passed": 19, "failed": 0}
        assert dl_mod._compute_verdict(chain, lr) == 'COMPLIANT'

    def test_partially_compliant_on_test_failures(self, dl_mod):
        chain = {"is_consistent": True, "stale_steps": [],
                 "missing_steps": []}
        lr = {"total": 19, "passed": 18, "failed": 1}
        assert dl_mod._compute_verdict(chain, lr) == 'PARTIALLY COMPLIANT'

    def test_non_compliant_on_broken_chain(self, dl_mod):
        chain = {"is_consistent": False, "stale_steps": ["hazard"],
                 "missing_steps": []}
        lr = {"total": 19, "passed": 18, "failed": 1}
        assert dl_mod._compute_verdict(chain, lr) == 'NON-COMPLIANT'

    def test_non_compliant_on_missing_steps(self, dl_mod):
        chain = {"is_consistent": True, "stale_steps": [],
                 "missing_steps": ["propertyhc"]}
        lr = {"total": 19, "passed": 19, "failed": 0}
        assert dl_mod._compute_verdict(chain, lr) == 'NON-COMPLIANT'

    def test_non_compliant_on_majority_failures(self, dl_mod):
        chain = {"is_consistent": True, "stale_steps": [],
                 "missing_steps": []}
        lr = {"total": 19, "passed": 9, "failed": 10}
        assert dl_mod._compute_verdict(chain, lr) == 'NON-COMPLIANT'

    def test_partially_compliant_when_no_tests_run(self, dl_mod):
        """No tests run cannot prove compliance."""
        chain = {"is_consistent": True, "stale_steps": [],
                 "missing_steps": []}
        lr = {"total": 0, "passed": 0, "failed": 0}
        assert dl_mod._compute_verdict(chain, lr) == 'PARTIALLY COMPLIANT'

    def test_empty_lineage_results(self, dl_mod):
        chain = {"is_consistent": True, "stale_steps": [],
                 "missing_steps": []}
        assert dl_mod._compute_verdict(chain, {}) == 'PARTIALLY COMPLIANT'


class TestComputeHealth:
    """_compute_health must downgrade on any issue."""

    def test_consistent_when_all_clear(self, dl_mod):
        chain = {"is_consistent": True, "stale_steps": []}
        lr = {"total": 19, "passed": 19, "failed": 0}
        assert dl_mod._compute_health(chain, lr) == 'CONSISTENT'

    def test_degraded_on_test_failures(self, dl_mod):
        chain = {"is_consistent": True, "stale_steps": []}
        lr = {"total": 19, "passed": 18, "failed": 1}
        assert dl_mod._compute_health(chain, lr) == 'DEGRADED'

    def test_degraded_on_stale_steps(self, dl_mod):
        chain = {"is_consistent": True, "stale_steps": ["propertyhc"]}
        lr = {"total": 19, "passed": 19, "failed": 0}
        assert dl_mod._compute_health(chain, lr) == 'DEGRADED'

    def test_inconsistent_on_broken_chain(self, dl_mod):
        chain = {"is_consistent": False, "stale_steps": ["hazard"]}
        lr = {"total": 19, "passed": 18, "failed": 1}
        assert dl_mod._compute_health(chain, lr) == 'INCONSISTENT'

    def test_health_colour_mapping(self, dl_mod):
        assert dl_mod._health_colour('CONSISTENT') == dl_mod.GREEN
        assert dl_mod._health_colour('DEGRADED') == dl_mod.AMBER
        assert dl_mod._health_colour('INCONSISTENT') == dl_mod.RED
        assert dl_mod._health_colour('UNKNOWN') == dl_mod.RED


# ---------------------------------------------------------------------------
# Topology ownership column
# ---------------------------------------------------------------------------

class TestTopologyOwnership:
    """Topology table should include owner column."""

    def test_step_owners_covers_all_graph_steps(self, dl_mod):
        from lineage.manifest import DEPENDENCY_GRAPH
        for step in DEPENDENCY_GRAPH:
            assert step in dl_mod.STEP_OWNERS, (
                f"STEP_OWNERS missing entry for '{step}'")

    def test_topology_renders_owner(self, dl_mod, sample_data_consistent):
        S = dl_mod._styles()
        story = []
        dl_mod._build_topology(sample_data_consistent, story, S)
        from reportlab.platypus import Table
        tables = [e for e in story if isinstance(e, Table)]
        assert len(tables) >= 1
        header_row = tables[0]._cellvalues[0]
        assert 'Owner' in header_row


# ---------------------------------------------------------------------------
# Reconciliation BCBS principle column
# ---------------------------------------------------------------------------

class TestReconciliationPrinciples:
    """Reconciliation table should include BCBS principle mapping."""

    def test_recon_table_has_principle_column(self, dl_mod,
                                               sample_data_consistent):
        S = dl_mod._styles()
        story = []
        dl_mod._build_reconciliation(sample_data_consistent, story, S)
        from reportlab.platypus import Table
        tables = [e for e in story if isinstance(e, Table)]
        header_row = tables[0]._cellvalues[0]
        assert 'BCBS Principle(s)' in header_row

    def test_failure_metadata_covers_key_tests(self, dl_mod):
        expected = [
            'test_no_stale_inputs',
            'test_gauge_id_consistency',
            'test_deterministic_ids',
        ]
        for name in expected:
            assert name in dl_mod.FAILURE_METADATA, (
                f"FAILURE_METADATA missing '{name}'")
            meta = dl_mod.FAILURE_METADATA[name]
            assert 'principle' in meta
            assert 'description' in meta
            assert 'remediation' in meta
