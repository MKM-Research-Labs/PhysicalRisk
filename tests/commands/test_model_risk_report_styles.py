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

"""Tests for model_risk styles and data loaders."""

import json
from unittest.mock import patch

import pytest


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
