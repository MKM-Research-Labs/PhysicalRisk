# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""
Full Audit Report — Integrated Code Quality & Test Evidence Package.

Consolidates all audit data into a single executive-level PDF:
  1. Executive Summary (test stats, coverage, git SHA)
  2. Test Suite Detail (by package)
  3. Code Coverage Analysis (by package, files with gaps)
  4. Code Modularisation (large files over threshold)
  5. Hard-Coding Audit (parameter governance)
  6. Remediation Roadmap

Data sources (all must exist in data/output/audit/):
  - junit.xml        — test counts, pass/fail/skip
  - coverage.xml     — line coverage by package

Also runs fresh live scans via existing audit modules:
  - docs.models.hardcoding  — parameter governance
  - docs.models.project     — file size analysis

Output:  data/output/audit/full_audit_report.pdf

Usage:
    python -m docs.models.full_audit
"""

import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from pathlib import Path

_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_root / 'src'))

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        HRFlowable,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError:
    print("ERROR: reportlab is required.  pip install reportlab")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

AUDIT_DIR = _root / 'data' / 'output' / 'audit'
SRC_DIR = _root / 'src'
OUTPUT_PDF = AUDIT_DIR / 'full_audit_report.pdf'

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------

NAVY = colors.HexColor('#1A237E')
STEEL = colors.HexColor('#37474F')
BLUE = colors.HexColor('#1565C0')
LIGHT_BG = colors.HexColor('#F5F5F5')
HEADER_BG = colors.HexColor('#E8EAF6')
GREEN = colors.HexColor('#2E7D32')
AMBER = colors.HexColor('#E65100')
RED = colors.HexColor('#B71C1C')
GREY = colors.HexColor('#90A4AE')


# ---------------------------------------------------------------------------
# Style setup
# ---------------------------------------------------------------------------

def _styles():
    base = getSampleStyleSheet()
    return {
        'cover_title': ParagraphStyle(
            'FATitle', parent=base['Heading1'],
            fontSize=26, textColor=NAVY, spaceAfter=8,
            alignment=TA_CENTER, fontName='Helvetica-Bold'),
        'cover_sub': ParagraphStyle(
            'FASub', parent=base['Normal'],
            fontSize=13, textColor=STEEL, spaceAfter=4,
            alignment=TA_CENTER),
        'cover_meta': ParagraphStyle(
            'FAMeta', parent=base['Normal'],
            fontSize=9, textColor=colors.HexColor('#546E7A'),
            alignment=TA_CENTER, spaceAfter=2),
        'h2': ParagraphStyle(
            'FAH2', parent=base['Heading2'],
            fontSize=13, textColor=NAVY,
            spaceBefore=14, spaceAfter=6, fontName='Helvetica-Bold'),
        'h3': ParagraphStyle(
            'FAH3', parent=base['Heading3'],
            fontSize=10, textColor=STEEL,
            spaceBefore=8, spaceAfter=4, fontName='Helvetica-Bold'),
        'body': ParagraphStyle(
            'FABody', parent=base['BodyText'],
            fontSize=9, leading=13),
        'small': ParagraphStyle(
            'FASmall', parent=base['Normal'],
            fontSize=7.5, textColor=colors.HexColor('#78909C'), leading=11),
        'tbl_hdr': ParagraphStyle(
            'FATHdr', parent=base['Normal'],
            fontSize=8.5, textColor=colors.white, fontName='Helvetica-Bold'),
        'tbl_cell': ParagraphStyle(
            'FATCell', parent=base['Normal'],
            fontSize=8, leading=11),
        'tbl_cell_r': ParagraphStyle(
            'FATCellR', parent=base['Normal'],
            fontSize=8, leading=11, alignment=TA_RIGHT),
        'metric_val': ParagraphStyle(
            'FAMetricV', parent=base['Normal'],
            fontSize=20, textColor=NAVY, fontName='Helvetica-Bold',
            alignment=TA_CENTER),
        'metric_lbl': ParagraphStyle(
            'FAMetricL', parent=base['Normal'],
            fontSize=8, textColor=STEEL, alignment=TA_CENTER),
    }


# ---------------------------------------------------------------------------
# Data parsers
# ---------------------------------------------------------------------------

def _parse_junit(junit_path: Path) -> dict:
    """Parse JUnit XML into summary dict."""
    result = {
        'total': 0, 'passed': 0, 'failed': 0,
        'errors': 0, 'skipped': 0, 'time_s': 0.0,
        'by_package': {},
    }
    if not junit_path.exists():
        return result

    tree = ET.parse(str(junit_path))
    root = tree.getroot()

    # Handle both <testsuites> wrapper and bare <testsuite>
    suites = root.findall('.//testsuite')
    if not suites and root.tag == 'testsuite':
        suites = [root]

    pkg_counts: dict = defaultdict(lambda: {'total': 0, 'fail': 0, 'skip': 0})

    for suite in suites:
        total = int(suite.get('tests', 0))
        fail = int(suite.get('failures', 0))
        err = int(suite.get('errors', 0))
        skip = int(suite.get('skipped', 0))
        t = float(suite.get('time', 0))

        result['total'] += total
        result['failed'] += fail + err
        result['skipped'] += skip
        result['time_s'] += t

        # Package from test classnames
        for tc in suite.findall('testcase'):
            classname = tc.get('classname', '')
            # e.g. "tests.models.hazard.TestGEV" → "models.hazard"
            parts = classname.split('.')
            if len(parts) >= 3 and parts[0] == 'tests':
                pkg = parts[1]
            elif len(parts) >= 2:
                pkg = parts[0]
            else:
                pkg = 'other'

            is_skip = tc.find('skipped') is not None
            is_fail = (tc.find('failure') is not None or
                       tc.find('error') is not None)

            pkg_counts[pkg]['total'] += 1
            if is_fail:
                pkg_counts[pkg]['fail'] += 1
            if is_skip:
                pkg_counts[pkg]['skip'] += 1

    result['passed'] = result['total'] - result['failed'] - result['skipped']
    result['by_package'] = dict(pkg_counts)
    return result


def _parse_coverage(cov_path: Path) -> dict:
    """Parse coverage.xml into summary + per-package breakdown."""
    result = {
        'line_rate': 0.0,
        'lines_valid': 0,
        'lines_covered': 0,
        'by_package': [],   # list of (pkg_name, rate, valid, covered)
    }
    if not cov_path.exists():
        return result

    tree = ET.parse(str(cov_path))
    root = tree.getroot()

    result['line_rate'] = float(root.get('line-rate', 0))
    result['lines_valid'] = int(root.get('lines-valid', 0))
    result['lines_covered'] = int(root.get('lines-covered', 0))

    pkg_rows = []
    for pkg in root.findall('.//package'):
        name = pkg.get('name', '').lstrip('.')
        if not name:
            continue
        rate = float(pkg.get('line-rate', 0))
        valid = sum(int(c.get('lines-valid', 0))
                    for c in pkg.findall('classes/class'))
        covered = sum(int(c.get('lines-covered', 0))
                      for c in pkg.findall('classes/class'))
        if valid == 0:
            # Fall back: count lines from class elements
            valid = sum(len(c.findall('.//line')) for c in pkg.findall('classes/class'))
            covered = sum(
                sum(1 for ln in c.findall('.//line') if ln.get('hits', '0') != '0')
                for c in pkg.findall('classes/class')
            )
        if valid > 0:
            pkg_rows.append((name, rate * 100, valid, covered))

    pkg_rows.sort(key=lambda x: x[1])   # ascending by coverage rate
    result['by_package'] = pkg_rows
    return result


def _git_sha() -> str:
    import subprocess
    try:
        r = subprocess.run(['git', 'rev-parse', 'HEAD'],
                           capture_output=True, text=True,
                           cwd=str(_root), timeout=5)
        if r.returncode == 0:
            return r.stdout.strip()[:12]
    except Exception:
        pass
    return 'unknown'


# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------

_TBL_STYLE_BASE = [
    ('FONTSIZE',       (0, 0), (-1, 0),  8.5),
    ('FONTNAME',       (0, 0), (-1, 0),  'Helvetica-Bold'),
    ('BACKGROUND',     (0, 0), (-1, 0),  NAVY),
    ('TEXTCOLOR',      (0, 0), (-1, 0),  colors.white),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
    ('GRID',           (0, 0), (-1, -1), 0.4, colors.HexColor('#CFD8DC')),
    ('BOX',            (0, 0), (-1, -1), 1.0, STEEL),
    ('FONTSIZE',       (0, 1), (-1, -1), 8),
    ('TOPPADDING',     (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING',  (0, 0), (-1, -1), 4),
    ('LEFTPADDING',    (0, 0), (-1, -1), 6),
    ('RIGHTPADDING',   (0, 0), (-1, -1), 6),
    ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
]


def _metric_box(value: str, label: str, col: colors.Color, styles) -> Table:
    data = [
        [Paragraph(value, styles['metric_val'])],
        [Paragraph(label, styles['metric_lbl'])],
    ]
    tbl = Table(data, colWidths=[36 * mm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HEADER_BG),
        ('BOX',        (0, 0), (-1, -1), 1.5, col),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return tbl


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _build_cover(junit: dict, cov: dict, git_sha: str,
                 report_date: datetime, styles) -> list:
    elems = []

    elems.append(Spacer(1, 18 * mm))
    elems.append(Paragraph('MKM Physical Risk Platform', styles['cover_sub']))
    elems.append(Paragraph('Full Audit Report', styles['cover_title']))
    elems.append(Spacer(1, 4 * mm))
    elems.append(HRFlowable(width='100%', thickness=2, color=NAVY))
    elems.append(Spacer(1, 6 * mm))

    elems.append(Paragraph(
        f'Report Date: {report_date.strftime("%d %B %Y")}',
        styles['cover_meta']))
    elems.append(Paragraph(
        f'Git SHA: {git_sha}',
        styles['cover_meta']))
    elems.append(Paragraph(
        'Governance Framework: SR 11-7 / SS1/23 Model Risk Management',
        styles['cover_meta']))

    elems.append(Spacer(1, 10 * mm))

    # Summary metrics row
    cov_pct = cov['line_rate'] * 100
    total_tests = junit['total']
    pass_rate = (junit['passed'] / total_tests * 100) if total_tests else 0

    cov_col = GREEN if cov_pct >= 90 else (AMBER if cov_pct >= 70 else RED)
    pass_col = GREEN if pass_rate >= 99 else (AMBER if pass_rate >= 95 else RED)

    # Load supplementary results for cover metrics
    dl_cov = _load_json_report('data_lineage_results.json')
    e2e_cov = _load_json_report('e2e_results.json')
    dl_ok = dl_cov.get('failed', 0) == 0 if dl_cov else True
    dl_label = 'PASS' if dl_ok else 'FAIL'
    dl_col = GREEN if dl_ok else RED

    e2e_total = e2e_cov.get('total', 0) if e2e_cov else 0
    e2e_failed = e2e_cov.get('failed', 0) if e2e_cov else 0
    e2e_status = e2e_cov.get('status', '') if e2e_cov else ''
    if e2e_status == 'SKIPPED':
        e2e_label = 'SKIP'
        e2e_col = GREY
    elif e2e_total > 0:
        e2e_label = f'{e2e_total - e2e_failed}/{e2e_total}'
        e2e_col = GREEN if e2e_failed == 0 else RED
    else:
        e2e_label = 'N/A'
        e2e_col = GREY

    metrics = Table([
        [
            _metric_box(f'{total_tests:,}',  'Total Tests',     BLUE,     styles),
            _metric_box(f'{pass_rate:.1f}%', 'Pass Rate',       pass_col, styles),
            _metric_box(f'{cov_pct:.1f}%',   'Line Coverage',   cov_col,  styles),
            _metric_box(dl_label,             'Data Lineage',    dl_col,   styles),
            _metric_box(e2e_label,            'E2E Tests',       e2e_col,  styles),
        ],
    ], colWidths=[34 * mm] * 5)
    metrics.setStyle(TableStyle([
        ('ALIGN',   (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',  (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    elems.append(metrics)

    elems.append(Spacer(1, 10 * mm))

    elems.append(Paragraph('Report Contents', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=0.5, color=GREY))
    elems.append(Spacer(1, 3 * mm))

    toc = [
        ('1', 'Executive Summary',
         'Key metrics, pass/fail totals, coverage headline, and test run metadata.'),
        ('2', 'Test Suite Detail',
         'Test counts by package with pass, fail, and skip breakdown.'),
        ('3', 'Code Coverage Analysis',
         'Line coverage by package, files with coverage gaps.'),
        ('4', 'Code Modularisation',
         'Files exceeding 300 lines — candidates for refactoring.'),
        ('5', 'Hard-Coding Audit',
         'Parameter governance scan — constants outside config.py.'),
        ('6', 'Data Lineage Consistency',
         'BCBS 239 Principle 3 pre-flight checks — ID consistency across pipeline data.'),
        ('7', 'E2E Browser Tests',
         'Playwright end-to-end tests — full-stack UI verification.'),
        ('8', 'Remediation Roadmap',
         'Prioritised action list for identified quality issues.'),
    ]
    toc_data = [['§', 'Section', 'Description']]
    for num, title, desc in toc:
        toc_data.append([
            Paragraph(f'<b>{num}</b>', styles['tbl_cell']),
            Paragraph(f'<b>{title}</b>', styles['tbl_cell']),
            Paragraph(desc, styles['tbl_cell']),
        ])
    toc_tbl = Table(toc_data, colWidths=[8 * mm, 52 * mm, 108 * mm])
    toc_tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
    elems.append(toc_tbl)

    elems.append(Spacer(1, 6 * mm))
    elems.append(HRFlowable(width='100%', thickness=0.5, color=GREY))
    elems.append(Spacer(1, 3 * mm))
    elems.append(Paragraph(
        'This report is generated automatically as part of the MKM Research Labs '
        'model governance pipeline (app.py test --audit). It covers the Python '
        'source codebase under src/ and the tests/ directory. All figures reflect '
        'the state of the repository at the git SHA shown above.',
        styles['small']))

    return elems


def _build_exec_summary(junit: dict, cov: dict, report_date: datetime,
                        styles) -> list:
    elems = []
    elems.append(Paragraph('1. Executive Summary', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 3 * mm))

    total = junit['total']
    passed = junit['passed']
    failed = junit['failed']
    skipped = junit['skipped']
    t_secs = junit['time_s']
    cov_pct = cov['line_rate'] * 100
    lines_valid = cov['lines_valid']
    lines_cov = cov['lines_covered']

    # Load supplementary results for exec summary
    dl_data = _load_json_report('data_lineage_results.json')
    e2e_data = _load_json_report('e2e_results.json')

    dl_status_str = 'Not run'
    if dl_data:
        dl_f = dl_data.get('failed', 0)
        dl_t = dl_data.get('total', 0)
        dl_status_str = f'{dl_t} checks, {dl_f} failed'

    e2e_status_str = 'Not run'
    if e2e_data:
        e2e_st = e2e_data.get('status', '')
        if e2e_st == 'SKIPPED':
            e2e_status_str = f'Skipped ({e2e_data.get("reason", "")})'
        elif e2e_st in ('TIMEOUT', 'ERROR'):
            e2e_status_str = e2e_st
        else:
            e2e_t = e2e_data.get('total', 0)
            e2e_f = e2e_data.get('failed', 0)
            e2e_status_str = f'{e2e_t} tests, {e2e_f} failed'

    rows = [
        ['Metric',                     'Value',         'Status'],
        ['Total tests',                f'{total:,}',    _status(total >= 5000, total >= 3000)],
        ['Tests passed',               f'{passed:,}',   _status(failed == 0, failed <= 5)],
        ['Tests failed',               f'{failed:,}',   _status_inv(failed == 0, failed <= 5)],
        ['Tests skipped',              f'{skipped:,}',  'INFO'],
        ['Test suite run time',        f'{t_secs:.1f}s', 'INFO'],
        ['Lines analysed (src/)',       f'{lines_valid:,}', 'INFO'],
        ['Lines covered',              f'{lines_cov:,}', 'INFO'],
        ['Line coverage',              f'{cov_pct:.2f}%',
         _status(cov_pct >= 90, cov_pct >= 75)],
        ['Data lineage consistency',   dl_status_str,
         _status_inv(dl_data.get('failed', 0) == 0, True) if dl_data else 'INFO'],
        ['E2E browser tests',          e2e_status_str,
         _status_inv(e2e_data.get('failed', 0) == 0,
                     e2e_data.get('failed', 0) <= 3) if (
             e2e_data and e2e_data.get('status') not in ('SKIPPED', None)) else 'INFO'],
        ['Report generated',           report_date.strftime('%Y-%m-%d %H:%M:%S'), 'INFO'],
    ]

    tbl_data = []
    row_styles = list(_TBL_STYLE_BASE)
    for i, row in enumerate(rows):
        if i == 0:
            tbl_data.append([Paragraph(f'<b>{c}</b>', styles['tbl_hdr']) for c in row])
        else:
            status_str = row[2]
            status_col = _status_colour(status_str)
            tbl_data.append([
                Paragraph(row[0], styles['tbl_cell']),
                Paragraph(f'<b>{row[1]}</b>', styles['tbl_cell_r']),
                Paragraph(f'<b>{status_str}</b>',
                          ParagraphStyle('S', parent=getSampleStyleSheet()['Normal'],
                                         fontSize=7.5, textColor=status_col,
                                         fontName='Helvetica-Bold')),
            ])

    tbl = Table(tbl_data, colWidths=[90 * mm, 50 * mm, 28 * mm])
    tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
    elems.append(tbl)

    elems.append(Spacer(1, 4 * mm))
    elems.append(Paragraph(
        f'The test suite comprises <b>{total:,} tests</b> across all packages '
        f'with <b>{passed:,} passing</b>, <b>{failed} failing</b>, and '
        f'<b>{skipped} skipped</b>. '
        f'Line coverage stands at <b>{cov_pct:.1f}%</b> across '
        f'{lines_valid:,} analysed source lines.',
        styles['body']))

    return elems


def _build_test_detail(junit: dict, styles) -> list:
    elems = []
    elems.append(Paragraph('2. Test Suite Detail', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph(
        'Tests broken down by top-level package directory. '
        'Package names correspond to subdirectories of tests/.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    by_pkg = junit['by_package']
    rows_sorted = sorted(by_pkg.items(), key=lambda x: -x[1]['total'])

    tbl_data = [[
        Paragraph('<b>Package</b>', styles['tbl_hdr']),
        Paragraph('<b>Total</b>', styles['tbl_hdr']),
        Paragraph('<b>Passed</b>', styles['tbl_hdr']),
        Paragraph('<b>Failed</b>', styles['tbl_hdr']),
        Paragraph('<b>Skipped</b>', styles['tbl_hdr']),
        Paragraph('<b>Pass%</b>', styles['tbl_hdr']),
    ]]
    row_extras = []
    for pkg, counts in rows_sorted:
        t = counts['total']
        f = counts['fail']
        s = counts['skip']
        p = t - f - s
        pct = p / t * 100 if t else 0
        pct_col = GREEN if pct >= 99 else (AMBER if pct >= 95 else RED)

        tbl_data.append([
            Paragraph(pkg, styles['tbl_cell']),
            Paragraph(str(t), styles['tbl_cell_r']),
            Paragraph(str(p), styles['tbl_cell_r']),
            Paragraph(str(f) if f else '—',
                      ParagraphStyle('Fail', parent=getSampleStyleSheet()['Normal'],
                                     fontSize=8, alignment=TA_RIGHT,
                                     textColor=RED if f else GREY)),
            Paragraph(str(s) if s else '—', styles['tbl_cell_r']),
            Paragraph(f'{pct:.1f}%',
                      ParagraphStyle('Pct', parent=getSampleStyleSheet()['Normal'],
                                     fontSize=8, alignment=TA_RIGHT,
                                     textColor=pct_col, fontName='Helvetica-Bold')),
        ])
        if f > 0:
            idx = len(tbl_data) - 1
            row_extras.append(('BACKGROUND', (0, idx), (-1, idx),
                                colors.HexColor('#FFEBEE')))

    tbl = Table(tbl_data, colWidths=[58 * mm, 18 * mm, 18 * mm, 18 * mm, 18 * mm, 18 * mm])
    style_cmds = list(_TBL_STYLE_BASE) + row_extras
    tbl.setStyle(TableStyle(style_cmds))
    elems.append(tbl)

    return elems


def _build_coverage(cov: dict, styles) -> list:
    elems = []
    elems.append(Paragraph('3. Code Coverage Analysis', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 3 * mm))

    cov_pct = cov['line_rate'] * 100
    elems.append(Paragraph(
        f'Overall line coverage: <b>{cov_pct:.2f}%</b> '
        f'({cov["lines_covered"]:,} of {cov["lines_valid"]:,} lines). '
        'Packages are sorted by coverage rate ascending — lowest coverage first.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    pkg_rows = cov['by_package']
    if not pkg_rows:
        elems.append(Paragraph('No per-package coverage data available.', styles['body']))
        return elems

    tbl_data = [[
        Paragraph('<b>Package</b>', styles['tbl_hdr']),
        Paragraph('<b>Coverage</b>', styles['tbl_hdr']),
        Paragraph('<b>Lines Valid</b>', styles['tbl_hdr']),
        Paragraph('<b>Lines Covered</b>', styles['tbl_hdr']),
        Paragraph('<b>Gap</b>', styles['tbl_hdr']),
    ]]
    row_extras = []
    for name, rate, valid, covered in pkg_rows:
        gap = valid - covered
        rate_col = GREEN if rate >= 90 else (AMBER if rate >= 70 else RED)
        short_name = name if len(name) <= 55 else '…' + name[-52:]
        tbl_data.append([
            Paragraph(short_name, styles['tbl_cell']),
            Paragraph(f'{rate:.1f}%',
                      ParagraphStyle('CovPct', parent=getSampleStyleSheet()['Normal'],
                                     fontSize=8, textColor=rate_col,
                                     fontName='Helvetica-Bold')),
            Paragraph(str(valid), styles['tbl_cell_r']),
            Paragraph(str(covered), styles['tbl_cell_r']),
            Paragraph(str(gap) if gap else '—',
                      ParagraphStyle('Gap', parent=getSampleStyleSheet()['Normal'],
                                     fontSize=8, alignment=TA_RIGHT,
                                     textColor=RED if gap > 50 else STEEL)),
        ])
        if rate < 70:
            idx = len(tbl_data) - 1
            row_extras.append(('BACKGROUND', (0, idx), (-1, idx),
                                colors.HexColor('#FFEBEE')))

    tbl = Table(tbl_data, colWidths=[78 * mm, 22 * mm, 22 * mm, 26 * mm, 20 * mm])
    tbl.setStyle(TableStyle(list(_TBL_STYLE_BASE) + row_extras))
    elems.append(tbl)

    # Summary counts
    below_90 = sum(1 for _, r, v, _ in pkg_rows if r < 90 and v >= 10)
    below_70 = sum(1 for _, r, v, _ in pkg_rows if r < 70 and v >= 10)
    elems.append(Spacer(1, 3 * mm))
    elems.append(Paragraph(
        f'Packages with &lt;90% coverage: <b>{below_90}</b> &nbsp;|&nbsp; '
        f'Packages with &lt;70% coverage: <b>{below_70}</b> '
        f'(excluding trivial packages with &lt;10 lines).',
        styles['body']))

    return elems


def _build_modularisation(styles) -> list:
    elems = []
    elems.append(Paragraph('4. Code Modularisation', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 3 * mm))

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            '_proj_mod',
            str(_root / 'docs' / 'models' / 'project' / '__init__.py'))
        proj = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(proj)
        all_files, large_files = proj.analyze_code_files(_root / 'src')
    except Exception as exc:
        elems.append(Paragraph(
            f'Could not run modularisation scan: {exc}', styles['body']))
        return elems

    total_files = len(all_files)
    total_large = len(large_files)

    elems.append(Paragraph(
        f'Scope: <b>src/</b> &nbsp;|&nbsp; '
        f'Files scanned: <b>{total_files}</b> &nbsp;|&nbsp; '
        f'Files over 300 lines: <b>{total_large}</b>. '
        'Files exceeding 300 non-blank lines are candidates for modularisation.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    if not large_files:
        elems.append(Paragraph(
            'No files exceed the 300-line threshold.', styles['body']))
        return elems

    tbl_data = [[
        Paragraph('<b>File (relative to project root)</b>', styles['tbl_hdr']),
        Paragraph('<b>Ext</b>', styles['tbl_hdr']),
        Paragraph('<b>Lines</b>', styles['tbl_hdr']),
        Paragraph('<b>Priority</b>', styles['tbl_hdr']),
    ]]
    row_extras = []
    for fi in large_files[:40]:
        rel = str(fi.relative_path)
        if len(rel) > 70:
            rel = '…' + rel[-68:]
        lc = fi.line_count
        priority = 'High' if lc > 600 else ('Medium' if lc > 400 else 'Low')
        p_col = RED if lc > 600 else (AMBER if lc > 400 else GREEN)

        tbl_data.append([
            Paragraph(rel, styles['tbl_cell']),
            Paragraph(fi.extension, styles['tbl_cell']),
            Paragraph(str(lc), styles['tbl_cell_r']),
            Paragraph(f'<b>{priority}</b>',
                      ParagraphStyle('Pri', parent=getSampleStyleSheet()['Normal'],
                                     fontSize=8, textColor=p_col,
                                     fontName='Helvetica-Bold')),
        ])
        if lc > 600:
            idx = len(tbl_data) - 1
            row_extras.append(('BACKGROUND', (0, idx), (-1, idx),
                                colors.HexColor('#FFF3E0')))

    tbl = Table(tbl_data, colWidths=[108 * mm, 14 * mm, 18 * mm, 28 * mm])
    tbl.setStyle(TableStyle(list(_TBL_STYLE_BASE) + row_extras))
    elems.append(tbl)

    if total_large > 40:
        elems.append(Spacer(1, 2 * mm))
        elems.append(Paragraph(
            f'Showing top 40 of {total_large} files over threshold.',
            styles['small']))

    return elems


def _build_hardcoding(styles) -> list:
    elems = []
    elems.append(Paragraph('5. Hard-Coding Audit', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph(
        'Policy: every configurable domain parameter must be defined once in '
        'config.py and imported at every use site. '
        'This section reports parameters found as hard-coded literals outside '
        'config.py.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            '_hc_mod',
            str(_root / 'docs' / 'models' / 'hardcoding' / '__init__.py'))
        hc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hc)
        findings = hc.collect_all(SRC_DIR, _root)
    except Exception as exc:
        elems.append(Paragraph(
            f'Could not run hard-coding scan: {exc}', styles['body']))
        return elems

    files_scanned = findings['files_scanned']
    n_dup = len(findings['duplicates'])
    allcaps = findings['allcaps']
    caps_action = [f for f in allcaps if not f.get('precision_ok', False)]
    n_infra = len(findings['infra'])
    n_inline = len(findings['inline'])

    # Summary table
    summary_data = [
        ['Category', 'Findings', 'Status'],
        ['Files scanned', str(files_scanned), 'INFO'],
        ['Duplicate constants (same name, multiple files)',
         str(n_dup), _status_inv(n_dup == 0, n_dup <= 3)],
        ['ALL_CAPS constants outside config.py (action required)',
         str(len(caps_action)), _status_inv(len(caps_action) == 0, len(caps_action) <= 10)],
        ['ALL_CAPS constants (precision/tolerance — acceptable)',
         str(len(allcaps) - len(caps_action)), 'OK'],
        ['Infrastructure literals (IP / port)',
         str(n_infra), _status_inv(n_infra == 0, n_infra <= 2)],
        ['Inline simulation parameters',
         str(n_inline), _status_inv(n_inline == 0, n_inline <= 3)],
    ]
    tbl_data = []
    row_extras = []
    for i, row in enumerate(summary_data):
        if i == 0:
            tbl_data.append([Paragraph(f'<b>{c}</b>', styles['tbl_hdr']) for c in row])
        else:
            status_str = row[2]
            status_col = _status_colour(status_str)
            tbl_data.append([
                Paragraph(row[0], styles['tbl_cell']),
                Paragraph(f'<b>{row[1]}</b>', styles['tbl_cell_r']),
                Paragraph(f'<b>{status_str}</b>',
                          ParagraphStyle('HCS', parent=getSampleStyleSheet()['Normal'],
                                         fontSize=7.5, textColor=status_col,
                                         fontName='Helvetica-Bold')),
            ])
    tbl = Table(tbl_data, colWidths=[118 * mm, 20 * mm, 30 * mm])
    tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
    elems.append(tbl)
    elems.append(Spacer(1, 4 * mm))

    # Duplicate constants detail
    if findings['duplicates']:
        elems.append(Paragraph(
            'Duplicate Constants (defined in multiple files):', styles['h3']))
        dup_data = [['Constant', 'Files']]
        for item in findings['duplicates'][:15]:
            locs = item.get('locations', [])
            files_str = ', '.join(loc[0] for loc in locs[:4])
            if len(locs) > 4:
                files_str += f' (+{len(locs) - 4} more)'
            dup_data.append([
                Paragraph(f'<b>{item["name"]}</b>', styles['tbl_cell']),
                Paragraph(files_str, styles['tbl_cell']),
            ])
        dup_tbl = Table(dup_data, colWidths=[40 * mm, 128 * mm])
        dup_tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
        elems.append(dup_tbl)
        elems.append(Spacer(1, 3 * mm))

    # ALL_CAPS action items
    if caps_action:
        elems.append(Paragraph(
            f'ALL_CAPS Constants Requiring Migration to config.py '
            f'(showing up to 20 of {len(caps_action)}):',
            styles['h3']))
        ac_data = [['File', 'Line', 'Constant', 'Value']]
        for item in caps_action[:20]:
            ac_data.append([
                Paragraph(item['file'][:50], styles['tbl_cell']),
                Paragraph(str(item['line']), styles['tbl_cell_r']),
                Paragraph(f'<b>{item["name"]}</b>', styles['tbl_cell']),
                Paragraph(str(item['value'])[:20], styles['tbl_cell']),
            ])
        ac_tbl = Table(ac_data, colWidths=[75 * mm, 12 * mm, 52 * mm, 29 * mm])
        ac_tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
        elems.append(ac_tbl)

    return elems


def _load_json_report(filename: str) -> dict:
    """Load a JSON report from the audit directory, returning {} on failure."""
    import json
    path = AUDIT_DIR / filename
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def _build_data_lineage(styles) -> list:
    """Section 6: Data Lineage Consistency (BCBS 239 Principle 3)."""
    elems = []
    elems.append(Paragraph('6. Data Lineage Consistency', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph(
        'Pre-flight checks verifying that gauge IDs, property IDs, and trade '
        'references are consistent across all pipeline data files '
        '(BCBS 239 Principle 3 — Accuracy). Failures indicate stale or '
        'out-of-order pipeline data.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    data = _load_json_report('data_lineage_results.json')
    if not data:
        elems.append(Paragraph(
            'Data lineage results not available — tests were not run or '
            'data_lineage_results.json is missing.', styles['body']))
        return elems

    total = data.get('total', 0)
    passed = data.get('passed', 0)
    failed = data.get('failed', 0)
    skipped = data.get('skipped', 0)

    overall = 'OK' if failed == 0 else 'ACTION REQUIRED'
    overall_col = GREEN if failed == 0 else RED

    # Summary table
    tbl_data = [
        [Paragraph('<b>Metric</b>', styles['tbl_hdr']),
         Paragraph('<b>Value</b>', styles['tbl_hdr']),
         Paragraph('<b>Status</b>', styles['tbl_hdr'])],
        [Paragraph('Total checks', styles['tbl_cell']),
         Paragraph(f'<b>{total}</b>', styles['tbl_cell_r']),
         Paragraph('INFO', ParagraphStyle('DLI', parent=getSampleStyleSheet()['Normal'],
                                           fontSize=7.5, textColor=STEEL,
                                           fontName='Helvetica-Bold'))],
        [Paragraph('Passed', styles['tbl_cell']),
         Paragraph(f'<b>{passed}</b>', styles['tbl_cell_r']),
         Paragraph(_status(passed == total, passed > 0),
                   ParagraphStyle('DLP', parent=getSampleStyleSheet()['Normal'],
                                   fontSize=7.5,
                                   textColor=GREEN if passed == total else AMBER,
                                   fontName='Helvetica-Bold'))],
        [Paragraph('Failed', styles['tbl_cell']),
         Paragraph(f'<b>{failed}</b>', styles['tbl_cell_r']),
         Paragraph(_status_inv(failed == 0, failed <= 2),
                   ParagraphStyle('DLF', parent=getSampleStyleSheet()['Normal'],
                                   fontSize=7.5,
                                   textColor=GREEN if failed == 0 else RED,
                                   fontName='Helvetica-Bold'))],
        [Paragraph('Skipped', styles['tbl_cell']),
         Paragraph(f'<b>{skipped}</b>', styles['tbl_cell_r']),
         Paragraph('INFO', ParagraphStyle('DLS', parent=getSampleStyleSheet()['Normal'],
                                           fontSize=7.5, textColor=STEEL,
                                           fontName='Helvetica-Bold'))],
    ]
    tbl = Table(tbl_data, colWidths=[90 * mm, 40 * mm, 38 * mm])
    style_cmds = list(_TBL_STYLE_BASE)
    if failed > 0:
        style_cmds.append(('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#FFEBEE')))
    tbl.setStyle(TableStyle(style_cmds))
    elems.append(tbl)

    # Failure details
    failures = data.get('failures', [])
    if failures:
        elems.append(Spacer(1, 3 * mm))
        elems.append(Paragraph('Failed Consistency Checks:', styles['h3']))
        fail_data = [[
            Paragraph('<b>Test</b>', styles['tbl_hdr']),
            Paragraph('<b>Error</b>', styles['tbl_hdr']),
        ]]
        for f in failures[:10]:
            name = f.get('name', 'unknown')
            msg = f.get('message', '')
            if len(msg) > 200:
                msg = msg[:200] + '...'
            fail_data.append([
                Paragraph(name, styles['tbl_cell']),
                Paragraph(msg, styles['tbl_cell']),
            ])
        fail_tbl = Table(fail_data, colWidths=[60 * mm, 108 * mm])
        fail_tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
        elems.append(fail_tbl)

    if failed > 0:
        elems.append(Spacer(1, 3 * mm))
        elems.append(Paragraph(
            '<b>Remediation:</b> Regenerate data in the correct order: '
            'python app.py port --gauge → port --stressm → port --hazard → port --blotter',
            styles['body']))

    # ------------------------------------------------------------------
    # Generation Manifest (from data/data_lineage.json)
    # ------------------------------------------------------------------
    import json as _json
    _lineage_path = _root / 'data' / 'data_lineage.json'
    _manifest = {}
    if _lineage_path.exists():
        try:
            with open(_lineage_path) as _lf:
                _manifest = _json.load(_lf)
        except Exception:
            _manifest = {}

    if _manifest.get('steps'):
        elems.append(Spacer(1, 5 * mm))
        elems.append(Paragraph('Generation Manifest', styles['h3']))

        manifest_data = [[
            Paragraph('<b>Step</b>', styles['tbl_hdr']),
            Paragraph('<b>Generator</b>', styles['tbl_hdr']),
            Paragraph('<b>Timestamp</b>', styles['tbl_hdr']),
            Paragraph('<b>Status</b>', styles['tbl_hdr']),
            Paragraph('<b>Run ID</b>', styles['tbl_hdr']),
        ]]
        for step_name, step_info in sorted(_manifest['steps'].items()):
            gen = step_info.get('generator', 'unknown')
            ts = step_info.get('timestamp', '')
            if len(ts) > 19:
                ts = ts[:19]  # trim to YYYY-MM-DDTHH:MM:SS
            st = step_info.get('status', 'unknown')
            rid = step_info.get('run_id', '')
            st_col = GREEN if st == 'success' else RED
            manifest_data.append([
                Paragraph(step_name, styles['tbl_cell']),
                Paragraph(gen, styles['tbl_cell']),
                Paragraph(ts, styles['tbl_cell']),
                Paragraph(f'<b>{st}</b>',
                          ParagraphStyle('MFSt', parent=getSampleStyleSheet()['Normal'],
                                         fontSize=8, textColor=st_col,
                                         fontName='Helvetica-Bold')),
                Paragraph(rid, styles['tbl_cell']),
            ])
        mf_tbl = Table(manifest_data, colWidths=[30 * mm, 35 * mm, 38 * mm, 22 * mm, 43 * mm])
        mf_tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
        elems.append(mf_tbl)

    # ------------------------------------------------------------------
    # Staleness Assessment
    # ------------------------------------------------------------------
    elems.append(Spacer(1, 5 * mm))
    elems.append(Paragraph('Staleness Assessment', styles['h3']))

    try:
        from lineage.validation import validate_full_chain as _validate
        _val = _validate()
        if _val.get('is_consistent'):
            elems.append(Paragraph(
                '<b>All steps consistent</b> — no stale inputs detected.',
                ParagraphStyle('StaleOK', parent=getSampleStyleSheet()['Normal'],
                               fontSize=9, textColor=GREEN,
                               fontName='Helvetica-Bold')))
        else:
            stale_list = _val.get('stale_steps', [])
            missing_list = _val.get('missing_steps', [])
            detail_map = _val.get('details', {})

            if missing_list:
                elems.append(Paragraph(
                    f'<b>Missing steps</b> (never run): {", ".join(missing_list)}',
                    ParagraphStyle('StaleMiss', parent=getSampleStyleSheet()['Normal'],
                                   fontSize=9, textColor=AMBER,
                                   fontName='Helvetica-Bold')))
                elems.append(Spacer(1, 2 * mm))

            if stale_list:
                stale_data = [[
                    Paragraph('<b>Step</b>', styles['tbl_hdr']),
                    Paragraph('<b>Issue</b>', styles['tbl_hdr']),
                ]]
                for s in stale_list:
                    issues = detail_map.get(s, [])
                    issue_text = '; '.join(issues[:3])
                    if len(issue_text) > 150:
                        issue_text = issue_text[:150] + '...'
                    stale_data.append([
                        Paragraph(s, styles['tbl_cell']),
                        Paragraph(issue_text, styles['tbl_cell']),
                    ])
                stale_tbl = Table(stale_data, colWidths=[40 * mm, 128 * mm])
                stale_tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
                elems.append(stale_tbl)
    except ImportError:
        elems.append(Paragraph(
            'Lineage validation package not available — staleness check skipped.',
            styles['body']))
    except Exception as _exc:
        elems.append(Paragraph(
            f'Staleness check failed: {_exc}', styles['body']))

    # ------------------------------------------------------------------
    # Dependency Chain
    # ------------------------------------------------------------------
    if _manifest.get('steps'):
        elems.append(Spacer(1, 5 * mm))
        elems.append(Paragraph('Dependency Chain', styles['h3']))

        try:
            from lineage.manifest import DEPENDENCY_GRAPH as _DEP_GRAPH
        except ImportError:
            _DEP_GRAPH = _manifest.get('dependency_graph', {})

        if _DEP_GRAPH:
            chain_lines = []
            for step, deps in sorted(_DEP_GRAPH.items()):
                if deps:
                    chain_lines.append(
                        f'{", ".join(deps)} &rarr; <b>{step}</b>')
                else:
                    chain_lines.append(f'<b>{step}</b> (root)')
            elems.append(Paragraph(
                '<br/>'.join(chain_lines), styles['body']))
        else:
            elems.append(Paragraph(
                'Dependency graph not available.', styles['body']))

    return elems


def _build_e2e(styles) -> list:
    """Section 7: E2E Browser Tests (Playwright)."""
    elems = []
    elems.append(Paragraph('7. E2E Browser Tests', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph(
        'End-to-end browser tests exercising the full application stack via '
        'Playwright (headless Chromium). These tests verify that the UI loads, '
        'panels open, data renders, and user workflows complete successfully.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    data = _load_json_report('e2e_results.json')
    if not data:
        elems.append(Paragraph(
            'E2E test results not available — tests were not run or '
            'e2e_results.json is missing.', styles['body']))
        return elems

    status = data.get('status', 'UNKNOWN')
    reason = data.get('reason', '')
    total = data.get('total', 0)
    passed = data.get('passed', 0)
    failed = data.get('failed', 0)
    skipped_count = data.get('skipped', 0)

    if status == 'SKIPPED':
        elems.append(Paragraph(
            f'E2E tests were <b>skipped</b>: {reason}. '
            'Install Playwright to enable: pip install playwright && playwright install chromium',
            styles['body']))
        return elems

    if status == 'TIMEOUT':
        elems.append(Paragraph(
            f'E2E tests <b>timed out</b>: {reason}.',
            styles['body']))
        return elems

    if status == 'ERROR':
        elems.append(Paragraph(
            f'E2E tests encountered an <b>error</b>: {reason}.',
            styles['body']))
        return elems

    # Summary table
    pass_rate = (passed / total * 100) if total > 0 else 0
    pass_col = GREEN if pass_rate >= 99 else (AMBER if pass_rate >= 90 else RED)

    tbl_data = [
        [Paragraph('<b>Metric</b>', styles['tbl_hdr']),
         Paragraph('<b>Value</b>', styles['tbl_hdr']),
         Paragraph('<b>Status</b>', styles['tbl_hdr'])],
        [Paragraph('Total E2E tests', styles['tbl_cell']),
         Paragraph(f'<b>{total}</b>', styles['tbl_cell_r']),
         Paragraph('INFO', ParagraphStyle('E2I', parent=getSampleStyleSheet()['Normal'],
                                           fontSize=7.5, textColor=STEEL,
                                           fontName='Helvetica-Bold'))],
        [Paragraph('Passed', styles['tbl_cell']),
         Paragraph(f'<b>{passed}</b>', styles['tbl_cell_r']),
         Paragraph(_status(failed == 0, passed > 0),
                   ParagraphStyle('E2P', parent=getSampleStyleSheet()['Normal'],
                                   fontSize=7.5, textColor=GREEN if failed == 0 else AMBER,
                                   fontName='Helvetica-Bold'))],
        [Paragraph('Failed', styles['tbl_cell']),
         Paragraph(f'<b>{failed}</b>', styles['tbl_cell_r']),
         Paragraph(_status_inv(failed == 0, failed <= 3),
                   ParagraphStyle('E2F', parent=getSampleStyleSheet()['Normal'],
                                   fontSize=7.5, textColor=GREEN if failed == 0 else RED,
                                   fontName='Helvetica-Bold'))],
        [Paragraph('Skipped', styles['tbl_cell']),
         Paragraph(f'<b>{skipped_count}</b>', styles['tbl_cell_r']),
         Paragraph('INFO', ParagraphStyle('E2S', parent=getSampleStyleSheet()['Normal'],
                                           fontSize=7.5, textColor=STEEL,
                                           fontName='Helvetica-Bold'))],
        [Paragraph('Pass rate', styles['tbl_cell']),
         Paragraph(f'<b>{pass_rate:.1f}%</b>', styles['tbl_cell_r']),
         Paragraph(_status(pass_rate >= 99, pass_rate >= 90),
                   ParagraphStyle('E2R', parent=getSampleStyleSheet()['Normal'],
                                   fontSize=7.5, textColor=pass_col,
                                   fontName='Helvetica-Bold'))],
    ]
    tbl = Table(tbl_data, colWidths=[90 * mm, 40 * mm, 38 * mm])
    style_cmds = list(_TBL_STYLE_BASE)
    if failed > 0:
        style_cmds.append(('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#FFEBEE')))
    tbl.setStyle(TableStyle(style_cmds))
    elems.append(tbl)

    # Failure details
    failures = data.get('failures', [])
    if failures:
        elems.append(Spacer(1, 3 * mm))
        elems.append(Paragraph('Failed E2E Tests:', styles['h3']))
        fail_data = [[
            Paragraph('<b>Test</b>', styles['tbl_hdr']),
            Paragraph('<b>Error</b>', styles['tbl_hdr']),
        ]]
        for f in failures[:15]:
            name = f.get('name', 'unknown')
            msg = f.get('message', '')
            if len(msg) > 300:
                msg = msg[:300] + '...'
            fail_data.append([
                Paragraph(name, styles['tbl_cell']),
                Paragraph(msg, styles['tbl_cell']),
            ])
        fail_tbl = Table(fail_data, colWidths=[60 * mm, 108 * mm])
        fail_tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
        elems.append(fail_tbl)

    return elems


def _build_roadmap(junit: dict, cov: dict, styles) -> list:
    elems = []
    elems.append(Paragraph('8. Remediation Roadmap', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph(
        'Prioritised actions derived from this audit cycle. '
        'Items are ranked by risk impact under SR 11-7 / SS1/23.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    cov_pct = cov['line_rate'] * 100
    n_failed = junit['failed']

    actions = []
    if n_failed > 0:
        actions.append(('P1', 'CRITICAL',
                         f'Fix {n_failed} failing test(s)',
                         'Failing tests indicate broken or regressed functionality. '
                         'Address immediately before any release.'))
    if cov_pct < 80:
        actions.append(('P2', 'HIGH',
                         f'Increase line coverage from {cov_pct:.1f}% to ≥90%',
                         'Low coverage leaves model logic unverified. '
                         'Add targeted tests for uncovered packages first.'))
    elif cov_pct < 90:
        actions.append(('P2', 'MEDIUM',
                         f'Increase line coverage from {cov_pct:.1f}% to ≥90%',
                         'Close remaining gaps to meet the 90% governance target.'))
    else:
        actions.append(('P2', 'OK',
                         f'Maintain coverage at {cov_pct:.1f}%',
                         'Coverage meets or exceeds the 90% governance target. '
                         'Continue enforcing --cov-fail-under=90 in CI.'))

    # Data lineage check
    dl_road = _load_json_report('data_lineage_results.json')
    if dl_road and dl_road.get('failed', 0) > 0:
        dl_n = dl_road['failed']
        actions.append(('P1', 'CRITICAL',
                         f'Fix {dl_n} data lineage inconsistency(ies)',
                         'Pipeline data is inconsistent. Regenerate in order: '
                         'port --gauge → port --stressm → port --hazard → port --blotter'))

    # E2E check
    e2e_road = _load_json_report('e2e_results.json')
    if e2e_road and e2e_road.get('failed', 0) > 0:
        e2e_n = e2e_road['failed']
        actions.append(('P2', 'HIGH',
                         f'Fix {e2e_n} failing E2E browser test(s)',
                         'End-to-end tests detect UI regressions visible to users. '
                         'Review tests/e2e/ for details.'))

    actions += [
        ('P3', 'MEDIUM',
         'Migrate ALL_CAPS constants to config.py',
         'Distributed hard-coded parameters create recalibration risk. '
         'Run python -m docs.models.hardcoding for the full list.'),
        ('P4', 'MEDIUM',
         'Modularise files over 600 lines',
         'Large files are harder to test and review. '
         'See Section 4 for the current priority list.'),
        ('P5', 'LOW',
         'Review code duplication hotspots',
         'See code_duplication_report.pdf in data/output/audit/ '
         'for clone-pair details and refactoring recommendations.'),
        ('P6', 'LOW',
         'Run full audit before each model governance review',
         'Execute: python app.py test --audit to regenerate all artefacts.'),
    ]

    tbl_data = [[
        Paragraph('<b>Priority</b>', styles['tbl_hdr']),
        Paragraph('<b>Severity</b>', styles['tbl_hdr']),
        Paragraph('<b>Action</b>', styles['tbl_hdr']),
        Paragraph('<b>Detail</b>', styles['tbl_hdr']),
    ]]
    row_extras = []
    for i, (pri, sev, action, detail) in enumerate(actions, 1):
        sev_col = _status_colour(_map_sev(sev))
        tbl_data.append([
            Paragraph(f'<b>{pri}</b>', styles['tbl_cell']),
            Paragraph(f'<b>{sev}</b>',
                      ParagraphStyle('Sev', parent=getSampleStyleSheet()['Normal'],
                                     fontSize=8, textColor=sev_col,
                                     fontName='Helvetica-Bold')),
            Paragraph(action, styles['tbl_cell']),
            Paragraph(detail, styles['tbl_cell']),
        ])
        if sev == 'CRITICAL':
            row_extras.append(('BACKGROUND', (0, i), (-1, i),
                                colors.HexColor('#FFEBEE')))
        elif sev == 'HIGH':
            row_extras.append(('BACKGROUND', (0, i), (-1, i),
                                colors.HexColor('#FFF8E1')))

    tbl = Table(tbl_data, colWidths=[16 * mm, 20 * mm, 60 * mm, 72 * mm])
    tbl.setStyle(TableStyle(list(_TBL_STYLE_BASE) + row_extras))
    elems.append(tbl)

    elems.append(Spacer(1, 6 * mm))
    elems.append(HRFlowable(width='100%', thickness=0.5, color=GREY))
    elems.append(Spacer(1, 3 * mm))
    elems.append(Paragraph(
        'Supporting artefacts in data/output/audit/: '
        'test_report.pdf &nbsp;|&nbsp; '
        'large_file_report.pdf &nbsp;|&nbsp; large_test_report.txt &nbsp;|&nbsp; '
        'code_duplication_report.pdf &nbsp;|&nbsp; '
        'hardcoding_report.pdf &nbsp;|&nbsp; '
        'coverage/ (HTML) &nbsp;|&nbsp; '
        'junit.xml &nbsp;|&nbsp; coverage.xml',
        styles['small']))
    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(
        'Model Governance Reference: SR 11-7 (Federal Reserve), SS1/23 (PRA) — '
        'Model Risk Management. This report is produced automatically; '
        'human review is required before formal model approval.',
        styles['small']))

    return elems


# ---------------------------------------------------------------------------
# Status helpers
# ---------------------------------------------------------------------------

def _status(good: bool, ok: bool = True) -> str:
    if good:
        return 'OK'
    if ok:
        return 'REVIEW'
    return 'ACTION REQUIRED'


def _status_inv(good: bool, ok: bool = True) -> str:
    """For counts where 0 = good."""
    if good:
        return 'OK'
    if ok:
        return 'REVIEW'
    return 'ACTION REQUIRED'


def _status_colour(status: str) -> colors.Color:
    m = {'OK': GREEN, 'REVIEW': AMBER, 'ACTION REQUIRED': RED,
         'INFO': STEEL, 'CRITICAL': RED, 'HIGH': RED,
         'MEDIUM': AMBER, 'LOW': STEEL}
    return m.get(status, STEEL)


def _map_sev(sev: str) -> str:
    return {'CRITICAL': 'ACTION REQUIRED', 'HIGH': 'ACTION REQUIRED',
            'MEDIUM': 'REVIEW', 'LOW': 'INFO', 'OK': 'OK'}.get(sev, sev)


# ---------------------------------------------------------------------------
# Header/footer callback
# ---------------------------------------------------------------------------

def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    # Header bar
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 20 * mm, w, 20 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawString(20 * mm, h - 12 * mm, 'MKM Physical Risk Platform')
    canvas.setFont('Helvetica', 9)
    canvas.drawRightString(
        w - 20 * mm, h - 12 * mm,
        f'Full Audit Report  |  {datetime.now().strftime("%d %B %Y")}')
    # Footer
    canvas.setFillColor(STEEL)
    canvas.rect(0, 0, w, 8 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica', 7.5)
    canvas.drawString(
        20 * mm, 2.5 * mm,
        'CONFIDENTIAL — MKM Research Labs  |  SR 11-7 / SS1/23 Model Governance')
    canvas.drawRightString(
        w - 20 * mm, 2.5 * mm,
        f'Page {doc.page}')
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def create_pdf_report() -> Path:
    """Generate the full audit PDF and save to data/output/audit/."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    report_date = datetime.now()
    git_sha = _git_sha()

    print(' Parsing junit.xml …')
    junit = _parse_junit(AUDIT_DIR / 'junit.xml')

    print(' Parsing coverage.xml …')
    cov = _parse_coverage(AUDIT_DIR / 'coverage.xml')

    sty = _styles()

    story = []

    # Cover page
    story.extend(_build_cover(junit, cov, git_sha, report_date, sty))
    story.append(PageBreak())

    # Executive summary
    story.extend(_build_exec_summary(junit, cov, report_date, sty))
    story.append(PageBreak())

    # Test detail
    story.extend(_build_test_detail(junit, sty))
    story.append(PageBreak())

    # Coverage
    story.extend(_build_coverage(cov, sty))
    story.append(PageBreak())

    # Modularisation
    story.extend(_build_modularisation(sty))
    story.append(PageBreak())

    # Hard-coding audit
    story.extend(_build_hardcoding(sty))
    story.append(PageBreak())

    # Data lineage consistency
    story.extend(_build_data_lineage(sty))
    story.append(PageBreak())

    # E2E browser tests
    story.extend(_build_e2e(sty))
    story.append(PageBreak())

    # Roadmap
    story.extend(_build_roadmap(junit, cov, sty))

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=24 * mm,
        bottomMargin=14 * mm,
    )
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return OUTPUT_PDF


def main():
    print('Generating Full Audit Report …')
    out = create_pdf_report()
    size_kb = out.stat().st_size / 1024
    print(f' Written: {out}  ({size_kb:.1f} KB)')


if __name__ == '__main__':
    main()
