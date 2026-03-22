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

"""Tests for data_lineage — collect_all() and create_pdf_report()."""

from pathlib import Path
from unittest.mock import patch

import pytest

from tests.commands.data_lineage_helpers import (
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
# collect_all()
# ---------------------------------------------------------------------------

class TestCollectAll:

    def test_returns_dict(self, dl_mod):
        """collect_all() returns a dict with expected keys."""
        data = dl_mod.collect_all()
        assert isinstance(data, dict)
        assert 'manifest' in data
        assert 'graph' in data
        assert 'step_io' in data
        assert 'chain_result' in data
        assert 'step_details' in data

    def test_num_steps_positive(self, dl_mod):
        """Pipeline must have at least one step."""
        data = dl_mod.collect_all()
        assert data['num_steps'] > 0

    def test_step_details_list(self, dl_mod):
        """step_details is a list of dicts."""
        data = dl_mod.collect_all()
        assert isinstance(data['step_details'], list)
        for sd in data['step_details']:
            assert isinstance(sd, dict)
            assert 'step' in sd
            assert 'dependencies' in sd
            assert 'inputs' in sd
            assert 'outputs' in sd
            assert 'status' in sd

    def test_chain_result_structure(self, dl_mod):
        """chain_result has expected keys."""
        data = dl_mod.collect_all()
        chain = data['chain_result']
        assert 'is_consistent' in chain
        assert 'stale_steps' in chain
        assert 'missing_steps' in chain

    def test_graph_matches_step_details(self, dl_mod):
        """Every step in graph should have a step_details entry."""
        data = dl_mod.collect_all()
        graph_steps = set(data['graph'].keys())
        detail_steps = {sd['step'] for sd in data['step_details']}
        assert graph_steps == detail_steps


# ---------------------------------------------------------------------------
# create_pdf_report() — PDF generation
# ---------------------------------------------------------------------------

class TestCreatePdfReport:

    def test_returns_path(self, dl_mod, tmp_path, sample_data_consistent):
        """create_pdf_report() returns a Path object."""
        out = tmp_path / 'data_lineage_report.pdf'
        with patch.object(dl_mod, 'OUTPUT_PDF', out), \
             patch.object(dl_mod, 'AUDIT_DIR', tmp_path):
            result = dl_mod.create_pdf_report(sample_data_consistent)
        assert isinstance(result, Path)

    def test_pdf_created(self, dl_mod, tmp_path, sample_data_consistent):
        """PDF file is created on disk."""
        out = tmp_path / 'data_lineage_report.pdf'
        with patch.object(dl_mod, 'OUTPUT_PDF', out), \
             patch.object(dl_mod, 'AUDIT_DIR', tmp_path):
            dl_mod.create_pdf_report(sample_data_consistent)
        assert out.exists()

    def test_pdf_header(self, dl_mod, tmp_path, sample_data_consistent):
        """Generated file has PDF magic bytes."""
        out = tmp_path / 'data_lineage_report.pdf'
        with patch.object(dl_mod, 'OUTPUT_PDF', out), \
             patch.object(dl_mod, 'AUDIT_DIR', tmp_path):
            dl_mod.create_pdf_report(sample_data_consistent)
        assert out.read_bytes()[:4] == b'%PDF'

    def test_pdf_nonempty(self, dl_mod, tmp_path, sample_data_consistent):
        """PDF has reasonable size (multi-page report)."""
        out = tmp_path / 'data_lineage_report.pdf'
        with patch.object(dl_mod, 'OUTPUT_PDF', out), \
             patch.object(dl_mod, 'AUDIT_DIR', tmp_path):
            dl_mod.create_pdf_report(sample_data_consistent)
        assert out.stat().st_size > 5000

    def test_pdf_with_issues(self, dl_mod, tmp_path, sample_data_issues):
        """PDF generates correctly when pipeline has stale/missing steps."""
        out = tmp_path / 'data_lineage_report.pdf'
        with patch.object(dl_mod, 'OUTPUT_PDF', out), \
             patch.object(dl_mod, 'AUDIT_DIR', tmp_path):
            dl_mod.create_pdf_report(sample_data_issues)
        assert out.exists()
        assert out.read_bytes()[:4] == b'%PDF'
        assert out.stat().st_size > 5000

    def test_pdf_with_no_lineage_results(self, dl_mod, tmp_path,
                                          sample_data_consistent):
        """PDF renders when lineage_results is empty (tests not run)."""
        data = dict(sample_data_consistent)
        data['lineage_results'] = {}
        out = tmp_path / 'data_lineage_report.pdf'
        with patch.object(dl_mod, 'OUTPUT_PDF', out), \
             patch.object(dl_mod, 'AUDIT_DIR', tmp_path):
            dl_mod.create_pdf_report(data)
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_pdf_with_empty_step_details(self, dl_mod, tmp_path):
        """PDF renders when no steps have been recorded."""
        data = {
            "manifest": {"runs": {}, "steps": {}},
            "graph": {},
            "step_io": {},
            "chain_result": {
                "is_consistent": False,
                "stale_steps": [],
                "missing_steps": [],
                "details": {},
            },
            "lineage_results": {},
            "step_details": [],
            "num_runs": 0,
            "num_steps": 0,
            "num_recorded": 0,
        }
        out = tmp_path / 'data_lineage_report.pdf'
        with patch.object(dl_mod, 'OUTPUT_PDF', out), \
             patch.object(dl_mod, 'AUDIT_DIR', tmp_path):
            dl_mod.create_pdf_report(data)
        assert out.exists()
        assert out.read_bytes()[:4] == b'%PDF'
