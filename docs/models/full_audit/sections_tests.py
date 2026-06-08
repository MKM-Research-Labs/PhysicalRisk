# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Test suite detail, coverage analysis, and modularisation sections."""

from xml.sax.saxutils import escape as _xml_escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from ._constants import NAVY, STEEL, GREEN, AMBER, RED, GREY, _root, _TBL_STYLE_BASE
from .helpers import _load_json_report


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

    # 2.1 — individual unit-test failures
    elems.extend(_build_unit_failures(styles))

    return elems


def _short_msg(longrepr: str) -> str:
    """Pull a concise one-line message from a pytest longrepr blob.

    The last non-empty line of a pytest traceback is usually the assertion or
    error (e.g. ``AssertionError: ...``), which is the most useful summary.
    """
    if not longrepr:
        return '—'
    lines = [ln.strip() for ln in longrepr.splitlines() if ln.strip()]
    if not lines:
        return '—'
    msg = lines[-1]
    return msg[:160] + ('…' if len(msg) > 160 else '')


def _build_unit_failures(styles) -> list:
    """Subsection 2.1: list the individual failing unit tests, sourced from
    test_failures_report.json (written by ``app.py test --unit``). Section 2's
    table only gives per-package counts — this names the actual failures."""
    elems = []
    elems.append(Spacer(1, 5 * mm))
    elems.append(Paragraph('2.1 Failed Unit Tests', styles['h3']))
    elems.append(Spacer(1, 2 * mm))

    report = _load_json_report('test_failures_report.json')
    if not report:
        elems.append(Paragraph(
            'test_failures_report.json not found — run '
            '<b>python app.py test --unit</b> to generate it.', styles['body']))
        return elems

    summary = report.get('summary', {})
    failures = report.get('failures', [])
    total = summary.get('total', 0)
    failed = summary.get('failed', len(failures))

    if not failures:
        elems.append(Paragraph(
            f'All <b>{total:,}</b> unit tests passed — <b>0 failures</b>. '
            '<b>PASS</b>', styles['body']))
        return elems

    elems.append(Paragraph(
        f'<b>{failed}</b> of {total:,} unit tests failed (showing up to 60):',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    data = [[
        Paragraph('<b>Test</b>', styles['tbl_hdr']),
        Paragraph('<b>File</b>', styles['tbl_hdr']),
        Paragraph('<b>Message</b>', styles['tbl_hdr']),
    ]]
    for f in failures[:60]:
        fpath = f.get('file', '') or f.get('class', '')
        data.append([
            Paragraph(_xml_escape(f.get('name', '')), styles['tbl_cell']),
            Paragraph(_xml_escape(fpath), styles['tbl_cell']),
            Paragraph(_xml_escape(_short_msg(f.get('longrepr', ''))), styles['tbl_cell']),
        ])
    tbl = Table(data, colWidths=[50 * mm, 53 * mm, 65 * mm])
    tbl.setStyle(TableStyle(list(_TBL_STYLE_BASE) + [
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFEBEE')),
    ]))
    elems.append(tbl)

    if len(failures) > 60:
        elems.append(Spacer(1, 2 * mm))
        elems.append(Paragraph(
            f'… and {len(failures) - 60} more. See '
            '<b>test_failures_report.json</b> for the full list.', styles['body']))
    return elems


def _build_coverage(cov: dict, styles) -> list:
    elems = []
    elems.append(Paragraph('3. Code Coverage Analysis', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 3 * mm))

    all_pkg_rows = cov['by_package']
    if not all_pkg_rows:
        cov_pct = cov['line_rate'] * 100
        elems.append(Paragraph(
            f'Overall line coverage: <b>{cov_pct:.2f}%</b> '
            f'({cov["lines_covered"]:,} of {cov["lines_valid"]:,} lines).',
            styles['body']))
        elems.append(Spacer(1, 2 * mm))
        elems.append(Paragraph('No per-package coverage data available.', styles['body']))
        return elems

    full_cov_count = sum(1 for _, r, _, _ in all_pkg_rows if r >= 100)
    cov_pct = cov['line_rate'] * 100
    elems.append(Paragraph(
        f'Overall line coverage: <b>{cov_pct:.2f}%</b> '
        f'({cov["lines_covered"]:,} of {cov["lines_valid"]:,} lines). '
        'Packages are sorted by coverage rate ascending — lowest coverage first. '
        f'{full_cov_count} package(s) with 100% coverage are omitted.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    pkg_rows = all_pkg_rows

    # Exclude packages with 100% coverage — only show those needing attention
    pkg_rows = [(n, r, v, c) for n, r, v, c in pkg_rows if r < 100]
    if not pkg_rows:
        elems.append(Paragraph(
            'All packages have 100% line coverage.', styles['body']))
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
        from docs.models.project import analyze_repo_files
        all_files, large_files = analyze_repo_files(_root)
    except Exception as exc:
        elems.append(Paragraph(
            f'Could not run modularisation scan: {exc}', styles['body']))
        return elems

    total_files = len(all_files)
    total_large = len(large_files)

    elems.append(Paragraph(
        f'Scope: <b>all non-test source</b> (src/, app/, config/, tools/, docs/) '
        f'&nbsp;|&nbsp; Files scanned: <b>{total_files}</b> &nbsp;|&nbsp; '
        f'Files over 300 lines: <b>{total_large}</b>. '
        'Files exceeding 300 raw lines are candidates for modularisation.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    if not large_files:
        elems.append(Paragraph(
            'No files exceed the 300-line threshold.', styles['body']))
    else:
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

    # 4.1 — __init__.py substantive-code audit
    elems.extend(_build_init_audit(styles))

    return elems


def _build_init_audit(styles) -> list:
    """Subsection 4.1: flag __init__.py files that contain functions, classes,
    or route decorators — substantive code that should live in a dedicated
    module, not in a package initialiser."""
    elems = []
    elems.append(Spacer(1, 5 * mm))
    elems.append(Paragraph('4.1 __init__.py Substantive-Code Audit', styles['h3']))
    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(
        'Policy: <b>__init__.py</b> files must only wire a package together — '
        'imports, re-exports, <b>__all__</b>, and Blueprint assignment. Any '
        'function, class, or route/view decorator defined directly in an '
        'initialiser should be moved to a dedicated module.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    try:
        from docs.models.project import analyze_init_files
        issues = analyze_init_files(_root / 'src')
    except Exception as exc:
        elems.append(Paragraph(
            f'Could not run __init__.py audit: {exc}', styles['body']))
        return elems

    if not issues:
        elems.append(Paragraph(
            'No __init__.py file contains substantive code. '
            '<b>PASS</b>', styles['body']))
        return elems

    elems.append(Paragraph(
        f'{len(issues)} __init__.py file(s) contain substantive code '
        f'(showing up to 25):', styles['body']))
    elems.append(Spacer(1, 2 * mm))

    data = [[
        Paragraph('<b>File (relative to src/)</b>', styles['tbl_hdr']),
        Paragraph('<b>Lines</b>', styles['tbl_hdr']),
        Paragraph('<b>Functions</b>', styles['tbl_hdr']),
        Paragraph('<b>Classes</b>', styles['tbl_hdr']),
        Paragraph('<b>Routes</b>', styles['tbl_hdr']),
    ]]
    for it in issues[:25]:
        rel = it.relative_path
        if len(rel) > 60:
            rel = '…' + rel[-58:]
        data.append([
            Paragraph(rel, styles['tbl_cell']),
            Paragraph(str(it.line_count), styles['tbl_cell_r']),
            Paragraph(str(len(it.functions)), styles['tbl_cell_r']),
            Paragraph(str(len(it.classes)), styles['tbl_cell_r']),
            Paragraph(str(it.routes), styles['tbl_cell_r']),
        ])
    tbl = Table(data, colWidths=[96 * mm, 16 * mm, 22 * mm, 18 * mm, 16 * mm])
    tbl.setStyle(TableStyle(list(_TBL_STYLE_BASE) + [
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF3E0')),
    ]))
    elems.append(tbl)

    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(
        'Full breakdown (with function/class names per file) in the standalone '
        '<b>init_audit_report.pdf</b> / <b>init_audit_results.json</b> under '
        'data/output/audit/.', styles['body']))

    return elems
