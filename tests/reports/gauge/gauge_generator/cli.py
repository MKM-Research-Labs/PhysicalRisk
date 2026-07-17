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

"""Tests for the __main__ CLI block of gauge_generator (lines 379-453).

runpy.run_module re-executes the source in a fresh namespace, so patching
reports.gauge.gauge_generator.GaugeReportGenerator has no effect.
Fix: patch reportlab.platypus.SimpleDocTemplate (read via sys.modules during
the fresh module execution), so doc.build() is a no-op and we can assert it
was called without writing real PDF files.

Unlike property_generator, gauge_generator's else branch (line 445) uses
args.pages (the correct argparse attribute), so the 'full' report type
succeeds without raising.
"""

import json
import runpy
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_main(argv):
    """Run the __main__ block with mocked sys.argv, swallowing SystemExit."""
    with patch.object(sys, 'argv', argv):
        try:
            runpy.run_module('reports.gauge.gauge_generator', run_name='__main__')
        except SystemExit:
            pass


@pytest.fixture
def mock_pdf():
    """Patch SimpleDocTemplate so generation tests don't write real PDF files.

    runpy re-executes gauge_generator in a fresh namespace, but base_generator
    is already cached in sys.modules with the real SimpleDocTemplate bound.
    We must patch the name on the module object that _build_report reads at
    call time — ``reports.shared.base_generator.SimpleDocTemplate``.
    """
    mock_doc = MagicMock()
    with patch('reportlab.platypus.SimpleDocTemplate', return_value=mock_doc), \
         patch('reports.shared.base_generator.SimpleDocTemplate', return_value=mock_doc):
        yield mock_doc


def _write_gauge_json(tmp_path, gauge_id='GAUGE-001'):
    data = {
        'flood_gauges': [{
            'FloodGauge': {
                'Header': {'GaugeID': gauge_id, 'GaugeName': 'Test'},
                'SensorDetails': {'GaugeInformation': {'GaugeType': 'Pressure'}},
                'FloodStage': {'UK': {'FloodAlert': 4.5}},
            }
        }]
    }
    p = tmp_path / 'gauge.json'
    p.write_text(json.dumps(data))
    return str(p)


def _write_timeseries_json(tmp_path):
    data = {
        'gauge_id': 'GAUGE-001',
        'readings': [{'timestamp': '2024-01-15T00:00:00', 'level': 4.2}],
    }
    p = tmp_path / 'timeseries.json'
    p.write_text(json.dumps(data))
    return str(p)


# ---------------------------------------------------------------------------
# --list-pages  (lines 405-410)
# ---------------------------------------------------------------------------

class TestListPages:

    def test_list_pages_runs_without_error(self):
        """Lines 405-410: --list-pages iterates available pages, sys.exit(0)."""
        _run_main(['prog', '--gauge-file', 'dummy.json', '--list-pages'])

    def test_list_pages_does_not_open_gauge_file(self, tmp_path):
        """sys.exit(0) fires before the gauge file is opened."""
        _run_main(['prog', '--gauge-file', str(tmp_path / 'nowhere.json'), '--list-pages'])
        # No FileNotFoundError — file was never opened


# ---------------------------------------------------------------------------
# --list-categories  (lines 412-419)
# ---------------------------------------------------------------------------

class TestListCategories:

    def test_list_categories_runs_without_error(self):
        """Lines 412-419: --list-categories iterates category dict, sys.exit(0)."""
        _run_main(['prog', '--gauge-file', 'dummy.json', '--list-categories'])

    def test_list_categories_does_not_open_gauge_file(self, tmp_path):
        """sys.exit(0) fires before the gauge file is opened."""
        _run_main(['prog', '--gauge-file', str(tmp_path / 'nowhere.json'), '--list-categories'])


# ---------------------------------------------------------------------------
# Optional loading  (lines 427-433)
# ---------------------------------------------------------------------------

class TestOptionalLoading:

    def test_timeseries_file_is_loaded(self, tmp_path, mock_pdf):
        """Lines 427-429: --timeseries-file → timeseries JSON opened and parsed."""
        _run_main([
            'prog',
            '--gauge-file', _write_gauge_json(tmp_path),
            '--timeseries-file', _write_timeseries_json(tmp_path),
            '--output-dir', str(tmp_path),
            '--report-type', 'basic',
        ])
        mock_pdf.build.assert_called_once()

    def test_gauge_id_filters_data(self, tmp_path, mock_pdf):
        """Lines 432-433: --gauge-id → _find_gauge_by_id called."""
        _run_main([
            'prog',
            '--gauge-file', _write_gauge_json(tmp_path),
            '--gauge-id', 'GAUGE-001',
            '--output-dir', str(tmp_path),
            '--report-type', 'basic',
        ])
        mock_pdf.build.assert_called_once()


