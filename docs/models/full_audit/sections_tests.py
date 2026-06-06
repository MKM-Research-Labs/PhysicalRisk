# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Test suite detail, coverage analysis, and modularisation sections."""

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from ._constants import NAVY, STEEL, GREEN, AMBER, RED, GREY, _root, _TBL_STYLE_BASE


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
