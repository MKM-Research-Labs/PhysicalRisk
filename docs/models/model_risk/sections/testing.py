# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Section 8: Test & Sensitivity Evidence."""

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table

from ..styles import GREEN, RED, section_rule, tbl_style


def build_test_evidence(data, story, S):
    story.append(Paragraph("8. Test &amp; Sensitivity Evidence", S['h2']))
    section_rule(story)

    junit = data['junit']
    coverage = data.get('coverage_pct')
    models = data['models']
    sens = data['sensitivity_generators']

    # Test summary
    story.append(Paragraph("Test Suite Results:", S['h3']))
    if junit['total'] > 0:
        test_data = [
            ['Metric', 'Value'],
            ['Total tests', str(junit['total'])],
            ['Passed', str(junit['passed'])],
            ['Failed', str(junit['failed'])],
            ['Errors', str(junit['errors'])],
            ['Skipped', str(junit['skipped'])],
            ['Duration', f"{junit['time_s']:.1f}s"],
        ]
        if coverage:
            test_data.append(['Line coverage', f"{coverage:.1f}%"])
        tbl = Table(test_data, colWidths=[2.0 * inch, 2.0 * inch])
        tbl.setStyle(tbl_style())
        story.append(tbl)
    else:
        story.append(Paragraph(
            "Test results not available. Run test --audit.", S['note']))

    # Per-model test coverage
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("Per-Model Test Coverage:", S['h3']))
    tc_data = [['Model', 'Unit', 'Integration', 'Benchmark', 'Test File']]
    for m in models:
        tc = m.get('test_coverage', {})
        if not tc:
            continue
        tc_data.append([
            m.get('model_id', ''),
            '\u2713' if tc.get('unit_tests') else '\u2717',
            '\u2713' if tc.get('integration_tests') else '\u2717',
            '\u2713' if tc.get('benchmark_tests') else '\u2717',
            (tc.get('test_file', '') or '')[-35:],
        ])
    if len(tc_data) > 1:
        tbl = Table(tc_data,
                    colWidths=[0.95 * inch, 0.5 * inch, 0.75 * inch,
                               0.7 * inch, 2.5 * inch])
        ts = tbl_style()
        for ri in range(1, len(tc_data)):
            for ci in range(1, 4):
                cell_val = tc_data[ri][ci]
                col = GREEN if cell_val == '\u2713' else RED
                ts.add('TEXTCOLOR', (ci, ri), (ci, ri), col)
                ts.add('ALIGN', (ci, ri), (ci, ri), 'CENTER')
        tbl.setStyle(ts)
        story.append(tbl)

    # Sensitivity generators
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        f"Sensitivity Analysis ({len(sens)} generators):", S['h3']))
    if sens:
        for g in sens:
            story.append(Paragraph(f"&bull; {g}", S['note']))
    else:
        story.append(Paragraph("No sensitivity generators found.", S['note']))
