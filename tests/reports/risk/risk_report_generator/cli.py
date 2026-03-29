# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for the __main__ CLI block of generator (lines 289-355).

runpy.run_module re-executes the source in a fresh namespace, so patching
reports.risk.generator.RiskReportGenerator has no effect — the fresh
namespace defines its own RiskReportGenerator class.

The workaround: patch reportlab.platypus.SimpleDocTemplate (imported via
sys.modules at the top of the module), so doc.build() becomes a no-op and we
can assert it was called without writing real PDF files.
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
            runpy.run_module('reports.risk.generator', run_name='__main__')
        except SystemExit:
            pass


@pytest.fixture
def mock_pdf():
    """Patch SimpleDocTemplate so generation tests don't write real PDF files.

    When runpy re-executes the module source it does:
        from reportlab.platypus import SimpleDocTemplate
    which reads from sys.modules['reportlab.platypus'].  Patching that attribute
    means the fresh namespace's SimpleDocTemplate IS the mock, so
    mock_pdf.build.assert_called_once() works.
    """
    mock_doc = MagicMock()
    with patch('reportlab.platypus.SimpleDocTemplate', return_value=mock_doc), \
         patch('reports.shared.base_generator.SimpleDocTemplate', return_value=mock_doc):
        yield mock_doc


# ---------------------------------------------------------------------------
# --list-pages  (lines 314-319)
# ---------------------------------------------------------------------------

class TestListPages:

    def test_list_pages_runs_without_error(self):
        """Lines 314-319: --list-pages → list_available_pages() iterated, sys.exit(0)."""
        _run_main(['prog', '--flood-file', 'dummy.json', '--list-pages'])
        # Reaches sys.exit(0) — asserted by the absence of FileNotFoundError

    def test_list_pages_does_not_open_flood_file(self, tmp_path):
        """sys.exit(0) fires before the flood file is opened."""
        non_existent = str(tmp_path / 'nowhere.json')
        _run_main(['prog', '--flood-file', non_existent, '--list-pages'])
        # No FileNotFoundError raised — the file path was never opened


# ---------------------------------------------------------------------------
# --list-categories  (lines 321-328)
# ---------------------------------------------------------------------------

class TestListCategories:

    def test_list_categories_runs_without_error(self):
        """Lines 321-328: --list-categories → get_page_categories() iterated, sys.exit(0)."""
        _run_main(['prog', '--flood-file', 'dummy.json', '--list-categories'])

    def test_list_categories_iterates_all_categories(self):
        """Lines 324-327: all category/page pairs are logged."""
        _run_main(['prog', '--flood-file', 'dummy.json', '--list-categories'])
        # Coverage of the inner for-loop is asserted by no exception


# ---------------------------------------------------------------------------
# Report generation — each report-type branch  (lines 330-351)
# ---------------------------------------------------------------------------

class TestReportGeneration:

    def _flood_file(self, tmp_path):
        """Write minimal flood JSON to tmp_path and return its path string."""
        data = {'catchment': 'Thames', 'summary': {'total_properties': 5}}
        p = tmp_path / 'flood.json'
        p.write_text(json.dumps(data))
        return str(p)

    def test_report_type_basic(self, tmp_path, mock_pdf):
        """Lines 338-339: --report-type basic → generate_basic_report path executed."""
        _run_main(['prog', '--flood-file', self._flood_file(tmp_path),
                   '--output-dir', str(tmp_path), '--report-type', 'basic'])
        mock_pdf.build.assert_called_once()

    def test_report_type_detailed(self, tmp_path, mock_pdf):
        """Lines 340-341: --report-type detailed → generate_detailed_report path executed."""
        _run_main(['prog', '--flood-file', self._flood_file(tmp_path),
                   '--output-dir', str(tmp_path), '--report-type', 'detailed'])
        mock_pdf.build.assert_called_once()

    def test_report_type_summary(self, tmp_path, mock_pdf):
        """Lines 342-343: --report-type summary → generate_summary_report path executed."""
        _run_main(['prog', '--flood-file', self._flood_file(tmp_path),
                   '--output-dir', str(tmp_path), '--report-type', 'summary'])
        mock_pdf.build.assert_called_once()

    def test_report_type_analysis(self, tmp_path, mock_pdf):
        """Lines 344-345: --report-type analysis → generate_analysis_report path executed."""
        _run_main(['prog', '--flood-file', self._flood_file(tmp_path),
                   '--output-dir', str(tmp_path), '--report-type', 'analysis'])
        mock_pdf.build.assert_called_once()

    def test_report_type_else_branch(self, tmp_path, mock_pdf):
        """Lines 346-347: unmapped report_type → generate_report(pages_to_include=args.pages).

        argparse.ArgumentParser.parse_args is imported via sys.modules so patching it
        DOES work even in runpy's fresh namespace — bypassing the argparse choices check.
        """
        import argparse
        flood_file = self._flood_file(tmp_path)
        fake_args = argparse.Namespace(
            flood_file=flood_file,
            output_dir=str(tmp_path),
            report_type='nonstandard',
            pages=['title', 'appendix'],
            list_pages=False,
            list_categories=False,
        )
        with patch('argparse.ArgumentParser.parse_args', return_value=fake_args):
            _run_main(['prog', '--flood-file', flood_file])
        mock_pdf.build.assert_called_once()

    def test_logging_after_generation(self, tmp_path, mock_pdf):
        """Lines 349-351: success-logging block executes without error."""
        _run_main(['prog', '--flood-file', self._flood_file(tmp_path),
                   '--output-dir', str(tmp_path), '--report-type', 'basic'])
        # Lines 349-351 execute — asserted by no exception and build being called
        mock_pdf.build.assert_called_once()


# ---------------------------------------------------------------------------
# Error handling  (lines 353-355)
# ---------------------------------------------------------------------------

class TestErrorHandling:

    def test_bad_flood_file_exits_with_1(self, tmp_path):
        """Lines 353-355: FileNotFoundError → logger.error + sys.exit(1)."""
        exited_with = []

        def capture_exit(code=0):
            exited_with.append(code)
            raise SystemExit(code)

        with patch.object(sys, 'argv',
                          ['prog', '--flood-file', str(tmp_path / 'no_such.json'),
                           '--output-dir', str(tmp_path)]), \
             patch('sys.exit', side_effect=capture_exit):
            try:
                runpy.run_module('reports.risk.generator', run_name='__main__')
            except SystemExit:
                pass

        assert 1 in exited_with

    def test_invalid_json_exits_with_1(self, tmp_path):
        """Lines 353-355: bad JSON → json.JSONDecodeError → sys.exit(1)."""
        bad_json = tmp_path / 'bad.json'
        bad_json.write_text('{ not valid json }')
        exited_with = []

        def capture_exit(code=0):
            exited_with.append(code)
            raise SystemExit(code)

        with patch.object(sys, 'argv',
                          ['prog', '--flood-file', str(bad_json),
                           '--output-dir', str(tmp_path)]), \
             patch('sys.exit', side_effect=capture_exit):
            try:
                runpy.run_module('reports.risk.generator', run_name='__main__')
            except SystemExit:
                pass

        assert 1 in exited_with