# ---------------------------------------------------------------------------
# Report generation branches  (lines 438-449)
# ---------------------------------------------------------------------------

class TestReportGeneration:

    def test_report_type_basic(self, tmp_path, mock_pdf):
        """Lines 438-439: --report-type basic → generate_basic_report path."""
        _run_main([
            'prog',
            '--gauge-file', _write_gauge_json(tmp_path),
            '--output-dir', str(tmp_path),
            '--report-type', 'basic',
        ])
        mock_pdf.build.assert_called_once()

    def test_report_type_monitoring_with_timeseries(self, tmp_path, mock_pdf):
        """Lines 440-441: --report-type monitoring + timeseries → monitoring path."""
        _run_main([
            'prog',
            '--gauge-file', _write_gauge_json(tmp_path),
            '--timeseries-file', _write_timeseries_json(tmp_path),
            '--output-dir', str(tmp_path),
            '--report-type', 'monitoring',
        ])
        mock_pdf.build.assert_called_once()

    def test_report_type_analysis(self, tmp_path, mock_pdf):
        """Lines 442-443: --report-type analysis → generate_analysis_report path."""
        _run_main([
            'prog',
            '--gauge-file', _write_gauge_json(tmp_path),
            '--output-dir', str(tmp_path),
            '--report-type', 'analysis',
        ])
        mock_pdf.build.assert_called_once()

    def test_report_type_full_hits_else_branch(self, tmp_path, mock_pdf):
        """Lines 444-445: --report-type full (not basic/monitoring/analysis) → else branch.
        args.pages is the correct attribute name here, so the else branch succeeds."""
        _run_main([
            'prog',
            '--gauge-file', _write_gauge_json(tmp_path),
            '--output-dir', str(tmp_path),
            '--report-type', 'full',
        ])
        mock_pdf.build.assert_called_once()

    def test_monitoring_without_timeseries_hits_else(self, tmp_path, mock_pdf):
        """Lines 444-445: monitoring without timeseries_data → condition False → else."""
        _run_main([
            'prog',
            '--gauge-file', _write_gauge_json(tmp_path),
            '--output-dir', str(tmp_path),
            '--report-type', 'monitoring',
        ])
        mock_pdf.build.assert_called_once()

    def test_success_logging_executes(self, tmp_path, mock_pdf):
        """Lines 447-449: success-logging block runs after generation."""
        _run_main([
            'prog',
            '--gauge-file', _write_gauge_json(tmp_path),
            '--output-dir', str(tmp_path),
            '--report-type', 'basic',
        ])
        mock_pdf.build.assert_called_once()


# ---------------------------------------------------------------------------
# Error handling  (lines 451-453)
# ---------------------------------------------------------------------------

class TestErrorHandling:

    def test_bad_gauge_file_exits_with_1(self, tmp_path):
        """Lines 451-453: FileNotFoundError → logger.error + sys.exit(1)."""
        exited = []

        def cap(code=0):
            exited.append(code)
            raise SystemExit(code)

        with patch.object(sys, 'argv',
                          ['prog', '--gauge-file', str(tmp_path / 'no_such.json'),
                           '--output-dir', str(tmp_path)]), \
             patch('sys.exit', side_effect=cap):
            try:
                runpy.run_module('reports.gauge.gauge_generator', run_name='__main__')
            except SystemExit:
                pass
        assert 1 in exited

    def test_invalid_json_exits_with_1(self, tmp_path):
        """Lines 451-453: bad JSON → json.JSONDecodeError → sys.exit(1)."""
        bad = tmp_path / 'bad.json'
        bad.write_text('{ not valid json }')
        exited = []

        def cap(code=0):
            exited.append(code)
            raise SystemExit(code)

        with patch.object(sys, 'argv',
                          ['prog', '--gauge-file', str(bad),
                           '--output-dir', str(tmp_path)]), \
             patch('sys.exit', side_effect=cap):
            try:
                runpy.run_module('reports.gauge.gauge_generator', run_name='__main__')
            except SystemExit:
                pass
        assert 1 in exited
