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

"""Tests for docs.models.duplication — code duplication PDF generator."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Minimal jscpd report fixture
# ---------------------------------------------------------------------------

SAMPLE_REPORT = {
    'statistics': {
        'total': {
            'lines': 10000,
            'tokens': 50000,
            'sources': 50,
            'clones': 5,
            'duplicatedLines': 200,
            'duplicatedTokens': 1000,
            'percentage': 2.0,
            'percentageTokens': 2.0,
        },
        'formats': {
            'python': {
                'sources': {
                    'src/foo.py': {
                        'lines': 100, 'tokens': 500,
                        'clones': 2, 'duplicatedLines': 40,
                        'percentage': 40.0, 'percentageTokens': 8.0,
                        'sources': 1, 'duplicatedTokens': 40,
                        'newDuplicatedLines': 0, 'newClones': 0,
                    },
                }
            },
        },
    },
    'duplicates': [
        {
            'firstFile':  {'name': 'src/reports/gauge/gauge_page_00_base.py', 'start': 20},
            'secondFile': {'name': 'src/reports/risk/risk_page_00_base.py',   'start': 20},
            'lines': 30,
            'tokens': 300,
        },
        {
            'firstFile':  {'name': 'src/routes/governance/audit.py', 'start': 10},
            'secondFile': {'name': 'src/routes/governance/models.py', 'start': 10},
            'lines': 12,
            'tokens': 120,
        },
    ],
}


@pytest.fixture
def dup_mod():
    """Import the duplication module."""
    from docs.models.duplication import _analyse, _make_pdf, _run_jscpd
    return _analyse, _make_pdf, _run_jscpd


# ---------------------------------------------------------------------------
# _analyse
# ---------------------------------------------------------------------------

class TestAnalyse:

    def test_returns_dict(self, dup_mod):
        _analyse, _, _ = dup_mod
        result = _analyse(SAMPLE_REPORT)
        assert isinstance(result, dict)

    def test_total_present(self, dup_mod):
        _analyse, _, _ = dup_mod
        result = _analyse(SAMPLE_REPORT)
        assert 'total' in result
        assert result['total']['lines'] == 10000

    def test_num_clones_correct(self, dup_mod):
        _analyse, _, _ = dup_mod
        result = _analyse(SAMPLE_REPORT)
        assert result['num_clones'] == 2

    def test_worst_populated(self, dup_mod):
        _analyse, _, _ = dup_mod
        result = _analyse(SAMPLE_REPORT)
        assert len(result['worst']) > 0
        fname, count, dup_l = result['worst'][0]
        assert isinstance(fname, str)
        assert isinstance(count, int)
        assert count > 0

    def test_largest_sorted_descending(self, dup_mod):
        _analyse, _, _ = dup_mod
        result = _analyse(SAMPLE_REPORT)
        lines = [entry[4] for entry in result['largest']]
        assert lines == sorted(lines, reverse=True)

    def test_fmt_stats_has_python(self, dup_mod):
        _analyse, _, _ = dup_mod
        result = _analyse(SAMPLE_REPORT)
        assert 'python' in result['fmt_stats']

    def test_largest_line_numbers_not_question_mark(self, dup_mod):
        """Regression: jscpd uses 'start' not 'startLine' — must not produce '?' in output."""
        _analyse, _, _ = dup_mod
        result = _analyse(SAMPLE_REPORT)
        for entry in result['largest']:
            l1, l2 = entry[1], entry[3]
            assert l1 != '?', f"Line number for firstFile is '?' — check field name in _analyse()"
            assert l2 != '?', f"Line number for secondFile is '?' — check field name in _analyse()"

    def test_largest_line_numbers_are_integers(self, dup_mod):
        """Line numbers extracted from 'start' field must be integers."""
        _analyse, _, _ = dup_mod
        result = _analyse(SAMPLE_REPORT)
        for entry in result['largest']:
            assert isinstance(entry[1], int), f"firstFile line number should be int, got {type(entry[1])}"
            assert isinstance(entry[3], int), f"secondFile line number should be int, got {type(entry[3])}"

    def test_empty_report(self, dup_mod):
        _analyse, _, _ = dup_mod
        result = _analyse({'statistics': {}, 'duplicates': []})
        assert result['num_clones'] == 0
        assert result['worst'] == []
        assert result['largest'] == []


# ---------------------------------------------------------------------------
# _make_pdf
# ---------------------------------------------------------------------------

class TestMakePdf:

    def test_returns_bytes(self, dup_mod):
        from datetime import datetime
        _analyse, _make_pdf, _ = dup_mod
        analysis = _analyse(SAMPLE_REPORT)
        result = _make_pdf(analysis, datetime.now())
        assert isinstance(result, bytes)

    def test_pdf_header(self, dup_mod):
        from datetime import datetime
        _analyse, _make_pdf, _ = dup_mod
        analysis = _analyse(SAMPLE_REPORT)
        pdf = _make_pdf(analysis, datetime.now())
        assert pdf[:4] == b'%PDF'

    def test_pdf_nonempty(self, dup_mod):
        from datetime import datetime
        _analyse, _make_pdf, _ = dup_mod
        analysis = _analyse(SAMPLE_REPORT)
        pdf = _make_pdf(analysis, datetime.now())
        assert len(pdf) > 2000

    def test_good_rating_for_low_pct(self, dup_mod):
        """Report with 2% duplication should render without error."""
        from datetime import datetime
        _analyse, _make_pdf, _ = dup_mod
        analysis = _analyse(SAMPLE_REPORT)
        assert analysis['total']['percentage'] < 3
        pdf = _make_pdf(analysis, datetime.now())
        assert len(pdf) > 0

    def test_high_rating_report(self, dup_mod):
        """Report with >8% duplication renders correctly."""
        from datetime import datetime
        _analyse, _make_pdf, _ = dup_mod
        high_report = json.loads(json.dumps(SAMPLE_REPORT))
        high_report['statistics']['total']['percentage'] = 12.0
        analysis = _analyse(high_report)
        analysis['total']['percentage'] = 12.0
        pdf = _make_pdf(analysis, datetime.now())
        assert pdf[:4] == b'%PDF'


# ---------------------------------------------------------------------------
# main() integration (mocked jscpd)
# ---------------------------------------------------------------------------

class TestMain:

    def test_main_produces_pdf(self, tmp_path):
        """main() writes code_duplication_report.pdf to audit dir."""
        from docs.models import duplication as dup_mod_full

        with patch.object(dup_mod_full, '_run_jscpd', return_value=SAMPLE_REPORT), \
             patch.object(dup_mod_full, 'AUDIT_DIR', tmp_path), \
             patch.object(dup_mod_full, 'OUTPUT_PDF', tmp_path / 'code_duplication_report.pdf'):
            dup_mod_full.main()

        assert (tmp_path / 'code_duplication_report.pdf').exists()
        assert (tmp_path / 'code_duplication_report.pdf').stat().st_size > 1000

    def test_main_prints_stats(self, tmp_path, capsys):
        """main() prints file/clone/pct stats to stdout."""
        from docs.models import duplication as dup_mod_full

        with patch.object(dup_mod_full, '_run_jscpd', return_value=SAMPLE_REPORT), \
             patch.object(dup_mod_full, 'AUDIT_DIR', tmp_path), \
             patch.object(dup_mod_full, 'OUTPUT_PDF', tmp_path / 'code_duplication_report.pdf'):
            dup_mod_full.main()

        out = capsys.readouterr().out
        assert 'Clones' in out
        assert 'PDF saved' in out

    def test_main_handles_jscpd_error(self, tmp_path, capsys):
        """main() exits cleanly if jscpd fails."""
        from docs.models import duplication as dup_mod_full

        with patch.object(dup_mod_full, '_run_jscpd',
                          side_effect=RuntimeError('jscpd not found')):
            with pytest.raises(SystemExit):
                dup_mod_full.main()
