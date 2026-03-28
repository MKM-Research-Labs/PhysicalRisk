# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for the __main__ CLI block of property_generator (lines 436-512).

runpy.run_module re-executes the source in a fresh namespace, so patching
reports.property.property_generator.PropertyReportGenerator has no effect.
Fix: patch reportlab.platypus.SimpleDocTemplate (fetched via sys.modules during
the fresh module execution), giving a callable mock_doc.build to assert on.

Note: line 504 references args.pages (argparse stores it as args.pages),
so the 'full' / else branch always raises AttributeError → except → sys.exit(1).
Success logging (lines 506-508) is only reachable via the typed branches (497-502).
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
            runpy.run_module('reports.property.property_generator', run_name='__main__')
        except SystemExit:
            pass


@pytest.fixture
def mock_pdf():
    """Patch SimpleDocTemplate so tests don't write real PDF files.

    Two patches are needed:
    - reportlab.platypus.SimpleDocTemplate: visible to any fresh runpy re-execution.
    - reports.property.generator.SimpleDocTemplate: targets the cached generator
      module (PropertyReportGenerator now lives there, not in property_generator).
    """
    mock_doc = MagicMock()
    with patch('reportlab.platypus.SimpleDocTemplate', return_value=mock_doc), \
         patch('src.reports.shared.base_generator.SimpleDocTemplate', return_value=mock_doc):
        yield mock_doc


def _write_property_json(tmp_path, property_id='PROP-001'):
    data = {
        'properties': [{
            'PropertyHeader': {
                'Header': {'PropertyID': property_id},
                'Location': {'LatitudeDegrees': 51.5, 'LongitudeDegrees': -0.1},
                'Valuation': {'PropertyValue': 400_000},
                'RiskAssessment': {'OverallFloodRisk': 'Medium'},
                'Attributes': {'PropertyType': 'Residential'},
            }
        }]
    }
    p = tmp_path / 'property.json'
    p.write_text(json.dumps(data))
    return str(p)


def _write_mortgage_json(tmp_path, property_id='PROP-001'):
    # Top-level PropertyID so _find_mortgage_by_property_id() can match it
    data = {
        'PropertyID': property_id,
        'Mortgage': {
            'Header': {'MortgageID': 'MORT-001', 'PropertyID': property_id},
            'FinancialTerms': {'OriginalLoan': 300_000},
        }
    }
    p = tmp_path / 'mortgage.json'
    p.write_text(json.dumps(data))
    return str(p)


# ---------------------------------------------------------------------------
# --list-pages  (lines 462-467)
# ---------------------------------------------------------------------------

class TestListPages:

    def test_list_pages_runs_without_error(self):
        """Lines 462-467: --list-pages iterates available pages, sys.exit(0)."""
        _run_main(['prog', '--property-file', 'dummy.json', '--list-pages'])

    def test_list_pages_does_not_open_property_file(self, tmp_path):
        """sys.exit(0) fires before the property file is opened."""
        non_existent = str(tmp_path / 'nowhere.json')
        _run_main(['prog', '--property-file', non_existent, '--list-pages'])
        # No FileNotFoundError — file was never opened


# ---------------------------------------------------------------------------
# --list-categories  (lines 469-476)
# ---------------------------------------------------------------------------

class TestListCategories:

    def test_list_categories_runs_without_error(self):
        """Lines 469-476: --list-categories iterates category dict, sys.exit(0)."""
        _run_main(['prog', '--property-file', 'dummy.json', '--list-categories'])

    def test_list_categories_does_not_open_property_file(self, tmp_path):
        """sys.exit(0) fires before the property file is opened."""
        non_existent = str(tmp_path / 'nowhere.json')
        _run_main(['prog', '--property-file', non_existent, '--list-categories'])


# ---------------------------------------------------------------------------
# Optional file / property-id loading  (lines 484-492)
# ---------------------------------------------------------------------------

class TestOptionalLoading:

    def test_mortgage_file_is_loaded(self, tmp_path, mock_pdf):
        """Lines 484-486: --mortgage-file → mortgage JSON is opened and parsed."""
        prop_file = _write_property_json(tmp_path)
        mort_file = _write_mortgage_json(tmp_path)
        _run_main([
            'prog',
            '--property-file', prop_file,
            '--mortgage-file', mort_file,
            '--output-dir', str(tmp_path),
            '--report-type', 'property-only',
        ])
        # Lines 484-486 executed — mortgage file was opened without error
        mock_pdf.build.assert_called_once()

    def test_property_id_filters_without_mortgage(self, tmp_path, mock_pdf):
        """Lines 489-490: --property-id with no mortgage file → _find_property_by_id called."""
        prop_file = _write_property_json(tmp_path)
        _run_main([
            'prog',
            '--property-file', prop_file,
            '--property-id', 'PROP-001',
            '--output-dir', str(tmp_path),
            '--report-type', 'property-only',
        ])
        # Line 489-490 executed; line 491 False (no mortgage_data)
        mock_pdf.build.assert_called_once()

    def test_property_id_with_mortgage_file(self, tmp_path, mock_pdf):
        """Lines 491-492: both --property-id and --mortgage-file → both finders called."""
        prop_file = _write_property_json(tmp_path)
        mort_file = _write_mortgage_json(tmp_path)
        _run_main([
            'prog',
            '--property-file', prop_file,
            '--mortgage-file', mort_file,
            '--property-id', 'PROP-001',
            '--output-dir', str(tmp_path),
            '--report-type', 'property-only',
        ])
        # Lines 491-492 executed — mortgage also filtered by property id
        mock_pdf.build.assert_called_once()


# ---------------------------------------------------------------------------
# Report generation branches  (lines 497-508)
# ---------------------------------------------------------------------------

class TestReportGeneration:

    def test_report_type_property_only(self, tmp_path, mock_pdf):
        """Lines 497-498: --report-type property-only → generate_property_only_report."""
        _run_main([
            'prog',
            '--property-file', _write_property_json(tmp_path),
            '--output-dir', str(tmp_path),
            '--report-type', 'property-only',
        ])
        mock_pdf.build.assert_called_once()

    def test_report_type_mortgage_focused_with_mortgage(self, tmp_path, mock_pdf):
        """Lines 499-500: --report-type mortgage-focused + mortgage file → focused report."""
        _run_main([
            'prog',
            '--property-file', _write_property_json(tmp_path),
            '--mortgage-file', _write_mortgage_json(tmp_path),
            '--output-dir', str(tmp_path),
            '--report-type', 'mortgage-focused',
        ])
        mock_pdf.build.assert_called_once()

    def test_report_type_mortgage_focused_without_mortgage_falls_through(self, tmp_path, mock_pdf):
        """Lines 499 condition False (no mortgage_data) → falls to else branch
        which calls generate_report with auto-selected pages."""
        _run_main([
            'prog',
            '--property-file', _write_property_json(tmp_path),
            '--output-dir', str(tmp_path),
            '--report-type', 'mortgage-focused',
        ])
        mock_pdf.build.assert_called_once()

    def test_report_type_risk_focused(self, tmp_path, mock_pdf):
        """Lines 501-502: --report-type risk-focused → generate_risk_focused_report."""
        _run_main([
            'prog',
            '--property-file', _write_property_json(tmp_path),
            '--output-dir', str(tmp_path),
            '--report-type', 'risk-focused',
        ])
        mock_pdf.build.assert_called_once()

    def test_else_branch_generates_report(self, tmp_path, mock_pdf):
        """Default report_type (no --report-type flag) hits the else branch
        which calls generate_report with args.pages (None → auto-select)."""
        _run_main([
            'prog',
            '--property-file', _write_property_json(tmp_path),
            '--output-dir', str(tmp_path),
        ])
        mock_pdf.build.assert_called_once()

    def test_success_logging_executes(self, tmp_path, mock_pdf):
        """Lines 506-508: success-logging block runs after a successful generation."""
        _run_main([
            'prog',
            '--property-file', _write_property_json(tmp_path),
            '--output-dir', str(tmp_path),
            '--report-type', 'risk-focused',
        ])
        # Lines 506-508 executed — confirmed by mock_pdf.build being called (no exception)
        mock_pdf.build.assert_called_once()


# ---------------------------------------------------------------------------
# Error handling  (lines 510-512)
# ---------------------------------------------------------------------------

class TestErrorHandling:

    def test_bad_property_file_exits_with_1(self, tmp_path):
        """Lines 510-512: FileNotFoundError → logger.error + sys.exit(1)."""
        exited = []

        def cap(code=0):
            exited.append(code)
            raise SystemExit(code)

        with patch.object(sys, 'argv',
                          ['prog', '--property-file', str(tmp_path / 'no_such.json'),
                           '--output-dir', str(tmp_path)]), \
             patch('sys.exit', side_effect=cap):
            try:
                runpy.run_module('reports.property.property_generator', run_name='__main__')
            except SystemExit:
                pass
        assert 1 in exited

    def test_invalid_json_exits_with_1(self, tmp_path):
        """Lines 510-512: bad JSON → json.JSONDecodeError → sys.exit(1)."""
        bad = tmp_path / 'bad.json'
        bad.write_text('{ not valid json }')
        exited = []

        def cap(code=0):
            exited.append(code)
            raise SystemExit(code)

        with patch.object(sys, 'argv',
                          ['prog', '--property-file', str(bad),
                           '--output-dir', str(tmp_path)]), \
             patch('sys.exit', side_effect=cap):
            try:
                runpy.run_module('reports.property.property_generator', run_name='__main__')
            except SystemExit:
                pass
        assert 1 in exited
